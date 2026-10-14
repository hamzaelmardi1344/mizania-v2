# Source locations are a directory, NOT an ingested/validated corpus or tax rules.
SOURCES = [
 {"id":"sgg","authority":"Secrétariat général du gouvernement","title":"Bulletin officiel","url":"https://www.sgg.gov.ma/BulletinOfficiel.aspx","host":"www.sgg.gov.ma"},
 {"id":"dgi","authority":"Direction générale des impôts","title":"Documentation fiscale","url":"https://www.tax.gov.ma/","host":"www.tax.gov.ma"},
 {"id":"cnc","authority":"Ministère de l’Économie et des Finances","title":"Normes comptables / CNC","url":"https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx","host":"www.finances.gov.ma"},
 {"id":"cndp","authority":"CNDP","title":"Protection des données personnelles","url":"https://www.cndp.ma/","host":"www.cndp.ma"},
 {"id":"changes","authority":"Office des Changes","title":"Réglementation des changes","url":"https://www.oc.gov.ma/fr/reglementations","host":"www.oc.gov.ma"},
 {"id":"cnss","authority":"CNSS","title":"Références sociales","url":"https://www.cnss.ma/","host":"www.cnss.ma"},
]
MODULES = [
 {"id":"overview","label":"Vue d’ensemble","icon":"home","ready":True,"tabs":[]},
 {"id":"work","label":"À traiter","icon":"task","ready":True,"tabs":[]},
 {"id":"purchases","label":"Achats","icon":"card","ready":False,"tabs":["Synthèse","Dépôt de pièces","Factures à traiter","Immobilisations","Crédit-bail","Notes de frais","Paramétrage"]},
 {"id":"sales","label":"Ventes","icon":"chart","ready":False,"tabs":["Synthèse","Dépôt de pièces","Devis et factures","Produits","Caisse","Statistiques","Paramétrage"]},
 {"id":"accounting","label":"Comptabilité","icon":"calculator","ready":False,"tabs":["Synthèse","Comptes","Journaux","Recherche","Éditions","Saisies","Déclarations","Outils","Suivi","Plan comptable","Paramétrage"]},
 {"id":"treasury","label":"Trésorerie","icon":"wallet","ready":False,"tabs":["Synthèse","Échéancier","Caisse","Remises de chèques","Emprunts"]},
 {"id":"banking","label":"Banques & rapprochement","icon":"bank","ready":False,"tabs":["Relevés bancaires","Rapprochement","Saisie des relevés","Import"]},
 {"id":"tax","label":"Fiscalité","icon":"scale","ready":False,"tabs":["Synthèse","Obligations","Préparations","Contrôles","Historique"]},
 {"id":"review","label":"Révision","icon":"shield","ready":False,"tabs":["Synthèse","Anomalies","Révision"]},
 {"id":"reporting","label":"Tableaux de bord","icon":"dashboard","ready":False,"tabs":["Synthèse","Graphiques standards","Graphiques personnels","Tableaux synchronisés"]},
 {"id":"documents","label":"Documents","icon":"folder","ready":True,"tabs":[]},
 {"id":"requests","label":"Échanges client","icon":"mail","ready":True,"tabs":[]},
 {"id":"settings","label":"Paramètres du dossier","icon":"settings","ready":True,"tabs":[]},
]
