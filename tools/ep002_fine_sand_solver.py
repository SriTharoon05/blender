"""Dissipative spherical DEM: every grain has gravity, contact impulses, Coulomb friction and spin."""
import sys,json,struct,time,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'physics_deps'))
import numpy as np
from scipy.spatial import cKDTree
EP=Path(__file__).resolve().parent.parent/'02_EPISODES/EP002_Impossible_Blankets'
spec=json.loads((EP/'cache/particles/fine_grain_colliders_v023.json').read_text());start,end=spec['start'],spec['end'];rng=np.random.default_rng(2277)
nx,ny,nz=90,110,6;z,y,x=np.meshgrid(np.arange(nz),np.arange(ny),np.arange(nx),indexing='ij');p=np.column_stack(((x.ravel()-(nx-1)/2)*.0198,-.96+(y.ravel()-(ny-1)/2)*.0198,3.12+z.ravel()*.0198));N=len(p);p+=rng.uniform(-.0003,.0003,p.shape);r=rng.uniform(.0083,.0092,N);mass=2650*(4*np.pi/3)*r**3;inv=1/mass;inertia=.4*mass*r*r;v=np.zeros_like(p);omega=np.zeros_like(p);rotation=np.broadcast_to(np.eye(3),(N,3,3)).copy();dt=1/480;mu=.62;restitution=.025;boxes=[]
for b in spec['boxes']:
 if b['name']=='COLL_EP002_Floor':continue
 mats=np.asarray(b['matrices']);scale=np.linalg.norm(mats[:,:3,:3],axis=1);R=mats[:,:3,:3]/scale[:,None,:];localcentre=(np.array(b['lo'])+b['hi'])/2;half=(np.array(b['hi'])-b['lo'])/2
 centre=mats[:,:3,3]+np.einsum('nij,j->ni',mats[:,:3,:3],localcentre);boxes.append((centre,R,half*scale))
def contact_boxes(frame,alpha):
 global p,v,omega
 for centre,R,half in boxes:
  k=min(frame,len(centre)-2);C=centre[k]*(1-alpha)+centre[k+1]*alpha;rot=R[k]*(1-alpha)+R[k+1]*alpha;H=half[k];extent=np.abs(rot)@H+.01;broad=np.flatnonzero(np.all(np.abs(p-C)<=extent,axis=1))
  if not len(broad):continue
  local=(p[broad]-C)@rot;clipped=np.clip(local,-H,H);delta=local-clipped;dist=np.linalg.norm(delta,axis=1);inside=np.all(np.abs(local)<H,axis=1);mask=(dist<r[broad])|inside
  if not np.any(mask):continue
  localids=np.flatnonzero(mask);ids=broad[localids];q=local[localids];d=delta[localids];ds=dist[localids];normal=d/np.maximum(ds[:,None],1e-12);pen=r[ids]-ds
  ii=inside[localids]
  if np.any(ii):
   axis=np.argmin(H-np.abs(q[ii]),axis=1);normal[ii]=0;normal[np.flatnonzero(ii),axis]=np.where(q[ii,axis]>=0,1,-1);pen[ii]=r[ids[ii]]+np.min(H-np.abs(q[ii]),axis=1)
  normal=normal@rot.T;surface=clipped[localids];surface[ii]=q[ii]+normal[ii]@rot*(pen[ii]-r[ids[ii]])[:,None]
  cv=(centre[k+1]-centre[k])*60+surface@(R[k+1]-R[k]).T*60
  rel=v[ids]-cv;vn=np.sum(rel*normal,axis=1);closing=np.maximum(0,-vn);v[ids]+=normal*(closing*(1+restitution))[:,None]
  vt=rel-normal*vn[:,None]+np.cross(omega[ids],-normal*r[ids,None]);speed=np.linalg.norm(vt,axis=1);j=np.minimum(speed/3.5,mu*closing);dv=-vt/np.maximum(speed[:,None],1e-12)*j[:,None];v[ids]+=dv;omega[ids]+=np.cross(-normal*r[ids,None],dv)*mass[ids,None]/inertia[ids,None];p[ids]+=normal*np.maximum(0,pen-.00005)[:,None]
 ids=np.flatnonzero(p[:,2]<r-.00005)
 if len(ids):
  closing=np.maximum(0,-v[ids,2]);normal=np.zeros((len(ids),3));normal[:,2]=1;vt=v[ids]+np.cross(omega[ids],-normal*r[ids,None]);vt[:,2]=0;speed=np.linalg.norm(vt,axis=1);j=np.minimum(speed/3.5,mu*closing);dv=-vt/np.maximum(speed[:,None],1e-12)*j[:,None];v[ids]+=dv;v[ids,2]+=closing*(1+restitution);omega[ids]+=np.cross(-normal*r[ids,None],dv)*mass[ids,None]/inertia[ids,None];p[ids,2]=r[ids]-.00005
