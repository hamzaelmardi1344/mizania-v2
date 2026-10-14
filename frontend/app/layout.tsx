import type { Metadata } from 'next';
import './globals.css';
import './v2.css';
export const metadata:Metadata={title:'Mizania — Votre espace cabinet',description:'Vos dossiers, documents et références dans un espace sécurisé.',robots:{index:false,follow:false}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="fr"><body>{children}</body></html>;}
