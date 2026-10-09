import subprocess,json,time,struct,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP003_Gaming_Laptop_GP';BIN=ROOT/'tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin'
while True:
    log=(EP/'edit/render_animation.log').read_text(errors='replace')
    if 'GP_RENDER_COMPLETE' in log:break
    if 'Traceback' in log:raise RuntimeError(log[-2000:])
    time.sleep(3)
folder=EP/'renders/frames_1080p60'
for f in range(1,661):
    with (folder/f'EP003_{f:06d}.png').open('rb') as h:head=h.read(24)
    assert head[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>2I',head[16:24])==(1080,1920)
final=ROOT/'03_FINAL_OUTPUT/YouTube/EP003_Gaming_Laptop_GreasePencil_1080p60_v001.mp4'
with (EP/'edit/encode.log').open('w') as log:
    subprocess.run([str(BIN/'ffmpeg.exe'),'-hide_banner','-y','-framerate','60','-start_number','1','-i',str(folder/'EP003_%06d.png'),'-i',str(EP/'audio/EP003_Original_Laptop_SoundDesign_v001.wav'),'-frames:v','660','-t','11','-c:v','h264_nvenc','-preset','p4','-rc','vbr','-cq','18','-b:v','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart',str(final)],stdout=log,stderr=subprocess.STDOUT,check=True)
probe=json.loads(subprocess.check_output([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(final)]));v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1080,1920,'60/1',660)
assert abs(float(probe['format']['duration'])-11)<.05 and a['channels']==2 and a['sample_rate']=='48000'
with (EP/'edit/decode_check.log').open('w') as log:subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-xerror','-i',str(final),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
shutil.copy2(final,EP/'renders'/final.name)
report={'status':'Complete and verified','video':str(final),'blend':str(EP/'blend/EP003_Gaming_Laptop_GP_v006.blend'),'medium':'Native Grease Pencil animation and caption fills','frames':660,'fps':60,'resolution':[1080,1920],'duration_seconds':11,'audio':'Original synchronized synthesized metal hinge, whine, silence and engine startup/roar','renderer':'Eevee GPU','encoding':'NVIDIA NVENC H.264','full_decode_passed':True,'protected_files_unchanged':len(hashes)}
(EP/'edit/delivery_verification.json').write_text(json.dumps(report,indent=2));print('EP003_COMPLETE',str(final),flush=True)
