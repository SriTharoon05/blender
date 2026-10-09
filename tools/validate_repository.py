"""Cloud-safe syntax, production policy, and immutable master-asset checks.

This does not import bpy, start Blender, render, or imply visual validation.
Run --refresh-assets only when intentionally updating the approved inventory.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
INVENTORY=ROOT/'config/approved_assets.json'
SECRET_PATTERNS=[
    re.compile(rb'(?:ghp_|github_pat_|gho_)[A-Za-z0-9_]{25,}'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'sk-(?:proj-)?[A-Za-z0-9_-]{40,}'),
    re.compile(rb'AIza[0-9A-Za-z_-]{35}'),
    re.compile(rb'gsk_[A-Za-z0-9]{40,}'),
]

def candidates(root=ROOT):
    result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=root,check=True,capture_output=True)
    return sorted(set(Path(item.decode('utf-8')) for item in result.stdout.split(b'\0') if item))

def asset_paths(root=ROOT):
    return [p for p in candidates(root) if p.parts[0] in ['00_LIBRARY','01_TEMPLATES'] and (root/p).is_file()]

def refresh_assets():
    record={'schema_version':1,'purpose':'Exact approved reusable library/template bytes; historical episodes are preserved separately.','assets':{}}
    for rel in asset_paths():
        data=(ROOT/rel).read_bytes()
        record['assets'][rel.as_posix()]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    INVENTORY.parent.mkdir(exist_ok=True)
    INVENTORY.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(record["assets"])} approved asset records to {INVENTORY.relative_to(ROOT)}')

def validate():
    policy=json.loads((ROOT/'config/production_defaults.json').read_text(encoding='utf-8'))
    assert policy['resolution']==[1080,1920], 'New 2D default resolution changed'
    assert policy['fps']==24 and policy['engine']=='BLENDER_EEVEE'
    assert policy['render_concurrency']==1 and policy['allow_cpu_cycles_fallback'] is False
    assert policy['caption_main_bounds_px']==[108,300,918,480]
    assert policy['caption_tag_bounds_px']==[108,500,918,548]
    assert policy['character_frame_by_frame_redraw'] is False, 'Use persistent skeletal puppet parts'
    assert policy['background_count']==1, 'Use one static background plate'
    required_parts={'head','torso','upper_arm.L','lower_arm.L','hand.L',
                    'upper_arm.R','lower_arm.R','hand.R','upper_leg.L',
                    'lower_leg.L','upper_leg.R','lower_leg.R'}
    assert required_parts.issubset(policy['character_parts']), 'Missing modular skeletal body parts'
    peter_voice=policy['tts_character_voices']['Peter']
    assert peter_voice['provider']=='Gemini' and peter_voice['voice']=='Charon', 'Peter uses his fixed Charon voice'
    assert peter_voice['gender']=='male' and peter_voice['locked'] is True, 'Peter voice must remain male and locked'
    assert peter_voice['allow_voice_fallback'] is False, 'Do not switch Peter voices automatically'
    if policy.get('caption_mode')=='Audio-aligned one word at a time with brief scale-in pop':
        assert policy['caption_dialogue_bounds_px']==[130,1340,870,1470]
        assert (ROOT/policy['caption_font_file']).is_file()
        assert (ROOT/policy['character_svg']).is_file()
        assert (ROOT/policy['character_contours']).is_file()
    for key in ['template','character_library','character_reference','caption_layout']:
        assert (ROOT/policy[key]).is_file(), f'Missing {key}: {policy[key]}'
    spec=json.loads((ROOT/policy['caption_layout']).read_text(encoding='utf-8'))
    assert spec['resolution']==policy['resolution']
    assert spec['slots']['main']==policy['caption_main_bounds_px']
    assert spec['slots']['tag']==policy['caption_tag_bounds_px']
    if 'caption_dialogue_bounds_px' in policy:
        assert spec['slots']['dialogue']==policy['caption_dialogue_bounds_px']

    parsed=0;total=0;files=candidates()
    for rel in files:
        path=ROOT/rel
        if not path.is_file():continue
        size=path.stat().st_size;total+=size
        assert size<100*1024*1024, f'File exceeds regular GitHub size limit: {rel}'
        if path.suffix=='.py':
            ast.parse(path.read_text(encoding='utf-8-sig'),filename=rel.as_posix());parsed+=1
        if path.suffix in ['.py','.json','.md','.yml','.yaml','.txt','.sh','.ps1']:
            raw=path.read_bytes()
            for pattern in SECRET_PATTERNS:
                assert not pattern.search(raw), f'Credential-like literal in {rel}; remove it before publication'
    assets=json.loads(INVENTORY.read_text(encoding='utf-8'))['assets']
    assert assets, 'Approved asset inventory cannot be empty'
    for relative,record in assets.items():
        raw=(ROOT/relative).read_bytes()
        assert len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256'], f'Approved asset bytes changed: {relative}'
    print(json.dumps({'status':'pass','python_files_parsed':parsed,'approved_assets_unchanged':len(assets),'repository_files':len(files),'repository_source_bytes':total,'checks':['Python syntax','production policy','required assets','approved asset hashes','file-size limits','credential-like literals'],'not_checked':['Blender execution','GPU availability','visual quality','sound synchronization']},indent=2))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-assets',action='store_true')
    args=parser.parse_args()
    if args.refresh_assets:refresh_assets()
    validate()

if __name__=='__main__':main()
