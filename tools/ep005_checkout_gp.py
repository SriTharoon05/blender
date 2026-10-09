"""Editable native Grease Pencil checkout comedy, 1080x1920, 24fps."""
import bpy,math,ast,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP005_Lost_Mom_Checkout'
for f in ['blend','audio','previews','renders/frames_1080p24','edit']:(EP/f).mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='render':
    s=bpy.data.scenes['EP005_Lost_Mom_Checkout'];bpy.context.window.scene=s;s.render.filepath=str(EP/'renders/frames_1080p24/EP005_######')
    def progress(scene,*args):
        if scene.frame_current%12==0:(EP/'edit/render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'total':528,'fps':24}))
    bpy.app.handlers.render_write.append(progress);bpy.ops.render.render(animation=True)
    import gpu
    print('ACTUAL_GPU',gpu.platform.renderer_get(),flush=True);print('EP005_RENDER_COMPLETE',flush=True);sys.exit(0)
def extract(file,names):
    tree=ast.parse((ROOT/'tools'/file).read_text())
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
extract('ep003_gp_laptop.py',{'color','shape','line','ellipse','rect','curve','smooth','mix','head'})
extract('ep004_keyboard_gp.py',{'mesh_caption'})
extract('ep004_polish.py',{'caption_outline'})
protected=[p for top in ['00_LIBRARY','01_TEMPLATES'] for p in (ROOT/top).rglob('*') if p.is_file()]
protected.extend(p for p in (ROOT/'02_EPISODES').rglob('*.blend') if 'EP005' not in str(p))
(EP/'edit/protected_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},indent=2))
assert not (EP/'blend/EP005_Checkout_GP_v001.blend').exists()
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP005_Checkout_GP_v001.blend'),compress=True)
s=bpy.data.scenes.new('EP005_Lost_Mom_Checkout');bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=528
s.eevee.taa_render_samples=8;s.eevee.use_raytracing=False;s.render.use_motion_blur=False;s.render.use_sequencer=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=50;s.render.filepath='//../renders/frames_1080p24/EP005_######'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.world=bpy.data.worlds.new('EP005_FlatWorld');s.world.color=color('F6EBD6')[:3]
cd=bpy.data.cameras.new('CAM_EP005_Vertical');cd.type='ORTHO';cd.ortho_scale=16;camera=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(camera);camera.location=(0,0,30);s.camera=camera
INK='202D46'
palette={'cream':'F6EBD6','navy':INK,'yellow':'F5CE56','red':'E74C50','ghost':'D6D3CE','skin':'F6EBD6','skinShade':'F6EBD6','hair':INK,'white':'F6EBD6','ink':INK,'sweat':'E74C50'}
gp=bpy.data.grease_pencils.new('GP_EP005_Checkout_Drawings');gp.stroke_depth_order='2D';obj=bpy.data.objects.new(gp.name,gp);s.collection.objects.link(obj);indices={}
for name,h in list(palette.items())+[('line',INK),('lightLine','F5CE56'),('redLine','E74C50')]:
    m=bpy.data.materials.new('GP_EP005_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.fill_color=color(h);m.grease_pencil.color=color(INK if name not in ['line','lightLine','redLine'] else h);gp.materials.append(m);indices[name]=len(gp.materials)-1
# Red anxiety tint and two emergency flashes are intentional overlay fills.
for name,alpha in [('tint',.09),('alert',.46)]:
    m=bpy.data.materials.new('GP_EP005_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.fill_color=color('E74C50')[:3]+(alpha,);m.grease_pencil.color=(0,0,0,0);gp.materials.append(m);indices[name]=len(gp.materials)-1
layer=gp.layers.new('Checkout acting - native drawings at 24fps',set_active=True);layer.use_lights=False
strokes=[]
def transform(first,cx,cy,scale=1,dx=0,dy=0,angle=0):
    ca,si=math.cos(angle),math.sin(angle)
    for i in range(first,len(strokes)):
        pts,mat,w,closed=strokes[i]
        strokes[i]=([(cx+scale*((x-cx)*ca-(y-cy)*si)+dx,cy+scale*((x-cx)*si+(y-cy)*ca)+dy) for x,y in pts],mat,w*scale,closed)
GLYPHS={'L':[(0,1),(0,0),(.6,0)],'A':[(0,0),(.3,1),(.6,0),(.45,.5),(.15,.5)],'N':[(0,0),(0,1),(.6,0),(.6,1)],'E':[(.6,1),(0,1),(0,0),(.6,0),(0,0),(0,.5),(.5,.5)],'4':[(.5,0),(.5,1),(0,.35),(.7,.35)]}
def sign_text(x,y,text,scale=.42):
    for c in text:
        if c in GLYPHS:line([(x+scale*a,y+scale*b) for a,b in GLYPHS[c]],width=.034)
        x+=scale*.88
def gumball(t):
    first=len(strokes);x=-3.18;y=-3.48
    rect(x-.49,y-1.02,.98,.80,'yellow',.028);rect(x-.61,y-1.15,1.22,.16,'navy',.021)
    ellipse(x,y+.32,.64,.68,'cream',.033)
    for a,b,c in [(-.25,.25,'red'),(.2,.36,'yellow'),(0,.03,'navy'),(-.32,.55,'yellow'),(.28,.07,'red'),(.03,.63,'navy')]:ellipse(x+a,y+b,.13,.13,c,.009,n=16)
    rect(x-.4,y-.51,.8,.18,'navy',.014);ellipse(x,y-.64,.1,.1,'cream',.019);line([(x-.05,y-.64),(x+.12,y-.64)],width=.023)
    rect(x-.25,y-.93,.5,.14,'cream',.015)
    wig=.065*math.sin((t-20)*40)*math.exp(-(t-20)*5) if 20<=t<21 else 0
    transform(first,x,y-1.1,angle=wig)
def backdrop(t,empty=False):
    rect(-8,-13,16,26,'cream',0)
    # Single minimal store backdrop, with distant, deliberately featureless shoppers.
    for x,y in [(-3.7,2.25),(-.7,2.48),(1.1,2.14)]:
        ellipse(x,y,.29,.34,'ghost',0);shape([(x-.48,y-1.4),(x-.42,y-.4),(x-.2,y-.2),(x+.23,y-.2),(x+.44,y-.4),(x+.47,y-1.4)],'ghost',0)
    line([(-5,-2.0),(5,-2.0)],width=.018)
    for y in [-3.4,-4.7,-6,-7.3]:line([(-6,y),(6,y)],width=.012)
    for x in [-5,-2.5,0,2.5,5]:line([(x*.45,-2),(x,-8.7)],width=.012)
    if empty:
        # This cut frames the visibly vacant place beside the lane.
        rect(2.7,-2.7,3.1,.7,'navy',.035);line([(2.9,-2.45),(5.5,-2.45)],'lightLine',.026)
        return
    line([(-3.9,4.2),(-3.9,3.42)],width=.023);line([(-1.33,4.2),(-1.33,3.42)],width=.023)
    rect(-4.125,2.82,2.98,.70,'yellow',.032);sign_text(-3.82,2.98,'LANE 4',.42)
    # Simplified cashier chest up, wearing a vest and name badge.
    shape([(1.23,-.72),(1.3,.35),(1.7,.66),(2.78,.66),(3.1,.34),(3.2,-.72)],'navy',.032)
    rect(1.99,.52,.42,.52,'cream',.024);ellipse(2.19,1.44,.68,.76,'cream',.027)
    shape([(1.52,1.62),(1.6,2.12),(2.19,2.31),(2.82,2.02),(2.85,1.62),(2.49,1.9),(1.91,1.91)],'navy',.027)
    for ex in [1.92,2.43]:line([(ex-.11,1.42),(ex+.11,1.42)],width=.023);ellipse(ex,1.34,.045,.04,'navy',0,n=12)
    line([(2.06,1.04),(2.38,1.04)],width=.022);rect(2.5,.08,.37,.22,'yellow',.013)
    # Conveyor, divider, register and receipt printer.
    shape([(-5,-.82),(3.25,-.82),(3.84,-1.58),(-5,-1.58)],'navy',.036);rect(-5,-2.24,8.84,.66,'yellow',.032)
    line([(-4.7,-1.17),(1.44,-1.17)],'lightLine',.024);shape([(-2.8,-1.08),(-1.93,-1.08),(-1.78,-1.30),(-2.68,-1.30)],'cream',.018)
    rect(2.26,-1.39,1.14,.28,'cream',.024);rect(2.42,-1.29,.84,.08,'red',.008)
    rect(3.42,-.85,.7,1.23,'navy',.029);rect(3.50,-.21,.52,.45,'yellow',.015);line([(3.60,-.05),(3.93,-.05)],width=.019)
    rect(3.51,-1.42,.76,.36,'cream',.023);rect(3.58,-1.10,.46,.17,'navy',.016)
    # One cereal box; cashier scans it twice, exactly on both beep cues.
    if t<2.5:bx=.69
    elif t<3:bx=mix(.69,2.70,smooth((t-2.5)/.5))
    elif t<3.4:bx=mix(2.70,2.05,smooth((t-3)/.4))
    elif t<4.125:bx=mix(2.05,2.70,smooth((t-3.4)/.7))
    else:bx=mix(2.70,3.12,smooth((t-4.125)/.6))
    shape([(2.77,.31),(2.96,.05),(bx+.22,-.19),(bx+.02,-.11),(2.7,.0)],'cream',.024)
    rect(bx-.27,-1.02,.56,.91,'yellow',.025);rect(bx-.2,-.44,.42,.23,'navy',.012)
    ellipse(bx,-.74,.14,.09,'cream',.017);line([(bx-.16,-.26),(bx+.16,-.26)],width=.017)
    if any(0<=t-c<2/24 for c in [3,4.125]):line([(2.35,-1.19),(3.22,-.04)],'redLine',.055)
    # Side candy rack, kept small and outside the protagonist silhouette.
    rect(3.34,-4.55,.94,1.57,'cream',.028)
    for row in range(3):
        for col in range(3):rect(3.43+col*.26,-4.4+row*.44,.18,.30,'yellow' if col%2==0 else 'navy',.009)
    gumball(t)
def kid(t):
    x=-.28;y=.29
    # All poses retain the recurring character's approved facial/hair geometry.
    panic=t>=10;frozen=t>=16
    turn=0
    if 5<=t<6.4:turn=-1.9*smooth((t-5)/.45)
    elif 6.4<=t<7.65:turn=mix(-1.9,1.9,smooth((t-6.4)/.4))
    elif 8.15<=t<10:turn=mix(1.9,0,smooth((t-8.15)/.55))
    # Sneakers, shorts, striped T-shirt, rigid arms and reusable bag.
    rect(x-.58,-3.99,.30,.89,'cream',.027);rect(x+.25,-3.99,.30,.89,'cream',.027)
    for xx in [x-.63,x+.21]:
        shape([(xx,-4.0),(xx+.36,-4),(xx+.53,-4.2),(xx+.5,-4.34),(xx-.14,-4.34),(xx-.16,-4.1258)],'cream',.03)
        line([(xx-.13,-4.22),(xx+.49,-4.22)],width=.02);line([(xx+.15,-4.05),(xx+.31,-4.1252)],width=.019)
    shape([(x-.75,-2.53),(x+.74,-2.53),(x+.62,-3.4),(x+.12,-3.4),(x,-3.07),(x-.14,-3.4),(x-.66,-3.4)],'navy',.032)
    shape([(x-.76,-2.59),(x-.83,-.89),(x-.50,-.49),(x+.49,-.49),(x+.83,-.89),(x+.75,-2.59)],'cream',.034)
    for yy in [-1.10,-1.48,-1.86,-2.24]:rect(x-.74,yy,1.48,.14,'navy',0)
    rect(x-.23,-.68,.46,.52,'cream',.026)
    for side in [-1,1]:
        armx=x+side*.85
        shape([(armx-side*.16,-.85),(armx+side*.20,-1.03),(armx+side*.21,-2.48),(armx-side*.11,-2.49)],'cream',.028)
        ellipse(armx+side*.03,-2.55,.18,.24,'cream',.024)
    bagx=x+1.3
    curve([(bagx-.32,-2.88),(bagx-.47,-2.25),(bagx+.03,-2.26),(bagx+.3,-2.88)],width=.032)
    shape([(bagx-.48,-2.81),(bagx+.48,-2.81),(bagx+.57,-3.98),(bagx-.56,-3.98)],'cream',.032)
    ellipse(bagx,-3.38,.18,.20,'yellow',.018);line([(bagx,-3.25),(bagx,-3.52)],width=.022)
    first=len(strokes);head(x,y,'calm',turn,t);strokes.pop()
    # Eyes grow while pupils shrink: the same face, progressively more panicked acting.
    growth=.22*smooth((t-8.4)/1.6)+.46*smooth((t-10)/1.6)
    for i in range(first,len(strokes)):
        pts,mat,w,closed=strokes[i]
        if mat==indices['white'] and len(pts)==40:
            ex=sum(p[0] for p in pts)/len(pts);ey=sum(p[1] for p in pts)/len(pts)
            strokes[i]=([(ex+(a-ex)*(1+growth),ey+(b-ey)*(1+growth*1.4)) for a,b in pts],mat,w,closed)
        elif mat==indices['ink'] and len(pts)==24:
            ex=sum(p[0] for p in pts)/len(pts);ey=sum(p[1] for p in pts)/len(pts);shrink=1-.5*min(growth/.68,1)
            strokes[i]=([(ex+(a-ex)*shrink,ey+(b-ey)*shrink) for a,b in pts],mat,w,closed)
    if frozen:
        ellipse(x,y-.53,.29,.40,'navy',.025);ellipse(x,y-.75,.14,.09,'red',0)
    elif panic:ellipse(x,y-.57,.14,.095,'navy',.017)
    else:curve([(x-.27,y-.50),(x,y-.55),(x+.28,y-.5)],width=.025)
    if panic:
        drop=.4*smooth((t-10)/3.5);sx=x+1.03;sy=y+.62-drop
        shape([(sx,sy+.28),(sx+.15,sy-.08),(sx+.09,sy-.23),(sx-.09,sy-.23),(sx-.15,sy-.08)],'red',.022)
        line([(x-.75,y-.4),(x-.75,y-.56)],'redLine',.018)
    transform(first,x,y,scale=.80,angle=.055*turn)
    if frozen:
        for i in range(12):
            a=2*math.pi*i/12;r=1.17
            cx=x+r*math.cos(a);cy=y+.12+r*math.sin(a)
            line([(cx,cy),(cx+.27*math.cos(a+.13),cy+.27*math.sin(a+.13)),(cx+.22*math.cos(a),cy+.22*math.sin(a)),(cx+.53*math.cos(a),cy+.53*math.sin(a))],'redLine',.026)
def draw(t,frame):
    global strokes
    strokes=[];empty=7.65<=t<8.15
    if 10<=t<16:rect(-8,-13,16,26,'cream',0)
    else:backdrop(t,empty)
    if not empty:kid(t)
    # Push in, cut away to Mom's empty spot, then an extreme face close-up.
    if empty:
        transform(1,-.9,-4.1,1.65,dx=.9,dy=3.3)
    elif 5<=t<10:
        z=1+.30*smooth((t-5)/1.2);transform(1,-.28,.29,z,dy=-.3*(z-1))
    elif 10<=t<16:
        z=3.0+.25*smooth((t-10)/1.0);jitter=.055 if frame in [241,242,313,314] else 0
        transform(1,-.28,.29,z,dx=.28+(-1 if frame%2 else 1)*jitter,dy=-1.15+jitter)
        rect(-8,-13,16,26,'tint',0)
    elif t>=16:
        # Whole-body bolt-upright freeze, with two two-frame emergency alerts.
        if frame in [385,386,433,434]:rect(-8,-13,16,26,'alert',0)
    if t>=20:rect(-3.25,-6.60,6.5,.60,'yellow',.024)
    d=layer.frames.new(frame).drawing;d.add_strokes([len(p) for p,_,_,_ in strokes])
    for j,(pts,mat,w,closed) in enumerate(strokes):
        st=d.strokes[j];st.material_index=mat;st.cyclic=closed;st.fill_id=j+1 if closed else 0;st.fill_opacity=1
        if w==0:st.hide_stroke=True
        for p,(x,y) in zip(st.points,pts):p.position=(x,y,j*.001);p.radius=w;p.opacity=1
    d.tag_positions_changed()
for frame in range(1,529):
    draw((frame-1)/24,frame)
    if frame%48==0:print('BUILD_FRAME',frame,flush=True)
main=mesh_caption(s,'When you lose your mom\nin the grocery store\ncheckout line','CAPTION_EP005_Main',baseline=7.10,size=.53,outline=0);caption_outline(main)
main['style']='Arial Black, white, thick black outline. Top 30% of this episode.'
tag=mesh_caption(s,'MISSION: FIND MOM — INITIATED.','CAPTION_EP005_Tag',baseline=-6.35,size=.31,outline=0);caption_outline(tag)
for ob,keys in [(main,[(1,0),(25,1)]),(tag,[(1,0),(480,0),(481,0),(489,1)])]:
    for la in ob.data.layers:
        for fr,value in keys:la.opacity=value;la.keyframe_insert(data_path='opacity',frame=fr)
ed=s.sequence_editor_create();snd=ed.strips.new_sound('EP005 Original synchronized sound',str(EP/'audio/EP005_Checkout_Original_Sound_48k.wav'),channel=1,frame_start=1)
snd.sound.filepath='//../audio/EP005_Checkout_Original_Sound_48k.wav'
for label,fr in [('Setup',1),('Scanner 1',73),('Scanner 2',100),('Look for Mom',121),('Heartbeat starts',145),('Empty spot',185),('Panic close-up',241),('Digital silence',337),('AWOOGA 1',385),('AWOOGA 2',433),('Mission stamp',481)]:s.timeline_markers.new(label,frame=fr)
obj['character_reference']='Younger role variant of approved School_Guy_2D: exact inherited face/hair geometry, striped T-shirt, shorts and sneakers.'
s['production_spec']='22 seconds; 528 frames; 1080x1920; 24fps; GPU Eevee; native editable Grease Pencil; original packed stereo sound.'
s['art_palette']='cream F6EBD6, navy 202D46, red E74C50, yellow F5CE56; requested distant grey silhouettes and white/black captions.'
bpy.ops.file.pack_all();s.frame_set(49);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP005_Checkout_GP_v002.blend'),compress=True)
for frame in [49,185,289,405,505]:
    s.frame_set(frame);s.render.filepath=str(EP/'previews'/f'EP005_Review_{frame:04d}.png');bpy.ops.render.render(write_still=True)
print('EP005_BUILD_COMPLETE',flush=True)

