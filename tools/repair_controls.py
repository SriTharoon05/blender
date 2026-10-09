import bpy, json
from pathlib import Path
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
s=bpy.context.scene; rig=bpy.data.objects['RIG_BRIX']
# Recompile after all driver variables have been added. This also persists a
# fully initialized expression cache across fresh file loads in Blender 5.2.
for db in list(bpy.data.objects)+list(bpy.data.shape_keys):
    if db.animation_data:
        for f in db.animation_data.drivers:
            expr=f.driver.expression
            if f.driver.type=='SCRIPTED':f.driver.expression='('+expr+') + 0.0'
        db.update_tag()
expressions=['NEUTRAL','CONFIDENT','CURIOUS','SUSPICIOUS','SURPRISED','SCARED','DISGUSTED','IMPRESSED','RELIEVED','EXCITED']
mouth=bpy.data.objects['CHAR_BRIX_Mouth']; report={'expression_checks':{},'manual_controls':{},'selector_checks':{},'invalid_drivers':[]}
def refresh():
    rig.update_tag(refresh={'OBJECT'})
    for k in bpy.data.shape_keys:k.update_tag()
    s.frame_set(s.frame_current+1); bpy.context.view_layer.update()
for expr in expressions:
    for e in expressions:rig[e]=float(e==expr)
    refresh(); v=mouth.data.shape_keys.key_blocks[expr].value
    dep=bpy.context.evaluated_depsgraph_get(); obj=mouth.evaluated_get(dep); me=obj.to_mesh(); coords=[tuple(v.co) for v in me.vertices]; obj.to_mesh_clear()
    report['expression_checks'][expr]={'driver_value':v,'width':max(v[0] for v in coords)-min(v[0] for v in coords),'height':max(v[2] for v in coords)-min(v[2] for v in coords)}
    assert v==1,(expr,v)
for e in expressions:rig[e]=0.
for ctrl in ['blink','squint','wide_open','look_x','look_y','smile','nervous_smile','open_surprise','frown','worried','impressed_O']:
    rig[ctrl]=1.; refresh()
    if ctrl in ['blink','squint','wide_open']:
        v=bpy.data.objects['CHAR_BRIX_Eye_L'].data.shape_keys.key_blocks[ctrl].value; assert v==1,(ctrl,v)
    elif ctrl.startswith('look'):
        axis=0 if ctrl=='look_x' else 2; v=bpy.data.objects['CHAR_BRIX_Pupil_L'].location[axis]
    else:
        v=mouth.data.shape_keys.key_blocks[ctrl].value; assert v==1,(ctrl,v)
    report['manual_controls'][ctrl]=v; rig[ctrl]=0.
ctrl=bpy.data.objects['CTRL_UI']
labels=['SLIME','GLASS','CLOTH','WATER','HONEY','SAND','LAVA']
for i,label in enumerate(labels):
    # Each selector's type stays readable in both selected and idle states.
    o=bpy.data.objects['UI_MaterialSelector_Label_'+label]
    m=bpy.data.materials.new('MAT_UI_Label_'+label); m.use_nodes=True; m.use_fake_user=True; n=m.node_tree.nodes; n.clear(); out=n.new('ShaderNodeOutputMaterial'); em=n.new('ShaderNodeEmission'); m.node_tree.links.new(em.outputs[0],out.inputs['Surface'])
    for a in range(3):
        f=em.inputs[0].driver_add('default_value',a); d=f.driver; v=d.variables.new(); v.name='selected'; v.type='SINGLE_PROP'; v.targets[0].id=ctrl; v.targets[0].data_path='["selected_material"]'; d.expression=f'0.012 if selected == {i} else 0.9'
    o.data.materials.clear(); o.data.materials.append(m)
for i,label in enumerate(labels):
    ctrl['selected_material']=i; ctrl.update_tag(); s.frame_set(s.frame_current+1); bpy.context.view_layer.update()
    visible=[l for l in labels if not bpy.data.objects['UI_MaterialSelector_Selected_'+l].hide_render]; report['selector_checks'][label]=visible
    assert visible==[label],visible
ctrl['selected_material']=0; ctrl.update_tag()
rig['CONFIDENT']=1.; refresh(); s.frame_set(1)
for db in list(bpy.data.objects)+list(bpy.data.shape_keys)+[m.node_tree for m in bpy.data.materials if m.use_nodes]:
    if db.animation_data:
        for f in db.animation_data.drivers:
            if not f.is_valid:report['invalid_drivers'].append(db.name+':'+f.data_path)
assert not report['invalid_drivers'],report['invalid_drivers']
report.update({'blender_version':bpy.app.version_string,'objects':len(bpy.data.objects),'base_mesh_vertices':sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),'rig_bones':len(rig.data.bones),'simulations':0,'engine':s.render.engine})
(ROOT/'01_TEMPLATES/Previews/validation_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/Versions/BRIX_Foundation_v005.blend'))
s.render.filepath=str(ROOT/'01_TEMPLATES/Previews/BRIX_Foundation_v004.png'); bpy.ops.render.render(write_still=True)
print(json.dumps(report,indent=2))
