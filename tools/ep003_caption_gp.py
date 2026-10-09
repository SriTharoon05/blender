import bpy
from pathlib import Path
EP=Path(__file__).resolve().parent.parent/'02_EPISODES/EP003_Gaming_Laptop_GP'
s=bpy.data.scenes['EP003_Gaming_Laptop_GreasePencil'];bpy.context.window.scene=s
o=bpy.data.objects['GP_EP003_Characters_Set_Laptops'];o.data.stroke_depth_order='2D'
source=bpy.data.objects['TXT_EP003_Constant_Caption'];evaluated=source.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();mesh.calc_loop_triangles()
layer=o.data.layers.new('Constant caption letters - editable GP fills',set_active=True);layer.use_lights=False;d=layer.frames.new(1).drawing;d.add_strokes([3]*len(mesh.loop_triangles));idx=next(i for i,m in enumerate(o.data.materials) if m.name=='GP_EP003_ink')
for i,triangle in enumerate(mesh.loop_triangles):
    st=d.strokes[i];st.cyclic=True;st.material_index=idx;st.fill_id=i+1;st.fill_opacity=1;st.hide_stroke=True
    for p,vertex in zip(st.points,triangle.vertices):
        pos=source.matrix_world@mesh.vertices[vertex].co;p.position=(pos.x,pos.y,1);p.radius=0;p.opacity=1
d.tag_positions_changed();evaluated.to_mesh_clear();source.hide_render=True;source.hide_viewport=True
source['purpose']='Editable caption source. Matching font contours are on the GP caption letters layer.'
s.frame_set(75);bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP003_Gaming_Laptop_GP_v005.blend'),compress=True)
for f in [75,145,340,440]:
    s.frame_set(f);s.render.filepath=str(EP/'previews'/f'EP003_Final_Review_{f:04d}.png');bpy.ops.render.render(write_still=True)
print('CAPTION_GP_COMPLETE',len(d.strokes),flush=True)
