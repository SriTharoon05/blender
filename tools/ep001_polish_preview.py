import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
EP=Path(r'C:\Users\assri\OneDrive\Documents\ChatGPT\Blender\02_EPISODES\EP001_Material_Test'); s=bpy.data.scenes['EP001_Material_Test']; bpy.context.window.scene=s
# Correct the blocking of the console approach using the existing character.
r=bpy.data.objects['RIG_BRIX']
for f in [38,72]:r.location=(3.64,-.48,0); r.keyframe_insert(data_path='location',frame=f)
# Episode-only clarity variants repair EEVEE's dark screen-space transmission.
# The original material assets remain untouched in the library and template.
def clarity(source,name,amount):
    m=bpy.data.materials[source].copy(); m.name=name; m.use_fake_user=True; n=m.node_tree.nodes; l=m.node_tree.links; out=n.get('Material Output'); p=n.get('Principled BSDF'); tr=n.new('ShaderNodeBsdfTransparent'); mix=n.new('ShaderNodeMixShader'); mix.inputs[0].default_value=amount; l.new(p.outputs[0],mix.inputs[1]); l.new(tr.outputs[0],mix.inputs[2]); l.new(mix.outputs[0],out.inputs['Surface']); return m
glass=clarity('MAT_Glass_Clear','MAT_EP001_Glass_Clarity',.5); shieldmat=clarity('MAT_Glass_Clear','MAT_EP001_Shield_Clarity',.88); water=clarity('MAT_Water','MAT_EP001_Water_Clarity',.38)
for o in bpy.data.objects:
    if o.name.startswith('EP001_GlassShard_'):o.data.materials[0]=glass
    if o.name=='PROP_SafetyShield' or o.name.startswith('EP001_Containment_'):o.data.materials[0]=shieldmat
bpy.data.objects['EP001_Water_Domain'].data.materials[0]=water
# A translucent cyan edge makes the closing containment visible on a phone.
col=bpy.data.collections['EP001_TestAssets']
for side,x in [('L',.06),('R',2.04)]:
    d=bpy.data.curves.new('EP001_ContainmentEdge_'+side,'CURVE'); d.dimensions='3D'; d.bevel_depth=.014; d.bevel_resolution=2; sp=d.splines.new('POLY'); sp.points.add(2)
    for p,co in zip(sp.points,[(x,-.65,.48),(x,-.65,1.81),(1.05,-.65,1.81)]):p.co=(*co,1)
    d.materials.append(bpy.data.materials['MAT_Light_Cyan']); o=bpy.data.objects.new('EP001_ContainmentEdge_'+side,d); col.objects.link(o)
    for f,z in [(1,-1.8),(1045,-1.8),(1084,0),(1180,0),(1210,-1.8)]:o.location.z=z; o.keyframe_insert(data_path='location',index=2,frame=f)
    for f,v in [(1,True),(1045,False),(1211,True)]:o.hide_render=v; o.keyframe_insert(data_path='hide_render',frame=f)
# Replace only the crude episode granular proxy with a coherent mound morph.
sand=bpy.data.objects['EP001_Sand_Block']; sand.name='EP001_Sand_GranularProxy'
for m in list(sand.modifiers):sand.modifiers.remove(m)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1); tmp=bpy.context.view_layer.objects.active; unit=[v.co.copy() for v in tmp.data.vertices]; sand.data=tmp.data; sand.data.name='EP001_Sand_CollapseMesh'; bpy.data.objects.remove(tmp,do_unlink=True); sand.data.materials.append(bpy.data.materials['MAT_Sand'])
for v,p in zip(sand.data.vertices,unit):v.co=p*(.385/max(abs(a) for a in p))
sand.shape_key_add(name='Basis'); k=sand.shape_key_add(name='GranularCollapse'); rng=random.Random(841)
for v,p in zip(k.data,unit):v.co=(p.x*.99,p.y*.99,-.385+.49*max(0,p.z)**1.8+rng.uniform(-.018,.018))
for p in sand.data.polygons:p.use_smooth=True
for f,loc in [(865,(1.05,.35,2.4)),(891,(1.05,.35,1.55)),(908,(1.05,.35,.97)),(929,(1.05,.35,.985)),(950,(1.05,.35,.985))]:sand.location=loc; sand.keyframe_insert(data_path='location',frame=f); sand.scale=(1,1,1); sand.keyframe_insert(data_path='scale',frame=f)
for f,v in [(865,0),(908,0),(927,.78),(949,1),(975,1)]:k.value=v; k.keyframe_insert(data_path='value',frame=f)
# Label the actual simulation and cache strategy in the episode file.
s['simulation_plan']='Slime:98 vertex guided soft-body MDD; glass:14 Voronoi rigid bodies sampled to transforms; cloth:625 vertex simulated drape MDD; water/honey:32 div liquid caches; sand:96 instanced grains + mound proxy; lava:viscous proxy'
for o in bpy.data.objects:
    if o.name.startswith('EP001_') and o.type=='MESH':
        if any(m.type=='MESH_CACHE' for m in o.modifiers):o['preview_cache']='Portable actual simulation result; source solver disabled. Re-bake only in a new episode version.'
s.frame_set(24); bpy.context.view_layer.update(); bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP001_v007.blend'),compress=True)
print('POLISHED_PREVIEW_CHECKPOINT_SAVED')
