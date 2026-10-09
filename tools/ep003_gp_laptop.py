"""Original editable Grease Pencil short, drawn on ones at 60fps."""
import bpy, math, json, sys, hashlib, time
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parent.parent
EP=ROOT/'02_EPISODES/EP003_Gaming_Laptop_GP'
for folder in ['blend','audio','previews','renders/frames_1080p60','edit']:(EP/folder).mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='render':
    s=bpy.data.scenes['EP003_Gaming_Laptop_GreasePencil'];bpy.context.window.scene=s
    assert s.render.engine=='BLENDER_EEVEE' and s.render.fps==60
    s.render.filepath=str(EP/'renders/frames_1080p60/EP003_######')
    def progress(scene,*args):
        if scene.frame_current%20==0:
            (EP/'edit/render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'total':660,'resolution':[1080,1920],'fps':60}))
    bpy.app.handlers.render_write.append(progress);bpy.ops.render.render(animation=True)
    import gpu
    print('ACTUAL_GPU',gpu.platform.renderer_get(),gpu.platform.vendor_get(),flush=True)
    print('GP_RENDER_COMPLETE',flush=True);sys.exit(0)

# Save an episode copy first, retaining the existing production assets in their original scene.
protected=[p for top in ['00_LIBRARY','01_TEMPLATES'] for p in (ROOT/top).rglob('*') if p.is_file()]
protected.extend((ROOT/'02_EPISODES/EP001_Material_Test').rglob('*.blend'))
protected.extend((ROOT/'02_EPISODES/EP002_Impossible_Blankets/blend').glob('*.blend'))
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
(EP/'edit/protected_hashes.json').write_text(json.dumps(hashes,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP003_Gaming_Laptop_GP_v001.blend'),compress=True)
s=bpy.data.scenes.new('EP003_Gaming_Laptop_GreasePencil');bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=60;s.frame_start=1;s.frame_end=660
s.eevee.taa_render_samples=8;s.eevee.use_raytracing=False;s.render.use_motion_blur=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=10
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
s.world=bpy.data.worlds.new('EP003_FlatWorld');s.world.color=(.2,.1,.06)
camdata=bpy.data.cameras.new('CAM_EP003_2D');cam=bpy.data.objects.new('CAM_EP003_2D',camdata);s.collection.objects.link(cam);cam.location=(0,0,30);camdata.type='ORTHO';camdata.ortho_scale=16;camdata.lens=50;s.camera=cam

def color(hexcode):
    rgb=[int(hexcode[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb)+(1,)
INK='28252D';palette={
'wall':'D47A5A','wallShade':'BB654E','panel':'F8E8CE','ink':INK,'desk':'A56745','deskTop':'C88A5A','deskEdge':'784B38','skin':'F1BD91','skinShade':'D98F6F','hair':'302D35','hairLight':'50444A','shirt':'568594','shirtShade':'386571','shirtLight':'77A3AA','white':'FFF8E7','red':'FF4E4F','redDark':'BD343E','laptop':'34343D','laptopDark':'20212B','laptopLight':'4A4A54','silver':'C9D2D6','silverShade':'A2ACB4','silverLight':'E9EFF0','window':'A7C4CD','blind':'F1D8B3','sweat':'93D9E3','shadow':'B1664C'}
gp=bpy.data.grease_pencils.new('EP003_Original_2D_Drawings');obj=bpy.data.objects.new('GP_EP003_Characters_Set_Laptops',gp);s.collection.objects.link(obj)
indices={}
for name,h in palette.items():
    m=bpy.data.materials.new('GP_EP003_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.show_fill=True;m.grease_pencil.fill_color=color(h);m.grease_pencil.color=color(INK);m.grease_pencil.show_stroke=True;obj.data.materials.append(m);indices[name]=len(obj.data.materials)-1
for name,h in [('line',INK),('redLine','FF4E4F'),('chalk','F6DEC4'),('lightLine','C48B71')]:
    m=bpy.data.materials.new('GP_EP003_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.show_fill=False;m.grease_pencil.color=color(h);obj.data.materials.append(m);indices[name]=len(obj.data.materials)-1
layer=gp.layers.new('Animation - 60fps drawings',set_active=True);layer.use_lights=False
strokes=[]
def shape(points,mat='skin',width=.027,closed=True):strokes.append((points,indices[mat],width,closed))
def line(points,mat='line',width=.025):shape(points,mat,width,False)
def ellipse(x,y,rx,ry,mat='skin',width=.027,n=40):shape([(x+rx*math.cos(i*2*math.pi/n),y+ry*math.sin(i*2*math.pi/n)) for i in range(n)],mat,width)
def rect(x,y,w,h,mat,width=.027):shape([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],mat,width)
def curve(points,n=24,mat='line',width=.026):
    # Quadratic/cubic Bezier, used for brows, mouths and gestures.
    pts=[]
    for i in range(n):
        t=i/(n-1)
        if len(points)==3:
            w=[(1-t)**2,2*(1-t)*t,t*t]
        else:w=[(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3]
        pts.append(tuple(sum(w[k]*points[k][j] for k in range(len(points))) for j in range(2)))
    line(pts,mat,width)
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def mix(a,b,t):return a+(b-a)*t

def background(classmate=False):
    rect(-5,-9,10,18,'wall',0)
    rect(-5,-6,10,2.4,'wallShade',0)
    line([(-4.6,-3.65),(4.6,-3.65)],'lightLine',.018)
    if classmate:
        rect(-3.85,.9,3.2,4.05,'deskEdge',.035);rect(-3.65,1.1,2.8,3.65,'window',.02)
        for y in [1.35+i*.36 for i in range(10)]:rect(-3.65,y,2.8,.18,'blind',.012)
        line([(-.5,4.7),(-.5,1.45)],width=.018);ellipse(-.5,1.4,.05,.1,'deskEdge',.015)
    else:
        rect(.6,3.25,3.0,1.5,'wallShade',.03);rect(.78,3.44,2.63,1.1,'panel',.018)
        line([(1.0,4.2),(3.1,4.2)],'lightLine',.018);line([(1.0,3.95),(2.7,3.95)],'lightLine',.018);line([(1.0,3.7),(2.9,3.7)],'lightLine',.018)
        ellipse(-3.0,4,.58,.58,'panel',.028);ellipse(-3,4,.035,.035,'ink',0);line([(-3,4),(-3,4.32)],width=.02);line([(-3,4),(-2.73,3.89)],width=.02)
        for a in range(12):
            t=a*math.pi/6;line([(-3+.47*math.sin(t),4+.47*math.cos(t)),(-3+.52*math.sin(t),4+.52*math.cos(t))],width=.009)
    # Chair and desk are flat drawings, not 3D geometry.
    rect(-2.65,-4.7,2.9,4,'deskEdge',.04);rect(-2.45,-4.5,2.5,3.7,'deskTop',.025)

def torso(x=-1.05,raised=False):
    shape([(x-1.18,-2.9),(x-1.17,-.8),(x-.78,-.32),(x+.8,-.32),(x+1.17,-.85),(x+1.23,-2.9)],'shirt',.04)
    shape([(x-.75,-.45),(x-.45,-1.3),(x+.28,-1.6),(x+.74,-.45),(x+.46,-.2),(x-.44,-.2)],'shirtShade',.026)
    line([(x-.75,-.42),(x-.23,-1.11),(x+.15,-1.11),(x+.73,-.42)],width=.025)
    line([(x-.25,-1.18),(x-.28,-1.73)],'chalk',.017);line([(x+.18,-1.18),(x+.2,-1.68)],'chalk',.017)
    rect(x-.33,-.45,.65,.75,'skin',.03)

def head(x,y,expression='strain',turn=0,t=0):
    # Matching face/hair design for both characters; only the acting changes.
    ellipse(x-1.04,y-.05,.2,.29,'skinShade',.027);ellipse(x+1.04,y-.05,.2,.29,'skinShade',.027)
    shape([(x-1.02,y+.7),(x-.8,y+1.07),(x-.2,y+1.18),(x+.65,y+1.07),(x+1.04,y+.59),(x+.99,y-.59),(x+.62,y-.91),(x-.48,y-.98),(x-.9,y-.68)],'skin',.037)
    shape([(x-1.04,y+.2),(x-1.18,y+.81),(x-.91,y+1.2),(x-.29,y+1.42),(x+.0,y+1.18),(x+.79,y+1.23),(x+1.1,y+.88),(x+.93,y+.35),(x+.66,y+.73),(x+.25,y+.63),(x-.1,y+.98),(x-.47,y+.65),(x-.82,y+.68),(x-.81,y+.18)],'hair',.035)
    curve([(x-.94,y+1.03),(x-.62,y+1.27),(x-.4,y+1.2)],mat='lightLine',width=.019)
    eye_y=y+.1
    worried=expression in ['strain','panic'];startled=expression=='alarm'
    for ex in [x-.46,x+.48]:
        if expression=='annoyed':
            ellipse(ex,eye_y,.28,.15,'white',.022)
            line([(ex-.29,eye_y+.12),(ex+.29,eye_y+.06)],width=.035)
        else:ellipse(ex,eye_y,.27,.28 if startled else .22,'white',.022)
        ellipse(ex+turn*.11,eye_y-.02,.07,.115 if startled else .095,'ink',0,n=24)
    if worried:
        line([(x-.76,y+.5),(x-.24,y+.64)],width=.04);line([(x+.25,y+.64),(x+.78,y+.5)],width=.04)
    elif expression=='annoyed':
        line([(x-.75,y+.56),(x-.23,y+.42)],width=.04);line([(x+.23,y+.42),(x+.78,y+.56)],width=.04)
    else:
        curve([(x-.75,y+.54),(x-.44,y+.77),(x-.21,y+.61)],width=.035);curve([(x+.2,y+.61),(x+.46,y+.77),(x+.76,y+.54)],width=.035)
    curve([(x+.02,y+.07),(x+.14,y-.19),(x+.02,y-.22)],width=.02)
    if expression=='strain':
        curve([(x-.36,y-.5),(x-.03,y-.41),(x+.37,y-.56)],width=.026)
        line([(x-.31,y-.6),(x+.27,y-.62)],width=.018)
    elif expression in ['panic','alarm']:
        ellipse(x+.02,y-.52,.19,.18 if expression=='alarm' else .11,'ink',.018)
    else:curve([(x-.28,y-.53),(x,y-.45),(x+.29,y-.52)],width=.027)
    if expression=='panic':
        shape([(x+.99,y+.85),(x+1.15,y+.5),(x+1.02,y+.38),(x+.93,y+.53)],'sweat',.02)
        line([(x+.78,y-.38),(x+.78,y-.56)],'redLine',.012)

def desktop():
    shape([(-4.7,-2.68),(4.7,-2.68),(4.7,-4.1),(-4.7,-4.1)],'deskTop',.035)
    rect(-4.7,-7.6,9.4,3.5,'desk',.035);rect(-4.7,-4.25,9.4,.22,'deskEdge',.025)
    line([(-3.8,-5.2),(-1.9,-5.2)],'lightLine',.016);line([(1.8,-6.9),(3.6,-6.9)],'lightLine',.016)

def laptop(opening,t,mac=False,vibration=0):
    dx=vibration*math.sin(t*math.pi*36);dy=vibration*.35*math.sin(t*math.pi*47)
    left=.2+dx;right=3.05+dx;bottom=-2.5+dy;height=.18+opening*2.7
    base='silver' if mac else 'laptop';shade='silverShade' if mac else 'laptopDark';light='silverLight' if mac else 'laptopLight'
    shape([(left-.48,bottom-.03),(right-.2,bottom-.03),(right+.48,bottom-.63),(left-.34,bottom-.63)],light,.035)
    shape([(left-.34,bottom-.63),(right+.48,bottom-.63),(right+.48,bottom-(.71 if mac else .91)),(left-.34,bottom-(.71 if mac else .91))],shade,.025)
    if not mac:
        for i in range(8):line([(left+.65+i*.23,bottom-.68),(left+.7+i*.23,bottom-.84)],'redLine',.012)
        line([(left-.14,bottom-.82),(left+.25,bottom-.82)],'redLine',.019)
    corners=[(left,bottom),(right,bottom),(right-.23,bottom+height),(left+.13,bottom+height+.12)]
    shape(corners,base,.043 if not mac else .026)
    if opening>.3:
        line([(left+.25,bottom+height-.12),(right-.42,bottom+height-.22)],'lightLine',.013)
        cx=(left+right)/2;cy=bottom+height*.53
        if mac:
            ellipse(cx,cy,.16,.19,'silverLight',.008);shape([(cx+.04,cy+.24),(cx+.18,cy+.34),(cx+.12,cy+.19)],'silverLight',.006)
        else:
            shape([(cx-.26,cy+.26),(cx+.03,cy+.07),(cx+.25,cy+.2),(cx+.12,cy-.21),(cx-.06,cy-.09),(cx-.28,cy-.24)],'red',.012)
            line([(cx-.26,cy+.26),(cx+.03,cy+.07),(cx+.25,cy+.2)],'redLine',.03)
    if vibration>.008:
        for side in [-1,1]:
            xx=left-.22 if side<0 else right+.25
            curve([(xx,bottom+.6),(xx+side*.24,bottom+1.1),(xx,bottom+1.6)],mat='redLine',width=.025)

def arm(points,mat='shirt'):shape(points,mat,.033)

def draw_main(t):
    background();torso()
    bury=smooth((t-4.87)/.53)
    expression='strain' if t<3 else 'panic'
    if bury<.99:
        hx=mix(-1.16,-1.65,bury);hy=mix(1.5,-1.37,bury)
        head(hx,hy,expression,turn=.3,t=t)
    else:
        # Face is hidden against the sleeve; the back of the head remains readable.
        ellipse(-1.55,-1.47,1.05,.65,'skin',.034)
        shape([(-2.55,-1.6),(-2.63,-1.17),(-2.35,-.86),(-1.89,-.74),(-1.42,-.89),(-.84,-.82),(-.53,-1.12),(-.58,-1.46),(-.98,-1.66),(-1.48,-1.46),(-1.77,-1.69),(-2.17,-1.47)],'hair',.032)
        curve([(-2.3,-1.05),(-1.91,-.88),(-1.58,-1.02)],mat='lightLine',width=.018)
    desktop()
    if t<3:opening=.10+.28*smooth(t/2)
    else:opening=.38+.46*smooth((t-3)/1.45)
    height=.18+opening*2.7;top=-2.5+height+.12
    if bury<.5:
        arm([(-2.15,-.79),(-2.4,-1.3),(-1.52,-2.7),(-.48,-2.91),(-.26,-2.49),(-1.19,-2.26),(-1.51,-1.21)],'shirtShade')
        ellipse(-.26,-2.64,.33,.23,'skin',.026)
        arm([(-.24,-.64),(.12,-1.04),(.46,top-.23),(.95,top-.15),(.71,-1.61),(-.2,-2.03)],'shirt')
    else:
        arm([(-2.82,-2.11),(-2.66,-1.74),(-.52,-1.92),(.15,-2.62),(-.32,-2.97),(-1.0,-2.45),(-2.5,-2.62)],'shirt')
        line([(-2.5,-2.26),(-1.22,-2.4)],'chalk',.018)
        ellipse(.05,-2.7,.35,.23,'skin',.027)
        arm([(-2.75,-2.41),(-2.48,-2.86),(-.72,-2.94),(-.43,-2.6),(-.64,-2.27)],'shirtShade')
    vib=(.035+.035*math.sin(t*9)**2) if t>=5 else 0
    laptop(opening,t,vibration=vib)
    if bury<.5:
        ellipse(.67,top+.04,.28,.19,'skin',.027)
        for i in range(2):line([(.48+i*.12,top-.08),(.56+i*.12,top+.12)],width=.014)
    if t>=5:
        for i in range(3):
            x=2.55+i*.27;h=.22+.14*math.sin(t*15+i)
            curve([(x,-2.79),(x+.14,-2.72+h),(x,-2.6+h)],mat='redLine',width=.021)

def draw_classmate(t):
    background(True);torso(x=-.74)
    if t<3:
        u=smooth((t-2)/.15);head(-.74-.15*u,1.5,'annoyed',turn=-u,t=t)
        if t<2.23:
            for y in [1.0,1.4]:line([(1.05,y),(1.45,y+.13)],width=.022)
    else:
        u=smooth((t-6.8)/.18);head(-.74-.13*u,1.53+.10*math.sin(t*2),'alarm',turn=-.9,t=t)
        line([(-2.24,2.84),(-2.51,3.14)],width=.035);line([(-2.58,2.44),(-2.96,2.57)],width=.035)
    desktop()
    arm([(-1.8,-.73),(-2.18,-1.2),(-1.76,-2.66),(-.51,-2.87),(-.37,-2.51),(-1.4,-2.17),(-1.27,-1.03)],'shirtShade');ellipse(-.34,-2.67,.3,.21,'skin',.026)
    arm([(.19,-.81),(.66,-1.27),(.85,-2.67),(.46,-2.88),(.17,-2.05),(-.14,-1.07)],'shirt');ellipse(.65,-2.66,.3,.21,'skin',.026)
    laptop(.82,t,mac=True)

def commit(frame):
    drawing=layer.frames.new(frame).drawing;drawing.add_strokes([len(x[0]) for x in strokes])
    for j,(points,mat,width,closed) in enumerate(strokes):
        st=drawing.strokes[j];st.material_index=mat;st.cyclic=closed;st.fill_id=j+1 if closed else 0;st.fill_opacity=1
        for i,(x,y) in enumerate(points):
            p=st.points[i];p.position=(x,y,j*.001);p.radius=width;p.opacity=1
    drawing.tag_positions_changed()

for frame in range(1,661):
    t=(frame-1)/60;strokes=[]
    reaction=(2<=t<3) or (6.8<=t<8.35) or (9.45<=t<10.05)
    draw_classmate(t) if reaction else draw_main(t)
    commit(frame)
    if frame%60==0:print('GP_DRAWN',frame,flush=True)

# Caption is native editable text, always visible and word-for-word as requested.
header=gp.layers.new('Constant caption panel',set_active=True);header.use_lights=False
old=layer;layer=header;strokes=[];rect(-4.5,5.37,9,2.63,'panel',0);line([(-3.95,5.55),(3.95,5.55)],'redLine',.035);commit(1);layer=old
font=bpy.data.fonts.load(r'C:/Windows/Fonts/arialbd.ttf');font.pack()
caption=bpy.data.curves.new('TXT_EP003_Exact_POV_Caption','FONT');caption.body='Pov: You bring a gaming\nlaptop to school instead of\nthe normal mac book';caption.font=font;caption.size=.52;caption.align_x='CENTER';caption.align_y='TOP_BASELINE';caption.space_line=1.2
text=bpy.data.objects.new('TXT_EP003_Constant_Caption',caption);s.collection.objects.link(text);text.location=(0,7.32,1)
m=bpy.data.materials.new('MAT_EP003_Caption_Ink');m.diffuse_color=color(INK);m.use_nodes=True;nodes=m.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=color(INK);m.node_tree.links.new(em.outputs[0],out.inputs[0]);caption.materials.append(m)

cuts=[(1,'01 SETUP - hinge squeak'),(121,'02 REACTION - high whine'),(181,'03 STRUGGLE - silence'),(301,'04 STARTUP - sputter then roar'),(409,'05 CLASSMATE - alarm'),(502,'06 HIDING - engine idle'),(568,'07 CLASSMATE - disbelief'),(604,'08 FINAL - embarrassment')]
for frame,label in cuts:s.timeline_markers.new(label,frame=frame)
sound=EP/'audio/EP003_Original_Laptop_SoundDesign_v001.wav'
if sound.exists():
    editor=s.sequence_editor_create();strip=editor.strips.new_sound('Original hinge and engine - synchronized',str(sound),channel=1,frame_start=1);strip.sound.filepath='//../audio/'+sound.name;strip.volume=1
s.render.use_sequencer=False
s['caption_exact']='Pov: You bring a gaming laptop to school instead of the normal mac book';s['medium']='Native editable Grease Pencil strokes and fills; two matching character designs, animated at 60fps.';s['sound_timing']='Hinge 0-3s; quiet struggle 3-5s; engine starts exactly 5s, roars through 11s.'
s.frame_set(75);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP003_Gaming_Laptop_GP_v002.blend'),compress=True)
report={'resolution':[1080,1920],'fps':60,'frames':660,'duration_seconds':11,'medium':'Native Grease Pencil','drawings':len(old.frames),'caption':s['caption_exact'],'cut_frames':[f for f,label in cuts],'audio':'Original synthesized hinge, whine, engine sputter and roar','protected_files':len(hashes)}
(EP/'edit/build_report.json').write_text(json.dumps(report,indent=2))
for f in [75,145,255,340,440]:
    s.frame_set(f);s.render.filepath=str(EP/'previews'/f'EP003_Review_{f:04d}.png');bpy.ops.render.render(write_still=True)
print('GP_BUILD_REVIEW_COMPLETE',flush=True)
