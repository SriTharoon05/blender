"""Native GP caption placement. Coordinates measured in the 1080x1920 export.

POV titles use the upper band. The latest user preference puts spoken
word captions in a measured lower band above platform channel controls.
"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent.parent
def policy():
    settings=json.loads((ROOT/'config/production_defaults.json').read_text())
    return json.loads((ROOT/settings['caption_layout']).read_text(encoding='utf-8'))

def place_caption(ob,slot='main',camera_height=16):
    """Fit the complete GP outline bounds; keep all fade animation intact.

    Expects a straight-on orthographic portrait camera, like the 2D master.
    Font source remains editable; native GP lettering is the rendered caption.
    Returns the final exported pixel bounding rectangle, including outlines.
    """
    spec=policy();width,height=spec['resolution'];box=spec['slots'][slot]
    pts=[(p,st) for la in ob.data.layers for fr in la.frames for st in fr.drawing.strokes for p in st.points]
    assert pts and ob.type=='GREASEPENCIL'
    assert abs(ob.rotation_euler.z)<.0001 and abs(ob.scale.x-ob.scale.y)<.0001
    # Caption mesh helpers bake their font coordinates into GP points. Account
    # for object translation and uniform scale when deriving actual bounds.
    def bounds():
        xy=[]
        for p,st in pts:
            v=ob.matrix_world@p.position
            radius=0 if st.hide_stroke else p.radius*ob.scale.x
            xy.extend([(v.x-radius,v.y-radius),(v.x+radius,v.y+radius)])
        return min(a for a,b in xy),max(a for a,b in xy),min(b for a,b in xy),max(b for a,b in xy)
    x0,x1,y0,y1=bounds();unit=camera_height/height
    left,right=(box[0]-width/2)*unit,(box[2]-width/2)*unit
    bottom,top=(height/2-box[3])*unit,(height/2-box[1])*unit
    factor=min((right-left)/(x1-x0),(top-bottom)/(y1-y0),1)
    cx=(x0+x1)/2;cy=(y0+y1)/2
    tx=(left+right)/2;ty=top-(y1-y0)*factor/2
    inv=ob.matrix_world.inverted()
    for p,st in pts:
        v=ob.matrix_world@p.position
        v.x=tx+(v.x-cx)*factor;v.y=ty+(v.y-cy)*factor
        p.position=inv@v;p.radius*=factor
    for la in ob.data.layers:
        for fr in la.frames:fr.drawing.tag_positions_changed()
    ob['caption_safe_slot']=slot;ob['caption_safe_policy']=policy().get('placement','Measured safe band')
    ob['caption_placement']='Lower spoken-caption safe band above UI controls.' if slot=='dialogue' else 'Upper title band below notification/status area.'
    a,b,c,d=bounds()
    result=[a/unit+width/2,height/2-d/unit,b/unit+width/2,height/2-c/unit]
    assert result[0]>=box[0]-.1 and result[1]>=box[1]-.1 and result[2]<=box[2]+.1 and result[3]<=box[3]+.1,result
    ob['caption_export_bounds_px']=result
    return result
