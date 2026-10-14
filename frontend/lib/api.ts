export class ApiError extends Error { constructor(message:string,public status:number){super(message);} }
export async function api<T>(path:string,options:RequestInit={},csrf?:string):Promise<T>{
  const headers=new Headers(options.headers);
  if(options.body && !(options.body instanceof FormData)) headers.set('Content-Type','application/json');
  if(csrf) headers.set('X-CSRF-Token',csrf);
  const response=await fetch(`/api${path}`,{...options,headers,credentials:'same-origin',cache:'no-store'});
  if(response.status===401 && path!='/auth/login') { window.location.replace('/connexion'); throw new ApiError('Session expirée.',401); }
  if(!response.ok){
    const data=await response.json().catch(()=>({detail:'Le service est momentanément indisponible.'}));
    throw new ApiError(typeof data.detail==='string'?data.detail:'Vérifiez les champs saisis.',response.status);
  }
  return response.json() as Promise<T>;
}
export const dateLabel=(value:number|string)=>new Date(typeof value==='number'?value*1000:value).toLocaleDateString('fr-MA',{day:'2-digit',month:'short',year:'numeric'});
export const statusLabel:Record<string,string>={received:'Reçu',review:'À examiner',blocked:'Bloqué',open:'En attente',answered:'Réponse reçue',closed:'Clôturée',draft:'À vérifier',verified:'Source vérifiée',rejected:'Écart constaté',manager:'Responsable',collaborator:'Collaborateur',reviewer:'Réviseur',client:'Client'};
