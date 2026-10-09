"""EP008 original 3D Cycles background plates; two locked-camera GPU-only stills."""
import bpy, math, random, time, json, datetime, sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parent.parent
EP = ROOT / '02_EPISODES/EP008_Research_Then_Now'
for part in ['plates', 'blend', 'edit']:
    (EP / part).mkdir(parents=True, exist_ok=True)

if '--' in sys.argv and sys.argv[sys.argv.index('--')+1] in ['polish_b','polish_native']:
    mode=sys.argv[sys.argv.index('--')+1]
    sc=bpy.data.scenes['Plate_B_Cold_Research_Workstation']; bpy.context.window.scene=sc
    bpy.context.view_layer.update()
    for ob in list(sc.objects):
        if ob.name.endswith('black bezel'):
            # All browser meshes were authored in absolute world coordinates.
            # Preserve those coordinates directly, rather than relying on the
            # lazily evaluated world-matrix caches of an inactive background scene.
            for child in list(ob.children):
                pos=child.location.copy(); rot=child.rotation_euler.copy(); scale=child.scale.copy()
                child.parent=None; child.location=pos; child.rotation_euler=rot; child.scale=scale
            ob.rotation_euler.z=0
    bpy.context.view_layer.update()
    versioned=EP/('plates/EP008_Background_Worker_4_2_v003.blend' if mode=='polish_b' else 'plates/EP008_Background_Plates_Polished_5_2_v002.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(versioned),compress=False)
    if mode=='polish_native':
        print('NATIVE_MONITOR_POLISH_COMPLETE',flush=True); sys.exit(0)
    prefs=bpy.context.preferences.addons['cycles'].preferences; prefs.compute_device_type='OPTIX'; prefs.get_devices()
    devices=[]
    for device in prefs.devices:
        device.use=device.type=='OPTIX' and '1650' in device.name
        if device.use: devices.append(device.name)
    assert devices, 'GTX GPU is required; CPU fallback is forbidden.'
    sc.cycles.device='GPU'; sc.render.filepath=str(EP/'plates/Plate_B_Workstation_1080p.png')
    started=time.perf_counter(); bpy.ops.render.render(write_still=True); elapsed=time.perf_counter()-started
    data=json.loads((EP/'edit/plate_render_time.json').read_text()); data['plate_b_previous_render_seconds']=data['plate_b_seconds']; data['plate_b_final_render_seconds']=elapsed; data['plate_b_seconds']+=elapsed; data['render_seconds']=data['plate_a_seconds']+data['plate_b_seconds']; data['plates'][1]['render_seconds']=data['plate_b_seconds']; data['monitor_overlap_corrected']=True; data['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (EP/'edit/plate_render_time.json').write_text(json.dumps(data,indent=2))
    print('EP008_PLATES_POLISH_COMPLETE',elapsed,flush=True); sys.exit(0)

if '--' in sys.argv and sys.argv[sys.argv.index('--')+1] == 'render_optix':
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    devices=[]
    for device in prefs.devices:
        device.use=device.type=='OPTIX' and '1650' in device.name
        if device.use: devices.append(device.name)
    assert devices, 'GTX GPU is required; CPU fallback is forbidden.'
    times=[]
    for scene_name,png in [('Plate_A_Warm_University_Library','Plate_A_Library_1080p.png'),('Plate_B_Cold_Research_Workstation','Plate_B_Workstation_1080p.png')]:
        sc=bpy.data.scenes[scene_name]; bpy.context.window.scene=sc; sc.cycles.device='GPU'
        sc.render.filepath=str(EP/'plates'/png)
        print('GPU_OPTIX_START',scene_name,flush=True)
        started=time.perf_counter(); bpy.ops.render.render(write_still=True); elapsed=time.perf_counter()-started
        times.append({'name':png,'path':str(EP/'plates'/png),'render_seconds':elapsed})
        data={'gpu':devices[0],'engine':'Cycles','compute_backend':'OptiX','cpu_render_enabled':False,'samples':40,'resolution':[1080,1920],'plate_a_seconds':times[0]['render_seconds'],'plate_b_seconds':times[1]['render_seconds'] if len(times)>1 else None,'render_seconds':sum(t['render_seconds'] for t in times),'plates':times,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        (EP/'edit/plate_render_time.json').write_text(json.dumps(data,indent=2))
        print('PLATE_COMPLETE',png,elapsed,flush=True)
    print('EP008_PLATES_RENDER_COMPLETE',flush=True)
    sys.exit(0)
random.seed(808)
bpy.ops.wm.read_factory_settings(use_empty=True)

# Rendering really uses the laptop CUDA device. The CPU rendering device is disabled.
prefs = bpy.context.preferences.addons['cycles'].preferences
BACKEND='OPTIX' if bpy.app.version < (5,0,0) else 'CUDA'
prefs.compute_device_type = BACKEND
prefs.get_devices()
devices = []
for device in prefs.devices:
    device.use = device.type == BACKEND and '1650' in device.name
    if device.use:
        devices.append(device.name)
assert devices, 'A GTX 1650 Ti CUDA device is required; CPU fallback is not permitted.'

def rgba(h):
    vals = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in vals) + (1,)

def material(name, h, roughness=.5, metallic=0, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba(h)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = rgba(h)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    if emission:
        p.inputs['Emission Color'].default_value = rgba(h)
        p.inputs['Emission Strength'].default_value = emission
    return m

def wood(name, dark, light, grain=(1, 25, 5)):
    m = material(name, light, .39)
    n, l = m.node_tree.nodes, m.node_tree.links
    tex = n.new('ShaderNodeTexCoord')
    mul = n.new('ShaderNodeVectorMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = grain
    noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 2.9; noise.inputs['Detail'].default_value = 4; noise.inputs['Roughness'].default_value = .68
    ramp = n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = .17; ramp.color_ramp.elements[0].color = rgba(dark); ramp.color_ramp.elements[1].position = .84; ramp.color_ramp.elements[1].color = rgba(light)
    fine = n.new('ShaderNodeTexNoise'); fine.inputs['Scale'].default_value = 43; fine.inputs['Detail'].default_value = 2
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .19; bump.inputs['Distance'].default_value = .024
    p = n.get('Principled BSDF')
    l.new(tex.outputs['Generated'], mul.inputs[0]); l.new(mul.outputs['Vector'], noise.inputs['Vector']); l.new(noise.outputs['Fac'], ramp.inputs['Fac']); l.new(ramp.outputs['Color'], p.inputs['Base Color'])
    l.new(mul.outputs['Vector'], fine.inputs['Vector']); l.new(fine.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m

def paper(name, h):
    m = material(name, h, .84)
    n, l = m.node_tree.nodes, m.node_tree.links
    noise = n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 140; noise.inputs['Detail'].default_value = 2
    bump = n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .13; bump.inputs['Distance'].default_value = .006
    l.new(noise.outputs['Fac'], bump.inputs['Height']); l.new(bump.outputs['Normal'], n.get('Principled BSDF').inputs['Normal'])
    return m

M = {
    'desk': wood('Warm oak / true procedural grain', '3D2015', '9A683E', (1, 36, 5)),
    'shelf': wood('Old library walnut', '26170F', '68472D', (2, 17, 4)),
    'floor': wood('Waxed maple parquet', '614938', 'B49268', (2, 28, 3)),
    'wall': material('Aged warm plaster', 'B7AA90', .9),
    'trim': wood('Traditional wainscot', '38251A', '7F6242', (2, 8, 23)),
    'paper': paper('Off-white acid-free paper', 'F0E4CA'),
    'oldPaper': paper('Aged book page edges', 'C9B996'),
    'ink': material('Printed ink graphite', '443C35', .85),
    'brass': material('Antique brass', '98733A', .27, .8),
    'green': material('Banker lamp green enamel', '254533', .23, .13),
    'warmBulb': material('Warm lamp diffuser', 'FFF0B8', .5, emission=3.7),
    'dark': material('Black workstation plastic', '121926', .26),
    'screen': material('Cold blue LCD emission', '7399D5', .25, emission=1.2),
    'screenDark': material('Dark mode blue-gray browser', '142039', .3, emission=.7),
    'screenLight': material('Browser content soft blue', 'B8CBE9', .3, emission=1.25),
    'screenCyan': material('UI cyan selection', '5EAACB', .3, emission=1.5),
    'sticky': paper('Yellow sticky note paper', 'D8CA76'),
    'stickyPink': paper('Coral sticky note paper', 'CE9381'),
    'cable': material('Rubber black cable', '172026', .55),
    'can': material('Brushed aluminum beverage can', '939EA9', .31, .75),
    'canLabel': material('Deep orange energy drink label', 'B14922', .4),
    'mug': material('Ceramic mug blue-gray', '8AABAA', .2),
    'coffee': material('Coffee black-brown', '21140D', .15),
}
book_colors = ['785045', '345647', '686D67', 'AC976B', '655A76', '8B7A52', '32434C', '5E312D', 'BFAC88']
BOOK_M = [material('Cloth-bound book ' + str(i), col, .76) for i, col in enumerate(book_colors)]

def activate(scene):
    bpy.context.window.scene = scene

def cube(name, pos, scale, mat, bevel=0, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos, rotation=rotation)
    ob = bpy.context.object; ob.name = name; ob.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat: ob.data.materials.append(mat)
    if bevel:
        b = ob.modifiers.new('Soft worn edge', 'BEVEL'); b.width = bevel; b.segments = 3
        b.affect = 'EDGES'
        for poly in ob.data.polygons: poly.use_smooth = True
        wn = ob.modifiers.new('Face weighted normals', 'WEIGHTED_NORMAL')
    return ob

def cylinder(name, pos, radius, depth, mat, rotation=(0,0,0), verts=40):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth, location=pos, rotation=rotation)
    ob = bpy.context.object; ob.name = name; ob.data.materials.append(mat)
    for p in ob.data.polygons: p.use_smooth=True
    b = ob.modifiers.new('Small rolled edge', 'BEVEL'); b.width=.008; b.segments=2
    return ob

def curve(name, points, mat, thickness=.013):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions='3D'; cu.resolution_u=12; cu.bevel_depth=thickness; cu.bevel_resolution=3
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
    for p, coord in zip(sp.bezier_points, points): p.co=coord; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name,cu); bpy.context.scene.collection.objects.link(ob); cu.materials.append(mat)
    return ob

def text(name, body, pos, size, mat, rotation=(math.pi/2,0,0), align='LEFT'):
    cu=bpy.data.curves.new(name,'FONT'); cu.body=body; cu.size=size; cu.align_x=align; cu.space_character=1.05
    ob=bpy.data.objects.new(name,cu); bpy.context.scene.collection.objects.link(ob); ob.location=pos; ob.rotation_euler=rotation; cu.materials.append(mat)
    return ob

def light(name, pos, power, color, size, target, kind='AREA'):
    data=bpy.data.lights.new(name,kind); data.energy=power; data.color=color
    if kind=='AREA': data.shape='DISK'; data.size=size
    ob=bpy.data.objects.new(name,data); bpy.context.scene.collection.objects.link(ob); ob.location=pos; ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob

def scene(name, temperature):
    sc=bpy.data.scenes.new(name); activate(sc)
    sc.render.engine='CYCLES'; sc.cycles.device='GPU'; sc.cycles.samples=40; sc.cycles.use_adaptive_sampling=True; sc.cycles.adaptive_threshold=.035
    sc.cycles.use_denoising=True; sc.cycles.denoiser='OPTIX'; sc.cycles.denoising_use_gpu=True
    sc.cycles.max_bounces=7; sc.cycles.diffuse_bounces=3; sc.cycles.glossy_bounces=3; sc.cycles.transmission_bounces=4; sc.cycles.volume_bounces=1
    sc.cycles.use_light_tree=True
    sc.render.resolution_x=1080; sc.render.resolution_y=1920; sc.render.resolution_percentage=100
    sc.render.fps=24; sc.render.image_settings.file_format='PNG'; sc.render.image_settings.color_mode='RGB'; sc.render.image_settings.color_depth='8'; sc.render.image_settings.compression=50
    sc.render.film_transparent=False; sc.render.use_file_extension=True
    sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=0
    world=bpy.data.worlds.new(name+' world'); world.use_nodes=True
    world.node_tree.nodes.get('Background').inputs['Color'].default_value=temperature
    world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.13 if 'Library' in name else .035
    sc.world=world
    sc['render_pipeline']='One real 3D Cycles still, CUDA GTX 1650 Ti only; CPU rendering disabled'
    sc['composition']='Locked identical camera. Clean character space x350–730px y700–1300px. Title y300–480, upper tag y500–548.'
    return sc

A=scene('Plate_A_Warm_University_Library',(0.55,.43,.28,1))
camera_data=bpy.data.cameras.new('CAM_EP008_LOCKED_3D'); camera_data.lens=44; camera_data.sensor_fit='HORIZONTAL'; camera_data.sensor_width=36
camera=bpy.data.objects.new(camera_data.name,camera_data); A.collection.objects.link(camera)
camera.location=(0,-7.2,5.5); camera.rotation_euler=(Vector((0,0,3.05))-camera.location).to_track_quat('-Z','Y').to_euler(); A.camera=camera
camera.lock_location=(True,True,True); camera.lock_rotation=(True,True,True); camera.lock_scale=(True,True,True)
focus=bpy.data.objects.new('Desk focus / shared',None); A.collection.objects.link(focus); focus.location=(0,-.4,1.5)
camera_data.dof.use_dof=True; camera_data.dof.focus_object=focus; camera_data.dof.aperture_fstop=5.6; camera_data.dof.aperture_blades=7

# The room and desk are the same objects in both shots. Original procedural geometry only.
cube('Rear plaster wall',(0,3.7,3.5),(11,.18,7),M['wall'])
cube('Left plaster wall',(-5.4,0,3.5),(.15,8,7),M['wall'])
cube('Right plaster wall',(5.4,0,3.5),(.15,8,7),M['wall'])
cube('Upper cornice',(0,3.45,6.6),(10.8,.42,.28),M['trim'],.025)
cube('Lower wainscot',(0,3.56,.78),(10.8,.15,1.56),M['trim'],.016)
for i in range(20):
    cube('Parquet floor board %02d'%i,(-5.14+i*.55,0,-.08),(.54,12,.12),M['floor'],.011)

def shelf_unit(x, name):
    cube(name+' backing',(x,3.44,3.0),(2.2,.11,5.7),M['shelf'],.012)
    for dx in [-1.08,1.08]: cube(name+' pillar',(x+dx,3.0,3.0),(.14,.83,5.8),M['shelf'],.015)
    for j,z in enumerate([.32,1.25,2.18,3.11,4.04,4.97,5.9]):
        cube(name+' shelf '+str(j),(x,3.0,z),(2.26,.90,.13),M['shelf'],.018)
    for row in range(6):
        xx=x-1.0
        while xx<x+.89:
            thick=random.uniform(.075,.17); height=random.uniform(.62,.78); depth=random.uniform(.38,.52)
            cover=BOOK_M[random.randrange(len(BOOK_M))]
            tilt=random.choice([0,0,0,-.045,.04])
            z=.385+row*.93+height/2
            cube(name+' book spine',(xx+thick/2,2.88,z),(thick,depth,height),cover,.006,rotation=(0,tilt,0))
            cube(name+' page top',(xx+thick/2,2.91,z+height/2+.002),(thick*.72,depth*.85,.007),M['oldPaper'],.002)
            if random.random()<.57:
                cube(name+' gold spine rule',(xx+thick/2,2.88-depth/2-.004,z+.15),(thick*.75,.006,.012),M['brass'],.001)
                cube(name+' spine lower rule',(xx+thick/2,2.88-depth/2-.004,z-.15),(thick*.75,.006,.007),M['brass'],.001)
            xx+=thick+.012

shelf_unit(-3.0,'West library bookshelves'); shelf_unit(3.0,'East library bookshelves')
# Central wall has subdued flat panels: a deliberate clean space for the 2D researcher.
cube('Central wood wall panel',(0,3.51,3.85),(3.67,.11,3.75),M['trim'],.012)
for x in [-1.83,1.83]: cube('Panel frame vertical',(x,3.40,3.85),(.055,.09,3.8),M['brass'],.005)
cube('Panel frame upper',(0,3.40,5.74),(3.7,.09,.055),M['brass'],.005)
cube('Panel frame lower',(0,3.40,1.97),(3.7,.09,.055),M['brass'],.005)

# Desk top is rear y~1180, center y~1250, front y~1430 in the final locked camera.
cube('SHARED hero desk top',(0,-.50,1.22),(6.3,2.60,.16),M['desk'],.035)
cube('SHARED desk front apron',(0,-1.75,.97),(6.07,.13,.33),M['shelf'],.018)
for x in [-2.76,2.76]:
    for y in [-1.48,.49]: cube('SHARED desk leg',(x,y,.57),(.17,.17,1.11),M['shelf'],.016)
cube('SHARED desktop leather blotter',(0,-.43,1.309),(1.75,.98,.014),material('Worn dark green leather blotter','3E4D3D',.67),.015)

# Distant dusty west window; no full-scene volume cost.
windowmat=material('Warm sunset window glass','E5DCC0',.23,emission=1.8)
cube('Window luminous glass',(-5.31,.45,3.6),(.018,3.25,3.75),windowmat,.003)
for y in [-1.19,.45,2.10]: cube('Window wood vertical mullion',(-5.23,y,3.6),(.12,.055,3.8),M['trim'],.012)
for z in [1.70,3.60,5.50]: cube('Window wood horizontal rail',(-5.23,.45,z),(.12,3.4,.07),M['trim'],.012)

base_objects=set(A.objects)

def flat_sheet(name,x,y,z,angle=0,w=.50,h=.70,mat=None):
    ob=cube(name,(x,y,z),(w,h,.008),mat or M['paper'],.003,rotation=(0,0,angle))
    return ob

def handwriting(sheet, lines=7):
    x,y,z=sheet.location; w,h=sheet.dimensions[:2]; a=sheet.rotation_euler.z
    for k in range(lines):
        length=w*random.uniform(.50,.78); yy=-h*.33+k*h*.095
        pts=[]
        for j in range(15):
            xx=-w*.36+length*j/14; sy=yy+random.uniform(-.003,.003)
            pts.append((x+xx*math.cos(a)-sy*math.sin(a),y+xx*math.sin(a)+sy*math.cos(a),z+.006))
        curve('Handwritten graphite line',pts,M['ink'],.0009)

def lying_book(name,x,y,z,w=.55,d=.73,thickness=.13,angle=0,color=None):
    col=color or BOOK_M[random.randrange(len(BOOK_M))]
    book=cube(name+' page block',(x,y,z+thickness/2),(w*.96,d*.97,thickness*.82),M['oldPaper'],.003,rotation=(0,0,angle))
    for zz in [z+.012,z+thickness-.007]: cube(name+' cloth cover',(x,y,zz),(w,d,.018),col,.004,rotation=(0,0,angle))
    # Fine physical page layers read as realistic texture close to the camera.
    for k in range(4):
        zz=z+.027+k*thickness*.17
        curve(name+' visible page edge',[(x-w/2*.96,y-d/2-.002,zz),(x+w/2*.96,y-d/2-.002,zz)],M['ink'],.0006)
    return book

# Plate A: scholarly, calm arrangement at the margins; large center open for acting.
for i in range(4): lying_book('Neat reference stack left',-2.31,.01,1.312+i*.13,w=.64,d=.77,thickness=.13,angle=.025*(i%2))
for i in range(3): lying_book('Reference stack right',2.53,.25,1.312+i*.12,w=.62,d=.74,thickness=.12,angle=-.02)
sheet=flat_sheet('Research notes left',-1.51,-.87,1.317,.16,w=.46,h=.63); handwriting(sheet)
for i in range(4):
    flat_sheet('Cream index card',1.69+i*.03,-.53+i*.02,1.318+i*.006,angle=-.05+i*.035,w=.29,h=.17)
curve('Pencil shaft',[(-1.95,-1.20,1.323),(-1.48,-1.04,1.323)],material('Original yellow pencil lacquer','CFA54B',.43),.013)
curve('Pencil dark writing tip',[(-1.47,-1.04,1.323),(-1.40,-1.01,1.323)],M['ink'],.009)

# Classic banker lamp: real brass and curved green glazed hood.
cylinder('Lamp heavy brass foot',(-1.72,.45,1.335),.19,.055,M['brass'])
cylinder('Lamp brass stem',(-1.72,.45,1.68),.027,.69,M['brass'])
curve('Lamp arch',[(-1.72,.45,1.94),(-1.72,.42,2.09),(-1.72,.28,2.14)],M['brass'],.025)
# Half cylinder shade, extruded in x, curved green upper surface.
verts=[]; faces=[]; N=32
for side in [-.39,.39]:
    for i in range(N+1):
        theta=math.pi*i/N
        verts.append((-1.72+side,.27+.235*math.cos(theta),2.08+.235*math.sin(theta)))
for i in range(N): faces.append((i,i+1,N+2+i,N+1+i))
mesh=bpy.data.meshes.new('Curved banker shade mesh'); mesh.from_pydata(verts,[],faces); mesh.materials.append(M['green'])
ob=bpy.data.objects.new('Curved banker green glass shade',mesh); A.collection.objects.link(ob)
for p in mesh.polygons:p.use_smooth=True
sol=ob.modifiers.new('Glass enamel thickness','SOLIDIFY'); sol.thickness=.015
cube('Banker lamp warm underside',(-1.72,.27,2.075),(.69,.38,.016),M['warmBulb'],.024)
light('Banker warm desk pool',(-1.72,.24,2.03),50,(1.0,.68,.31),.44,(-1.5,-.8,1.2))
light('Warm west window',(-4.8,-.6,4.9),1050,(1.0,.69,.39),2.1,(1.3,1.5,1.1))
light('Soft warm camera fill',(0,-3.8,5.0),210,(.85,.78,.65),4.2,(0,.0,1.9))
light('Library shelf bounce',(2.7,1.1,5.8),160,(1.0,.73,.43),2.7,(1.6,3.2,3.1))
sun=light('Afternoon warm sun',(-6,-1,5.5),1.9,(1,.72,.41),1,(1.3,2.7,.5),'SUN'); sun.data.angle=.07

# The warm dust volume is confined to a small cone from the window.
volume=bpy.data.materials.new('Restricted dust / one small sunlight cone'); volume.use_nodes=True
vn=volume.node_tree.nodes; vl=volume.node_tree.links; vn.clear(); out=vn.new('ShaderNodeOutputMaterial'); pv=vn.new('ShaderNodeVolumeScatter'); pv.inputs['Density'].default_value=.014; pv.inputs['Anisotropy'].default_value=.48; pv.inputs['Color'].default_value=(.73,.63,.47,1); vl.new(pv.outputs['Volume'],out.inputs['Volume'])
start=Vector((-4.8,-.6,4.8)); end=Vector((.15,1.1,1.65)); mid=(start+end)/2
bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=1.05,radius2=.18,depth=(end-start).length,location=mid)
cone=bpy.context.object; cone.name='Localized afternoon dust beam cone'; cone.rotation_euler=(start-end).to_track_quat('Z','Y').to_euler(); cone.data.materials.append(volume)

# Specks are subtle genuine 3D motes restricted to the incoming warm beam.
mote=material('Tiny illuminated dust motes','ECD8B8',.8,emission=.35)
for i in range(26):
    q=random.uniform(.08,.78); pt=start.lerp(end,q); pt.x+=random.uniform(-.25,.25); pt.y+=random.uniform(-.26,.26); pt.z+=random.uniform(-.16,.16)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=random.uniform(.002,.007),location=pt)
    ob=bpy.context.object; ob.name='Dust mote'; ob.data.materials.append(mote)

B=scene('Plate_B_Cold_Research_Workstation',(0.19,.28,.48,1))
for ob in base_objects:
    if ob.name != 'Window luminous glass': B.collection.objects.link(ob)
B.camera=camera
activate(B)
cube('Night moonlit window glass',(-5.31,.45,3.6),(.018,3.25,3.75),material('Cold nighttime window','627AA1',.3,emission=.18),.003)

def monitor(name,x,y,z,width=1.35,height=1.08,angle=0):
    # Screen faces camera (-Y); tiny native browser cells form real emissive geometry.
    front=y-.061
    main=cube(name+' black bezel',(x,y,z),(width,.12,height),M['dark'],.027)
    main.rotation_euler.z=0
    # The plate is static: UI is independent, authored in absolute world space.
    # Front-facing monitor cards avoid incidental bezel/UI intersections.
    content=[]
    content.append(cube(name+' blue LCD',(x,front,z),(width-.075,.008,height-.074),M['screenDark'],.004))
    top=z+height/2-.11
    for k in range(10):
        tw=(width-.11)/10
        content.append(cube(name+' browser tab '+str(k),(x-width/2+.07+tw*(k+.5),front-.007,top),(tw-.013,.006,.045),M['screenCyan'] if k==3 else M['screen'],.004))
    content.append(cube(name+' URL bar',(x,front-.008,top-.066),(width-.15,.007,.029),M['screenLight'],.008))
    # Actual research content: alternating columns, snippets, sources, and chart-like article blocks.
    for row in range(12):
        zz=top-.145-row*.049
        ww=(width-.24)*random.uniform(.30,.79)
        cx=x-width/2+.105+ww/2
        content.append(cube(name+' article line',(cx,front-.009,zz),(ww,.006,.012),M['screenLight'] if row%4 else M['screenCyan'],.001))
    for k in range(3):
        content.append(cube(name+' research sidebar card',(x+width*.31,front-.009,top-.21-k*.15),(width*.20,.006,.10),M['screen'],.004))
    textob=text(name+' browser tiny title','RESEARCH / SOURCES',(x-width/2+.10,front-.016,top-.10),.035,M['screenLight'])
    cylinder(name+' stand neck',(x,y,1.47),.043,.29,M['dark'])
    cube(name+' stand foot',(x,y,1.321),(.41,.28,.035),M['dark'],.018)
    # Screen area lights cast the requested actual blue monitor lighting.
    light(name+' emitted blue pool',(x,y-.19,z),26,(.26,.45,1.0),.9,(x*.60,-1.0,1.2))
    return main

monitor('Left monitor primary',-2.21,-.23,2.10,width=1.31,height=1.16,angle=-.035)
monitor('Right monitor primary',2.16,-.16,2.15,width=1.35,height=1.18,angle=.035)
monitor('Left stacked research monitor',-2.23,.30,3.26,width=1.25,height=.98,angle=-.025)
monitor('Right stacked research monitor',2.29,.34,3.35,width=1.26,height=.99,angle=.025)

# Peripheral laptop at far right, leaving the center desk empty for animated 2D props.
cube('Thin laptop base', (2.76,-1.03,1.343),(.67,.53,.05),M['dark'],.018,rotation=(0,0,-.10))
cube('Laptop peripheral blue screen',(2.79,-.76,1.64),(.61,.07,.54),M['screenDark'],.017,rotation=(-.17,0,-.1))
cube('Laptop lit panel',(2.79,-.804,1.64),(.55,.009,.47),M['screen'],.007,rotation=(-.17,0,-.1))

for i in range(15):
    x=random.choice([-1,1])*random.uniform(1.20,2.68); y=random.uniform(-1.50,.46)
    z=1.319+random.uniform(0,.035)
    sheet=flat_sheet('Scattered research paper',x,y,z,random.uniform(-.40,.40),w=random.uniform(.37,.57),h=random.uniform(.50,.72)); handwriting(sheet,random.randrange(5,10))
for i in range(6):
    x=random.choice([-1,1])*random.uniform(1.20,2.63); y=random.uniform(-1.60,.24)
    st=flat_sheet('Scattered sticky note',x,y,1.368,random.uniform(-.7,.7),w=.17,h=.17,mat=M['sticky'] if i%2 else M['stickyPink']); handwriting(st,3)
for x in [-2.72,1.70,2.65]:
    y=random.uniform(-1.29,-.78); can=cylinder('Energy drink aluminum can',(x,y,1.51),.086,.36,M['can'])
    cylinder('Energy drink paper wrap',(x,y,1.51),.087,.23,M['canLabel'])
    cylinder('Can lip',(x,y,1.697),.076,.008,M['can'])
    text('Energy can small label','BOOST',(x-.053,y-.09,1.505),.025,M['paper'])
    bpy.ops.mesh.primitive_torus_add(major_radius=.022,minor_radius=.004,major_segments=20,minor_segments=8,location=(x,y-.011,1.704))
    bpy.context.object.name='Can pull tab'; bpy.context.object.data.materials.append(M['dark'])

for side in [-1,1]:
    for i in range(3):
        x=side*(1.35+i*.39); yy=-.36+i*.06
        curve('Tangled charging cable',[(x,yy,1.33),(x-side*.15,-.78,1.337),(x+side*.31,-1.06,1.34),(x+side*.13,-1.44,1.337),(x+side*.37,-1.35,1.337)],M['cable'],.012)

cube('Side phone charging',(1.56,-1.33,1.358),(.21,.38,.035),M['dark'],.018,rotation=(0,0,-.15))
cube('Side phone notification screen',(1.56,-1.33,1.38),(.178,.34,.006),M['screen'],.006,rotation=(0,0,-.15))
for i in range(4): cube('Phone notification pill',(1.56,-1.43+i*.063,1.387),(.132,.039,.005),M['screenLight'],.007)

# Marginal coffee cup and piled books remain believable props, not central obstructions.
cylinder('Night ceramic mug',(-2.85,-1.19,1.46),.12,.28,M['mug'])
cylinder('Dark coffee surface',(-2.85,-1.19,1.603),.105,.004,M['coffee'])
curve('Mug handle',[(-2.73,-1.19,1.58),(-2.59,-1.19,1.56),(-2.58,-1.19,1.40),(-2.73,-1.19,1.37)],M['mug'],.024)
for i in range(3): lying_book('Messy books back left',-2.79,.44,1.316+i*.10,w=.52,d=.62,thickness=.10,angle=.13*(i-1))

light('Cold overhead rectangle',(0,-.1,6.1),330,(.42,.58,1.0),3.5,(0,0,1.2))
light('Cold camera fill',(0,-4.0,4.6),60,(.32,.51,1.0),3.0,(0,.5,1.7))
light('Night shelf edge',(-3,1.5,5.9),75,(.35,.53,.92),2.7,(-1.5,3.4,2.7))
light('Night weak window moon',(-4.8,-.3,5),130,(.31,.48,.90),2.2,(1,1.5,1.0))

# Keep Cycles plates unbaked by post processing. The master layered compositor
# adds its very subtle screen glow after the transparent Grease Pencil pass.
for sc in [A,B]:
    sc['camera_locked']=True
    sc['gpu_enabled']=devices[0]
    sc['samples']=40
    sc.render.filepath='//../plates/'+('Plate_A_Library_1080p.png' if sc==A else 'Plate_B_Workstation_1080p.png')

projections={}
for label,p in [('desk_back',(0,.8,1.30)),('desk_middle',(0,-.5,1.30)),('desk_front',(0,-1.8,1.30)),('left_monitor_inner',(-1.55,-.23,2.1)),('right_monitor_inner',(1.5,-.16,2.1))]:
    co=world_to_camera_view(A,camera,Vector(p)); projections[label]=[round(co.x*1080,1),round((1-co.y)*1920,1)]
print('LOCKED_PROJECTIONS',projections,flush=True)
(EP/'edit/plate_composition.json').write_text(json.dumps({'camera_location':list(camera.location),'camera_rotation_euler':list(camera.rotation_euler),'lens_mm':44,'projections':projections,'gpu':devices,'cpu_enabled':False,'samples':40,'denoiser':'OptiX GPU'},indent=2))

activate(A)
native=EP/('plates/EP008_Background_Worker_4_2.blend' if bpy.app.version < (5,0,0) else 'blend/EP008_Background_Plates_v001.blend')
assert not native.exists(), 'Native background v001 already exists; do not overwrite.'
bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
times=[]
for sc,name in [(A,'Plate_A_Library_1080p.png'),(B,'Plate_B_Workstation_1080p.png')]:
    activate(sc); sc.render.filepath=str(EP/'plates'/name)
    started=time.perf_counter(); bpy.ops.render.render(write_still=True); elapsed=time.perf_counter()-started
    times.append({'name':name,'path':str(EP/'plates'/name),'render_seconds':elapsed})
    print('PLATE_COMPLETE',name,elapsed,flush=True)
    data={'gpu':devices[0],'engine':'Cycles','compute_backend':BACKEND,'blender_render_version':bpy.app.version_string,'native_project_version':'5.2.2','cpu_render_enabled':False,'samples':40,'resolution':[1080,1920],'plate_a_seconds':times[0]['render_seconds'],'plate_b_seconds':times[1]['render_seconds'] if len(times)>1 else None,'render_seconds':sum(t['render_seconds'] for t in times),'plates':times,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (EP/'edit/plate_render_time.json').write_text(json.dumps(data,indent=2))
print('EP008_PLATES_RENDER_COMPLETE',flush=True)
