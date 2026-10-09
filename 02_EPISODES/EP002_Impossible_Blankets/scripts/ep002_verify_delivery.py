import json,hashlib,struct
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender'); EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets'
hashes=json.loads((EP/'edit/protected_hashes.json').read_text()); changed=[p for p,h in hashes.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]; assert not changed,changed
report={'protected_files_checked':len(hashes),'protected_files_unchanged':True}
movie=EP/'previews/EP002_Review_v009.mp4'
if movie.exists():
    data=movie.read_bytes()
    def boxes(a,b):
        while a+8<=b:
            size,kind=struct.unpack_from('>I4s',data,a); h=8
            if size==1:size=struct.unpack_from('>Q',data,a+8)[0];h=16
            if size==0:size=b-a
            if size<h or a+size>b:break
            yield kind,a+h,a+size
            a+=size
    for kind,a,b in boxes(0,len(data)):
        if kind==b'moov':
            for k,x,y in boxes(a,b):
                if k==b'mvhd':
                    version=data[x]; off=x+(20 if version==1 else 12); rate=struct.unpack_from('>I',data,off)[0]; dur=struct.unpack_from('>Q' if version==1 else '>I',data,off+4)[0];report['movie_duration_seconds']=dur/rate
                if k==b'trak':
                    for t,u,v in boxes(x,y):
                        if t==b'tkhd':report['movie_resolution']=[int(n/65536) for n in struct.unpack_from('>2I',data,v-8)]
    report['movie_bytes']=len(data)
    assert report['movie_resolution']==[324,576],report
    assert 37.4<=report['movie_duration_seconds']<=37.8,report
(EP/'edit/delivery_verification.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))
