"""Original audio, no downloaded samples: quiet room / metal hinge / absurd engine."""
import numpy as np, wave, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP003_Gaming_Laptop_GP'
(EP/'audio').mkdir(parents=True,exist_ok=True);(EP/'edit').mkdir(exist_ok=True)
SR=48000;duration=11;t=np.arange(SR*duration)/SR;rng=np.random.default_rng(303)
noise=rng.normal(0,1,len(t));spectrum=np.fft.rfft(noise);freq=np.fft.rfftfreq(len(t),1/SR)
def band(lo,hi):
    a=np.fft.irfft(spectrum*((freq>=lo)&(freq<=hi)),len(t));return a/np.std(a)
air=band(700,6500);low=band(80,900);metal=band(1600,7500)
L=air*.00085;R=np.roll(air,333)*.00085
def envelope(a,b,fade=.025):return np.minimum(np.clip((t-a)/fade,0,1),np.clip((b-t)/fade,0,1))
def add(signal,env,gain=1,pan=0):
    global L,R
    L+=signal*env*gain*(1-pan*.25);R+=signal*env*gain*(1+pan*.25)
hinge_env=envelope(.14,2.98,.065)
hinge_env*=.66+.2*np.sin(t*12)+.14*np.sin(t*31)
hz=440+190*t+95*np.sin(2*np.pi*t*2.9)+32*np.sin(t*43)
phase=2*np.pi*np.cumsum(hz)/SR
squeak=np.sin(phase)+.31*np.sin(2.01*phase)+.13*np.sin(3.07*phase)+.045*metal
add(squeak,hinge_env,.25,-.2)
# Reaction whine spikes, then clean quiet from 3 to 5 seconds.
whine_phase=2*np.pi*np.cumsum(1350+np.clip(t-2,0,1)*620)/SR
add(np.sin(whine_phase)+.10*np.sin(whine_phase*2),envelope(2.16,2.95,.035),.105,.12)
# Soft contact click establishes the beat before the engine punchline.
add(low,envelope(4.72,4.8,.008),.017,-.2)
engine_envelope=np.zeros_like(t);rpm=np.zeros_like(t)+65
for a,b,start,end in [(5.00,5.52,28,92),(5.64,6.02,30,103),(6.12,6.64,37,133)]:
    e=envelope(a,b,.024);engine_envelope+=e*(.75+.25*np.sin(t*63)**2)
    q=np.clip((t-a)/(b-a),0,1);rpm+=e*(start+(end-start)*q-65)
catch=envelope(6.65,11,.025);engine_envelope+=catch
rpm+=catch*(48+26*np.sin(t*1.9)+8*np.sin(t*14))
p=2*np.pi*np.cumsum(rpm)/SR
engine=np.zeros_like(t)
for harmonic in range(1,17):engine+=(1/harmonic**.8)*np.sin(harmonic*p+.16*harmonic)
engine=np.tanh(engine*1.8)
pulses=(.30+.70*np.clip(np.cos(p*.5),0,1)**3)
engine=.54*engine+.21*low*pulses+.10*air*(.5+.5*np.sin(p)**2)
add(engine,engine_envelope,.75,-.18)
# Pull-start rasp and gritty ignition impulses.
for at in [5.00,5.64,6.12]:add(metal,envelope(at,at+.12,.014),.12,-.2)
for at in [5.46,5.93,6.58]:add(low*np.exp(-np.maximum(0,t-at)*34),envelope(at,at+.10,.006),.22,-.2)
# Short room reflections remain below the direct engine and never obscure the quiet beat.
directL=L.copy();directR=R.copy()
for delay,gain in [(int(.055*SR),.08),(int(.107*SR),.045)]:
    L[delay:]+=directR[:-delay]*gain;R[delay:]+=directL[:-delay]*gain
fade=np.clip((11-t)/.06,0,1);audio=np.column_stack([L,R])*fade[:,None]
peak=float(np.abs(audio).max());audio*=.89/max(peak,.89)
pcm=(np.clip(audio,-1,1)*32767).astype('<i2');path=EP/'audio/EP003_Original_Laptop_SoundDesign_v001.wav'
with wave.open(str(path),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
report={'original_synthesized':True,'sample_rate':SR,'channels':2,'duration_seconds':duration,'peak_dbfs':float(20*np.log10(np.abs(audio).max())),'quiet_3_to_5_rms':float(np.sqrt(np.mean(audio[int(3.1*SR):int(4.6*SR)]**2))),'engine_7_to_10_rms':float(np.sqrt(np.mean(audio[int(7*SR):int(10*SR)]**2))),'cues':[{'time':.14,'cue':'metal hinge'},{'time':2.16,'cue':'reaction whine'},{'time':3,'cue':'quiet beat'},{'time':5,'cue':'engine pull-start'},{'time':6.65,'cue':'roaring engine idle'}]}
(EP/'edit/audio_report.json').write_text(json.dumps(report,indent=2));print('ORIGINAL_SOUND_COMPLETE',str(path))
