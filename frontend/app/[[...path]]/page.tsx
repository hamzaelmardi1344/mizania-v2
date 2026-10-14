import { cookies } from 'next/headers';
import { redirect, notFound } from 'next/navigation';
import { Workspace } from '@/components/workspace';
import { LoginPage } from '@/components/login';
import type { Session,Dossier,Module } from '@/lib/types';
export const dynamic='force-dynamic';
const backend=process.env.API_INTERNAL_URL||'http://127.0.0.1:8000';
async function get(path:string){
  const jar=await cookies();
  const cookie=jar.get('mizania_session');
  return fetch(`${backend}/api${path}`,{headers:cookie?{cookie:`mizania_session=${cookie.value}`}:{},cache:'no-store',signal:AbortSignal.timeout(8000)});
}
export default async function Page({params}:{params:Promise<{path?:string[]}>}){
  const {path=[]}=await params;
  if(path[0]==='activation')return <LoginPage activation/>;
  let result:Response;
  try{result=await get('/auth/session');}catch{return <LoginPage unavailable/>;}
  if(result.status===401){if(path[0]!=='connexion')redirect('/connexion');return <LoginPage/>;}
  if(!result.ok)return <LoginPage unavailable/>;
  const session=await result.json() as Session;
  const root=session.kind==='client'?'portail':'cabinet';
  if(path[0]!==root)redirect(`/${root}`);
  const list=await get('/dossiers');
  if(!list.ok)return <LoginPage unavailable/>;
  const dossiers=await list.json() as Dossier[];
  if(path.length===1 && root==='portail' && dossiers.length===1)redirect(`/portail/dossiers/${dossiers[0].id}/overview`);
  let dossier:Dossier|undefined;let modules:Module[]=[];
  let section='dossiers';
  if(path[1]==='references' && root==='cabinet' && path.length===2){section='references';}
  else if(path[1]==='dossiers' && path[2] && path.length<=4){
    const detail=await get(`/dossiers/${encodeURIComponent(path[2])}`);
    if(detail.status===404)notFound();
    if(!detail.ok)redirect(`/${root}`);
    dossier=await detail.json() as Dossier;
    section=path[3]||'overview';
    if(root==='cabinet'){
      const moduleResponse=await get(`/dossiers/${dossier.id}/modules`);
      if(!moduleResponse.ok)notFound();modules=await moduleResponse.json() as Module[];
      if(!modules.some(m=>m.id===section))notFound();
    }else{
      modules=[{id:'overview',label:'Mon entreprise',icon:'home',ready:true,tabs:[]},{id:'documents',label:'Mes documents',icon:'folder',ready:true,tabs:[]},{id:'requests',label:'Mes échanges',icon:'mail',ready:true,tabs:[]},{id:'published',label:'Documents partagés',icon:'book',ready:true,tabs:[]}];
      if(!modules.some(m=>m.id===section))notFound();
    }
  }else if(path.length!==1)notFound();
  return <Workspace key={`${session.id}:${dossier?.id||''}:${section}`} session={session} dossiers={dossiers} dossier={dossier} section={section} modules={modules}/>;
}
