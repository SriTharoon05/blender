import bpy, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender')
scene=bpy.context.scene
# Store revision before material and framing changes.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/Versions/BRIX_Foundation_v002.blend'))
press=bpy.data.objects['CTRL_Experiment_Press']
for name,z in [('PROP_TestMachine_Piston',0),('PROP_TestMachine_PressHead',-.35),('PROP_TestMachine_PressPad',-.45)]:
    o=bpy.data.objects[name]; o.location=(0,0,z); o.matrix_parent_inverse.identity()
# Extend backdrop outside every camera ray.
me=bpy.data.objects['ENV_Lab_SeamlessCove'].data
for v in me.vertices:
    if abs(v.co.x)>11:v.co.x=60 if v.co.x>0 else -60
    if v.co.y<-6:v.co.y=-60
    if v.co.z>8:v.co.z=35
me.update()
cam=scene.camera; cam.location=(5.2,-12.8,5.7); cam.rotation_euler=(Vector((0,.65,2.25))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.lens=72
# UI coordinates must follow the narrower lens field.
# New width at 1m = 0.5m, height = 0.889m. Retain the same normalized placement.
for o in bpy.data.collections['ASSET_MobileUI'].objects:
    if o.name=='CTRL_UI':continue
    o.location.x*=2/3; o.location.y*=2/3
    if o.type=='FONT':o.data.size*=2/3
    elif o.type=='MESH':o.scale.x*=2/3; o.scale.y*=2/3
# Pure emission avoids scene lighting changing UI legibility.
for name in ['MAT_UI_White']:
    m=bpy.data.materials[name]; n=m.node_tree.nodes; n.clear(); out=n.new('ShaderNodeOutputMaterial'); e=n.new('ShaderNodeEmission'); e.inputs[0].default_value=(.86,.95,1,1); e.inputs[1].default_value=1; m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
ink=bpy.data.materials.new('MAT_UI_Navy'); ink.use_nodes=True; ink.use_fake_user=True; n=ink.node_tree.nodes; n.clear(); out=n.new('ShaderNodeOutputMaterial'); e=n.new('ShaderNodeEmission'); e.inputs[0].default_value=(.012,.028,.043,1); mlinks=ink.node_tree.links; mlinks.new(e.outputs[0],out.inputs['Surface']); ink.asset_mark()
labels=['SLIME','GLASS','CLOTH','WATER','HONEY','SAND','LAVA']
for i,label in enumerate(labels):
    row=0 if i<4 else 1; col=i if row==0 else i-4; count=4 if row==0 else 3
    x=(col-(count-1)/2)*.111; y=-.30-row*.041
    for prefix in ['Tile_','Selected_']:
        o=bpy.data.objects['UI_MaterialSelector_'+prefix+label]; o.location.x=x; o.location.y=y; o.scale.x=.11/.082; o.scale.y=.033/.037
        # Objects originally scaled to 2/3; reset full tile dimensions explicitly.
        o.dimensions.x=.103 if prefix=='Tile_' else .107; o.dimensions.y=.032 if prefix=='Tile_' else .036
        if prefix=='Tile_':o.data.materials.clear(); o.data.materials.append(ink)
    o=bpy.data.objects['UI_MaterialSelector_Label_'+label]; o.location.x=x; o.location.y=y-.006; o.data.size=.014
    if i==0:o.data.materials.clear(); o.data.materials.append(ink)
o=bpy.data.objects['UI_MaterialSelector_Caption']; o.location.y=-.267; o.data.size=.013
for name in ['MAT_Jelly_Red','MAT_Jelly_Blue']:
    m=bpy.data.materials[name]
    for n in m.node_tree.nodes:
        if n.type=='BUMP':n.inputs['Distance'].default_value=.0008; n.inputs['Strength'].default_value=.12
# Set normal material shading instead of reactive heavy previews during work.
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.shading.type='SOLID'
scene.render.filepath=str(ROOT/'01_TEMPLATES/Previews/BRIX_Foundation_v002.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'01_TEMPLATES/Versions/BRIX_Foundation_v003.blend'))
bpy.ops.render.render(write_still=True)
print('REFINED_PREVIEW_READY')
