"""Native GP Dad variant, comic keyboard impacts, 1080x1920 at 24fps."""
import bpy,math,json,ast,sys,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent.parent;EP=ROOT/'02_EPISODES/EP004_Dad_Mechanical_Keyboard'
for f in ['blend','audio','previews','renders/frames_1080p24','edit']:(EP/f).mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='render':
    s=bpy.data.scenes['EP004_Dad_Mechanical_Keyboard'];bpy.context.window.scene=s;s.render.filepath=str(EP/'renders/frames_1080p24/EP004_######')
    def progress(scene,*args):
        if scene.frame_current%12==0:(EP/'edit/render_progress.json').write_text(json.dumps({'frame':scene.frame_current,'total':240,'fps':24}))
    bpy.app.handlers.render_write.append(progress);bpy.ops.render.render(animation=True)
    import gpu
    print('ACTUAL_GPU',gpu.platform.renderer_get(),flush=True);print('EP004_RENDER_COMPLETE',flush=True);sys.exit(0)

# Reuse the approved character's exact face drawing and palette helpers.
tree=ast.parse((ROOT/'tools/ep003_gp_laptop.py').read_text())
names={'color','shape','line','ellipse','rect','curve','smooth','mix','head'}
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<approved-character-functions>','exec'),globals())
INK='28252D'
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='palette' for x in node.targets):exec(compile(ast.Module(body=[node],type_ignores=[]),'<approved-character-palette>','exec'),globals())
palette.update({'beige':'ECE1CA','wood':'D9BE99','woodEdge':'B89874','key':'F6F0E4','keyShade':'C7C2B8','keyHit':'FFCC77','keyboard':'35333E','rgb':'AA9CCB','glass':'B5D2D9','frame':'BAA288','coffee':'675143','mug':'E8A170','greyHair':'9A9790','orange':'FFAA57','flash':'FFF7D3','paper':'FBF8F0','lamp':'6D7775','lampOn':'FFF2BE'})

def mesh_caption(scene,body,name,baseline=7.28,size=.53,outline=.055):
    font=bpy.data.fonts.load(r'C:/Windows/Fonts/ariblk.ttf');font.pack()
    gp=bpy.data.grease_pencils.new(name+'_GP');gp.stroke_depth_order='2D';ob=bpy.data.objects.new(name+'_GP',gp);scene.collection.objects.link(ob);ob.location.z=1
    for label,c in [('outline','000000'),('white','FFFFFF')]:
        mat=bpy.data.materials.new(name+'_'+label);bpy.data.materials.create_gpencil_data(mat);mat.grease_pencil.fill_color=color(c);mat.grease_pencil.color=color(c);gp.materials.append(mat)
    sources=[]
    for k,offset in enumerate([outline,0]):
        cu=bpy.data.curves.new(name+'_EditableSource_'+str(k),'FONT');cu.body=body;cu.font=font;cu.size=size;cu.space_line=1.18;cu.align_x='CENTER';cu.offset=offset
        source=bpy.data.objects.new(cu.name,cu);scene.collection.objects.link(source);source.location=(0,baseline,.2);bpy.context.view_layer.update()
        ev=source.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles();layer=gp.layers.new('Black outline' if k==0 else 'White letters',set_active=True);layer.use_lights=False;d=layer.frames.new(1).drawing;d.add_strokes([3]*len(mesh.loop_triangles))
        for i,tri in enumerate(mesh.loop_triangles):
            st=d.strokes[i];st.cyclic=True;st.material_index=k;st.fill_id=i+1;st.hide_stroke=True;st.fill_opacity=1
            for p,j in zip(st.points,tri.vertices):
                v=source.matrix_world@mesh.vertices[j].co;p.position=(v.x,v.y,k*.01);p.radius=0;p.opacity=1
        d.tag_positions_changed();ev.to_mesh_clear();source.hide_render=True;source.hide_viewport=True;sources.append(source)
    ob['exact_text']=body.replace('\n',' ');ob['style']='Arial Black, white letters, 6-7px black outline, top 20% safe region.'
    return ob

