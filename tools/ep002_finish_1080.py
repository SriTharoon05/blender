import json, time, subprocess, struct, hashlib, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
EP=ROOT/'02_EPISODES/EP002_Impossible_Blankets'
BLENDER=Path(r'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')
BIN=ROOT/'tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin'
state=EP/'edit/EP002_Resume_State.json'
def status(phase,**extra):
    value={'status':phase,'latest_complete_project':'blend/EP002_v026.blend','render_authorized':True,'resolution':[1080,1920],'fps':60,'renderer':'Eevee NVIDIA GTX 1650 Ti','final_video_rendered':False,**extra}
    state.write_text(json.dumps(value,indent=2))
    print(phase,flush=True)

status('Rendering native 1080p60; all physical caches complete and validated.')
while 'FAST_RENDER_SEGMENT_COMPLETE' not in (EP/'edit/render_1080p60_part1_animation.log').read_text(errors='replace'):
    time.sleep(5)
with (EP/'edit/render_1080p60_part2_animation.log').open('w') as log:
    subprocess.run([str(BLENDER),'-b',str(EP/'blend/EP002_v026.blend'),'--python',str(ROOT/'tools/ep002_render_1080_fast.py'),'--','1256','2250'],stdout=log,stderr=subprocess.STDOUT,check=True)
assert 'FAST_RENDER_SEGMENT_COMPLETE' in (EP/'edit/render_1080p60_part2_animation.log').read_text(errors='replace')
folder=EP/'renders/frames_1080p60'
for f in range(1,2251):
    p=folder/f'EP002_1080p60_{f:06d}.png'
    with p.open('rb') as h: header=h.read(24)
    assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>2I',header[16:24])==(1080,1920),p
status('All 2250 native frames complete; NVIDIA MP4 encoding.')
video=EP/'renders/EP002_Impossible_Blankets_1080p60_Final_v001.mp4'
with (EP/'edit/final_1080p60_encode.log').open('w') as log:
    subprocess.run([str(BIN/'ffmpeg.exe'),'-hide_banner','-y','-framerate','60','-start_number','1','-i',str(folder/'EP002_1080p60_%06d.png'),'-i',str(EP/'audio/EP002_Original_Material_SoundDesign_v002.wav'),'-frames:v','2250','-t','37.5','-c:v','h264_nvenc','-preset','p4','-rc','vbr','-cq','19','-b:v','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart',str(video)],stdout=log,stderr=subprocess.STDOUT,check=True)
probe=json.loads(subprocess.check_output([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(video)]))
v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1080,1920,'60/1',2250)
assert abs(float(probe['format']['duration'])-37.5)<.05 and int(a['sample_rate'])==48000 and a['channels']==2
with (EP/'edit/final_1080p60_decode_check.log').open('w') as log:
    subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-xerror','-i',str(video),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
hashes=json.loads((EP/'edit/protected_hashes.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
delivery=ROOT/'03_FINAL_OUTPUT/YouTube/EP002_Impossible_Blankets_1080p60_v001.mp4'
delivery.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(video,delivery)
report={'status':'Complete and verified','video':str(delivery),'resolution':[1080,1920],'fps':60,'frames':2250,'duration_seconds':37.5,'video_codec':'H.264 NVIDIA NVENC','audio':'AAC stereo 48kHz 256kbps','renderer':'Eevee NVIDIA GTX 1650 Ti','samples':16,'full_decode_passed':True,'protected_files_unchanged':len(hashes),'limitations':['Fast Eevee raster transparency approximates optics; physical caches retain their simulations.']}
(EP/'edit/final_1080p60_delivery_verification.json').write_text(json.dumps(report,indent=2))
status('Complete: 1080p60 final video rendered and verified.',final_video_rendered=True,final_video=str(delivery),verification='edit/final_1080p60_delivery_verification.json')
print('FINAL_1080P60_DELIVERY_COMPLETE',str(delivery),flush=True)
