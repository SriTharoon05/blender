"""Original, sample-accurate sound design for the checkout short."""
from pathlib import Path
import numpy as np
import wave,json
ROOT=Path(__file__).resolve().parent.parent
EP=ROOT/'02_EPISODES/EP005_Lost_Mom_Checkout'
for p in ['audio','edit']:(EP/p).mkdir(parents=True,exist_ok=True)
SR=48000;N=22*SR;rng=np.random.default_rng(405);mix=np.zeros((N,2),dtype=np.float64)
def add(t,s,g=1,pan=0):
    i=round(t*SR);n=min(len(s),N-i)
    mix[i:i+n,0]+=s[:n]*g*(1-.25*pan);mix[i:i+n,1]+=s[:n]*g*(1+.25*pan)
def beep(duration=.15,f=1000):
    t=np.arange(round(duration*SR))/SR
    env=np.minimum(t/.006,1)*np.minimum((duration-t)/.018,1)
    return np.sin(2*np.pi*f*t)*env
# Quiet air-conditioning and indistinct, synthesized store murmur; exact cut at six seconds.
t=np.arange(6*SR)/SR
noise=rng.normal(size=len(t));murmur=np.convolve(noise,np.ones(180)/180,mode='same')
amb=.0018*np.sin(2*np.pi*60*t)+.003*murmur+.0008*np.sin(2*np.pi*121*t)
amb*=np.minimum(t/.3,1)
add(0,amb)
for start in [3,4.125]:
    add(start,beep(.11,1550),.17,.3);add(start+.13,beep(.12,1120),.13,.3)
beats=[];at=6
while at<13.94:
    k=min(1,(at-6)/7);beats.append(round(at,5))
    add(at,beep(min(.065,14-at),920),.045+.15*k,-.1)
    at+=.92*(1-k)+.145*k
# Intentionally no ambience, tails or heartbeat in [14,16).
mix[14*SR:16*SR]=0
def awooga(duration):
    t=np.arange(round(duration*SR))/SR
    # Mechanical klaxon spin-up, a rounded vowel bend, then a falling horn.
    freq=82+78*np.minimum(t/.19,1)-27*np.clip((t-.45)/(duration-.45),0,1)
    freq*=1+.018*np.sin(2*np.pi*19*t)
    phase=2*np.pi*np.cumsum(freq)/SR
    out=np.zeros_like(t)
    vowel=np.clip((t-.23)/.35,0,1)
    for h in range(1,24):
        hz=h*freq
        form1=540*(1-vowel)+330*vowel;form2=1140*(1-vowel)+780*vowel
        weights=.10/h+np.exp(-((hz-form1)/170)**2)*.22+np.exp(-((hz-form2)/230)**2)*.10
        out+=np.sin(h*phase)*weights
    env=np.minimum(t/.035,1)*np.minimum((duration-t)/.28,1)
    env*=.88+.12*np.sin(2*np.pi*6*t)
    return out*env
add(16,awooga(1.7),.46,-.08);add(18,awooga(2.8),.49,.08)
t=np.arange(round(.6*SR))/SR;phase=2*np.pi*np.cumsum(260*np.exp(-4*t)+70)/SR
add(20,np.sin(phase)*np.exp(-8*t)*np.minimum(t/.012,1),.17)
peak=np.max(np.abs(mix));mix*=min(1,.89125/peak)
pcm=(np.clip(mix,-1,1)*32767).astype('<i2')
wav=EP/'audio/EP005_Checkout_Original_Sound_48k.wav'
with wave.open(str(wav),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes(pcm.tobytes())
assert np.max(np.abs(mix[14*SR:16*SR]))==0
(EP/'edit/audio_cue_sheet.json').write_text(json.dumps({'sample_rate':SR,'duration':22,'scanner':[3,4.125],'heartbeat_beeps':beats,'digital_silence':[14,16],'awooga':[16,18],'boing':20,'alarm_ends':20.8,'peak_dbfs':float(20*np.log10(np.max(np.abs(mix)))),'source':'Original synthesis; no licensed samples'},indent=2))
print('EP005_AUDIO_COMPLETE',wav)

