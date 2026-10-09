"""Static SVG contour meshes rigidly bound to a 2D skeletal puppet.

No drawing-per-frame authoring, texture gradients, lights, or skin deformation.
Each modular part keeps fixed geometry and follows its named pivot bone.
"""
from __future__ import annotations
import math


def linear(hexcode):
    rgb=[int(hexcode.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)+(1.,)


def flat_material(name,hexcode):
    import bpy
    material=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color=linear(hexcode)
    material.use_nodes=True
    nodes=material.node_tree.nodes
    nodes.clear()
    emission=nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value=linear(hexcode)
    out=nodes.new('ShaderNodeOutputMaterial')
    material.node_tree.links.new(emission.outputs[0],out.inputs['Surface'])
    return material


def contour_mesh(name,paths,mapper,collection,*,z=0,scale=1):
    """Tessellate fixed fills and round stroke ribbons into one editable mesh."""
    import bpy
    from mathutils import Vector
    from mathutils.geometry import tessellate_polygon
    vertices,faces,face_colors=[],[],[]
    def polygon(points,color):
        if len(points)<3:
            return
        points=[Vector((x,y,z)) for x,y in points]
        offset=len(vertices)
        vertices.extend(tuple(p) for p in points)
        lookup={tuple(p):i+offset for i,p in enumerate(points)}
        for triangle in tessellate_polygon([points]):
            faces.append(tuple(i+offset for i in triangle) if isinstance(triangle[0],int)
                         else tuple(lookup[tuple(p)] for p in triangle))
            face_colors.append(color)
    def disk(cx,cy,radius,color):
        polygon([(cx+radius*math.cos(i*math.tau/12),cy+radius*math.sin(i*math.tau/12)) for i in range(12)],color)
    for record in paths:
        points=[mapper(*p) for p in record['points']]
        if len(points)>1 and points[-1]==points[0]:
            points=points[:-1]
        if record.get('fill'):
            polygon(points,record['fill'])
            z+=.0002
        stroke=record.get('stroke')
        radius=record.get('stroke_width',0)*scale/2
        if stroke and radius:
            pairs=list(zip(points,points[1:]))
            if record.get('closed'):
                pairs.append((points[-1],points[0]))
            for (ax,ay),(bx,by) in pairs:
                length=math.hypot(bx-ax,by-ay)
                if not length:
                    continue
                dx,dy=-(by-ay)/length*radius,(bx-ax)/length*radius
                polygon([(ax+dx,ay+dy),(bx+dx,by+dy),(bx-dx,by-dy),(ax-dx,ay-dy)],stroke)
            for x,y in points:
                disk(x,y,radius,stroke)
        z+=.0008
    mesh=bpy.data.meshes.new(name+'_Static_Vector_Geometry')
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    ob=bpy.data.objects.new(name,mesh)
    collection.objects.link(ob)
    colors=[]
    for color in face_colors:
        if color not in colors:
            colors.append(color)
            mesh.materials.append(flat_material('FLAT_'+color.lstrip('#'),color))
    for polygon,color in zip(mesh.polygons,face_colors):
        polygon.material_index=colors.index(color)
    ob['static_vector_part']=True
    ob['animation_contract']='Rigid bone-bound static geometry; no per-frame drawing or vertex animation'
    return ob


def make_rig(collection,bones,mapper,name='RIG_Peter_2D'):
    """bones maps names to {head:[x,y],tail:[x,y],parent:name|None}."""
    import bpy
    data=bpy.data.armatures.new(name+'_Skeleton')
    rig=bpy.data.objects.new(name,data)
    collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,spec in bones.items():
        bone=data.edit_bones.new(name)
        bone.head=(*mapper(*spec['head']),0)
        bone.tail=(*mapper(*spec['tail']),0)
        if (bone.tail-bone.head).length<.001:
            bone.tail.y+=.1
    for name,spec in bones.items():
        if spec.get('parent'):
            data.edit_bones[name].parent=data.edit_bones[spec['parent']]
            data.edit_bones[name].use_connect=False
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front=True
    data.display_type='STICK'
    for bone in rig.pose.bones:
        bone.rotation_mode='XYZ'
    rig['rig_type']='2D cut-out puppet: head, torso, upper/lower arms, hands, legs, feet and jaw pivots'
    return rig


def bind_part(ob,rig,bone):
    group=ob.vertex_groups.new(name=bone)
    group.add(list(range(len(ob.data.vertices))),1.,'REPLACE')
    modifier=ob.modifiers.new('Rigid single-part skeletal binding','ARMATURE')
    modifier.object=rig
    modifier.use_deform_preserve_volume=False
    ob.parent=rig
    ob['pivot_bone']=bone
    return ob


def rotate_joint(rig,bone,keys):
    """Keyframe only a pivot joint's local Z angle in degrees."""
    pose=rig.pose.bones[bone]
    for frame,degrees in keys:
        pose.rotation_euler.z=math.radians(degrees)
        pose.keyframe_insert(data_path='rotation_euler',frame=frame)


def visibility(ob,intervals,total_frames=432):
    """Switch prebuilt mouth/eye/cursor parts; never rebuild their geometry."""
    for frame,hidden in [(1,True),(total_frames+1,True)]:
        ob.hide_render=hidden
        ob.keyframe_insert(data_path='hide_render',frame=frame)
    for start,end in intervals:
        for frame,hidden in [(max(1,start-1),True),(start,False),(end+1,True)]:
            ob.hide_render=hidden
            ob.keyframe_insert(data_path='hide_render',frame=frame)


def shape(points,fill,stroke='#111827',stroke_width=5,closed=True):
    return {'points':points,'fill':fill,'stroke':stroke,'stroke_width':stroke_width,'closed':closed}


def ellipse(cx,cy,rx,ry,fill,stroke='#111827',stroke_width=5):
    return shape([(cx+rx*math.cos(i*math.tau/48),cy+ry*math.sin(i*math.tau/48)) for i in range(48)],fill,stroke,stroke_width)
