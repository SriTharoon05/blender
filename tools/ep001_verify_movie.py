import struct,json,hashlib
from pathlib import Path
EP=Path(__file__).resolve().parent.parent/'02_EPISODES/EP001_Material_Test'; path=EP/'previews/EP001_Review_v009.mp4'; data=path.read_bytes()
def boxes(start,end):
    pos=start
    while pos+8<=end:
        size,kind=struct.unpack_from('>I4s',data,pos); header=8
        if size==1:size=struct.unpack_from('>Q',data,pos+8)[0];header=16
        if size==0:size=end-pos
        if size<header or pos+size>end:break
        yield kind,pos+header,pos+size
        pos+=size
report={'file':str(path),'bytes':len(data)}
for kind,a,b in boxes(0,len(data)):
    if kind==b'moov':
        for k,x,y in boxes(a,b):
            if k==b'mvhd':
                version=data[x]; offset=x+(20 if version==1 else 12); timescale=struct.unpack_from('>I',data,offset)[0]; duration=struct.unpack_from('>Q' if version==1 else '>I',data,offset+4)[0]; report['duration_seconds']=duration/timescale
            if k==b'trak':
                for t,u,v in boxes(x,y):
                    if t==b'tkhd':report['resolution']=[int(n/65536) for n in struct.unpack_from('>2I',data,v-8)]
assert len(data)>100000 and 42<=report['duration_seconds']<=44,report
assert report['resolution']==[324,576],report
ROOT=EP.parent.parent; hashes=json.loads((EP/'edit/master_hashes.json').read_text()); report['master_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()); assert report['master_files_unchanged']
(EP/'edit/movie_verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
