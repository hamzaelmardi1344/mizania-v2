# Design conservé, parcours transformés

Référence : dépôt privé `hamzaelmardi1344/mizania`, branche main observée au commit `f7a37f3d88f86f41bd1253149fe6e591607f6abf`.

Sources consultées : `frontend/app/globals.css` (blob `48f178960f5ebdcdf6f44876b884fd8452f4156f`) et `frontend/components/cabinet/ui.tsx` (blob `b21aa52fd10d61273d3d8cb8a68f04e001dd49c6`). Réutilisation des primitives et tokens, sans copie de l’ancien store et de ses fixtures.

Tokens repris : navy `#101b2d`, ink `#101435`, muted `#6372a6`, primary `#4935ff`, line `#e8eefb`, surface `#f5f8ff`, sidebar 210 px, Arial/Helvetica ; gradients marine et indigo, cartes arrondies et icônes Lucide en trait 1.75. Les composants Card, Heading, Button et IconBox gardent leurs structures visuelles.

Les nouveaux écrans sont une transformation fonctionnelle : connexion, mes dossiers, accueil dossier, pièces, échanges, paramètres, référentiel, portail client. Les captures Bleez déterminent les domaines métier et non une nouvelle charte graphique.

Aucun chatbot ni liste d’agents dans les interfaces métier. Les résultats portent des statuts de travail : reçu, à vérifier, bloqué, partagé. Aucun score de modèle ou promesse de conformité sur un badge.

Les assets distants et logos tiers ne sont pas chargés automatiquement. Les règles d’accessibilité incluent labels, focus visible, dialogue natif, navigation clavier, tableaux défilants, adaptation mobile et mouvement réduit.
