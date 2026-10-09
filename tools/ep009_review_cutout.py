"""Explicit GPU review renders; never called by a preparation-only builder."""
import json
from pathlib import Path
import sys
import time
import bpy
import argparse
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from blender_queue_worker import render_gpu
EP=ROOT/'02_EPISODES/EP009_Wrong_Screen'
scene=bpy.data.scenes['EP009_Wrong_Screen_Cutout']
bpy.context.window.scene=scene
gpu=render_gpu(scene,'GTX 1650 Ti')
parser=argparse.ArgumentParser()
parser.add_argument('--frames',default='5,27,85,150,241,340,385,432')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
frames=[int(value) for value in args.frames.split(',')]
out=EP/'previews'
out.mkdir(exist_ok=True)
started=time.perf_counter()
for frame in frames:
    scene.frame_set(frame)
    scene.render.filepath=str(out/f'EP009_Cutout_Review_{frame:04d}.png')
    bpy.ops.render.render(write_still=True)
record={'frames':frames,'gpu':gpu,'review_render_seconds':time.perf_counter()-started,
        'rendered_images_exist':True,'visual_reviewed':False}
previous=EP/'edit/cutout_review_render_time.json'
history=json.loads(previous.read_text()).get('attempts',[]) if previous.exists() else []
if previous.exists() and not history:
    old=json.loads(previous.read_text());history=[{'frames':old['frames'],'seconds':old['review_render_seconds']}]
history.append({'frames':frames,'seconds':record['review_render_seconds']})
record['attempts']=history
record['all_review_render_seconds']=sum(item['seconds'] for item in history)
(EP/'edit/cutout_review_render_time.json').write_text(json.dumps(record,indent=2)+'\n')
print('EP009_REVIEW_RENDER_COMPLETE',json.dumps(record),flush=True)
