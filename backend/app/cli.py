"""Explicit bootstrap: never seeds a default password or real customer data."""
import argparse
import getpass
import os
from sqlalchemy import select
from .config import Settings
from .db import make_database
from .models import Cabinet, User, Source
from .catalog import SOURCES
from .security import password_hash, audit

def main():
    parser=argparse.ArgumentParser(description="Mizania administration locale")
    parser.add_argument("command",choices=["bootstrap","add-staff"])
    parser.add_argument("--name",required=True)
    parser.add_argument("--email",required=True)
    parser.add_argument("--cabinet",default="Mon cabinet")
    parser.add_argument("--cabinet-id")
    parser.add_argument("--knowledge-editor",action="store_true")
    args=parser.parse_args()
    password=os.getenv("MIZANIA_BOOTSTRAP_PASSWORD") or getpass.getpass("Mot de passe (14 caractères minimum) : ")
    if len(password)<14: raise SystemExit("Le mot de passe doit contenir au moins 14 caractères.")
    settings=Settings();settings.validate();_,factory=make_database(settings)
    with factory() as db:
        if db.scalar(select(User).where(User.email==args.email.lower())): raise SystemExit("Ce compte existe déjà. Aucun mot de passe n’a été modifié.")
        if args.command=="bootstrap":
            if db.scalar(select(Cabinet.id)): raise SystemExit("Le bootstrap est réservé à une base vide.")
            cabinet=Cabinet(name=args.cabinet);db.add(cabinet);db.flush()
        else:
            cabinet=db.get(Cabinet,args.cabinet_id)
            if not cabinet: raise SystemExit("Indiquez un --cabinet-id existant.")
        user=User(cabinet_id=cabinet.id,email=args.email.lower(),name=args.name,password_hash=password_hash(password),
                  kind="staff",cabinet_admin=args.command=="bootstrap",knowledge_editor=args.knowledge_editor)
        db.add(user);db.flush()
        for row in SOURCES:
            if not db.get(Source,row["id"]): db.add(Source(**row))
        audit(db,user,"user.provisioned",user.id);db.commit()
        print(f"Compte créé : {user.email} | Cabinet : {cabinet.id}. Aucun dossier n’est attribué implicitement.")
if __name__=="__main__": main()
