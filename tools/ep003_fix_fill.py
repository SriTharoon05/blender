import bpy
from pathlib import Path
EP=Path(__file__).resolve().parent.parent/'02_EPISODES/EP003_Gaming_Laptop_GP'
s=bpy.data.scenes['EP003_Gaming_Laptop_GreasePencil'];bpy.context.window.scene=s
obj=bpy.data.objects['GP_EP003_Characters_Set_Laptops']
obj.data.stroke_depth_order='3D'
for layer in obj.data.layers:
    for frame in layer.frames:
        t=(frame.frame_number-1)/60
        reaction=(2<=t<3) or (6.8<=t<8.35) or (9.45<=t<10.05)
        remove=[]
        for i,st in enumerate(frame.drawing.strokes):
            if st.cyclic:
                st.fill_id=i+1
                st.fill_opacity=1
            if layer.name=='Constant caption panel':
                for point in st.points:point.position=(point.position.x,point.position.y,.8+i*.001)
            if len(st.points)==4 and obj.data.materials[st.material_index].name=='GP_EP003_skin':
                ys=[round(p.position.y,2) for p in st.points]
                if min(ys)==-.45 and max(ys)==.3:
                    if t>=5.13 and not reaction:remove.append(i)
                    else:
                        for point in st.points:
                            if point.position.y>0:point.position=(point.position.x,.82,point.position.z)
        if remove:frame.drawing.remove_strokes(indices=remove)
        frame.drawing.tag_positions_changed()
s.frame_set(75)
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP003_Gaming_Laptop_GP_v004.blend'),compress=True)
for f in [75,145,255,340,440]:
    s.frame_set(f);s.render.filepath=str(EP/'previews'/f'EP003_Color_Review_{f:04d}.png');bpy.ops.render.render(write_still=True)
