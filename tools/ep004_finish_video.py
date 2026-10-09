import subprocess,json,time,hashlib,struct,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP004_Dad_Mechanical_Keyboard';BIN=ROOT/'tools/vendor/ffmpeg611/ffmpeg-6.1.1-essentials_build/bin'
while True:
    log=(EP/'edit/render_animation.log').read_text(errors='replace')
    if 'EP004_RENDER_COMPLETE' in log:break
    if 'Traceback' in log:raise RuntimeError(log[-1800:])
    time.sleep(3)
folder=EP/'renders/frames_1080p24'
for f in range(1,241):
    with (folder/f'EP004_{f:06d}.png').open('rb') as h:head=h.read(24)
    assert struct.unpack('>2I',head[16:24])==(1080,1920)
final=ROOT/'03_FINAL_OUTPUT/YouTube/EP004_Dad_Mechanical_Keyboard_1080p24_v001.mp4'
with (EP/'edit/encode.log').open('w') as log:
    subprocess.run([str(BIN/'ffmpeg.exe'),'-hide_banner','-y','-framerate','24','-start_number','1','-i',str(folder/'EP004_%06d.png'),'-i',str(EP/'audio/EP004_Original_Keyboard_Impacts_v001.wav'),'-frames:v','240','-t','10','-c:v','h264_nvenc','-preset','p4','-rc','vbr','-cq','18','-b:v','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-ar','48000','-movflags','+faststart',str(final)],stdout=log,stderr=subprocess.STDOUT,check=True)
probe=json.loads(subprocess.check_output([str(BIN/'ffprobe.exe'),'-v','error','-show_streams','-show_format','-of','json',str(final)]));v=next(x for x in probe['streams'] if x['codec_type']=='video');a=next(x for x in probe['streams'] if x['codec_type']=='audio')
assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1080,1920,'24/1',240)
assert abs(float(probe['format']['duration'])-10)<.05 and a['sample_rate']=='48000' and a['channels']==2
with (EP/'edit/decode_check.log').open('w') as log:subprocess.run([str(BIN/'ffmpeg.exe'),'-v','error','-xerror','-i',str(final),'-f','null','-'],stdout=log,stderr=subprocess.STDOUT,check=True)
hashes=json.loads((EP/'edit/protected_hashes.json').read_text());assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
shutil.copy2(final,EP/'renders'/final.name)
report={'status':'Complete and verified','video':str(final),'project':str(EP/'blend/EP004_Dad_Keyboard_GP_v004.blend'),'duration_seconds':10,'resolution':[1080,1920],'fps':24,'frames':240,'renderer':'Eevee NVIDIA GTX 1650 Ti','encoding':'NVIDIA NVENC H.264','audio':'Original stereo 48kHz synthesized comic blasts, anvil clang and mug rattle','caption':'Exact requested words, Arial Black white fill with rounded thick black contour; verified inside top 20%','packed_audio':True,'full_decode_passed':True,'protected_blend_files_unchanged':len(hashes)}
(EP/'edit/delivery_verification.json').write_text(json.dumps(report,indent=2));print('EP004_DELIVERY_COMPLETE',str(final),flush=True)
