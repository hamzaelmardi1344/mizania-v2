'use client';
import {useState,useEffect,useCallback,useRef,type FormEvent, type ReactNode} from 'react';
import {api,ApiError,dateLabel,statusLabel} from '@/lib/api';
import type {Session,Dossier,Module,Document,Overview,Work,ClientRequest,Source,SourceVersion,Assignment,Member} from '@/lib/types';
import {Icon,IconBox,Button,Badge,Card,Heading,Stat,SearchField,Empty,Modal} from './ui';

type Props={session:Session;dossiers:Dossier[];dossier?:Dossier;section:string;modules:Module[]};
type FormKind='dossier'|'exercise'|'invitation'|'request'|'reference'|'assignment';
type Field={name:string;label:string;type?:string;required?:boolean;options?:{value:string;label:string}[];minLength?:number;maxLength?:number};
type Loaded={overview?:Overview;documents?:Document[];work?:Work[];requests?:ClientRequest[];sources?:Source[];versions?:SourceVersion[];assignments?:Assignment[];members?:Member[];audit?:{id:string;action:string;at:number;target_id:string}[]};
const titleMap:Record<string,string>={dossiers:'Mes dossiers',references:'Référentiel réglementaire',overview:'Vue d’ensemble',work:'À traiter',documents:'Documents',requests:'Échanges client',published:'Documents partagés',settings:'Paramètres du dossier'};
export function Workspace({session,dossiers,dossier,section,modules}:Props){
 const portal=session.kind==='client';const root=portal?'/portail':'/cabinet';
 const context=dossier?`${root}/dossiers/${dossier.id}`:root;
 const base=dossier?`/dossiers/${dossier.id}`:'';
 const current=modules.find(m=>m.id===section);
 const [loaded,setLoaded]=useState<Loaded>({});const [loading,setLoading]=useState(true);
 const [error,setError]=useState('');const [notice,setNotice]=useState('');const [busy,setBusy]=useState(false);
 const [search,setSearch]=useState('');const [form,setForm]=useState<FormKind|null>(null);
 const [reply,setReply]=useState<ClientRequest|null>(null);const [reference,setReference]=useState<SourceVersion|null>(null);
 const [invitation,setInvitation]=useState('');const [mobile,setMobile]=useState(false);
 const uploadInput=useRef<HTMLInputElement>(null);
 const mounted=useRef(true);
 useEffect(()=>()=>{mounted.current=false;},[]);
 const load=useCallback(async()=>{
   try{
     let next:Loaded={};
     if(section==='references'){
       const [sources,versions]=await Promise.all([api<Source[]>('/knowledge/sources'),api<SourceVersion[]>('/knowledge/versions')]);next={sources,versions};
     }else if(dossier){
       // Revalidate scope on every refresh, including pages without list endpoints.
       await api(`/dossiers/${dossier.id}`);
       if(section==='overview')next.overview=await api<Overview>(base+'/overview');
       if(section==='documents'||section==='published')next.documents=await api<Document[]>(base+'/documents');
       if(section==='work')next.work=await api<Work[]>(base+'/work');
       if(section==='requests')next.requests=await api<ClientRequest[]>(base+'/requests');
       if(section==='settings' && ['manager','reviewer'].includes(dossier.role)){
         next.audit=await api<Loaded['audit']>(base+'/audit');
         if(dossier.role==='manager')next.assignments=await api<Assignment[]>(base+'/assignments');
         if(session.cabinet_admin)next.members=await api<Member[]>('/cabinet/users');
       }
     }
     if(mounted.current){setLoaded(next);setError('');}
   }catch(e){if(mounted.current){setLoaded({});setError(e instanceof Error?e.message:'Chargement indisponible.');}}
   finally{if(mounted.current)setLoading(false);}
 },[base,dossier,section,session.cabinet_admin]);
 useEffect(()=>{mounted.current=true;void load();},[load]);
 useEffect(()=>{
   const recheck=()=>{if(document.visibilityState==='visible')void api('/auth/session').then(()=>load()).catch(()=>setLoaded({}));};
   const id=setInterval(recheck,15000);document.addEventListener('visibilitychange',recheck);
   window.addEventListener('pageshow',recheck);
   return()=>{clearInterval(id);document.removeEventListener('visibilitychange',recheck);window.removeEventListener('pageshow',recheck);};
 },[load]);
 async function mutate(path:string,body?:unknown,method='POST'){
   setBusy(true);setNotice('');
   try{await api(path,{method,body:body===undefined?undefined:JSON.stringify(body)},session.csrf);await load();setNotice('Modification enregistrée.');}
   catch(e){setNotice(e instanceof Error?e.message:'L’enregistrement a échoué.');throw e;}
   finally{setBusy(false);}
 }
 async function uploadFiles(files:FileList|null){
   if(!files?.length||!dossier)return;
   setBusy(true);setNotice('');let count=0;const failures:string[]=[];
   try{
    for(const file of Array.from(files)){
     if(file.size>10*1024*1024){failures.push(`${file.name} : taille maximale de 10 Mo.`);continue;}
     const data=new FormData();data.append('file',file);
     try{await api(base+'/documents',{method:'POST',body:data},session.csrf);count++;}
     catch(e){failures.push(`${file.name} : ${e instanceof Error?e.message:'échec du dépôt'}`);}
    }
    await load();setNotice(`${count} document${count>1?'s':''} reçu${count>1?'s':''}.${failures.length?' '+failures.join(' '):' Les contrôles se poursuivent en arrière-plan.'}`);
   }finally{setBusy(false);if(uploadInput.current)uploadInput.current.value='';}
 }
 async function download(doc:Document){
   try{
    const response=await fetch(`/api${base}/documents/${doc.id}/download`,{credentials:'same-origin',cache:'no-store'});
    if(response.status===401){window.location.replace('/connexion');return;}
    if(!response.ok){const e=await response.json();throw new Error(e.detail);}
    const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=doc.filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
   }catch(e){setNotice(e instanceof Error?e.message:'Téléchargement indisponible.');}
 }
 async function submitForm(values:Record<string,string>){
   if(form==='dossier'){
    const created=await api<Dossier>('/dossiers',{method:'POST',body:JSON.stringify(values)},session.csrf);
    window.location.assign(`${root}/dossiers/${created.id}/overview`);return;
   }
   if(form==='invitation'){
    const result=await api<{activation_url:string}>(base+'/invitations',{method:'POST',body:JSON.stringify(values)},session.csrf);
    setForm(null);setInvitation(result.activation_url);return;
   }
   if(form==='reference'){
    const body={...values,effective_to:values.effective_to||null};await mutate('/knowledge/versions',body);
   }else if(form==='exercise'){
    await mutate(base+'/exercises',values);window.location.reload();return;
   }else if(form==='request')await mutate(base+'/requests',values);
   else if(form==='assignment')await mutate(base+'/assignments',{...values,active:true},'PUT');
   setForm(null);
 }
 const fields:Record<FormKind,Field[]>={
  dossier:[{name:'name',label:'Raison sociale',minLength:2,maxLength:160},{name:'code',label:'Code du dossier',minLength:2,maxLength:32},{name:'ice',label:'ICE (15 chiffres)',required:false,maxLength:15}],
  exercise:[{name:'label',label:'Libellé de l’exercice',maxLength:32},{name:'starts_on',label:'Date de début',type:'date'},{name:'ends_on',label:'Date de fin',type:'date'}],
  invitation:[{name:'name',label:'Nom du représentant',minLength:2},{name:'email',label:'Adresse e-mail',type:'email'}],
  request:[{name:'title',label:'Objet de la demande',minLength:3,maxLength:160},{name:'body',label:'Précisions pour le client',type:'textarea',minLength:3,maxLength:4000}],
  assignment:[{name:'user_id',label:'Collaborateur',options:(loaded.members||[]).filter(m=>m.kind==='staff').map(m=>({value:m.id,label:m.name+' · '+m.email}))},{name:'role',label:'Habilitation',options:[{value:'collaborator',label:'Collaborateur'},{value:'reviewer',label:'Réviseur'},{value:'manager',label:'Responsable'}]}],
  reference:[{name:'source_id',label:'Autorité officielle',options:(loaded.sources||[]).map(s=>({value:s.id,label:s.authority}))},{name:'title',label:'Intitulé du texte',minLength:5,maxLength:200},{name:'citation',label:'Référence, article et édition',minLength:5,maxLength:200},{name:'url',label:'Adresse officielle exacte',type:'url'},{name:'published_on',label:'Publication officielle',type:'date'},{name:'effective_from',label:'Début d’applicabilité',type:'date'},{name:'effective_to',label:'Fin d’applicabilité (facultatif)',type:'date',required:false},{name:'text',label:'Texte à archiver (aucune donnée client)',type:'textarea',minLength:50,maxLength:500000}]
 };
 const formTitles:Record<FormKind,string>={dossier:'Ouvrir un dossier',exercise:'Créer un exercice',invitation:'Inviter le client',request:'Demander un complément',reference:'Ajouter une version au référentiel',assignment:'Affecter un collaborateur'};
 const filteredDossiers=dossiers.filter(d=>(d.name+' '+d.code).toLowerCase().includes(search.toLowerCase()));
 const documentRows=(loaded.documents||[]).filter(d=>(section!=='published'||d.published)&&d.filename.toLowerCase().includes(search.toLowerCase()));
 const documentTable=(docs:Document[])=>!docs.length?<Empty title="Aucun document pour le moment">Les pièces reçues et les documents autorisés apparaîtront ici.</Empty>:<div className="table-scroll"><table><thead><tr><th>Document</th><th>Réception</th><th>État</th><th>Partage</th><th>Actions</th></tr></thead><tbody>{docs.map(doc=><tr key={doc.id}><td><span className="document-name"><Icon name="file" size={16}/>{doc.filename}</span><small className="muted">{(doc.size/1024).toFixed(1)} Ko</small></td><td>{dateLabel(doc.created_at)}</td><td><Badge tone={doc.state==='blocked'?'red':doc.state==='review'?'orange':'blue'}>{portal?(doc.state==='blocked'?'À remplacer':doc.state==='received'?'Reçu':'En cours de traitement'):statusLabel[doc.state]||doc.state}</Badge></td><td>{doc.published?<Badge tone="green">Partagé avec le client</Badge>:<span className="muted">{portal?'Transmis au cabinet':'Interne au cabinet'}</span>}</td><td><div className="row-actions"><Button icon="download" onClick={()=>void download(doc)}>Télécharger</Button>{!portal&&!doc.published&&['manager','reviewer'].includes(dossier?.role||'')&&<Button disabled={busy} onClick={()=>void mutate(base+`/documents/${doc.id}/publish`).catch(()=>{})}>Partager au client</Button>}</div></td></tr>)}</tbody></table></div>;
 return <div className="app-shell">
  <a className="skip-link" href="#main-content">Aller au contenu</a>
  <aside className={'sidebar '+(mobile?'is-open':'')} aria-label="Navigation principale">
   <a className="brand" href={root}><Icon name="logo" size={30}/><span><b>Mizania</b><small>Votre cabinet. Tout simplement.</small></span></a>
   {dossier&&<div className="dossier-context"><small>DOSSIER ACTIF</small><strong>{dossier.name}</strong><label className="sr-only" htmlFor="dossier-switch">Changer de dossier</label><select id="dossier-switch" value={dossier.id} onChange={e=>window.location.assign(`${root}/dossiers/${e.target.value}/overview`)}>{dossiers.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select></div>}
   <nav><a className={section==='dossiers'?'active':''} href={root}><Icon name="folder"/>Mes dossiers</a>{dossier&&<><span className="nav-label">{portal?'MON ENTREPRISE':'ESPACE DOSSIER'}</span>{modules.map(m=><a key={m.id} className={section===m.id?'active':''} aria-current={section===m.id?'page':undefined} href={`${context}/${m.id}`}><Icon name={m.icon} size={18}/>{m.label}</a>)}</>}{!portal&&<><span className="nav-label">RÉFÉRENCES</span><a className={section==='references'?'active':''} href="/cabinet/references"><Icon name="book"/>Base de connaissances</a></>}</nav>
   <div className="sidebar-bottom"><div className="cabinet-switch"><Icon name="building"/><span><b>{session.cabinet_name}</b><small>{portal?'Portail client':'Espace cabinet'}</small></span></div><div className="user-profile"><span className="avatar">{session.name.split(' ').map(x=>x[0]).slice(0,2).join('')}</span><span><b>{session.name}</b><small>{portal?'Représentant de l’entreprise':'Collaborateur du cabinet'}</small></span><button aria-label="Se déconnecter" title="Se déconnecter" onClick={()=>void api('/auth/logout',{method:'POST'},session.csrf).then(()=>window.location.replace('/connexion')).catch(e=>setNotice(e.message))}><Icon name="logout" size={17}/></button></div></div>
  </aside>
  <main className="main" id="main-content"><div className="topbar"><button className="icon-button mobile-menu" aria-label="Ouvrir le menu" onClick={()=>setMobile(!mobile)}><Icon name="menu"/></button><div className="topbar-breadcrumb"><span>{portal?'Portail client':'Cabinet'}</span><Icon name="right" size={12}/><b>{dossier?.name||'Mon espace'}</b></div><span className="secure-label"><Icon name="lock" size={13}/>Espace privé</span>{dossier&&<span className="topbar-date">{dossier.exercises?.[0]?.label?'Dernier exercice : '+dossier.exercises[0].label:'Aucun exercice ouvert'}</span>}</div>
   <div className="page-content"><Heading title={titleMap[section]||current?.label||'Mon espace'} subtitle={section==='dossiers'?'Chaque entreprise, son espace. Retrouvez les dossiers qui vous sont attribués.':section==='references'?'Sources officielles marocaines, versions et vérifications documentées.':dossier?.name} eyebrow={dossier?<><span>{dossier.code}</span><span>•</span><span>{statusLabel[dossier.role]}</span></>:undefined} actions={section==='dossiers'&&session.cabinet_admin?<Button kind="primary" icon="plus" onClick={()=>setForm('dossier')}>Ouvrir un dossier</Button>:section==='references'&&session.knowledge_editor?<Button kind="primary" icon="plus" onClick={()=>setForm('reference')}>Ajouter une référence</Button>:dossier&&['overview','documents'].includes(section)?<Button kind="primary" icon="upload" disabled={busy} onClick={()=>uploadInput.current?.click()}>Déposer des pièces</Button>:undefined}/>
   <input ref={uploadInput} type="file" className="sr-only" accept=".pdf,.png,.jpg,.jpeg" multiple onChange={e=>void uploadFiles(e.target.files)} aria-label="Déposer des pièces"/>
   {notice&&<div className="notice" role="status"><span>{notice}</span><button aria-label="Fermer le message" onClick={()=>setNotice('')}><Icon name="close" size={16}/></button></div>}
   {error?<Card><Empty title="Cet espace est momentanément indisponible">{error}</Empty><Button onClick={()=>void load()}>Réessayer</Button></Card>:loading?<div className="loading-state" role="status"><div className="skeleton"/><div className="skeleton"/><p>Chargement de votre espace…</p></div>:<>
    {section==='dossiers'&&<><div className="stats-grid"><Stat label="Dossiers attribués" value={dossiers.length} icon="folder" note="Votre périmètre personnel"/><Stat label="Accès" value={portal?'Client':'Cabinet'} icon="shield" tone="green" note="Droits vérifiés à chaque ouverture"/></div><div className="toolbar"><SearchField value={search} onChange={setSearch} placeholder="Rechercher une entreprise ou un code…"/></div>{!filteredDossiers.length?<Card><Empty title={search?'Aucun dossier ne correspond':'Aucun dossier attribué'}>{session.cabinet_admin?'Ouvrez votre premier dossier pour commencer.':'Votre responsable doit vous affecter un dossier avant de poursuivre.'}</Empty></Card>:<div className="grid three dossier-grid">{filteredDossiers.map(d=><a key={d.id} className="card dossier-card" href={`${root}/dossiers/${d.id}/overview`}><div className="card-header"><IconBox name="building"/><Badge tone="gray">{d.code}</Badge></div><h2>{d.name}</h2><p className="muted">{d.ice?'ICE '+d.ice:'Fiche entreprise à compléter'}</p><div className="dossier-card-bottom"><Badge>{statusLabel[d.role]}</Badge><span className="text-action">Ouvrir le dossier <Icon name="right" size={15}/></span></div></a>)}</div>}</>}
    {section==='overview'&&loaded.overview&&<><div className="stats-grid"><Stat label="Documents reçus" value={loaded.overview.documents} icon="file"/><Stat label={portal?'En cours de réception':'À examiner'} value={portal?loaded.overview.received:loaded.overview.work} icon="task" tone="orange"/><Stat label="Échanges ouverts" value={loaded.overview.requests} icon="mail" tone="purple"/><Stat label="Documents partagés" value={loaded.overview.published} icon="book" tone="green"/></div><div className="grid two"><Card title="Votre espace de travail" icon="folder"><div className="stack quick-actions"><a className="list-row" href={`${context}/documents`}><IconBox name="upload"/><span><b>Retrouver mes documents</b><small>Pièces reçues, documents et justificatifs.</small></span><Icon name="right"/></a><a className="list-row" href={`${context}/requests`}><IconBox name="mail" tone="purple"/><span><b>{portal?'Répondre au cabinet':'Échanger avec le client'}</b><small>{loaded.overview.requests} échange(s) en cours.</small></span><Icon name="right"/></a>{!portal&&<a className="list-row" href={`${context}/work`}><IconBox name="task" tone="orange"/><span><b>Examiner les pièces reçues</b><small>Les points nécessitant votre attention.</small></span><Icon name="right"/></a>}</div></Card><Card title="Déposer un document" icon="upload"><DropArea disabled={busy} onFiles={uploadFiles} onClick={()=>uploadInput.current?.click()}/><p className="muted upload-help">PDF, PNG ou JPEG · 10 Mo par fichier. Le dépôt est rattaché uniquement à {dossier?.name}.</p></Card></div><Card className="section-gap" title="Derniers documents" action={<a className="text-action" href={`${context}/documents`}>Tout consulter</a>}>{documentTable(loaded.overview.recent_documents)}</Card></>}
    {(section==='documents'||section==='published')&&<><div className="toolbar"><SearchField value={search} onChange={setSearch} placeholder="Rechercher un document…"/><Badge tone="gray">{documentRows.length} document(s)</Badge></div>{section==='documents'&&<DropArea compact disabled={busy} onFiles={uploadFiles} onClick={()=>uploadInput.current?.click()}/>}<Card className="section-gap">{documentTable(documentRows)}</Card></>}
    {section==='work'&&<Card title="Points à examiner" icon="task">{!loaded.work?.length?<Empty title="Aucun point à examiner">Les pièces reçues apparaîtront ici après leur contrôle.</Empty>:loaded.work.map(w=><div className="work-row" key={w.id}><IconBox name="file" tone="orange"/><div><h3>{w.title}</h3><p className="muted">{w.reason}</p></div><a className="btn" href={`${context}/documents`}>Consulter les pièces</a></div>)}</Card>}
    {section==='requests'&&<><div className="toolbar"><p className="muted">Les échanges restent rattachés à ce dossier.</p><span className="spacer"/>{!portal&&<Button kind="primary" icon="plus" onClick={()=>setForm('request')}>Demander un complément</Button>}</div>{!loaded.requests?.length?<Card><Empty title="Aucun échange en cours">Les demandes du cabinet et vos réponses apparaîtront ici.</Empty></Card>:<div className="stack">{loaded.requests.map(r=><Card key={r.id} title={r.title} action={<Badge tone={r.state==='closed'?'green':r.state==='answered'?'blue':'orange'}>{statusLabel[r.state]}</Badge>}><p className="preserve-text">{r.body}</p>{r.reply&&<div className="reply-box"><small>Réponse du client</small><p className="preserve-text">{r.reply}</p></div>}<div className="card-footer"><span className="muted">{dateLabel(r.created_at)}</span>{portal&&r.state==='open'&&<Button kind="primary" onClick={()=>setReply(r)}>Répondre</Button>}{!portal&&r.state!=='closed'&&<Button disabled={busy} onClick={()=>void mutate(base+`/requests/${r.id}/close`).catch(()=>{})}>Clôturer l’échange</Button>}</div></Card>)}</div>}</>}
    {section==='references'&&<><div className="notice"><Icon name="shield"/><span>Une source répertoriée n’est pas une règle validée. Chaque texte doit être vérifié avant d’être utilisé dans les contrôles métier.</span></div><div className="stats-grid"><Stat label="Autorités référencées" value={loaded.sources?.length||0} icon="building"/><Stat label="Versions archivées" value={loaded.versions?.length||0} icon="book" tone="purple"/><Stat label="Versions vérifiées" value={loaded.versions?.filter(v=>v.status==='verified').length||0} icon="shield" tone="green"/><Stat label="À examiner" value={loaded.versions?.filter(v=>v.status==='draft').length||0} icon="task" tone="orange"/></div><div className="grid three">{loaded.sources?.map(s=><Card key={s.id} title={s.title} icon="book"><p className="muted">{s.authority}</p><div className="card-footer"><Badge tone="gray">{s.versions} version(s)</Badge><a className="text-action" href={s.url} target="_blank" rel="noopener noreferrer">Source officielle ↗</a></div></Card>)}</div><Card className="section-gap" title="Versions & traçabilité"><div className="toolbar"><SearchField value={search} onChange={setSearch} placeholder="Rechercher une référence…"/></div>{!loaded.versions?.length?<Empty title="Le corpus est prêt à être alimenté">Aucun texte n’a encore été importé ni vérifié. Aucun taux ou calcul fiscal n’est activé par défaut.</Empty>:<div className="table-scroll"><table><thead><tr><th>Référence</th><th>Publication</th><th>Applicabilité</th><th>Vérification</th><th/></tr></thead><tbody>{loaded.versions.filter(v=>(v.title+' '+v.citation).toLowerCase().includes(search.toLowerCase())).map(v=><tr key={v.id}><td><b>{v.title}</b><small className="muted block">{v.citation}</small></td><td>{dateLabel(v.published_on)}</td><td>{dateLabel(v.effective_from)}{v.effective_to?' – '+dateLabel(v.effective_to):' · fin non renseignée'}</td><td><Badge tone={v.status==='verified'?'green':'orange'}>{statusLabel[v.status]}</Badge></td><td><Button onClick={()=>void api<SourceVersion>('/knowledge/versions/'+v.id).then(setReference).catch(e=>setNotice(e.message))}>Consulter</Button></td></tr>)}</tbody></table></div>}</Card></>}
    {section==='settings'&&<><div className="grid two"><Card title="Fiche entreprise" icon="building"><dl className="detail-list"><div><dt>Raison sociale</dt><dd>{dossier?.name}</dd></div><div><dt>Code</dt><dd>{dossier?.code}</dd></div><div><dt>ICE</dt><dd>{dossier?.ice||'Non renseigné'}</dd></div><div><dt>Votre habilitation</dt><dd>{statusLabel[dossier?.role||'']}</dd></div></dl></Card><Card title="Exercices" icon="calendar" action={dossier?.role==='manager'?<Button icon="plus" onClick={()=>setForm('exercise')}>Créer</Button>:undefined}>{!dossier?.exercises?.length?<Empty title="Aucun exercice ouvert"/>:dossier.exercises.map(e=><div className="list-row" key={e.id}><span><b>{e.label}</b><small>{dateLabel(e.starts_on)} — {dateLabel(e.ends_on)}</small></span><Badge tone="gray">{e.closed?'Clôturé':'Ouvert'}</Badge></div>)}</Card></div>{dossier?.role==='manager'&&<Card className="section-gap" title="Accès au dossier" action={<div className="row-actions">{session.cabinet_admin&&<Button icon="users" onClick={()=>setForm('assignment')}>Affecter</Button>}<Button kind="primary" icon="plus" onClick={()=>setForm('invitation')}>Inviter le client</Button></div>}>{loaded.assignments?.map(a=><div className="list-row" key={a.user_id}><span className="avatar blue">{a.name[0]}</span><span><b>{a.name}</b><small>{a.email}</small></span><Badge tone={a.active?'blue':'gray'}>{a.active?statusLabel[a.role]:'Accès retiré'}</Badge>{session.cabinet_admin&&a.user_id!==session.id&&a.active&&<Button disabled={busy} kind="danger" onClick={()=>{if(window.confirm(`Retirer l’accès de ${a.name} à ce dossier ?`))void mutate(base+'/assignments',{user_id:a.user_id,role:a.role,active:false},'PUT').catch(()=>{});}}>Retirer l’accès</Button>}</div>)}</Card>}{loaded.audit&&<Card className="section-gap" title="Historique des opérations"><div className="table-scroll"><table><thead><tr><th>Date</th><th>Opération</th><th>Référence</th></tr></thead><tbody>{loaded.audit.map(a=><tr key={a.id}><td>{dateLabel(a.at)}</td><td>{auditLabel(a.action)}</td><td className="muted">{a.target_id.slice(0,12)}</td></tr>)}</tbody></table></div></Card>}</>}
    {current&&!current.ready&&<Card><div className="tabs">{current.tabs.map(t=><span key={t}>{t}</span>)}</div><Empty title="Ce module est en cours de raccordement">Les parcours métier sont prévus dans ce dossier. Les calculs, écritures et déclarations ne sont pas encore activés dans cette version.</Empty><div className="notice"><Icon name="shield"/><span>Aucune finalisation comptable ou fiscale n’est possible sans règles applicables, tests et validation réglementaire.</span></div><div className="center-actions"><a className="btn primary" href={`${context}/documents`}>Consulter les pièces du dossier</a><a className="btn" href="/cabinet/references">Consulter les références</a></div></Card>}
   </>}
   <footer className="workspace-footer">Mizania · {dossier?`Espace dédié à ${dossier.name}`:'Votre espace professionnel'} · Version de développement</footer>
   </div>
  </main>
  {form&&<FormDialog title={formTitles[form]} fields={fields[form]} onClose={()=>setForm(null)} onSubmit={submitForm} note={form==='reference'?'N’importez que des textes publics. La source, la fidélité du texte et ses dates devront être contrôlées par un second responsable habilité.':undefined}/>}
  {reply&&<FormDialog title={'Répondre · '+reply.title} fields={[{name:'reply',label:'Votre réponse',type:'textarea',maxLength:4000}]} onClose={()=>setReply(null)} onSubmit={async values=>{await mutate(base+`/requests/${reply.id}/reply`,values);setReply(null);}}/>}
  {invitation&&<Modal title="Invitation créée" onClose={()=>setInvitation('')}><p>Transmettez ce lien personnel au représentant par un canal sécurisé. Il expire dans 48 heures et ne peut être utilisé qu’une fois.</p><label className="field">Lien d’activation<textarea readOnly value={invitation} rows={4} onFocus={e=>e.target.select()}/></label><p className="muted">Aucun e-mail n’a été envoyé automatiquement.</p></Modal>}
  {reference&&<Modal title={reference.title} onClose={()=>setReference(null)}><div className="reference-meta"><Badge tone={reference.status==='verified'?'green':'orange'}>{statusLabel[reference.status]}</Badge><a className="text-action" href={reference.url} target="_blank" rel="noopener noreferrer">Consulter l’original ↗</a></div><p className="muted">{reference.citation}</p><p className="hash">Empreinte SHA-256 du texte : {reference.sha256}</p><pre className="source-text">{reference.text}</pre>{reference.review_note&&<div className="notice">{reference.review_note}</div>}{session.knowledge_editor&&reference.status==='draft'&&reference.created_by!==session.id&&<InlineReview onSubmit={async values=>{await mutate('/knowledge/versions/'+reference.id+'/review',values);setReference(null);}}/>}{reference.created_by===session.id&&reference.status==='draft'&&<p className="muted">Un second responsable habilité doit vérifier cette version.</p>}</Modal>}
 </div>;
}
function DropArea({onFiles,onClick,disabled=false,compact=false}:{onFiles:(f:FileList|null)=>Promise<void>;onClick:()=>void;disabled?:boolean;compact?:boolean}){
 const [over,setOver]=useState(false);
 return <div className={`drop-area ${compact?'compact ':''}${over?'drag-over':''}`} onDragOver={e=>{e.preventDefault();if(!disabled)setOver(true);}} onDragLeave={()=>setOver(false)} onDrop={e=>{e.preventDefault();setOver(false);if(!disabled)void onFiles(e.dataTransfer.files);}}><IconBox name="upload"/><div><h3>{disabled?'Réception des documents…':'Glissez vos pièces ici'}</h3><p className="muted">ou sélectionnez-les depuis votre ordinateur.</p></div><Button disabled={disabled} onClick={onClick}>Choisir des fichiers</Button></div>;
}
function FormDialog({title,fields,onClose,onSubmit,note}:{title:string;fields:Field[];onClose:()=>void;onSubmit:(values:Record<string,string>)=>Promise<void>;note?:string}){
 const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();setBusy(true);setError('');const values=Object.fromEntries(new FormData(e.currentTarget).entries()) as Record<string,string>;try{await onSubmit(values);}catch(e){setError(e instanceof Error?e.message:'Enregistrement indisponible.');}finally{setBusy(false);}}
 return <Modal title={title} onClose={()=>{if(!busy)onClose();}}><form onSubmit={submit}>{note&&<p className="notice">{note}</p>}<div className="form-fields">{fields.map(f=><label className={'field '+(f.type==='textarea'?'wide-field':'')} key={f.name}>{f.label}{f.options?<select name={f.name} required={f.required!==false} disabled={busy}><option value="">Sélectionner…</option>{f.options.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>:f.type==='textarea'?<textarea name={f.name} rows={5} required={f.required!==false} minLength={f.minLength} maxLength={f.maxLength} disabled={busy}/>:<input name={f.name} type={f.type||'text'} required={f.required!==false} minLength={f.minLength} maxLength={f.maxLength} disabled={busy}/>}</label>)}</div>{error&&<p className="notice warning" role="alert">{error}</p>}<div className="modal-footer"><Button disabled={busy} onClick={onClose}>Annuler</Button><Button kind="primary" type="submit" disabled={busy}>{busy?'Enregistrement…':'Enregistrer'}</Button></div></form></Modal>;
}
function InlineReview({onSubmit}:{onSubmit:(values:Record<string,string>)=>Promise<void>}){
 const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 return <form className="review-form" onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');const values=Object.fromEntries(new FormData(e.currentTarget).entries()) as Record<string,string>;try{await onSubmit(values);}catch(e){setError(e instanceof Error?e.message:'Erreur.');}finally{setBusy(false);}}}><label className="field">Décision<select name="decision" required><option value="">Sélectionner…</option><option value="verified">Fidélité documentaire vérifiée</option><option value="rejected">Écart constaté</option></select></label><label className="field">Justification de la vérification<textarea name="note" required minLength={20} maxLength={4000} rows={3}/></label><p className="muted">Cette vérification porte sur le texte et sa provenance. Elle n’active aucune règle de calcul.</p>{error&&<p role="alert">{error}</p>}<Button type="submit" kind="primary" disabled={busy}>Enregistrer la vérification</Button></form>;
}
function auditLabel(code:string){const labels:Record<string,string>={'dossier.created':'Ouverture du dossier','exercise.created':'Création d’un exercice','assignment.updated':'Modification d’une habilitation','client.invited':'Invitation du client','client.activated':'Activation du portail client','document.received':'Réception d’un document','document.checked':'Contrôle du document','document.downloaded':'Téléchargement','document.published':'Partage avec le client','document.integrity_failed':'Écart d’intégrité','request.created':'Demande au client','request.answered':'Réponse du client','request.closed':'Clôture d’un échange'};return labels[code]||'Opération enregistrée';}
