"""Original stereo ringtone, soft lo-fi and synchronized comedy effects."""
from pathlib import Path
import numpy as np,wave,json
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP006_Call_Vs_Text'
for p in ['audio','edit']:(EP/p).mkdir(parents=True,exist_ok=True)
SR=48000;N=18*SR;rng=np.random.default_rng(606);audio=np.zeros((N,2))
def add(at,s,g=1,side=0):
    i=round(at*SR);n=min(len(s),N-i)
    if n<=0:return
    gains=(1,.12) if side<0 else (.12,1) if side>0 else (.7,.7)
    audio[i:i+n]+=np.asarray(s[:n])[:,None]*g*np.array(gains)
def tone(freq,duration):
    t=np.arange(round(duration*SR))/SR
    return np.sin(2*np.pi*freq*t)*np.minimum(t/.005,1)*np.minimum((duration-t)/.02,1)
# Original sparse minor-ninth progression; gentle, mostly in the right channel.
beat=60/76;chords=[[130.8128,155.5635,195.9977,233.0819,293.6648],[174.6141,207.6523,261.6256,311.1270,391.9954]]
for bar in range(6):
    at=1+bar*4*beat
    if at>=18:break
    for j,f in enumerate(chords[bar%2]):
        t=np.arange(round(2.6*SR))/SR
        snd=(np.sin(2*np.pi*f*t)+.25*np.sin(2*np.pi*2*f*t)+.07*np.sin(2*np.pi*3*f*t))*np.minimum(t/.035,1)*np.exp(-1.8*t)
        add(at+j*.027,snd,.0075,1)
    for b in range(4):
        start=at+b*beat
        if start>=18:continue
        t=np.arange(round(.25*SR))/SR
        if b%2==0:
            kick=np.sin(2*np.pi*np.cumsum(48+75*np.exp(-35*t))/SR)*np.exp(-22*t)*np.minimum(t/.003,1)
            add(start,kick,.035,1)
        else:
            noise=rng.normal(size=len(t));soft=np.convolve(noise,np.ones(17)/17,mode='same')
            add(start,soft*np.exp(-24*t)*np.minimum(t/.002,1),.036,1)
        add(start+.5*beat,rng.normal(size=2400)*np.exp(-np.arange(2400)/(SR*.012)),.006,1)
# Fade in from 1s and completely out by 18s.
t=np.arange(N)/SR;audio*=np.minimum(np.maximum((t-1)/.7,0),1)[:,None]*np.minimum(np.maximum((18-t)/3,0),1)[:,None]
# Dead air at the start and clear left/right contrast after the notification.
rings=[];at=3
while at<7.7:
    rings.append(round(at,5));duration=min(.43,8-at);q=np.arange(round(duration*SR))/SR
    gate=((q<.16)|((q>.235)&(q<.395))).astype(float)
    env=np.minimum(q/.004,1)*np.minimum((duration-q)/.012,1)
    ring=(np.sin(2*np.pi*940*q)+.65*np.sin(2*np.pi*1160*q))*.5*gate*env
    buzz=np.sin(2*np.pi*83*q)+.25*np.sin(2*np.pi*166*q)
    add(at,ring,.19,-1);add(at,buzz*env,.022,-1)
    at+=.96 if at<5.6 else .65
# Exact cushion contact at six seconds: low, heavily muffled thud.
q=np.arange(round(.32*SR))/SR;noise=rng.normal(size=len(q));noise=np.convolve(noise,np.ones(95)/95,mode='same')
add(6,(np.sin(2*np.pi*82*q)*.45+noise)*np.exp(-19*q)*np.minimum(q/.002,1),.25,-1)
taps=[4.0,4.24,4.51,4.94,5.18,5.45,5.98,6.22,6.53,6.83]
for at in taps:
    q=np.arange(1500)/SR;tap=rng.normal(size=len(q));tap-=np.convolve(tap,np.ones(15)/15,mode='same')
    add(at,tap*np.exp(-160*q)*np.minimum(q/.001,1),.030,1)
q=np.arange(round(.36*SR))/SR
whoosh=rng.normal(size=len(q));whoosh=np.convolve(whoosh,np.ones(13)/13,mode='same')
whoosh+=.20*np.sin(2*np.pi*np.cumsum(650+2100*q)/SR)
add(9,whoosh*np.sin(np.pi*q/.36)**2*np.exp(-3*q),.09,1)
audio[:SR]=0;audio[-2048:]=0
peak=np.max(np.abs(audio));audio*=min(1,.89125/peak)
out=EP/'audio/EP006_Original_Call_Text_48k.wav'
with wave.open(str(out),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes((audio*32767).astype('<i2').tobytes())
(EP/'edit/audio_cue_sheet.json').write_text(json.dumps({'original_synthesis':True,'duration':18,'rate':SR,'silent_start':[0,1],'ringtone_starts':rings,'ringtone_cuts_at':8,'cushion_thud':6,'typing':taps,'message_sent':9,'lofi_fade_out':[15,18],'final_silence_samples':2048,'stereo':'Call left / relaxed text and lo-fi right'},indent=2))
print('EP006_AUDIO_COMPLETE',out)
