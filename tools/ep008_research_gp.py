"""Editable native GP acting over two reusable Cycles library stills."""
import bpy, math, ast, sys, json, hashlib, time, datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
EP=ROOT/'02_EPISODES/EP008_Research_Then_Now'
for folder in ['blend','audio','edit','previews','renders/frames_1080p24']:
    (EP/folder).mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
SCENE='EP008_Research_Then_Now'

if mode=='render':
    s=bpy.data.scenes[SCENE];bpy.context.window.scene=s
    assert s.render.engine=='BLENDER_EEVEE' and s.render.fps==24
    assert s.compositing_node_group and s.render.film_transparent
    s.render.filepath=str(EP/'renders/frames_1080p24/EP008_######')
    started=time.perf_counter()
    def progress(scene,*args):
        if scene.frame_current%12==0:
            (EP/'edit/render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'total':576,'elapsed_seconds':time.perf_counter()-started}))
    bpy.app.handlers.render_write.append(progress)
    bpy.ops.render.render(animation=True)
    import gpu
    elapsed=time.perf_counter()-started
    data={'render_seconds':elapsed,'frames':576,'video_seconds':24,'renderer':'Eevee + GPU compositor','gpu':gpu.platform.renderer_get(),'average_seconds_per_frame':elapsed/576,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (EP/'edit/render_time.json').write_text(json.dumps(data,indent=2))
    print('EP008_RENDER_COMPLETE',data,flush=True)
    sys.exit(0)

sys.path.insert(0,str(ROOT/'tools'))
from shorts_caption_safe_area import place_caption
def extract(file,names):
    for node in ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8-sig')).body:
        if isinstance(node,ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
extract('ep003_gp_laptop.py',{'color','shape','line','ellipse','rect','curve','smooth','mix','head'})
extract('ep004_keyboard_gp.py',{'mesh_caption'})
extract('ep004_polish.py',{'caption_outline'})

def visibility(ob,keys):
    for la in ob.data.layers:
        for fr,value in keys:
            la.opacity=value;la.keyframe_insert(data_path='opacity',frame=fr)

if mode=='compose':
    s=bpy.data.scenes[SCENE];bpy.context.window.scene=s
    # Refresh the audited transition frames without rebuilding the saved setup.
    obj=bpy.data.objects['GP_EP008_Student_And_Research_Props'];gp=obj.data
    layer=gp.layers[0];indices={m.name.replace('GP_EP008_',''):i for i,m in enumerate(gp.materials)}
    for node in ast.parse(Path(__file__).read_text(encoding='utf-8')).body:
        if isinstance(node,ast.FunctionDef) and node.name not in ['extract','visibility']:
            exec(compile(ast.Module(body=[node],type_ignores=[]),'EP008 audited drawings','exec'),globals())
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in ['GLYPHS','CARDS'] for target in node.targets):
            exec(compile(ast.Module(body=[node],type_ignores=[]),'EP008 graphic definitions','exec'),globals())
    for fr in range(241,505):
        layer.frames.remove(fr);strokes=[];reality((fr-1)/24);commit(fr)
        if fr%48==0:print('EP008_AUDITED_FRAME',fr,flush=True)
    ng=bpy.data.node_groups.new('EP008_Static_Plates_Transparent_GP','CompositorNodeTree')
    s.compositing_node_group=ng
    ng.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    nodes,links=ng.nodes,ng.links
    out=nodes.new('NodeGroupOutput');out.location=(970,150)
    rl=nodes.new('CompositorNodeRLayers');rl.scene=s;rl.label='Eevee: transparent, editable GP';rl.location=(-330,-150)
    plate=[]
    for i,name in enumerate(['Plate_A_Library_1080p.png','Plate_B_Workstation_1080p.png']):
        im=bpy.data.images.load(str(EP/'plates'/name),check_existing=True)
        im.filepath='//../plates/'+name;im.pack()
        assert tuple(im.size)==(1080,1920)
        node=nodes.new('CompositorNodeImage');node.image=im;node.location=(-820,420-i*220)
        node.label='Cycles still: '+('warm library' if i==0 else 'night workstation')
        plate.append(node)
    switch=nodes.new('ShaderNodeMix');switch.data_type='RGBA';switch.location=(-600,350)
    switch.label='Locked plates: hard cut at 9 seconds'
    links.new(plate[0].outputs['Image'],switch.inputs[6]);links.new(plate[1].outputs['Image'],switch.inputs[7])
    factor=switch.inputs[0]
    for fr,val in [(1,0),(216,0),(217,1),(576,1)]:
        factor.default_value=val;factor.keyframe_insert(data_path='default_value',frame=fr)
    # Do not interpolate across the cut.
    action=ng.animation_data.action
    for slot in action.slots:
        for al in action.layers:
            for strip in al.strips:
                bag=strip.channelbag(slot,ensure=False)
                if bag:
                    for fc in bag.fcurves:
                        for k in fc.keyframe_points:k.interpolation='CONSTANT'
    move=nodes.new('CompositorNodeTransform');move.location=(-340,350)
    move.label='BG impact jitter only, 1–3 pixels; camera locked'
    links.new(switch.outputs[2],move.inputs['Image'])
    move.inputs['Scale'].default_value=1.006
    keys=[(1,0,0),(216,0,0),(217,3,-2),(218,-2,2),(219,1,-1),(220,0,0),(432,0,0),(433,-3,2),(434,2,-1),(435,-1,1),(436,0,0),(552,0,0)]
    keys.extend((fr,(-1 if fr%2 else 1)*2,1 if fr%3 else -1) for fr in range(553,571))
    keys.extend([(571,3,-2),(572,-2,1),(573,1,-1),(574,0,0),(576,0,0)])
    for fr,x,y in keys:
        for name,value in [('X',x),('Y',y)]:
            move.inputs[name].default_value=value;move.inputs[name].keyframe_insert(data_path='default_value',frame=fr)
    # Apply the faint emissive glow to the plates, preserving crisp GP/text.
    glow=nodes.new('CompositorNodeGlare');glow.location=(-100,350);glow.label='Faint screen glow; crisp outlines preserved'
    glow.inputs['Type'].default_value='Fog Glow';glow.inputs['Quality'].default_value='Low'
    glow.inputs['Threshold'].default_value=.9;glow.inputs['Strength'].default_value=.025
    glow.inputs['Size'].default_value=.20
    links.new(move.outputs[0],glow.inputs['Image'])
    over=nodes.new('CompositorNodeAlphaOver');over.location=(170,140);over.label='Native transparent GP over rendered stills'
    over.inputs['Factor'].default_value=1
    links.new(glow.outputs[0],over.inputs['Background']);links.new(rl.outputs['Image'],over.inputs['Foreground'])
    grade=nodes.new('ShaderNodeRGBCurve');grade.location=(430,140);grade.label='Neutral identity curve: retain warm/cold contrast'
    links.new(over.outputs[0],grade.inputs['Color']);links.new(grade.outputs[0],out.inputs['Image'])
    s.render.use_compositing=True;s.render.compositor_device='GPU'
    s.render.filepath='//../renders/frames_1080p24/EP008_######'
    s.frame_set(73)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP008_Research_GP_v003.blend'),compress=True)
    report=json.loads((EP/'edit/project_verification.json').read_text())
    report.update({'packed_cycles_plates':2,'compositor':'Two packed Image plates → timed cut → 1–3px BG shake → faint glow → Alpha Over transparent GP → RGB Curves → Group Image output','compositor_device':'GPU','camera_locked':True,'hard_cut_frame':217})
    (EP/'edit/project_verification.json').write_text(json.dumps(report,indent=2))
    for fr in [25,85,193,217,337,433,481,505,529,565,571,576]:
        s.frame_set(fr);s.render.filepath=str(EP/'previews'/f'EP008_Review_{fr:04d}.png')
        bpy.ops.render.render(write_still=True)
    s.frame_set(529);s.render.use_compositing=False
    s.render.filepath=str(EP/'previews/EP008_Transparent_GP_0529.png')
    bpy.ops.render.render(write_still=True)
    print('EP008_COMPOSITE_REVIEW_COMPLETE',flush=True)
    sys.exit(0)

protected=[p for top in ['00_LIBRARY','01_TEMPLATES'] for p in (ROOT/top).rglob('*') if p.is_file()]
protected.extend(p for p in (ROOT/'02_EPISODES').rglob('*.blend') if 'EP008' not in str(p))
(EP/'edit/protected_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},indent=2))
assert not (EP/'blend/EP008_Research_GP_v001.blend').exists()
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP008_Research_GP_v001.blend'),compress=True)
s=bpy.data.scenes.new(SCENE);bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100
s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=576
s.eevee.taa_render_samples=8;s.eevee.use_raytracing=False;s.render.use_motion_blur=False;s.render.use_sequencer=False
s.render.film_transparent=True;s.render.use_compositing=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.image_settings.compression=50
s.render.filepath='//../renders/frames_1080p24/EP008_######'
s.view_settings.view_transform='Standard';s.view_settings.look='None'
s.world=bpy.data.worlds.new('EP008_Transparent_World')
cd=bpy.data.cameras.new('CAM_EP008_Locked_2D');cd.type='ORTHO';cd.ortho_scale=16
camera=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(camera);camera.location=(0,0,30);s.camera=camera
INK='28252D'
palette={'skin':'F1BD91','skinShade':'D98F6F','hair':'302D35','hairLight':'50444A','shirt':'568594','shirtShade':'386571','shirtLight':'77A3AA','ink':INK,'white':'FFF8E7','paper':'F6E9CB','paperShade':'DBCDB1','book':'345B56','bookRed':'AF5651','gold':'EED080','red':'EF6269','screen':'A9D4E2','screenDim':'698FB2','dark':'303845','silver':'B9C8CF','sweat':'93D9E3','bag':'A394AB','blue':'7BB6CD','tab':'E1E8E8','tabPink':'E2B9BC'}
gp=bpy.data.grease_pencils.new('GP_EP008_Student_And_Research_Props');gp.stroke_depth_order='2D'
obj=bpy.data.objects.new(gp.name,gp);s.collection.objects.link(obj)
indices={}
for name,h in list(palette.items())+[('line',INK),('lightLine','CAB19A'),('redLine','EF6269'),('blueLine','7BB6CD'),('paperLine','A79B87')]:
    m=bpy.data.materials.new('GP_EP008_'+name);bpy.data.materials.create_gpencil_data(m)
    m.grease_pencil.fill_color=color(h);m.grease_pencil.color=color(h if name.endswith('Line') else INK)
    gp.materials.append(m);indices[name]=len(gp.materials)-1
layer=gp.layers.new('Drawings on ones: library → tabs → question → collapse',set_active=True);layer.use_lights=False
strokes=[]

def transform(first,cx=0,cy=0,sx=1,sy=1,dx=0,dy=0,angle=0):
    ca,si=math.cos(angle),math.sin(angle)
    for i in range(first,len(strokes)):
        pts,mat,w,closed=strokes[i]
        strokes[i]=([(cx+sx*(a-cx)*ca-sy*(b-cy)*si+dx,cy+sx*(a-cx)*si+sy*(b-cy)*ca+dy) for a,b in pts],mat,w*min(sx,sy),closed)

GLYPHS={
 'A':[[(0,0),(.5,1),(1,0)],[(.2,.4),(.8,.4)]],
 'B':[[(0,0),(0,1),(.7,1),(1,.75),(.7,.5),(0,.5)],[(.7,.5),(1,.25),(.7,0),(0,0)]],
 'C':[[(1,.85),(.7,1),(.1,.9),(0,.2),(.2,0),(.8,0),(1,.15)]],
 'D':[[(0,0),(0,1),(.6,1),(1,.8),(1,.2),(.6,0),(0,0)]],
 'E':[[(1,1),(0,1),(0,0),(1,0)],[(0,.5),(.8,.5)]],
 'F':[[(0,0),(0,1),(1,1)],[(0,.5),(.8,.5)]],
 'G':[[(1,.85),(.7,1),(.1,.9),(0,.2),(.2,0),(1,0),(1,.45),(.5,.45)]],
 'H':[[(0,0),(0,1)],[(1,0),(1,1)],[(0,.5),(1,.5)]],
 'I':[[(0,1),(1,1)],[(.5,1),(.5,0)],[(0,0),(1,0)]],
 'L':[[(0,1),(0,0),(1,0)]],
 'M':[[(0,0),(0,1),(.5,.5),(1,1),(1,0)]],
 'N':[[(0,0),(0,1),(1,0),(1,1)]],
 'O':[[(.2,0),(0,.2),(0,.8),(.2,1),(.8,1),(1,.8),(1,.2),(.8,0),(.2,0)]],
 'P':[[(0,0),(0,1),(.8,1),(1,.8),(1,.6),(.8,.5),(0,.5)]],
 'R':[[(0,0),(0,1),(.8,1),(1,.8),(1,.6),(.8,.5),(0,.5)],[(.5,.5),(1,0)]],
 'S':[[(1,.85),(.8,1),(.2,1),(0,.8),(.1,.6),(.9,.4),(1,.2),(.8,0),(.1,0),(0,.15)]],
 'T':[[(0,1),(1,1)],[(.5,1),(.5,0)]],
 'U':[[(0,1),(0,.2),(.2,0),(.8,0),(1,.2),(1,1)]],
 'V':[[(0,1),(.5,0),(1,1)]],
 'W':[[(0,1),(.2,0),(.5,.6),(.8,0),(1,1)]],
 'Y':[[(0,1),(.5,.5),(1,1)],[(.5,.5),(.5,0)]],
 '?':[[(0,.8),(.2,1),(.8,1),(1,.8),(.5,.45),(.5,.25)],[(.5,.08),(.5,0)]],
 '!':[[(.5,1),(.5,.25)],[(.5,.08),(.5,0)]],
 '2':[[(0,.8),(.2,1),(.8,1),(1,.8),(0,0),(1,0)]],
}
def letters(text,x,y,height=.13,width=.011,mat='line'):
    for ch in text:
        for pts in GLYPHS.get(ch,[]):line([(x+height*.58*a,y+height*b) for a,b in pts],mat,width)
        x+=height*.78

def hand(x,y,t,typing=False):
    yy=y+(.07*math.sin(t*93) if typing else 0)
    ellipse(x,yy,.23,.15,'skin',.022,n=24)
    for j in range(3):line([(x-.10+j*.09,yy+.03),(x-.08+j*.09,yy+.12)],width=.012)
    if typing:
        for j in range(2):line([(x-.19+j*.29,yy+.26),(x-.21+j*.31,yy+.4)],'blueLine',.015)

def face(x,y,t,chaos=False,angle=0,look=0):
    first=len(strokes);head(x,y,'calm',turn=0,t=t);strokes.pop()
    # Retain the approved exact face/ears/hair, replace expression features only.
    retained=strokes[:first]
    for pts,mat,w,closed in strokes[first:]:
        if mat in [indices['white'],indices['ink']] and closed and len(pts) in [40,24]:continue
        if mat==indices['line'] and not closed and len(pts)==24 and min(b for a,b in pts)>y+.4:continue
        retained.append((pts,mat,w,closed))
    strokes[:]=retained
    blink=any(abs(t-v)<.06 for v in [1.8,4.7,7.4,11.3,22.65])
    for side in [-1,1]:
        ex=x+(-.46 if side<0 else .48)
        if chaos:
            ellipse(ex,y-.08,.39,.26,'bag',.017,n=28)
            curve([(ex-.28,y-.30),(ex,y-.4),(ex+.26,y-.3)],width=.018)
        if blink:
            curve([(ex-.28,y+.13),(ex,y+.02),(ex+.28,y+.13)],width=.028)
        else:
            ey=y+.12;ry=.29 if chaos else .22
            ellipse(ex,ey,.30 if chaos else .27,ry,'white',.022,n=32)
            twitch=.022*math.sin(t*75) if 21<=t<22 else 0
            ellipse(ex+.09*look+twitch,ey-.02,.07,.09,'ink',0,n=20)
        if chaos:line([(ex-.30,y+.55),(ex+.24,y+.66)],width=.032)
        else:curve([(ex-.25,y+.55),(ex,y+.67),(ex+.26,y+.57)],width=.028)
    if chaos and t<21:
        ellipse(x+.02,y-.54,.25,.30,'ink',.024,n=32)
        ellipse(x+.04,y-.75,.12,.055,'red',0,n=20)
    elif chaos:
        curve([(x-.27,y-.57),(x+.02,y-.48),(x+.30,y-.57)],width=.026)
    else:curve([(x-.25,y-.5),(x+.02,y-.70),(x+.28,y-.5)],width=.027)
    # Reading spectacles remain open line shapes so eyes stay visible.
    gf=len(strokes)
    for ex in [x-.46,x+.48]:
        line([(ex-.35,y+.37),(ex+.34,y+.37),(ex+.34,y-.16),(ex-.35,y-.16),(ex-.35,y+.37)],width=.020)
    curve([(x-.12,y+.19),(x,y+.29),(x+.14,y+.19)],width=.021)
    line([(x-.98,y+.23),(x-.82,y+.20)],width=.02);line([(x+.83,y+.20),(x+1.01,y+.27)],width=.02)
    if chaos:transform(gf,x,y,angle=-.095)
    if chaos:
        for dx,dy in [(-.81,1.19),(-.3,1.37),(.52,1.20)]:
            shape([(x+dx-.16,y+dy-.12),(x+dx+.15,y+dy-.16),(x+dx+.25,y+dy+.32),(x+dx-.02,y+dy+.11)],'hair',.021)
        shape([(x+.95,y+.72),(x+1.12,y+.37),(x+.99,y+.25),(x+.91,y+.38)],'sweat',.017)
    transform(first,x,y,.82,.82,angle=angle)

def book(t):
    # Perspective pages sit on the native 3D desktop at y=1240..1430px.
    open_=smooth(t/.75);first=len(strokes)
    shape([(-2.06,-3.80),(1.23,-3.80),(1.04,-2.44),(-1.80,-2.44)],'book',.034)
    shape([(-1.94,-3.65),(-.43,-3.78),(-.45,-2.55),(-1.75,-2.49)],'paperShade',.019)
    shape([(-.43,-3.78),(1.10,-3.65),(.96,-2.49),(-.45,-2.55)],'paper',.019)
    line([(-.45,-2.57),(-.43,-3.73)],width=.022)
    for side in [-1,1]:
        for j in range(5):
            yy=-2.74-j*.15
            xx=-1.65 if side<0 else -.25
            line([(xx,yy),(xx+.97,yy-.025)],'paperLine',.008)
    if t>=6:line([(-.24,-3.02),(.63,-3.05)],'redLine',.011)
    if open_<1:
        shape([(-.43,-3.76),(-.43,-2.54),(-.43-1.34*open_,-2.48),(-.43-1.49*open_,-3.64)],'book',.032)
    flip=max((math.sin(math.pi*(t-v)/.45) for v in [1,2.6] if v<=t<v+.45),default=0)
    if flip:
        shape([(-.43,-3.74),(-.43,-2.56),(-.43+1.32*math.cos(flip*2.5),-2.35+flip*.48),(-.43+1.45*math.cos(flip*2.5),-3.33+flip*.40)],'paper',.019)
    letters('RESEARCH',-1.48,-3.54,.12,.009)

def setup(t):
    breathe=.025*math.sin(t*2.8);nod=.09*math.sin((t-6)*9) if 6<=t<6.65 else 0
    x=-.43;y=.85+breathe-nod
    first=len(strokes)
    shape([(x-1.05,-2.46),(x-.99,-.55),(x-.66,-.12),(x+.67,-.12),(x+1.04,-.56),(x+1.07,-2.46)],'shirt',.034)
    shape([(x-.69,-.18),(x-.1,-1.01),(x,-2.39),(x-.92,-2.39)],'shirtShade',.021)
    shape([(x+.65,-.18),(x+.1,-1.01),(x,-2.39),(x+.92,-2.39)],'shirtLight',.021)
    rect(x-.25,-.38,.51,.63,'skin',.023)
    line([(x-.59,-.2),(x,-.97),(x+.59,-.2)],width=.023)
    for yy in [-1.23,-1.65,-2.05]:ellipse(x,yy,.035,.04,'gold',.012,n=12)
    face(x,y,t,angle=-.025 if 3<=t<5.3 else 0,look=.25 if 3<=t<5.3 else -.2)
    # Left arm rests on the book; the writing hand follows the pencil contact.
    shape([(x-.82,-.48),(x-1.11,-1.0),(-1.70,-2.53),(-1.17,-2.74),(-.93,-2.34),(x-.49,-.83)],'shirtShade',.030)
    px=.55+(.21*math.sin(t*18) if 3<=t<5 else .12*smooth((t-6)/.55))
    py=-2.81+(.055*math.sin(t*25) if 3<=t<5 else 0)
    shape([(x+.81,-.5),(x+1.07,-.89),(1.15,-2.15),(px+.25,py+.37),(px-.15,py+.40),(.50,-1.76),(x+.5,-.78)],'shirt',.030)
    book(t);hand(-1.37,-2.62,t)
    # Index card and diagonal yellow pencil, nib exactly on page.
    shape([(1.15,-3.28),(2.33,-3.19),(2.18,-2.67),(1.08,-2.74)],'paper',.021)
    for j in range(3):line([(1.29,-2.91-j*.09),(1.99,-2.87-j*.09)],'paperLine',.008)
    if t>=3:
        for j in range(min(4,1+int((min(t,5)-3)*1.5))):line([(1.25,-2.98-j*.07),(1.74,-2.94-j*.07)],width=.009)
    line([(px,py),(px+.47,py+.75)],'lightLine',.056)
    line([(px+.03,py+.04),(px+.42,py+.68)],'paperLine',.013)
    shape([(px-.05,py+.04),(px+.03,py-.07),(px+.09,py+.06)],'ink',.01)
    hand(px+.29,py+.45,t)
    if 8<=t<9:
        for sx,sy in [(-1.85,1.51),(.95,1.82)]:
            rr=.13+.035*math.sin(t*5)
            shape([(sx-rr,sy),(sx-.03,sy+.03),(sx,sy+rr),(sx+.03,sy+.03),(sx+rr,sy),(sx+.03,sy-.03),(sx,sy-rr),(sx-.03,sy-.03)],'gold',.009)
    # Dust lives in the transparent layer; no 3D geometry is animated.
    for j in range(7):
        xx=-3.8+j*.91+.10*math.sin(t*.5+j);yy=2.7-((t*.12+j*.34)%2.4)
        ellipse(xx,yy,.010,.010,'paper',0,n=8)

def browser(x,y,w,h,label,index=0):
    rect(x,y,w,h,'tabPink' if label in ['NOPE','SOURCE?'] else 'tab',.020)
    rect(x,y+h-.22,w,.22,'screenDim',.016)
    for j in range(3):ellipse(x+.12+j*.13,y+h-.11,.025,.025,'red' if j==0 else 'gold',0,n=10)
    line([(x+w-.18,y+h-.06),(x+w-.08,y+h-.16)],width=.01)
    line([(x+w-.18,y+h-.16),(x+w-.08,y+h-.06)],width=.01)
    letters(label,x+.13,y+h-.47,min(.15,(w-.25)/(max(len(label),1)*.78)),.009)
    if label=='VIDEO':
        shape([(x+.21,y+.18),(x+.21,y+.46),(x+.48,y+.32)],'red',.011)
        for j in range(2):line([(x+.65,y+.25+j*.13),(x+w-.15,y+.25+j*.13)],'paperLine',.01)
    elif label=='NOPE':
        line([(x+.22,y+.15),(x+w-.20,y+.5)],'redLine',.035)
        line([(x+.22,y+.5),(x+w-.20,y+.15)],'redLine',.035)
    else:
        for j in range(3):line([(x+.14,y+.15+j*.10),(x+w-.15-(j%2)*.2,y+.15+j*.10)],'paperLine',.009)

CARDS=[(-3.72,.32,1.72,1.14,'PAPER'),(1.0,1.51,1.75,1.15,'VIDEO'),(-2.99,1.45,1.85,1.08,'FORUM'),(1.60,.33,1.85,1.15,'BLOG'),(-3.85,-1.40,1.60,1.10,'SOURCE?'),(2.04,-1.25,1.48,1.10,'NOPE'),(-2.72,-.50,1.55,1.05,'NEWS'),(.88,2.09,1.70,1.03,'WAIT')]
def tabs(t):
    if t<10 or t>=22:return
    count=1 if t<12 else min(8,2+int((t-12)*1.8))
    for j,(x,y,w,h,label) in enumerate(CARDS[:count]):
        pop=smooth((t-(10 if j==0 else 12+(j-1)*.52)+1/24)/.18)
        first=len(strokes);browser(x,y,w,h,label,j)
        transform(first,x+w/2,y+h/2,pop,pop,dy=.025*math.sin(t*6+j))
    if 18<=t<21:
        # Nested browser rectangles rush toward the viewer on the bass beat.
        u=smooth((t-18)/.24)
        for j in range(5):
            rr=(j+(t-18)*1.6)%5
            ww=1.15+rr*.97;hh=.70+rr*.71
            cx=-.43+.10*math.sin(j*1.3+t);cy=.18
            rect(cx-ww/2,cy-hh/2,ww,hh,'screenDim' if j%2 else 'tabPink',.028)
            rect(cx-ww/2+.07,cy-hh/2+.08,ww-.14,hh-.30,'dark',.009)
            labels=['PAPER','VIDEO','FORUM','NOPE','SOURCE?']
            letters(labels[j],cx-ww/2+.16,cy+hh/2-.22,.12,.012,mat='blueLine')
            # Cards are stacked behind the character; the frame travel is the zoom.
        for j in range(4):
            a=j*math.pi/2+t*.7;xx=-.43+3.17*math.cos(a);yy=.25+1.94*math.sin(a)
            browser(xx-.58,yy-.30,1.15,.78,['BLOG','VIDEO','NOPE','WHY?'][j],j)

def laptop(t):
    # Open screen faces camera so tab clutter is readable.
    shape([(.12,-3.50),(3.26,-3.50),(2.90,-2.72),(.30,-2.72)],'silver',.030)
    for j in range(4):
        for k in range(9):rect(.52+k*.24,-3.35+j*.12,.18,.065,'dark',.007)
    shape([(.32,-2.77),(2.84,-2.77),(2.74,-1.18),(.51,-1.18)],'dark',.037)
    shape([(.51,-2.58),(2.65,-2.58),(2.57,-1.35),(.65,-1.35)],'screen',.017)
    for j in range(6):rect(.69+j*.28,-1.61,.24,.13,'white' if j%2 else 'tabPink',.010)
    letters('SOURCE?',.83,-1.93,.14,.011)
    for j in range(3):line([(.74,-2.1-j*.13),(2.37,-2.1-j*.13)],'paperLine',.012)
    if 13<=t<21:
        line([(.70,-2.52),(2.51,-2.52)],'blueLine',.02)
    ellipse(3.26,-3.32,.20,.30,'silver',.021,n=24)
    line([(3.26,-3.03),(3.26,-3.25)],width=.013)

def phone(x,y,t):
    rect(x-.30,y-.64,.60,1.27,'dark',.025)
    rect(x-.24,y-.50,.48,.99,'screen',.013)
    line([(x-.07,y+.55),(x+.07,y+.55)],'blueLine',.012)
    for j in range(3):
        rect(x-.18,y+.22-j*.22,.36,.13,'red' if j==0 else 'white',.009)
    ellipse(x,y-.57,.026,.026,'white',0,n=12)
    if 10<=t<22 and int(t*7)%2:
        for side in [-1,1]:curve([(x+side*.4,y-.24),(x+side*.55,y),(x+side*.4,y+.26)],mat='redLine',width=.017)

def loose_papers(t):
    for j in range(4):
        x=-3.17+j*.27 if j<2 else 2.69+(j-2)*.35
        y=-3.04+(j%2)*.2
        shake=.07 if 23<=t<23.75 else (.025 if 13<=t<21 else 0)
        x+=shake*math.sin(t*101+j);y+=shake*math.sin(t*79+j)
        shape([(x,y),(x+.70,y+.05),(x+.65,y+.47),(x-.08,y+.4)],'paper',.018)
        for k in range(3):line([(x+.06,y+.11+k*.09),(x+.5,y+.14+k*.09)],'paperLine',.009)
    # Energy can: restrained idle motion except the overload/final impact.
    y=-3.53+(.07*abs(math.sin(t*85)) if 23<=t<23.82 else 0)
    rect(-2.89,y,.48,.91,'red',.020);ellipse(-2.65,y+.91,.24,.07,'silver',.014,n=20)
    ellipse(-2.65,y+.92,.08,.027,'dark',0,n=16)
    line([(-2.78,y+.16),(-2.51,y+.70)],'blueLine',.03)
    if 23.75<=t:
        for xx in [-2.04,.76]:
            line([(xx,-3.15),(xx-.15,-2.98)],'blueLine',.025)
            line([(xx,-3.44),(xx-.25,-3.41)],'blueLine',.020)

def reality(t):
    tabs(t)
    x=-.43;y=.81
    collapse=smooth((t-23.5)/.25) if t>=23.5 else 0
    snap=0 if t>=17 or t<13 else .20*(1 if math.sin(t*14)>0 else -1)
    vibrate=.04*math.sin(t*111) if 23<=t<23.5 else 0
    first=len(strokes)
    shape([(x-1.1,-2.54),(x-1.03,-.55),(x-.69,-.14),(x+.63,-.15),(x+1.06,-.62),(x+1.16,-2.50)],'shirt',.037)
    shape([(x-.74,-.20),(x-.30,-1.04),(x,-2.45),(x-.93,-2.45)],'shirtShade',.022)
    shape([(x+.68,-.19),(x+.06,-1.0),(x,-2.44),(x+.98,-2.45)],'shirtLight',.022)
    if collapse<.60:rect(x-.24,-.38,.50,.59,'skin',.024)
    line([(x-.63,-.23),(x-.19,-1.13),(x+.63,-.21)],width=.026)
    for yy in [-1.22,-1.61,-2.04]:ellipse(x-.10,yy,.034,.04,'gold',.011,n=12)
    if collapse:transform(first,x,-2.50,1+.22*collapse,1-.80*collapse,dx=-.23*collapse)
    note=22<=t<23.5
    if t<23.75:
        hy=mix(y,-2.50,collapse);hx=mix(x,-.81,collapse)
        face(hx+vibrate+snap*.28,hy,t,True,angle=snap-.3*collapse,look=0 if note or t>=21 else (1 if snap>0 else -1))
        if collapse==0 and snap and int(t*24)%5==0:
            # One-frame head-turn smears: short parallel contour accents.
            for yy in [.55,.94,1.31]:line([(x-1.23,yy),(x-1.57,yy-.06)],'blueLine',.023)
    if note:
        rise=smooth((t-22)/.55)
        shape([(x-.89,-.66),(x-1.18,-1.11),(-1.45,-2.18+rise*.4),(-.90,-2.13+rise*.4),(x-.59,-1.04)],'shirtShade',.030)
        shape([(x+.89,-.66),(x+1.17,-1.09),(1.05,-2.19+rise*.4),(.49,-2.09+rise*.4),(x+.49,-1.01)],'shirt',.030)
        py=-2.30+.40*rise
        rect(-1.44,py,2.01,1.31,'gold',.025)
        shape([(.36,py),(.57,py+.22),(.57,py),(.36,py)],'paperShade',.016)
        hand(-1.48,py+.30,t);hand(.62,py+.30,t)
    elif t<23.5:
        py=-1.08+.055*math.sin(t*27)
        shape([(x-.84,-.52),(x-1.16,-.99),(-1.83,py-.19),(-1.65,py+.33),(-1.20,-.72),(x-.55,-.75)],'shirtShade',.032)
        hand(-1.62,py,t);phone(-1.69,py+.23,t)
        if 18<=t<21:
            shape([(x+.83,-.52),(x+1.06,-.96),(1.83,-2.0),(3.48,-3.03),(3.10,-3.22),(1.46,-2.26),(.53,-1.94),(x+.5,-.77)],'shirt',.032)
        else:
            shape([(x+.83,-.52),(x+1.06,-.96),(1.52,-2.92),(1.11,-3.08),(.53,-1.94),(x+.5,-.77)],'shirt',.032)
    else:
        shape([(-1.60,-2.60),(-1.40,-2.36),(.03,-2.39),(.50,-2.74),(.24,-3.02),(-.88,-2.86)],'shirtShade',.030)
        hand(.31,-2.83,t)
    if t>=23.75:
        # Folded shoulders connect to the head resting ON the crossed sleeve.
        # Draw the head after the sleeve; the face is hidden against the desk.
        ellipse(-.80,-2.75,.89,.34,'hair',.031,n=32)
        ellipse(-1.57,-2.85,.12,.15,'skinShade',.022,n=24)
        shape([(-1.65,-2.78),(-1.70,-2.51),(-1.40,-2.30),(-1.03,-2.37),(-.79,-2.23),(-.34,-2.31),(.03,-2.56),(.07,-2.80),(-.31,-2.74),(-.60,-2.91),(-.90,-2.72),(-1.19,-2.89)],'hair',.032)
        curve([(-1.42,-2.50),(-1.07,-2.32),(-.80,-2.49)],mat='lightLine',width=.017)
    if 23<=t<23.5:transform(first,dx=vibrate,dy=.026*math.sin(t*97))
    laptop(t);loose_papers(t)
    if 18<=t<21:hand(3.26,-3.13+.04*math.sin(t*36),t)
    elif 9<=t<22:hand(1.27,-3.10,t,typing=13<=t<17)

def commit(frame):
    d=layer.frames.new(frame).drawing;d.add_strokes([len(pts) for pts,_,_,_ in strokes])
    for j,(pts,mat,w,closed) in enumerate(strokes):
        st=d.strokes[j];st.material_index=mat;st.cyclic=closed;st.fill_id=j+1 if closed else 0;st.fill_opacity=1
        if w==0:st.hide_stroke=True
        for p,(x,y) in zip(st.points,pts):p.position=(x,y,j*.0008);p.radius=w;p.opacity=1
    d.tag_positions_changed()

for fr in range(1,577):
    t=(fr-1)/24;strokes=[]
    if t<9:setup(t)
    else:reality(t)
    commit(fr)
    if fr%48==0:print('EP008_BUILD_FRAME',fr,flush=True)

main=mesh_caption(s,'POV: Researching a project\n— Then vs Now','CAPTION_EP008_Main',size=.57,outline=0)
caption_outline(main);main_bounds=place_caption(main)
then=mesh_caption(s,'THEN: ONE BOOK. ONE ANSWER.','CAPTION_EP008_Then_Tag',size=.30,outline=0)
caption_outline(then);then_bounds=place_caption(then,'tag')
now=mesh_caption(s,'NOW: 47 TABS. ZERO ANSWERS.','CAPTION_EP008_Now_Tag',size=.30,outline=0)
caption_outline(now);now_bounds=place_caption(now,'tag')
question=mesh_caption(s,'Which source is the actual source?','CAPTION_EP008_Question_Tag',size=.30,outline=0)
caption_outline(question);question_bounds=place_caption(question,'tag')
visibility(main,[(1,0),(13,1),(576,1)])
visibility(then,[(1,1),(216,1),(217,0),(576,0)])
visibility(now,[(1,0),(216,0),(217,1),(528,1),(529,0),(576,0)])
visibility(question,[(1,0),(528,0),(529,1),(576,1)])
# Exact question is also part of the physical sticky note, not only a subtitle.
note=mesh_caption(s,'Which source is\nthe actual\nsource?','PROP_EP008_Source_Question',baseline=-1.18,size=.245,outline=0)
note.data.layers.remove(note.data.layers['Black outline'])
note.data.materials[1].grease_pencil.fill_color=color(INK)
note.location.x=-.435;note.location.z=.8
visibility(note,[(1,0),(528,0),(529,1),(564,1),(565,0),(576,0)])
for fr in range(529,565):
    note.location.y=-.40*(1-smooth(((fr-1)/24-22)/.55));note.keyframe_insert(data_path='location',frame=fr)
    if fr>=553:note.location.x=-.435+.04*math.sin((fr-1)/24*111);note.keyframe_insert(data_path='location',frame=fr)

ed=s.sequence_editor_create();wav=EP/'audio/EP008_Original_Research_48k.wav'
assert wav.exists()
snd=ed.strips.new_sound('EP008 Original piano / notification overload / silence / collapse',str(wav),channel=1,frame_start=1)
snd.sound.filepath='//../audio/'+wav.name
markers=[('Calm book opening',1),('Page flip',25),('Pencil scribble',73),('Underline + confident nod',145),('Success',193),('Hard cut + record scratch',217),('First notification',241),('Tabs multiply',289),('Frantic typing + head snaps',313),('Rabbit hole bass + nested tabs',433),('Eye twitch freeze',505),('Silent camera-facing question',529),('Information overload bass',553),('Desk collapse impact',571)]
for label,fr in markers:s.timeline_markers.new(label,frame=fr)
bpy.ops.file.pack_all();assert snd.sound.packed_file
obj['approved_character']='Canonical School Guy face, ears, angular hair, skin and blue costume; original head helper reused; research glasses/cardigan and chaotic expression are story variants.'
s['production_spec']='24s, 576 frames, 1080x1920 at 24fps; native editable GP, transparent RGBA Eevee GPU pass over two static packed Cycles plates.'
s['caption_policy']='Higher top y300px; labels y500px. Fixed through shake. All caption/tag text at top.'
s['source_question']='Which source is the actual source?'
s.frame_set(85);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP008_Research_GP_v002.blend'),compress=True)
verification={'native_GP_drawings':576,'resolution':[1080,1920],'fps':24,'duration_seconds':24,'film_transparent':True,'RGBA':True,'packed_audio':True,'main_caption_bounds_px':main_bounds,'then_bounds_px':then_bounds,'now_bounds_px':now_bounds,'question_bounds_px':question_bounds,'safe_caption_policy':'Upper y300..480, tag500..548; never bottom','exact_caption':main['exact_text'],'exact_physical_question':note['exact_text'],'collapse_impact_frame':571,'silence_frames':[529,552],'previous_assets_protected':len(protected)}
(EP/'edit/project_verification.json').write_text(json.dumps(verification,indent=2))
print('EP008_NATIVE_GP_BUILD_COMPLETE',verification,flush=True)