# Version the future template before creating the new episode.
s=bpy.context.scene;s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1
s['future_2d_defaults']='1080x1920, 24fps, fast Eevee NVIDIA GTX1650Ti; approved recurring character.'
s['caption_defaults']='Top 20%; Arial Black; white fill; thick black outline; horizontal padding 6%, upper padding 3%.'
mesh_caption(s,'YOUR CAPTION\nGOES HERE','CAPTION_Template')
template=ROOT/'01_TEMPLATES/GreasePencil_Shorts_1080p24_Master_v002.blend';assert not template.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(template),compress=True)
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP004_Dad_Keyboard_GP_v001.blend'),compress=True)
s=bpy.data.scenes.new('EP004_Dad_Mechanical_Keyboard');bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=100;s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=240
s.eevee.taa_render_samples=8;s.eevee.use_raytracing=False;s.render.use_motion_blur=False;s.render.use_sequencer=False
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=50;s.render.filepath='//../renders/frames_1080p24/EP004_######'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.world=bpy.data.worlds.new('EP004_World');s.world.color=color('ECE1CA')[:3]
cd=bpy.data.cameras.new('CAM_EP004_POV');cd.type='ORTHO';cd.ortho_scale=16;camera=bpy.data.objects.new('CAM_EP004_POV',cd);s.collection.objects.link(camera);camera.location=(0,0,30);s.camera=camera
data=bpy.data.grease_pencils.new('GP_EP004_Dad_Office_Keyboard');data.stroke_depth_order='2D';obj=bpy.data.objects.new('GP_EP004_Dad_Office_Keyboard',data);s.collection.objects.link(obj)
indices={}
for name,h in palette.items():
    m=bpy.data.materials.new('GP_EP004_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.fill_color=color(h);m.grease_pencil.color=color(INK);data.materials.append(m);indices[name]=len(data.materials)-1
for name,h in [('line',INK),('redLine','FF4E4F'),('chalk','F6DEC4'),('lightLine','B89874')]:
    m=bpy.data.materials.new('GP_EP004_'+name);bpy.data.materials.create_gpencil_data(m);m.grease_pencil.color=color(h);data.materials.append(m);indices[name]=len(data.materials)-1
layer=data.layers.new('Dad and office - drawings on ones at 24fps',set_active=True);layer.use_lights=False
HITS=[4,5.5,6.5,7.5]
def age(t):return max(0,t-max((h for h in HITS if t>=h),default=-100))
def impact(t):
    return sum(math.exp(-(t-h)*17) for h in HITS if 0<=t-h<.5)
def rot_shapes(first,cx,cy,angle):
    ca,si=math.cos(angle),math.sin(angle)
    for i in range(first,len(strokes)):
        pts,mat,w,closed=strokes[i];strokes[i]=([(cx+(x-cx)*ca-(y-cy)*si,cy+(x-cx)*si+(y-cy)*ca) for x,y in pts],mat,w,closed)

def office(t):
    rect(-5,-9,10,18,'beige',0)
    rect(-3.8,2.9,2.25,2.05,'frame',.025);rect(-3.62,3.07,1.89,1.69,'glass',.017)
    line([(-2.66,3.07),(-2.66,4.76)],width=.019);line([(-3.62,3.89),(-1.73,3.89)],width=.019)
    shape([(-3.60,3.08),(-2.70,3.08),(-1.78,4.75),(-2.25,4.75)],'white',0)
    # Only a sliver of the monitor, as requested.
    rect(-4.8,-1.8,.95,4.7,'keyboard',.035);rect(-4.68,-1.62,.65,4.3,'glass',.015)
    rect(-2.25,-3.3,3.55,3.4,'woodEdge',.03)
    rect(-5,-7.9,10,5.45,'wood',.025);rect(-5,-6.65,10,.18,'woodEdge',.018)
    # Lamp sits on the desk behind the keyboard.
    ellipse(3.04,-2.02,.64,.12,'lamp',.025)
    line([(3.05,-1.97),(3.08,.69),(2.47,1.33)],width=.065)
    shape([(2.10,1.61),(2.72,1.61),(3.00,.99),(1.82,.99)],'lamp',.027)
    lit=age(t)<.125 and t>=4
    if lit:shape([(2.01,.96),(2.82,.96),(3.66,-1.87),(1.37,-1.87)],'lampOn',0)
    line([(3.05,-1.97),(3.08,.69),(2.47,1.33)],width=.065)
    shape([(2.10,1.61),(2.72,1.61),(3.00,.99),(1.82,.99)],'lamp',.027)

def dad(t):
    shock=impact(t) if t<7 else 0;dx=-shock*.12;dy=shock*.20-.07*smooth(t/.8)
    x=-.44+dx;y=1.35+dy
    # Broader, relaxed build and polo, while retaining the approved face/hair identity.
    shape([(x-1.47,-2.5),(x-1.55,-.82+dy),(x-1.1,-.26+dy),(x+1.08,-.26+dy),(x+1.57,-.86+dy),(x+1.42,-2.51)],'shirt',.035)
    rect(x-.33,-.37+dy,.66,1.16,'skin',.027)
    shape([(x-.85,-.35+dy),(x-.26,-.41+dy),(x,-1.0+dy),(x-.60,-.85+dy)],'shirtLight',.025)
    shape([(x+.85,-.35+dy),(x+.27,-.41+dy),(x,-1.0+dy),(x+.59,-.85+dy)],'shirtLight',.025)
    line([(x,-.95+dy),(x,-1.57+dy)],width=.017)
    ellipse(x,-1.14+dy,.032,.032,'white',0,n=12);ellipse(x,-1.38+dy,.032,.032,'white',0,n=12)
    start=len(strokes);head(x,y,'calm',turn=.2,t=t);strokes.pop()
    # Relaxed half smile; momentary squint on the first three impacts.
    curve([(x-.31,y-.43),(x-.03,y-.63),(x+.32,y-.42)],width=.026)
    for ex in [x-.46,x+.48]:
        line([(ex-.24,y+.16-shock*.07),(ex+.24,y+.13-shock*.07)],width=.02)
    # Reading glasses pushed up, grey temple accents, subtle cheek creases.
    shape([(x-.99,y+.45),(x-.87,y+.52),(x-.82,y+.23),(x-.98,y+.2)],'greyHair',.01)
    shape([(x+.86,y+.47),(x+1.00,y+.58),(x+.94,y+.25),(x+.83,y+.21)],'greyHair',.01)
    for ex in [x-.41,x+.4]:
        shape([(ex-.28,y+.98),(ex+.28,y+.98),(ex+.24,y+.69),(ex-.22,y+.69)],'skin',.014)
        # Glasses have clear centres; use a stroke-only contour.
        points,mat,w,closed=strokes.pop();line(points+[points[0]],width=.025)
    line([(x-.13,y+.83),(x+.12,y+.83)],width=.024)
    line([(x-.88,y+.86),(x-.70,y+.82)],width=.02);line([(x+.69,y+.84),(x+.91,y+.91)],width=.02)
    line([(x-.78,y-.23),(x-.65,y-.31)],'lightLine',.015);line([(x+.65,y-.25),(x+.8,y-.31)],'lightLine',.015)
    if shock>.1:
        line([(x-1.11,y+1.37),(x-1.30,y+1.61)],width=.022);line([(x+1.08,y+.88),(x+1.34,y+1.11)],width=.022)
    # Left/free arm remains casual, then raises the cup.
    sip=smooth((t-6.9)/.5)
    arm_end=(2.08-2.14*sip,-1.77+2.17*sip)
    shape([(x+1.10,-.47+dy),(x+1.56,-.91+dy),(1.39,-1.92+1.53*sip),(arm_end[0]+.28,arm_end[1]-.18),(arm_end[0]-.17,arm_end[1]-.35),(1.03,-1.7+1.54*sip),(x+.79,-.83+dy)],'shirtShade',.029)
    ellipse(arm_end[0],arm_end[1],.30,.22,'skin',.025)
    return arm_end,sip

def mug(x,y,angle=0):
    first=len(strokes)
    ellipse(x+.51,y+.02,.23,.25,'mug',.025);ellipse(x+.51,y+.02,.12,.14,'wood',.018)
    shape([(x-.40,y+.39),(x+.35,y+.39),(x+.28,y-.35),(x-.32,y-.35)],'mug',.029)
    ellipse(x-.025,y+.38,.375,.10,'coffee',.02)
    line([(x-.27,y+.19),(x-.23,y-.16)],'chalk',.016)
    rot_shapes(first,x,y,angle)

def papers(t):
    if t<4:
        shape([(-2.84,-2.53),(-1.98,-2.63),(-1.68,-2.91),(-2.61,-2.8)],'paper',.015);return
    elapsed=t-4
    for i in range(4):
        x=(-2.7 if i%2==0 else 2.6)+.20*math.sin(elapsed*2+i)
        y=-1.95+.55*math.sin(elapsed*2.7+i)+.3*impact(t)
        first=len(strokes);shape([(x-.34,y-.17),(x+.34,y-.17),(x+.34,y+.17),(x-.34,y+.17)],'paper',.012);line([(x-.2,y),(x+.18,y)],'lightLine',.010);rot_shapes(first,x,y,.4*math.sin(t*3+i))

def keyboard(t):
    hit=impact(t);a=age(t)
    if t>=4 and a<.17:
        power=1.0-a/.17;points=[]
        for i in range(24):
            theta=i*math.pi/12;r=(2.2 if i%2==0 else 1.1)*power+.35
            points.append((.2+r*math.cos(theta),-3.3+r*.67*math.sin(theta)))
        shape(points,'flash' if a<.043 else 'orange',.025)
    shape([(-3.42,-2.79),(3.34,-2.79),(4.05,-5.43),(-4.05,-5.43)],'keyboard',.035)
    shape([(-4.05,-5.43),(4.05,-5.43),(4.05,-5.64),(-4.05,-5.64)],'laptopDark',.025)
    line([(-3.84,-5.53),(3.84,-5.53)],'redLine' if hit>.1 else 'chalk',.028)
    for row in range(5):
        width=6.39+row*.26;left=-width/2;step=width/12;y=-3.02-row*.445
        for col in range(12):
            x=left+col*step;pressed=(row==1 and col==6 and hit>.07)
            drop=.085*hit if pressed else 0
            if row==4 and 3<=col<=8:
                if col!=3:continue
                shape([(x+.025,y-drop),(x+step*6-.055,y-drop),(x+step*6-.025,y-.33-drop),(x-.025,y-.33-drop)],'key',.012)
                continue
            shape([(x+.025,y-drop),(x+step-.055,y-drop),(x+step-.025,y-.33-drop),(x-.015,y-.33-drop)],'keyHit' if pressed else 'key',.012)
            line([(x+.10,y-.10-drop),(x+.17,y-.10-drop)],'lightLine',.009)
    if t>=4 and a<.30:
        for i in range(5):
            angle=(.15+i*.56);r=2.05+a*4;cx=.2+math.cos(angle)*r;cy=-3.3+math.sin(angle)*r
            line([(cx,cy),(cx+math.cos(angle)*.32,cy+math.sin(angle)*.32)],width=.03)

def tapping_hand(t):
    target_y=-3.54
    if t<2:tip_y=-1.47+.14*math.sin(t*9)*max(0,1-t/1.2)-.2*smooth((t-1.1)/.8)
    elif t<3.5:tip_y=mix(-1.67,target_y+.22,smooth((t-2)/1.5))
    elif t<4:tip_y=target_y+.22
    else:
        prev=max(h for h in HITS if h<=t);next_hit=next((h for h in HITS if h>t),None);dt=t-prev
        tip_y=target_y+.62*smooth(dt/.30)
        if next_hit is not None and next_hit-t<.40:tip_y=target_y+.62*smooth((next_hit-t)/.40)
        tip_y-=.09*impact(t)
    x=.30
    shape([(-1.79,-.65),(-2.05,-1.15),(-1.29,-2.15),(x-.25,tip_y+.44),(x-.03,tip_y+.89),(-1.00,-1.76),(-1.27,-.9)],'shirtShade',.028)
    ellipse(x-.25,tip_y+.61,.33,.24,'skin',.028)
    shape([(x-.11,tip_y+.65),(x+.10,tip_y+.63),(x+.12,tip_y+.05),(x+.06,tip_y-.02),(x-.08,tip_y-.01)],'skin',.025)
    for i in range(2):curve([(x-.51+i*.15,tip_y+.54),(x-.39+i*.15,tip_y+.69),(x-.27+i*.15,tip_y+.56)],width=.014)

def draw(t):
    office(t);arm_end,sip=dad(t);papers(t)
    jump=.36*impact(t)*(1-sip);mug(arm_end[0]+.17,arm_end[1]+.13+jump,-.15*sip+.09*impact(t)*math.sin(t*80)*(1-sip))
    keyboard(t);tapping_hand(t)

def commit(f,t):
    d=layer.frames.new(f).drawing;d.add_strokes([len(x[0]) for x in strokes])
    zoom=1+.10*smooth((t-3.2)/.3)*(1-smooth((t-7)/.45));pulse=impact(t)
    shake_x=.17*pulse*math.sin(t*math.pi*22);shake_y=.13*pulse*math.cos(t*math.pi*17)
    for j,(pts,mat,w,closed) in enumerate(strokes):
        st=d.strokes[j];st.material_index=mat;st.cyclic=closed;st.fill_id=j+1 if closed else 0;st.fill_opacity=1
        for p,(x,y) in zip(st.points,pts):p.position=(x*zoom+shake_x,(y+3.3)*zoom-3.3+shake_y,j*.001);p.radius=w;p.opacity=1
    d.tag_positions_changed()

for f in range(1,241):
    t=min((f-1)/24,9);strokes=[];draw(t);commit(f,t)
    if f%24==0:print('GP_DRAWN',f,flush=True)
caption=mesh_caption(s,'POV: Your dad uses your\nmechanical keyboard.','CAPTION_EP004_Main',baseline=7.20,size=.53,outline=.055)
for lay in caption.data.layers:
    lay.opacity=0;lay.keyframe_insert(data_path='opacity',frame=1);lay.opacity=1;lay.keyframe_insert(data_path='opacity',frame=7)
tag=mesh_caption(s,'...every. single. time.','CAPTION_EP004_Tag',baseline=5.34,size=.32,outline=.045)
for lay in tag.data.layers:
    lay.opacity=0;lay.keyframe_insert(data_path='opacity',frame=216);lay.opacity=1;lay.keyframe_insert(data_path='opacity',frame=225)
    for action in bpy.data.actions:
        if action.name.startswith(tag.data.name):pass
for frame,label in [(1,'SETUP - room tone'),(49,'FINGER DESCENDS'),(85,'SILENT PAUSE'),(97,'SHOTGUN - exact key contact'),(133,'ANVIL - exact key contact'),(157,'SHOTGUN - escalation'),(169,'WIDE REVEAL - sipping'),(181,'FINAL BOOM-CLANG'),(197,'ABRUPT QUIET'),(217,'FREEZE + TAG')]:s.timeline_markers.new(label,frame=frame)
audio=EP/'audio/EP004_Original_Keyboard_Impacts_v001.wav';ed=s.sequence_editor_create();snd=ed.strips.new_sound('Original synchronized keyboard impacts',str(audio),channel=1,frame_start=1);snd.sound.filepath='//../audio/'+audio.name
bpy.ops.file.pack_all();s['caption_exact']='POV: Your dad uses your mechanical keyboard.';s['tag_exact']='...every. single. time.';s['identity']='Dad variant of approved School Guy 2D: same face and angular hair, aged temples, reading glasses, casual polo.';s.frame_set(24)
bpy.context.view_layer.objects.active=obj;obj.select_set(True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(EP/'blend/EP004_Dad_Keyboard_GP_v002.blend'),compress=True)
for frame in [36,84,97,181,230]:
    s.frame_set(frame);s.render.filepath=str(EP/'previews'/f'EP004_Review_{frame:04d}.png');bpy.ops.render.render(write_still=True)
print('EP004_BUILD_COMPLETE',flush=True)
