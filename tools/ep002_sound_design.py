import numpy as np,wave,json
from pathlib import Path
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP002_Impossible_Blankets');sr=48000;duration=37.5;out=np.zeros((int(sr*duration),2),dtype=np.float64);rng=np.random.default_rng(2002)
def filtered_noise(n,cut=1000):
    x=rng.normal(0,1,n);fft=np.fft.rfft(x);hz=np.fft.rfftfreq(n,1/sr);fft*=1/(1+(hz/cut)**4);y=np.fft.irfft(fft,n);return y/(np.std(y)+1e-9)
def add(t,x,g=.2,pan=0):
    a=int(t*sr);b=min(len(out),a+len(x));x=x[:b-a]*g;out[a:b,0]+=x*np.sqrt((1-pan)/2);out[a:b,1]+=x*np.sqrt((1+pan)/2)
def pulse(t,freq,seconds,g,pan=0):
    n=int(seconds*sr);tt=np.arange(n)/sr;add(t,np.sin(2*np.pi*(freq*tt-.15*freq*tt**2))*np.exp(-tt*9/seconds),g,pan)
for t in [1.5,6,10.5,15,19.5,24,28.5]:pulse(t,950,.07,.075)
for release,impact in [(2.8,3.35),(7.366,7.84),(11.233,11.8),(16.4,16.95),(20.933,21.47),(24.8,25.35),(31.266,31.58)]:
    n=int((impact-release)*sr);u=np.linspace(0,1,n);add(release,filtered_noise(n,1600)*np.sin(np.pi*u)**2,.07)
# Slime elastic impact, wet pops and a decaying resonant wobble.
pulse(3.35,95,.4,.24);n=int(sr*.9);tt=np.arange(n)/sr;add(3.35,filtered_noise(n,550)*np.exp(-tt*5)*(1+.4*np.sin(tt*45)),.14)
for t in [3.55,3.82,4.14]:pulse(t,280,.1,.035)
# Small tempered-glass ticks, separate fragment pings and landing sounds.
for i in range(12):
    t=7.84+i*.012;pulse(t,2100+i*147,.25,.028,(i/11-.5)*.8);pulse(t+.035,4400-i*110,.14,.012)
add(7.84,filtered_noise(int(sr*.15),6500)*np.exp(-np.arange(int(sr*.15))/sr*32),.16)
for t in [8.15,8.28,8.48]:pulse(t,1700,.12,.025)
# Soft textile landing and slow weave rustle.
for t,d,g in [(11.8,.26,.095),(12.07,.48,.025),(13.12,.5,.016)]:
    n=int(sr*d);u=np.linspace(0,1,n);add(t,filtered_noise(n,1200)*np.sin(np.pi*u)**2,g)
# Honey sticky wet contact, occasional slow drips.
pulse(16.95,135,.35,.14);add(16.95,filtered_noise(int(sr*.6),480)*np.exp(-np.arange(int(sr*.6))/sr*7),.09)
for t in [17.36,17.9,18.47]:pulse(t,380,.1,.04)
# Granular impact and the rolling, fading grain shower.
n=int(sr*1.5);tt=np.arange(n)/sr;env=np.exp(-tt*2.4)*(1+.25*np.sin(tt*33));add(21.47,filtered_noise(n,5000)*env,.16)
for t in np.linspace(21.52,22.8,45):pulse(float(t)+rng.uniform(0,.018),rng.uniform(1800,3400),.028,.007,rng.uniform(-.7,.7))
# Water splash, trickles and drops.
n=int(sr*1.4);tt=np.arange(n)/sr;add(25.35,filtered_noise(n,3100)*np.exp(-tt*3.2),.25)
for t in [25.58,25.85,26.08,26.43,26.9]:pulse(t,rng.uniform(550,950),.12,.05,rng.uniform(-.4,.4))
# Shield mechanism, locked chime, viscous lava thud and gentle hot-surface hiss.
add(30.07,filtered_noise(int(sr*.64),1500)*np.sin(np.linspace(0,np.pi,int(sr*.64))),.065);pulse(30.73,1200,.1,.075);pulse(30.73,1800,.12,.055);pulse(31.58,70,.55,.22)
n=int(sr*2.4);tt=np.arange(n)/sr;add(31.60,filtered_noise(n,2800)*np.exp(-tt*1.15),.055)
# A restrained original outro sting leaves room for BRIX's final reaction.
for t,f in [(35.5,330),(35.68,440),(35.86,660)]:pulse(t,f,.4,.04)
peak=np.max(np.abs(out));out*=.88/max(.88,peak);fade=int(sr*.12);out[:fade]*=np.linspace(0,1,fade)[:,None];out[-fade:]*=np.linspace(1,0,fade)[:,None];pcm=(np.clip(out,-1,1)*32767).astype('<i2')
path=EP/'audio/EP002_Original_Material_SoundDesign_v002.wav'
with wave.open(str(path),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm.tobytes())
(EP/'edit/audio_report_v002.json').write_text(json.dumps({'source':'Original procedural material sound design; no sampled third-party audio.','sample_rate':sr,'channels':2,'duration':duration,'file':str(path),'peak_dbfs':float(20*np.log10(np.max(np.abs(out))))},indent=2));print('ORIGINAL_AUDIO_COMPLETE')
