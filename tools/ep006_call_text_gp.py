"""Native GP split-screen short with upper safe captions and measured render time."""
import bpy,math,ast,json,sys,time,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP006_Call_Vs_Text'
for f in ['blend','audio','previews','renders/frames_1080p24','edit']:(EP/f).mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='render':
    s=bpy.data.scenes['EP006_Call_Vs_Text'];bpy.context.window.scene=s;s.render.filepath=str(EP/'renders/frames_1080p24/EP006_######')
    def progress(scene,*args):
        if scene.frame_current%12==0:(EP/'edit/render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'total':432,'elapsed_seconds':time.perf_counter()-started}))
    bpy.app.handlers.render_write.append(progress);started=time.perf_counter();bpy.ops.render.render(animation=True);elapsed=time.perf_counter()-started
    import gpu
    report={'render_seconds':elapsed,'frames':432,'video_seconds':18,'renderer':'Eevee','gpu':gpu.platform.renderer_get(),'average_seconds_per_frame':elapsed/432,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (EP/'edit/render_time.json').write_text(json.dumps(report,indent=2));print('EP006_RENDER_COMPLETE',report,flush=True);sys.exit(0)
sys.path.insert(0,str(ROOT/'tools'));from shorts_caption_safe_area import place_caption
def extract(file,names):
    tree=ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8-sig'))
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),file,'exec'),globals())
extract('ep003_gp_laptop.py',{'color','shape','line','ellipse','rect','curve','smooth','mix','head'})
extract('ep004_keyboard_gp.py',{'mesh_caption'});extract('ep004_polish.py',{'caption_outline'})
protected=[p for top in ['00_LIBRARY','01_TEMPLATES'] for p in (ROOT/top).rglob('*') if p.is_file()]
protected.extend(p for p in (ROOT/'02_EPISODES').rglob('*.blend') if 'EP006' not in str(p))
(EP/'edit/protected_hashes.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},indent=2))
assert not (EP/'blend/EP006_Call_Text_GP_v001.blend').exists();bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP006_Call_Text_GP_v001.blend'),compress=True)
s=bpy.data.scenes.new('EP006_Call_Vs_Text');bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=432
s.eevee.taa_render_samples=8;s.eevee.use_raytracing=False;s.render.use_motion_blur=False;s.render.use_sequencer=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=50;s.render.filepath='//../renders/frames_1080p24/EP006_######'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.world=bpy.data.worlds.new('EP006_FlatWorld');s.world.color=color('E9ECF1')[:3]
cd=bpy.data.cameras.new('CAM_EP006_Split');cd.type='ORTHO';cd.ortho_scale=16;camera=bpy.data.objects.new(cd.name,cd);s.collection.objects.link(camera);camera.location=(0,0,30);s.camera=camera
INK='262833';palette={'grey':'E9ECF1','sofa':'CAD1DA','sofaShade':'AEB8C5','blue':'648DAB','red':'DD705B','redLight':'F4C6BE','blueLight':'BDD7E8','skin':'F1BD91','skinShade':'D98F6F','hair':'302D35','ink':INK,'white':'F8FAFD','shirt':'648DAB','shirtShade':'4D718D','shirtLight':'92B6CF','sweat':'F8FAFD'}
gp=bpy.data.grease_pencils.new('GP_EP006_Original_Split_Drawings');gp.stroke_depth_order='2D';obj=bpy.data.objects.new(gp.name,gp);s.collection.objects.link(obj);indices={}
for name,h in list(palette.items())+[('line',INK),('lightLine','92B6CF'),('redLine','DD705B'),('blueLine','648DAB')]:
    m=bpy.data.materials.new('GP_EP006_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.fill_color=color(h);m.grease_pencil.color=color(h if name.endswith('Line') else INK);gp.materials.append(m);indices[name]=len(gp.materials)-1
layer=gp.layers.new('Two contrasting performances - 24fps native GP',set_active=True);layer.use_lights=False;strokes=[];UI_LETTERS=[]
def transform(first,cx,cy,scale=1,dx=0,dy=0,angle=0):
    ca,si=math.cos(angle),math.sin(angle)
    for i in range(first,len(strokes)):
        pts,mat,w,closed=strokes[i];strokes[i]=([(cx+scale*((a-cx)*ca-(b-cy)*si)+dx,cy+scale*((a-cx)*si+(b-cy)*ca)+dy) for a,b in pts],mat,w*scale,closed)
def room(side,t):
    x=side*2.22;accent='red' if side<0 else 'blue'
    # Identical sofa, side table and wall on both sides.
    rect(x-1.93,-3.47,3.86,1.80,'sofa',.030)
    line([(x,-3.35),(x,-1.87)],width=.017)
    rect(x-1.77,-3.85,3.54,.55,'sofaShade',.029)
    for edge in [-1,1]:
        rect(x+edge*1.72-.22,-3.94,.44,1.18,'sofa',.033)
        rect(x+edge*1.52-.09,-4.13,.18,.25,'ink',.015)
    line([(x-1.5,-3.58),(x+1.5,-3.58)],width=.020)
    # Cushion remains in the same place; the left one receives the dive.
    shape([(x-1.38,-3.36),(x-.47,-3.52),(x-.29,-2.53),(x-1.20,-2.37)],accent,.027)
    tx=side*3.75
    rect(tx-.47,-1.57,.94,.16,'sofaShade',.026)
    for a in [-.35,.35]:line([(tx+a,-1.57),(tx+a,-2.80)],width=.028)
    line([(side*.35,-5.63),(side*4.40,-5.63)],width=.014)
def phone(x,y,t,state='idle',angle=0):
    first=len(strokes);w=.64;h=1.10
    active=state=='call' and 3<=t<8
    vibration=.035*math.sin(t*81) if active else 0;x+=vibration
    rect(x-w/2,y-h/2,w,h,'ink',.025);rect(x-w/2+.06,y-h/2+.08,w-.12,h-.18,'redLight' if active else 'white',.012)
    line([(x-.08,y+h/2-.05),(x+.08,y+h/2-.05)],'lightLine',.012)
    if state=='call':
        ellipse(x,y+.10,.14,.15,'red' if active else 'sofa',.012,n=24)
        curve([(x-.075,y+.18),(x-.07,y+.04),(x+.07,y+.06)],mat='line',width=.025)
        ellipse(x-.13,y-.32,.078,.078,'red',.009,n=16);ellipse(x+.13,y-.32,.078,.078,'blue',.009,n=16)
        line([(x-.21,y-.13),(x+.21,y-.13)],width=.015)
        line([(x-.12,y-.19),(x+.12,y-.19)],width=.013)
    elif state=='text':
        rect(x-.19,y+.03,.33,.20,'blueLight',.014);shape([(x+.06,y+.03),(x+.13,y-.04),(x+.13,y+.03)],'blueLight',.010)
        if t>=4:rect(x-.12,y-.24,.31,.19,'blue',.012)
        if t>=9:line([(x+.07,y-.18),(x+.11,y-.22),(x+.18,y-.13)],'lightLine',.017)
    transform(first,x,y,angle=angle)
    if active:
        for edge in [-1,1]:
            xx=x+edge*.49
            curve([(xx,y-.28),(xx+edge*.13,y),(xx,y+.28)],mat='redLine',width=.023)
            curve([(xx+edge*.15,y-.38),(xx+edge*.29,y),(xx+edge*.15,y+.38)],mat='redLine',width=.018)
        # Diegetic call notification card, in the upper part of the left panel.
        rect(x-.62,.44,1.24,.66,'redLight',.022)
        shape([(x-.12,.44),(x,.27),(x+.13,.44)],'redLight',.016)
        for tri in UI_LETTERS:shape([(x+a,.85+b) for a,b in tri],'ink',0)
def face(x,y,t,panic=False,tilt=0,dive=0):
    first=len(strokes);head(x,y,'calm',turn=-.35 if panic else .45,t=t);strokes.pop()
    for i in range(first,len(strokes)):
        pts,mat,w,closed=strokes[i]
        if panic and mat==indices['white'] and len(pts)==40:
            cx=sum(a for a,b in pts)/len(pts);cy=sum(b for a,b in pts)/len(pts)
            strokes[i]=([(cx+(a-cx)*1.6,cy+(b-cy)*1.85) for a,b in pts],mat,w,closed)
        if panic and mat==indices['ink'] and len(pts)==24:
            cx=sum(a for a,b in pts)/len(pts);cy=sum(b for a,b in pts)/len(pts)
            strokes[i]=([(cx+(a-cx)*.55,cy+(b-cy)*.55) for a,b in pts],mat,w,closed)
    if panic:
        ellipse(x,y-.53,.12,.13,'ink',.017)
        shape([(x+1.02,y+.70),(x+1.17,y+.32),(x+1.04,y+.23),(x+.95,y+.40)],'sweat',.021)
    else:curve([(x-.27,y-.48),(x,y-.72),(x+.33,y-.43)],width=.030)
    transform(first,x,y,.68,angle=tilt)
def body(x,t,side,dive=0):
    # Hoodie and loose sweatpants retain the recurring guy's identity.
    dy=.10 if side<0 and t>=3 else 0
    if dive<.8:
        shape([(x-.69,-3.32),(x-.68,-1.52+dy),(x-.40,-1.13+dy),(x+.40,-1.13+dy),(x+.74,-1.56+dy),(x+.78,-3.20)],'shirt',.032)
        shape([(x-.47,-1.23+dy),(x,-1.78+dy),(x+.46,-1.23+dy),(x+.18,-1.00+dy),(x-.22,-1.00+dy)],'shirtShade',.019)
        line([(x-.16,-1.68+dy),(x-.18,-2.14+dy)],'lightLine',.017);line([(x+.19,-1.68+dy),(x+.22,-2.12+dy)],'lightLine',.017)
        shape([(x-.57,-3.06),(x+.66,-3.06),(x+.86,-3.70),(x+.55,-4.86),(x+.12,-4.84),(x+.34,-3.84),(x+.04,-3.62),(x-.13,-3.70),(x-.28,-4.88),(x-.72,-4.76),(x-.76,-3.80),(x-.46,-3.64)],'sofaShade',.027)
        curve([(x-.43,-3.24),(x-.36,-3.59),(x-.64,-3.83)],width=.017)
        curve([(x+.44,-3.24),(x+.46,-3.57),(x+.64,-3.77)],width=.017)
        for xx in [x-.53,x+.33]:ellipse(xx,-4.95,.32,.16,'white',.028);line([(xx-.25,-5.04),(xx+.25,-5.04)],width=.016)
        rect(x-.19,-1.24+dy,.38,.51,'skin',.023)
        # Free arm lies naturally along the sofa edge.
        free=1 if side<0 else -1
        shape([(x+free*.52,-1.48+dy),(x+free*.83,-1.70+dy),(x+free*.93,-2.66),(x+free*.56,-2.73),(x+free*.38,-1.83+dy)],'shirtShade',.028)
        ellipse(x+free*.72,-2.70,.20,.17,'skin',.022)
    else:
        shape([(x+.76,-3.55),(x+.44,-2.67),(x-.63,-2.48),(x-1.01,-2.90),(x-.34,-3.53)],'shirt',.033)
        shape([(x+.71,-3.47),(x+1.03,-3.71),(x+.86,-4.61),(x+.37,-4.57),(x+.33,-3.78),(x-.01,-3.68)],'sofaShade',.029)
        ellipse(x+.62,-4.69,.36,.16,'white',.025)
        # One hand remains outside the cushion, with a tiny nervous twitch.
        twitch=.032*math.sin(t*34) if t>=8 else 0
        line([(x+.20,-2.62),(x+.43,-2.24),(x+.60,-2.04+twitch)],width=.065)
        ellipse(x+.60,-2.02+twitch,.19,.14,'skin',.023)
        for f in range(3):line([(x+.52+f*.06,-1.98+twitch),(x+.49+f*.06,-1.82+twitch)],width=.021)
def left(t):
    x=-2.00;d=smooth((t-5.58)/.42);panic=t>=3
    body(x,t,-1,d)
    if d<.86:
        first=len(strokes);face(x-.55*d,-.49-2.11*d,t,panic,.02-1.48*d)
        # Before hiding, his hand hovers at the red decline button but never presses.
        hover=smooth((t-3.15)/.7)
        hx=mix(x-.60,-3.69,hover);hy=mix(-2.66,-1.10,hover)
        shape([(x-.54,-1.50),(x-.82,-1.62),(hx+.15,hy-.15),(hx+.02,hy+.16),(x-.69,-1.36)],'shirt',.028)
        ellipse(hx,hy,.16,.15,'skin',.022)
        line([(hx+.03,hy-.04),(hx+.06,hy-.15)],width=.035)
    else:
        ellipse(x-.62,-2.76,.42,.25,'hair',.023)
        impact=max(0,1-(t-6)/.18) if t>=6 else 0
        shape([(x-1.46,-3.38),(x-.43,-3.56),(x-.21,-2.47-impact*.15),(x-1.27,-2.28-impact*.15)],'red',.032)
        curve([(x-1.13,-2.91),(x-.88,-3.03),(x-.53,-2.83)],width=.023)
        if impact>0:
            for a,b in [(-3.6,-2.40),(-3.4,-2.04),(-2.4,-2.1)]:line([(a,b),(a-.17,b+.19)],'redLine',.024)
    phone(-3.75,-.91,t,'call')
def right(t):
    x=2.0;body(x,t,1);face(x,-.49,t,False,tilt=-.10 if t>=3 else .02)
    grab=smooth((t-3)/.50);release=smooth((t-9.05)/.40)
    px=mix(3.75,2.68,grab);py=mix(-.91,-2.00,grab)
    if t<9.05:
        phone(px,py,t,'text' if t>=3 else 'idle',angle=-.12*grab)
    else:
        flight=min(t-9.05,.55);px=2.68+.55*flight/.55;py=-2+2.8*flight-8.925*flight*flight
        rotation=-.12-1.45*(flight/.55)
        if t>=9.60:py=-3.16+.035*math.sin((t-9.60)*38)*math.exp(-(t-9.60)*18);rotation=-math.pi/2
        phone(px,py,t,'text',angle=rotation)
    hx=mix(mix(2.60,px,grab),2.59,release);hy=mix(mix(-2.66,-2.02,grab),-2.72,release)
    if t>=9.60:hx=2.59;hy=-2.72
    shape([(x+.48,-1.52),(x+.78,-1.78),(hx+.17,hy-.11),(hx-.18,hy-.14),(x+.30,-1.83)],'shirt',.028)
    ellipse(hx,hy,.19,.17,'skin',.022)
    tap=0
    for at in [4,4.24,4.51,4.94,5.18,5.45,5.98,6.22,6.53,6.83,9]:
        if 0<=t-at<.11:tap=.09*math.sin(math.pi*(t-at)/.11)
    if t<9.05:line([(hx-.07,hy+.09),(hx-.13+tap,hy+.28-tap)],width=.049)
    if 3<=t<3.65:
        pop=smooth((t-3)/.13)*(1-smooth((t-3.40)/.25))
        first=len(strokes);rect(2.37,-.85,.73,.39,'blueLight',.022);shape([(2.67,-.85),(2.78,-1),(2.81,-.85)],'blueLight',.014)
        for a in [2.52,2.70,2.87]:ellipse(a,-.64,.034,.034,'blue',0,n=12)
        transform(first,2.72,-.69,pop)
    if 9<=t<9.7:
        fly=smooth((t-9)/.7);first=len(strokes)
        shape([(2.15+fly*.9,-1.55+fly*.95),(2.82+fly*.9,-1.43+fly*.95),(2.40+fly*.9,-1.88+fly*.95)],'blue',.015)
        line([(2.35+fly*.9,-1.57+fly*.95),(2.44+fly*.9,-1.78+fly*.95)],'lightLine',.014)
def draw(t,frame):
    global strokes
    strokes=[];rect(-5,-9,10,18,'grey',0)
    room(-1,t);room(1,t);left(t);right(t)
    # The divider begins beneath the clear shared caption header.
    pulse=.035*math.sin(math.pi*(t-8)/.33) if 8<=t<8.33 else 0
    rect(-.045-pulse,-8,.09+2*pulse,9.33,'ink',0)
    line([(-4.5,1.30),(-.08,1.30)],'redLine',.030);line([(.08,1.30),(4.5,1.30)],'blueLine',.030)
    d=layer.frames.new(frame).drawing;d.add_strokes([len(p) for p,_,_,_ in strokes])
    for j,(pts,mat,w,closed) in enumerate(strokes):
        st=d.strokes[j];st.material_index=mat;st.cyclic=closed;st.fill_id=j+1 if closed else 0;st.fill_opacity=1
        if w==0:st.hide_stroke=True
        for p,(a,b) in zip(st.points,pts):p.position=(a,b,j*.001);p.radius=w;p.opacity=1
    d.tag_positions_changed()
for frame in range(1,433):
    draw((frame-1)/24,frame)
    if frame%48==0:print('BUILD_FRAME',frame,flush=True)
main=mesh_caption(s,'Ignoring a phone call\nvs. replying via text','CAPTION_EP006_Main',size=.60,outline=0);caption_outline(main);main_bounds=place_caption(main)
tag=mesh_caption(s,'Same energy, different outcome.','CAPTION_EP006_Tag',size=.35,outline=0);caption_outline(tag);tag_bounds=place_caption(tag,'tag')
for ob,keys in [(main,[(1,0),(25,1)]),(tag,[(1,0),(336,0),(337,0),(349,1)])]:
    for la in ob.data.layers:
        for fr,v in keys:la.opacity=v;la.keyframe_insert(data_path='opacity',frame=fr)
ed=s.sequence_editor_create();snd=ed.strips.new_sound('EP006 Original Stereo Call vs Text',str(EP/'audio/EP006_Original_Call_Text_48k.wav'),channel=1,frame_start=1);snd.sound.filepath='//../audio/EP006_Original_Call_Text_48k.wav'
for label,fr in [('Silent setup',1),('Lo-fi fade in',25),('Ring and notification',73),('Typing starts',97),('Cushion contact',145),('Ring cuts / divider pulse',193),('Message sent',217),('Upper tagline',337),('Lo-fi fade out',361)]:s.timeline_markers.new(label,frame=fr)
assert main['exact_text']=='Ignoring a phone call vs. replying via text';assert tag['exact_text']=='Same energy, different outcome.'
assert len(layer.frames)==432 and snd.sound is not None
bpy.ops.file.pack_all();assert snd.sound.packed_file
obj['character']='Approved recurring School Guy: inherited head/hair geometry, hoodie, identical left/right identity.'
s['caption_defaults']='All captions at the upper safe band, no bottom text. Main and tag bounds validated including outline.'
s['production_spec']='18 seconds, 1080x1920, 24fps, fast GPU Eevee, native GP, original packed stereo audio; report actual render elapsed time.'
s.frame_set(97);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP006_Call_Text_GP_v002.blend'),compress=True)
(EP/'edit/project_verification.json').write_text(json.dumps({'native_GP_drawings':432,'packed_audio':True,'main_caption_bounds_px':main_bounds,'tag_caption_bounds_px':tag_bounds,'safe_caption_policy':'Upper band only','resolution':[1080,1920],'fps':24,'duration':18},indent=2))
for frame in [49,97,145,229,361]:
    s.frame_set(frame);s.render.filepath=str(EP/'previews'/f'EP006_Review_{frame:04d}.png');bpy.ops.render.render(write_still=True)
print('EP006_BUILD_COMPLETE',flush=True)
