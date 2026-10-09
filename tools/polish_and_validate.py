import bpy, math, json
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
scene=bpy.context.scene
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/Versions/BRIX_Foundation_v004.blend'))
scene.eevee.use_raytracing=True
scene.eevee.taa_render_samples=96
scene.eevee.shadow_ray_count=3
scene.eevee.shadow_step_count=8
for o in bpy.data.objects:
    if o.type=='MESH' and any(m.type=='WEIGHTED_NORMAL' for m in o.modifiers):
        for p in o.data.polygons:p.use_smooth=True
rig=bpy.data.objects['RIG_BRIX']
rig.pose.bones['head'].rotation_mode='XYZ'; rig.pose.bones['head'].rotation_euler.y=.24
rig.pose.bones['upper_arm.L'].rotation_mode='XYZ'; rig.pose.bones['upper_arm.L'].rotation_euler.z=-.15
rig.pose.bones['forearm.L'].rotation_mode='XYZ'; rig.pose.bones['forearm.L'].rotation_euler.z=-.4
rig.pose.bones['forearm.R'].rotation_mode='XYZ'; rig.pose.bones['forearm.R'].rotation_euler.x=-.18
for side in ['L','R']:
    for prefix in ['Pupil_','EyeCatchlight_']:
        o=bpy.data.objects['CHAR_BRIX_'+prefix+side]; d=o.driver_add('scale',2).driver
        d.expression='max(0.005,(1-blink)*(1-0.7*squint-0.2*CONFIDENT-0.4*SUSPICIOUS-0.3*RELIEVED+0.15*wide_open))'
        for prop in ['squint','CONFIDENT','SUSPICIOUS','RELIEVED','wide_open']:
            v=d.variables.new(); v.name=prop; v.type='SINGLE_PROP'; v.targets[0].id=rig; v.targets[0].data_path='["'+prop+'"]'
# Self-refraction noise is avoided with smooth, low roughness jelly surfaces.
for name in ['MAT_Jelly_Red','MAT_Jelly_Blue']:
    m=bpy.data.materials[name]; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Roughness'].default_value=.13; p.inputs['Transmission Weight'].default_value=.45; p.inputs['Coat Weight'].default_value=.35; p.inputs['Coat Roughness'].default_value=.12
    for n in m.node_tree.nodes:
        if n.type=='BUMP':n.inputs['Distance'].default_value=.00025
scene.render.filepath=str(ROOT/'01_TEMPLATES/Previews/BRIX_Foundation_v003.png')
bpy.ops.render.render(write_still=True)
# Evaluate actual deform geometry and driver validity for every preset and key control.
expressions=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
report={'blender_version':bpy.app.version_string,'expression_checks':{},'controls':{},'invalid_drivers':[]}
def evaluated_coords(name):
    bpy.context.view_layer.update(); dep=bpy.context.evaluated_depsgraph_get(); o=bpy.data.objects[name].evaluated_get(dep); me=o.to_mesh(); result=[list(v.co) for v in me.vertices]; o.to_mesh_clear(); return result
for expr in expressions:
    for e in expressions:rig[e]=float(e==expr)
    rig.update_tag(); bpy.context.view_layer.update()
    coords=evaluated_coords('CHAR_BRIX_Mouth'); report['expression_checks'][expr]={'mouth_extents':[max(v[a] for v in coords)-min(v[a] for v in coords) for a in [0,2]],'mouth_key_value':bpy.data.objects['CHAR_BRIX_Mouth'].data.shape_keys.key_blocks[expr].value}
for e in expressions:rig[e]=0.
for control in ['blink','squint','wide_open','look_x','look_y','smile','nervous_smile','open_surprise','frown','worried','impressed_O']:
    rig[control]=1.; rig.update_tag(); bpy.context.view_layer.update()
    report['controls'][control]='evaluated'
    rig[control]=0.; rig.update_tag()
rig['CONFIDENT']=1.; rig.update_tag(); bpy.context.view_layer.update()
for db in list(bpy.data.objects)+list(bpy.data.shape_keys):
    if db.animation_data:
        for f in db.animation_data.drivers:
            if not f.is_valid:report['invalid_drivers'].append(db.name+':'+f.data_path)
report['objects']=len(bpy.data.objects); report['base_mesh_vertices']=sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'); report['render_engine']=scene.render.engine; report['simulations']=len([m for o in bpy.data.objects for m in o.modifiers if m.type in {'FLUID','CLOTH','SOFT_BODY'}]); report['rig_bones']=len(rig.data.bones)
(ROOT/'01_TEMPLATES/Previews/validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not report['invalid_drivers'], report['invalid_drivers']
assert len({tuple(round(x,4) for x in v['mouth_extents']) for v in report['expression_checks'].values()})==10,'Expression shapes must be distinct'
assert all(v['mouth_key_value']==1 for v in report['expression_checks'].values())
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/Versions/BRIX_Foundation_v005.blend'))
print(json.dumps(report,indent=2))
