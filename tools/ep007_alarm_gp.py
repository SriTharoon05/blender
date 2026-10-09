"""Original native GP alarm comedy, high safe captions and GPU render timing."""
import bpy,math,ast,json,sys,time,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP007_Alarm_Expectation_Reality'
for folder in ['blend','audio','previews','renders/frames_1080p24','edit']:(EP/folder).mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='render':
    s=bpy.data.scenes['EP007_Alarm_Expectation_Reality'];bpy.context.window.scene=s;s.render.filepath=str(EP/'renders/frames_1080p24/EP007_######')
    def progress(scene,*args):
        if scene.frame_current%12==0:(EP/'edit/render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'total':432,'elapsed_seconds':time.perf_counter()-started}))
    bpy.app.handlers.render_write.append(progress);started=time.perf_counter();bpy.ops.render.render(animation=True);elapsed=time.perf_counter()-started
    import gpu
    data={'render_seconds':elapsed,'frames':432,'video_seconds':18,'renderer':'Eevee','gpu':gpu.platform.renderer_get(),'average_seconds_per_frame':elapsed/432,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (EP/'edit/render_time.json').write_text(json.dumps(data,indent=2));print('EP007_RENDER_COMPLETE',data,flush=True);sys.exit(0)
sys.path.insert(0,str(ROOT/'tools'));from shorts_caption_safe_area import place_caption
def extract(file,names):
    for node in ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8-sig')).body:
        if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
extract('ep003_gp_laptop.py',{'color','shape','line','ellipse','rect','curve','smooth','mix','head'})
extract('ep004_keyboard_gp.py',{'mesh_caption'});extract('ep004_polish.py',{'caption_outline'})
protected=[p for top in ['00_LIBRARY','01_TEMPLATES'] for p in (ROOT/top).rglob('*') if p.is_file()]
protected.extend(p for p in (ROOT/'02_EPISODES').rglob('*.blend') if 'EP007' not in str(p))
(EP/'edit/protected_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},indent=2))
assert not (EP/'blend/EP007_Alarm_GP_v001.blend').exists();bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP007_Alarm_GP_v001.blend'),compress=True)
s=bpy.data.scenes.new('EP007_Alarm_Expectation_Reality');bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=432
s.eevee.taa_render_samples=8;s.eevee.use_raytracing=False;s.render.use_motion_blur=False;s.render.use_sequencer=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=50;s.render.filepath='//../renders/frames_1080p24/EP007_######'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.world=bpy.data.worlds.new('EP007_BedroomWorld');s.world.color=color('E9E1D8')[:3]
cd=bpy.data.cameras.new('CAM_EP007_Alarm');cd.type='ORTHO';cd.ortho_scale=16;camera=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(camera);camera.location=(0,0,30);s.camera=camera
INK='292B36';palette={'wall':'E9E1D8','wallWarm':'F2E5CE','floor':'D5C5AE','wood':'AF9476','woodDark':'89745F','sky':'CADDEA','skyWarm':'E1EBDB','curtain':'B3BFBC','bed':'8B919E','bedEdge':'6B7181','blanket':'789CAF','blanketShade':'577B92','pillow':'F8F1E5','shirt':'94B6C6','shirtShade':'7394A8','skin':'F1BD91','skinShade':'D98F6F','hair':'302D35','ink':INK,'white':'FFF9EA','eyeBag':'A395B3','blood':'CB6263','drool':'A5D9DF','gold':'EBCF72','screen':'AECBC4','black':'000000'}
gp=bpy.data.grease_pencils.new('GP_EP007_Bedroom_Acting');gp.stroke_depth_order='2D';obj=bpy.data.objects.new(gp.name,gp);s.collection.objects.link(obj);indices={}
for name,h in list(palette.items())+[('line',INK),('lightLine','CAB19A'),('redLine','CB6263'),('blueLine','7DAFCA'),('clockLine','294B49')]:
    m=bpy.data.materials.new('GP_EP007_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.fill_color=color(h);m.grease_pencil.color=color(h if name.endswith('Line') else INK);gp.materials.append(m);indices[name]=len(gp.materials)-1
layer=gp.layers.new('Peaceful morning / elastic launch / zombie / collapse',set_active=True);layer.use_lights=False;strokes=[];HORNS=[7,8.75,10.25,11.75,13.25]
def transform(first,cx,cy,sx=1,sy=1,dx=0,dy=0,angle=0):
    ca,si=math.cos(angle),math.sin(angle)
    for i in range(first,len(strokes)):
        pts,mat,w,closed=strokes[i];strokes[i]=([(cx+sx*(a-cx)*ca-sy*(b-cy)*si+dx,cy+sx*(a-cx)*si+sy*(b-cy)*ca+dy) for a,b in pts],mat,w*min(sx,sy),closed)
def shock(t):return sum(math.exp(-(t-at)*15) for at in HORNS if 0<=t-at<.4)
def bird(x,y,t,offset):
    yy=y+.07*math.sin(t*5+offset);ellipse(x,yy,.16,.10,'pillow',.013,n=20)
    flap=.16*math.sin(t*11+offset);line([(x-.07,yy),(x-.22,yy+.11+flap)],width=.022);line([(x+.04,yy),(x+.15,yy+.13+flap)],width=.020)
    shape([(x+.13,yy+.02),(x+.25,yy+.015),(x+.14,yy-.035)],'gold',.008);ellipse(x+.06,yy+.03,.023,.023,'ink',0,n=10)
def room(t,close=False):
    rect(-6,-10,12,20,'wallWarm' if t<6 and t>2 else 'wall',0)
    rect(-6,-9,12,3.33,'floor',0);line([(-5,-5.67),(5,-5.67)],width=.019)
    # Window and curtains sit beneath the caption area, not behind the words.
    if not close:
        rect(-3.95,.98,2.67,1.84,'woodDark',.028);rect(-3.78,1.15,2.33,1.50,'skyWarm' if t<6 else 'sky',.018)
        line([(-2.63,1.15),(-2.63,2.65)],width=.024);line([(-3.78,1.86),(-1.45,1.86)],width=.020)
        shape([(-4.13,2.91),(-3.68,2.91),(-3.75,1.40),(-4.12,1.08)],'curtain',.024)
        shape([(-1.57,2.91),(-1.1,2.91),(-1.13,1.08),(-1.5,1.40)],'curtain',.024)
        line([(-4.19,2.96),(-1.0,2.96)],width=.030)
    if 1<=t<6:
        bird(-3.26,2.16,t,0);bird(-2.02,2.26,t,1.7)
    # Lamp, bedside table and a face-up smartphone.
    ellipse(3.66,-1.78,.43,.11,'woodDark',.020);line([(3.66,-1.71),(3.65,-.17)],width=.039)
    shape([(3.24,.22),(3.97,.22),(4.16,-.30),(3.02,-.30)],'gold' if t<6 else 'curtain',.026)
    rect(2.51,-2.17,1.72,.20,'wood',.029);rect(2.67,-3.17,1.37,.99,'woodDark',.025);line([(2.83,-2.52),(3.91,-2.52)],width=.018);ellipse(3.35,-2.71,.05,.04,'gold',.013)
    for xx in [2.68,3.94]:rect(xx,-4.5,.14,1.34,'woodDark',.015)
    shape([(3.57,-1.98),(4.00,-1.98),(4.10,-1.84),(3.68,-1.84)],'ink',.018);line([(3.70,-1.91),(3.94,-1.91)],'blueLine',.015)
    # Bed base and large soft pillow.
    rect(-3.14,-4.83,5.39,3.97,'bed',.034);rect(-3.26,-4.86,5.60,.34,'bedEdge',.026)
    rect(-2.95,-5.35,.22,.48,'woodDark',.021);rect(1.86,-5.35,.22,.48,'woodDark',.021)
    rect(-3.16,-1.22,5.42,1.77,'bedEdge',.032);line([(-2.93,.32),(2.03,.32)],width=.014)
    shape([(-2.45,-1.74),(.93,-1.74),(1.17,-.73),(-2.14,-.61)],'pillow',.036)
    curve([(-2.19,-1.23),(-.58,-1.49),(.81,-1.15)],mat='lightLine',width=.016)
DIGITS={0:'abcedf',1:'bc',2:'abged',3:'abgcd',4:'fgbc',5:'afgcd',6:'afgecd',7:'abc',8:'abcdefg',9:'abfgcd'}
SEG={'a':((0,1),(.65,1)),'b':((.65,1),(.65,.53)),'c':((.65,.47),(.65,0)),'d':((0,0),(.65,0)),'e':((0,0),(0,.47)),'f':((0,.53),(0,1)),'g':((0,.5),(.65,.5))}
def clock(t):
    jitter=.07*math.sin(t*81)*(.25+.75*shock(t)) if 7<=t<14 else 0
    x=2.48+jitter;y=-1.83+.02*math.sin(t*67) if 7<=t<14 else -1.83
    rect(x,y,1.64,.71,'ink',.026);rect(x+.11,y+.12,1.42,.47,'screen',.011)
    values=[6,0,1 if t>=17.5 else 0];sx=x+.20;sy=y+.20;unit=.30
    for j,value in enumerate(values):
        for seg in DIGITS[value]:line([(sx+unit*a,sy+unit*b) for a,b in SEG[seg]],'clockLine',.014)
        sx+=.30
        if j==0:
            for yy in [sy+.08,sy+.21]:ellipse(sx-.015,yy,.015,.017,'clockLine',0,n=10)
            sx+=.08
    # AM uses small stroke lettering on the display, as a physical prop label.
    ax=x+1.15;ay=y+.20
    line([(ax,ay),(ax+.055,ay+.12),(ax+.11,ay),(ax+.08,ay+.055),(ax+.03,ay+.055)],'clockLine',.009)
    line([(ax+.14,ay),(ax+.14,ay+.12),(ax+.20,ay+.06),(ax+.25,ay+.12),(ax+.25,ay)],'clockLine',.009)
    if 7<=t<14:
        for side in [-1,1]:
            xx=x+(.12 if side<0 else 1.54)+side*.25
            curve([(xx,y+.05),(xx+side*.15,y+.35),(xx,y+.65)],mat='redLine',width=.020)
def face(x,y,t,sleep=False,zombie=False,openness=1,angle=0,smile=False):
    first=len(strokes);head(x,y,'calm',turn=.30 if zombie else 0,t=t);strokes.pop()
    kept=strokes[:first]
    # Reuse the approved silhouette and hair, varying only expression features.
    for pts,mat,w,closed in strokes[first:]:
        if mat in [indices['white'],indices['ink']] and len(pts) in [40,24]:continue
        if not closed and len(pts)==24 and max(b for a,b in pts)>y+.4 and min(b for a,b in pts)>y+.4:continue
        kept.append((pts,mat,w,closed))
    strokes[:]=kept
    for ex in [x-.46,x+.48]:
        if sleep or openness<.05:
            curve([(ex-.25,y+.12),(ex,y-.01),(ex+.25,y+.12)],width=.030)
        elif zombie:
            ellipse(ex,y-.02,.37,.30,'eyeBag',.020)
            ellipse(ex,y+.12,.32,.245,'white',.023)
            for side in [-1,1]:line([(ex+side*.29,y+.17),(ex+side*.20,y+.09),(ex+side*.27,y+.02)],'redLine',.013)
            ellipse(ex+.07,y+.08,.060,.075,'ink',0,n=20)
            shape([(ex-.32,y+.36),(ex+.32,y+.36),(ex+.29,y+.15),(ex-.27,y+.21)],'skin',.020)
            line([(ex-.30,y+.51),(ex+.28,y+.44)],width=.028)
            curve([(ex-.27,y-.26),(ex,y-.38),(ex+.27,y-.26)],width=.022)
        else:
            ellipse(ex,y+.11,.28,.22*openness,'white',.023)
            ellipse(ex,y+.1,.076,.10*openness,'ink',0,n=24)
            curve([(ex-.25,y+.51),(ex,y+.70),(ex+.27,y+.54)],width=.025)
            if smile:
                line([(ex-.10,y+.16),(ex+.10,y+.04)],mat='lightLine',width=.022)
    if zombie:
        ellipse(x+.06,y-.55,.26,.30,'ink',.023);ellipse(x+.07,y-.73,.13,.055,'blood',0,n=20)
        shape([(x+.27,y-.60),(x+.35,y-.63),(x+.36,y-.88),(x+.31,y-.98),(x+.26,y-.86)],'drool',.014)
        # Angular bangs remain recognizable underneath the new sleep-mess tufts.
        for dx,dy in [(-.87,1.17),(-.46,1.36),(.32,1.20),(.83,1.06)]:
            shape([(x+dx-.17,y+dy-.17),(x+dx+.14,y+dy-.15),(x+dx+.12,y+dy+.40),(x+dx-.09,y+dy+.14)],'hair',.020)
    elif smile:
        shape([(x-.37,y-.35),(x+.39,y-.35),(x+.25,y-.68),(x-.08,y-.72),(x-.31,y-.61)],'white',.025)
        line([(x-.30,y-.49),(x+.29,y-.49)],width=.016)
    else:
        depth=-.54-.11*smooth((t-2)/.6) if sleep and t<6 else -.65
        curve([(x-.28,y-.52),(x,y+depth),(x+.29,y-.5)],width=.024)
    transform(first,x,y,.82,.82,angle=angle)
def arms(x,y,t,zombie=False,launch=0):
    flail=.85*math.sin((t-7.208333)*30)*math.exp(-max(0,t-7.5)*4) if 7.208333<=t<8.2 else 0
    reach=smooth((t-8)/1.2) if zombie else 0
    for side in [-1,1]:
        sx=x+side*.67;sy=y-.99
        if side>0 and zombie:
            ex=mix(x+1.07,2.63,reach);ey=mix(y-1.76,-.82,reach)
            if 13.72<=t<14.20:
                press=smooth((t-13.72)/.28)*(1-smooth((t-14)/.20));ey-=.14*press
        else:ex=x+side*(1.03+.15*launch);ey=y-1.79+abs(flail)*.8
        if flail:ey=y-.92+side*flail
        shape([(sx-side*.14,sy+.03),(sx+side*.24,sy-.13),(ex+side*.13,ey-.12),(ex-side*.15,ey-.18)],'shirtShade',.030)
        help_reach=smooth((t-11)/1.2) if zombie and side<0 else 0
        ellipse(ex,ey,.22+.15*help_reach,.17+.11*help_reach,'skin',.025)
        if zombie:
            line([(ex+.07,ey+.05),(ex+.25,ey+.16)],width=.037)
            line([(ex+.02,ey+.08),(ex+.18,ey+.24)],width=.026)
            if side<0 and help_reach>0:
                for j in range(3):line([(ex-.18+j*.12,ey+.10),(ex-.22+j*.13,ey+.40*help_reach)],width=.039)
def character(t):
    x=-.42;expect=t<6;sit=smooth((t-3)/.70) if expect else 0
    y=mix(-.70,.31,sit);sx=sy=1;collapse=smooth((t-16.50)/.25) if t>=16.50 else 0
    if not expect:
        if t<7:y=-1.04
        elif t<7.208333:
            q=(t-7)/.208333;y=-.91-.19*math.sin(math.pi*q);sx=1+.25*math.sin(math.pi*q);sy=1-.32*math.sin(math.pi*q)
        elif t<7.50:
            q=(t-7.208333)/.291667;y=mix(-1.04,1.19,smooth(q));sx=1-.22*math.sin(math.pi*q);sy=1+.72*math.sin(math.pi*q)
        elif t<7.95:y=mix(1.19,.15,smooth((t-7.5)/.45));sy=1-.13*math.sin(math.pi*(t-7.5)/.45)
        else:y=.15
        y=mix(y,-1.08,collapse)
    first=len(strokes);sleep=expect and t<3 or not expect and t<7
    zombie=not expect and t>=7.208333;upright=sit if expect else (1 if t>=7.208333 else 0)
    if collapse<.88:
        top=y-.95
        shape([(x-.98,top-1.74),(x-.98,top-.32),(x-.63,top),(x+.65,top),(x+1.02,top-.36),(x+.96,top-1.74)],'shirt',.034)
        rect(x-.23,y-1.04,.46,.55,'skin',.024)
        line([(x-.43,top-.58),(x-.50,top-1.51)],'blueLine',.017)
        # Pajamas are visible briefly during the launch; the duvet covers the lap.
        if not 7.208333<=t<7.95:
            shape([(x-.67,top-1.61),(x+.67,top-1.61),(x+.62,top-2.55),(x+.11,top-2.55),(x,top-2.02),(x-.13,top-2.55),(x-.63,top-2.55)],'blanketShade',.029)
        arms(x,y,t,zombie,1 if 7.208333<=t<7.95 else 0)
        face(x,y,t,sleep,zombie,openness=smooth((t-3)/.45) if expect else 1,angle=(-.12*(1-sit) if expect else -.10*collapse),smile=expect and t>=3)
        if sx!=1 or sy!=1:transform(first,x,y,sx,sy)
        # Keep the elastic launch beneath the caption/label area.
        topmax=max(b for pts,_,_,_ in strokes[first:] for a,b in pts)
        if topmax>2.98:transform(first,x,y,dy=2.98-topmax)
    else:
        # Face-first pillow impact hides the face; same angular hair peeks out.
        ellipse(-.68,-1.05,.81,.36,'hair',.031)
        shape([(-1.35,-1.05),(-1.39,-.75),(-.94,-.63),(-.61,-.68),(-.30,-.55),(.1,-.79),(.10,-1.07)],'hair',.031)
    return upright,collapse
def duvet(t,upright,collapse):
    top=-1.17-1.22*upright*(1-collapse)
    if t>=6 and t<7.208333:top=-1.12
    flutter=.13*shock(t) if 7<=t<14 else 0
    pop=.26*math.sin(math.pi*(t-16.75)/.23) if 16.75<=t<16.98 else 0
    top+=flutter+pop
    shape([(-3.06,-4.50),(2.17,-4.50),(2.13,top-.23),(1.14,top+.10),(-.24,top-.08),(-1.91,top+.09),(-3.02,top-.20)],'blanket',.036)
    curve([(-2.76,top-.27),(-.75,top-.02),(1.87,top-.40)],mat='blueLine',width=.022)
    for a in [-2.14,-.7,.84]:curve([(a,top-.38),(a-.15,top-1.23),(a+.10,-4.20)],mat='blueLine',width=.017)
    if t>=17.35:
        emerge=smooth((t-17.35)/.35);x=1.06;y=mix(top-.20,top+.72,emerge)
        shape([(x-.44,top-.13),(x-.21,top-.13),(x-.15,y-.08),(x-.39,y-.08)],'skin',.025)
        shape([(x-.36,y+.15),(x+.20,y+.15),(x+.29,y+.04),(x+.23,y-.15),(x-.32,y-.15)],'skin',.030)
        # Unmistakable downward-pointing thumb, held through the final frame.
        shape([(x+.15,y-.02),(x+.31,y-.07),(x+.28,y-.62),(x+.15,y-.65),(x+.09,y-.42)],'skin',.030)
        for j in range(3):line([(x-.27,y+.075-j*.080),(x+.05,y+.045-j*.080)],width=.019)
def sparkles(t):
    if not 3<=t<6:return
    strength=smooth((t-3)/.45)
    for x,y,phase in [(-1.90,.69,0),(.97,.63,.7),(-1.33,1.88,1.1),(.35,1.73,2)]:
        r=(.11+.06*math.sin(t*5+phase))*strength
        shape([(x-r,y),(x-r*.20,y+r*.20),(x,y+r*1.4),(x+r*.20,y+r*.20),(x+r,y),(x+r*.18,y-r*.20),(x,y-r*1.4),(x-r*.20,y-r*.20)],'gold',.012)
def draw(t,frame):
    global strokes
    strokes=[]
    if frame in [145,146,147]:rect(-8,-12,16,24,'black',0)
    else:
        clock_insert=13.75<=t<14.25
        room(t,close=11<=t<16.5 and not clock_insert);upright,collapse=character(t);duvet(t,upright,collapse);clock(t);sparkles(t)
        if t<6:
            zoom=1+.035*smooth(t/3)+.055*smooth((t-4)/2)
            transform(1,-.42,.05,zoom,zoom)
        elif 11<=t<16.5 and not clock_insert:
            zoom=1+.87*smooth((t-11)/1.25)
            jitter=.04*shock(t);transform(1,-.42,.15,zoom,zoom,dx=.42*smooth((t-11)/1.25)+jitter*math.sin(t*190),dy=-.22*smooth((t-11)/1.25))
        elif t>=16.5:
            # Hard return to the wide view lets the final clock and thumb gag read.
            pass
    d=layer.frames.new(frame).drawing;d.add_strokes([len(p) for p,_,_,_ in strokes])
    for j,(pts,mat,w,closed) in enumerate(strokes):
        st=d.strokes[j];st.material_index=mat;st.cyclic=closed;st.fill_id=j+1 if closed else 0;st.fill_opacity=1
        if w==0:st.hide_stroke=True
        for p,(a,b) in zip(st.points,pts):p.position=(a,b,j*.001);p.radius=w;p.opacity=1
    d.tag_positions_changed()
for fr in range(1,433):
    draw((fr-1)/24,fr)
    if fr%48==0:print('BUILD_FRAME',fr,flush=True)
main=mesh_caption(s,'POV: Your alarm goes\noff at 6 AM','CAPTION_EP007_Main',size=.60,outline=0);caption_outline(main);main_bounds=place_caption(main)
expect=mesh_caption(s,'EXPECTATION','CAPTION_EP007_Expectation',size=.38,outline=0);caption_outline(expect);expect_bounds=place_caption(expect,'tag')
real=mesh_caption(s,'REALITY','CAPTION_EP007_Reality',size=.38,outline=0);caption_outline(real);real_bounds=place_caption(real,'tag')
for ob,keys in [(main,[(1,0),(25,1),(144,1),(145,0),(147,0),(148,1)]),(expect,[(1,0),(96,0),(97,1),(144,1),(145,0)]),(real,[(1,0),(147,0),(148,1)])]:
    for la in ob.data.layers:
        for fr,value in keys:la.opacity=value;la.keyframe_insert(data_path='opacity',frame=fr)
ed=s.sequence_editor_create();wav=EP/'audio/EP007_Original_Alarm_Expectation_Reality_v001.wav';assert wav.exists()
snd=ed.strips.new_sound('EP007 Original Morning / Foghorn / Zombie',str(wav),channel=1,frame_start=1);snd.sound.filepath='//../audio/'+wav.name
for label,fr in [('Peaceful morning',1),('Birds in window',25),('Dreamy smile',73),('Expectation label',97),('Blackout 3 frames',145),('Reality',148),('Foghorn hit',169),('Spring launch',174),('Zombie face push',265),('Zombie groan',313),('Alarm off / clock smack',337),('Silent stare',361),('Collapse starts',397),('Pillow impact',403),('Clock 6:01',421),('Defeated thumb',425)]:s.timeline_markers.new(label,frame=fr)
assert len(layer.frames)==432;assert main['exact_text']=='POV: Your alarm goes off at 6 AM'
bpy.ops.file.pack_all();assert snd.sound.packed_file
s['production_spec']='18 seconds, 432 frames, 1080x1920@24, GPU Eevee, original native GP animation, original packed stereo sound.'
s['caption_defaults']='Higher caption: main top300px; expectation/reality in top label slot500px. No bottom caption.'
obj['character_reference']='Approved recurring School Guy exact head/hair helpers; story-requested T-shirt/pajama variant and temporary zombie expression.'
s.frame_set(109);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP007_Alarm_GP_v002.blend'),compress=True)
(EP/'edit/project_verification.json').write_text(json.dumps({'native_GP_drawings':432,'packed_audio':True,'main_caption_bounds_px':main_bounds,'expectation_bounds_px':expect_bounds,'reality_bounds_px':real_bounds,'safe_caption_policy':'Higher top, 300px; labels500px','resolution':[1080,1920],'fps':24,'duration':18,'blackout_frames':[145,146,147],'spring_launch_frame':174,'clock_change_frame':421},indent=2))
for fr in [37,109,148,177,289,361,429]:
    s.frame_set(fr);s.render.filepath=str(EP/'previews'/f'EP007_Review_{fr:04d}.png');bpy.ops.render.render(write_still=True)
print('EP007_BUILD_COMPLETE',flush=True)
