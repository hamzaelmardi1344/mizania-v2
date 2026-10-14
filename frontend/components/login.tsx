'use client';
import {useState,useEffect,type FormEvent} from 'react';
import {api} from '@/lib/api';
import {Icon,Button} from './ui';
export function LoginPage({activation=false,unavailable=false}:{activation?:boolean;unavailable?:boolean}){
 const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [token,setToken]=useState('');
 useEffect(()=>{if(activation){setToken(new URLSearchParams(window.location.hash.slice(1)).get('token')||'');history.replaceState(null,'','/activation');}},[activation]);
 async function submit(e:FormEvent<HTMLFormElement>){
  e.preventDefault();setBusy(true);setError('');const form=new FormData(e.currentTarget);
  try{
   if(activation){await api('/auth/activate',{method:'POST',body:JSON.stringify({token,password:form.get('password')})});window.location.replace('/connexion');}
   else {const result=await api<{kind:string}>('/auth/login',{method:'POST',body:JSON.stringify({email:form.get('email'),password:form.get('password')})});window.location.replace(result.kind==='client'?'/portail':'/cabinet');}
  }catch(e){setError(e instanceof Error?e.message:'Connexion indisponible.');}finally{setBusy(false);}
 }
 return <main className="login-page"><aside className="login-brand"><a className="brand" href="/"><Icon name="logo" size={34}/><span><b>Mizania</b><small>Votre cabinet. Tout simplement.</small></span></a><div><span className="eyebrow">UN ESPACE POUR CHAQUE ENTREPRISE</span><h1>Vos dossiers.<br/>L’essentiel,<br/>au même endroit.</h1><p>Documents, échanges et travaux réunis dans un espace dédié à votre entreprise.</p><div className="login-proof"><Icon name="shield"/><span>Un accès personnel. Des dossiers cloisonnés.</span></div></div><small>Mizania · Espace professionnel</small></aside><section className="login-form-panel"><form className="login-form" onSubmit={submit}><span className="icon-box blue"><Icon name="lock" size={24}/></span><h1>{activation?'Bienvenue dans votre espace':'Heureux de vous retrouver'}</h1><p className="muted">{activation?'Choisissez un mot de passe pour activer votre accès.':'Connectez-vous pour retrouver vos dossiers.'}</p>{unavailable?<div className="notice warning" role="alert">Le service est momentanément indisponible. Aucune donnée de dossier n’est affichée.<p><a className="text-action" href="/">Réessayer</a></p></div>:<>{!activation&&<label className="field">Adresse e-mail<input name="email" type="email" required autoComplete="username" placeholder="prenom@cabinet.ma"/></label>}<label className="field">Mot de passe<input name="password" type="password" required minLength={activation?14:1} maxLength={128} autoComplete={activation?'new-password':'current-password'}/></label>{activation&&<small className="muted">14 caractères minimum. Votre lien d’invitation est personnel et à usage unique.</small>}{error&&<p className="notice warning" role="alert">{error}</p>}<Button type="submit" kind="primary" disabled={busy||(activation&&!token)}>{busy?'Connexion en cours…':activation?'Activer mon compte':'Se connecter'}</Button><p className="login-help">L’accès est délivré par votre cabinet. Pour toute difficulté, contactez votre responsable.</p></>}</form></section></main>;
}
