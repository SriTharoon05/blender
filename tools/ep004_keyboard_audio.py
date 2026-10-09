import numpy as np,wave,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP004_Dad_Mechanical_Keyboard'
for f in ['audio','edit']:(EP/f).mkdir(parents=True,exist_ok=True)
SR=48000;t=np.arange(10*SR)/SR;rng=np.random.default_rng(404);noise=rng.normal(size=len(t));spectrum=np.fft.rfft(noise);freq=np.fft.rfftfreq(len(t),1/SR)
def band(a,b):
    x=np.fft.irfft(spectrum*((freq>a)&(freq<b)),len(t));return x/np.std(x)
crack=band(1200,15000);rumble=band(30,300);rattle=band(2100,9500)
audio=np.column_stack([.0007*np.sin(t*2*np.pi*50)+noise*.0003,.0007*np.sin(t*2*np.pi*50+.18)+np.roll(noise,97)*.0003])
def add(sig,pan=0):
    audio[:,0]+=sig*(1-pan*.2);audio[:,1]+=sig*(1+pan*.2)
def blast(at,gain=1):
    q=t-at;valid=(q>=0)&(q<.65);u=np.maximum(q,0)
    attack=np.clip(u/.0009,0,1)
    transient=crack*np.exp(-u*80)*.45
    boom=np.sin(2*np.pi*(42*u+9*(1-np.exp(-u*12))))*np.exp(-u*11)*.62
    body=rumble*np.exp(-u*17)*.19
    return (transient+boom+body)*valid*attack*gain
def anvil(at,gain=1):
    q=t-at;u=np.maximum(q,0);valid=(q>=0)&(q<.65);sig=np.zeros_like(t)
    for hz,amp,decay in [(237,.24,7),(421,.21,9),(637,.14,10),(1131,.13,12),(1789,.11,15),(2933,.08,17)]:sig+=amp*np.sin(2*np.pi*hz*u)*np.exp(-u*decay)
    sig+=.42*np.sin(2*np.pi*54*u)*np.exp(-u*20)+.18*crack*np.exp(-u*100)
    return sig*valid*np.clip(u/.0008,0,1)*gain
add(blast(4,.76),-.1);add(anvil(5.5,.79),.1);add(blast(6.5,.94),-.1)
add(blast(7.5,.83)+anvil(7.5,.78),0)
for at in [4,5.5,6.5,7.5]:
    for delay,g in [(.04,.055),(.10,.037),(.18,.018)]:
        q=t-at-delay;u=np.maximum(q,0);add(rattle*np.exp(-u*70)*(q>=0)*(q<.12)*g,.6)
# Abrupt near-silence at 8.15 seconds; retain only the tiny ambient hum afterwards.
mask=t>=8.15;audio[mask]=np.column_stack([.0007*np.sin(t[mask]*2*np.pi*50),.0007*np.sin(t[mask]*2*np.pi*50+.18)])
peak=np.abs(audio).max();audio*=.89/max(.89,peak);pcm=(audio*32767).astype('<i2')
p=EP/'audio/EP004_Original_Keyboard_Impacts_v001.wav'
with wave.open(str(p),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
(EP/'edit/audio_timing.json').write_text(json.dumps({'original_synthesis':True,'sample_rate':SR,'duration_seconds':10,'peak_dbfs':float(20*np.log10(np.abs(audio).max())),'hits':[{'seconds':4,'frame':97,'type':'shotgun-like comic blast'},{'seconds':5.5,'frame':133,'type':'anvil clang'},{'seconds':6.5,'frame':157,'type':'louder comic blast'},{'seconds':7.5,'frame':181,'type':'combined boom-clang'}],'abrupt_quiet_seconds':8.15},indent=2))
paths=[p for top in ['00_LIBRARY','01_TEMPLATES','02_EPISODES/EP001_Material_Test','02_EPISODES/EP002_Impossible_Blankets/blend','02_EPISODES/EP003_Gaming_Laptop_GP/blend'] for p in (ROOT/top).rglob('*.blend')]
(EP/'edit/protected_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
print('EP004_ORIGINAL_AUDIO_READY',flush=True)
