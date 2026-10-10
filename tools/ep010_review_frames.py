"""Explicit local GPU preview stage, separate from EP010 preparation builders."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.blender_queue_worker import render_gpu


def main():
    import bpy
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder',default='02_EPISODES/EP010_Binge_Watching/previews/v001')
    parser.add_argument('--frames',nargs='+',type=int,default=[25,65,201,302,391,461,528])
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:])
    folder=(ROOT/args.folder).resolve()
    if not folder.is_relative_to(ROOT):
        raise ValueError('Preview folder must stay in repository')
    if any(not 1<=frame<=528 for frame in args.frames):
        raise ValueError('EP010 review frame must be in 1..528')
    if __import__('os').environ.get('BLENDER_QUEUE_BUILD_ONLY')=='1':
        raise RuntimeError('Preview render is a separate explicit stage, never a build side effect')
    scene=bpy.data.scenes['EP010_Binge_Watching']
    bpy.context.window.scene=scene
    gpu_name=render_gpu(scene,'GTX 1650 Ti')
    folder.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    for frame in args.frames:
        target=folder/f'EP010_Review_{frame:04d}.png'
        if target.exists():
            raise FileExistsError('Choose a new preview directory instead of replacing reviewed frames')
        scene.frame_set(frame)
        scene.render.filepath=str(target)
        bpy.ops.render.render(write_still=True)
        print('EP010_REVIEW_FRAME',frame,flush=True)
    report={'frames':args.frames,'gpu':gpu_name,'review_render_seconds':time.perf_counter()-started,
        'project':Path(bpy.data.filepath).resolve().relative_to(ROOT).as_posix(),
        'finished_utc':datetime.now(timezone.utc).isoformat(),'visual_inspection_performed':False}
    (folder/'render_time.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('EP010_REVIEW_RENDER_COMPLETE',json.dumps(report),flush=True)


if __name__=='__main__':
    main()
