import subprocess,json,time,hashlib,struct,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP006_Call_Vs_Text';BIN=ROOT/'tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin'
while True:
    log=(EP/'edit/render_animation.log').read_text(errors='replace')
    if 'EP006_RENDER_COMPLETE' in log:break
    if 'Traceback' in log:raise RuntimeError(log[-2000:])
    time.sleep(3)
folder=EP/'renders/frames_1080p24'
for f in range(1,433):
    with (folder/f'EP006_{f:06d}.png').open('rb') as h:head=h.read(24)
    assert struct.unpack('>2I',head[16:24])==(1080,1920)
final=ROOT/'03_FINAL_OUTPUT/YouTube/EP006_Call_Vs_Text_1080p24_v001.mp4';started=time.perf_counter()
with (EP/'edit/encode.log').open('w') as log:
    subprocess.run([str(BIN/'ffmpeg.exe'),'-hide_banner','-y','-framerate','24','-start_number','1','-i',str(folder/'EP006_%06d.png'),'-i',str(EP/'audio/EP006_Original_Call_Text_48k.wav'),'-frames:v','432','-t','18','-c:v','h264_nvenc','-preset','p4','-rc','vbr','-cq','18','-b:v','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart',str(final)],stdout=log,stderr=subprocess.STDOUT,check=True)
encode_seconds=time.perf_counter()-started
probe=json.loads(subprocess.check_output([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(final)]));v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1080,1920,'24/1',432)
assert abs(float(probe['format']['duration'])-18)<.05 and a['sample_rate']=='48000' and a['channels']==2
with (EP/'edit/decode_check.log').open('w') as log:subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-xerror','-i',str(final),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
shutil.copy2(final,EP/'renders'/final.name);render=json.loads((EP/'edit/render_time.json').read_text());project=json.loads((EP/'edit/project_verification.json').read_text())
report={'status':'Complete and verified','video':str(final),'project':str(EP/'blend/EP006_Call_Text_GP_v003.blend'),'duration_seconds':18,'resolution':[1080,1920],'fps':24,'frames':432,'renderer_gpu':render['gpu'],'render_seconds':render['render_seconds'],'encode_seconds':encode_seconds,'render_and_encode_seconds':render['render_seconds']+encode_seconds,'audio':'Original ringtone / cushion thud left, original lo-fi / typing / message whoosh right','caption_bounds':project,'full_decode_passed':True,'protected_files_unchanged':len(hashes)}
(EP/'edit/delivery_verification.json').write_text(json.dumps(report,indent=2));print('EP006_DELIVERY_COMPLETE',json.dumps(report),flush=True)