def pair_contacts():
 global p,v,omega
 pairs=cKDTree(p).query_pairs(.0194,output_type='ndarray');a,b=pairs.T;delta=p[b]-p[a];dist=np.linalg.norm(delta,axis=1);overlap=r[a]+r[b]-dist;mask=overlap>0
 a=a[mask];b=b[mask];delta=delta[mask];dist=dist[mask];overlap=overlap[mask]
 if not len(a):return 0
 n=delta/np.maximum(dist[:,None],1e-12);rel=v[b]-v[a]+np.cross(omega[b],-n*r[b,None])-np.cross(omega[a],n*r[a,None]);vn=np.sum(rel*n,axis=1);inverse=inv[a]+inv[b];jn=np.maximum(0,-vn)*(1+restitution)/inverse;vt=rel-n*vn[:,None];speed=np.linalg.norm(vt,axis=1);jt=np.minimum(speed/(3.5*inverse),mu*jn);impulse=n*jn[:,None]-vt/np.maximum(speed[:,None],1e-12)*jt[:,None]
 np.add.at(v,a,-impulse*inv[a,None]);np.add.at(v,b,impulse*inv[b,None]);np.add.at(omega,a,np.cross(n*r[a,None],-impulse)/inertia[a,None]);np.add.at(omega,b,np.cross(-n*r[b,None],impulse)/inertia[b,None]);correction=n*(np.maximum(overlap-.00006,0)*.28/inverse)[:,None];np.add.at(p,a,-correction*inv[a,None]);np.add.at(p,b,correction*inv[b,None]);return len(a)
path=EP/'cache/particles/EP002_FineGranular_Physical60_v023.mdd';t=time.monotonic();ranges={};maxspeed=0
with path.open('wb') as file:
 file.write(struct.pack('>2i',end-start+1,N*4));file.write(np.arange(end-start+1,dtype='>f4').__mul__(1/60).astype('>f4').tobytes())
 for f in range(start,end+1):
  if f>start:
   for step in range(8):
    v[:,2]-=9.81*dt;v*=math.exp(-.025*dt);omega*=math.exp(-.1*dt);p+=v*dt
    if f>=1280:
     for iteration in range(2):contacts=pair_contacts();contact_boxes(f-start-1,(step+1)/8)
    angle=np.linalg.norm(omega,axis=1)*dt;axis=omega/np.maximum(np.linalg.norm(omega,axis=1)[:,None],1e-12);c=np.cos(angle);si=np.sin(angle);K=np.zeros((N,3,3));K[:,0,1]=-axis[:,2];K[:,0,2]=axis[:,1];K[:,1,0]=axis[:,2];K[:,1,2]=-axis[:,0];K[:,2,0]=-axis[:,1];K[:,2,1]=axis[:,0];D=np.eye(3)[None,:,:]*c[:,None,None]+axis[:,:,None]*axis[:,None,:]*(1-c[:,None,None])+K*si[:,None,None];rotation=np.einsum('nij,njk->nik',D,rotation)
  assert np.isfinite(p).all() and np.isfinite(v).all();maxspeed=max(maxspeed,float(np.linalg.norm(v,axis=1).max()));data=np.empty((N,4,3));data[:,0]=p
  for i in range(3):data[:,i+1]=p+rotation[:,:,i]*r[:,None]
  file.write(data.astype('>f4').tobytes())
  if (f-start)%10==0:
   report={'frame':f,'particles':N,'elapsed_seconds':round(time.monotonic()-t,1),'z_range':[float(p[:,2].min()),float(p[:,2].max())],'max_speed':maxspeed};ranges[f]=report['z_range'];(EP/'edit/fine_sand_progress.json').write_text(json.dumps(report,indent=2));print('FINE_GRAINS',report,flush=True)
np.savez(EP/'cache/particles/fine_grain_initial_v023.npz',radii=r,initial=data)
(EP/'edit/fine_sand_report_v023.json').write_text(json.dumps({'particles':N,'method':'Individual spherical dissipative discrete element dynamics, gravity, equal/opposite collision impulses, Coulomb friction, rotational inertia, moving oriented body contacts','fps':60,'substeps':8,'radius_m':[float(r.min()),float(r.max())],'friction':mu,'restitution':restitution,'ranges':ranges,'max_speed_m_s':maxspeed,'seconds':time.monotonic()-t},indent=2));print('FINE_GRAIN_SIMULATION_COMPLETE',flush=True)
