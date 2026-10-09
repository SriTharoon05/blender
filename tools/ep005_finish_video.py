import subprocess,json,time,hashlib,struct,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP005_Lost_Mom_Checkout';BIN=ROOT/'tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin'
while True:
    log=(EP/'edit/render_animation.log').read_text(errors='replace')
    if 'EP005_RENDER_COMPLETE' in log:break
    if 'Traceback' in log:raise RuntimeError(log[-1800:])
    time.sleep(3)
folder=EP/'renders/frames_1080p24'
for f in range(1,529):
    with (folder/f'EP005_{f:06d}.png').open('rb') as h:head=h.read(24)
    assert struct.unpack('>2I',head[16:24])==(1080,1920)
final=ROOT/'03_FINAL_OUTPUT/YouTube/EP005_Lost_Mom_Checkout_1080p24_v001.mp4'
with (EP/'edit/encode.log').open('w') as log:
    subprocess.run([str(BIN/'ffmpeg.exe'),'-hide_banner','-y','-framerate','24','-start_number','1','-i',str(folder/'EP005_%06d.png'),'-i',str(EP/'audio/EP005_Checkout_Original_Sound_48k.wav'),'-frames:v','528','-t','22','-c:v','h264_nvenc','-preset','p4','-rc','vbr','-cq','18','-b:v','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart',str(final)],stdout=log,stderr=subprocess.STDOUT,check=True)
probe=json.loads(subprocess.check_output([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(final)]));v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1080,1920,'24/1',528)
assert abs(float(probe['format']['duration'])-22)<.05 and a['sample_rate']=='48000' and a['channels']==2
with (EP/'edit/decode_check.log').open('w') as log:subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-xerror','-i',str(final),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
shutil.copy2(final,EP/'renders'/final.name)
report={'status':'Complete and verified','video':str(final),'project':str(EP/'blend/EP005_Checkout_GP_v003.blend'),'duration_seconds':22,'resolution':[1080,1920],'fps':24,'frames':528,'renderer':'Eevee NVIDIA GTX 1650 Ti','encoding':'NVIDIA NVENC H.264','audio':'Original stereo 48kHz scanner beeps, accelerating monitor, AWOOGA klaxon, boing; digital silence 14–16s','caption':'Exact requested words, native GP Arial Black white fill with thick black contour; top 30%','packed_audio':True,'full_decode_passed':True,'protected_files_unchanged':len(hashes)}
(EP/'edit/delivery_verification.json').write_text(json.dumps(report,indent=2));print('EP005_DELIVERY_COMPLETE',str(final),flush=True)
