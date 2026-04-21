
"""
Ce module gére l'extraction des données et les converti au format csv attendu pour le traitement interne
(allee,position)
"""
import pandas as pd
import re
from pathlib import Path



def read_commande_txt(path:Path):
    if path is None:
        raise ValueError("Fichier attendu")
    
    commande = []
    pattern = re.compile(r'\b([A-Ha-h]{1,2})\s*[-:]?\s*(\d+)\b')

    with path.open(encoding='utf-8') as file:
        for line in file:
           matches =pattern.findall(line)
           for allee, n in matches:
               commande.append((allee.upper(), int(n)))
    return commande

#un fichier Excel
def read_commande_excel(path: Path):
    if path is None:
        raise ValueError("Fichier attendu")
    
    commande = []
    dataF=pd.read_excel(path)
    for _,row in dataF.iterrows():
        allee = str(row['allee']).strip().upper()
        n = int(row['position'])
        commande.append((allee,n))
    return commande

def excel_vers_csv(file_xlsx,file_csv):
    dataF = pd.read_excel(file_xlsx)
    dataF[['allee','position']].to_csv(file_csv, index=False)

def load_commande(file_path):
    """
    Charge un fichier et retourne les données au format commande interne
    """
    if file_path is None:
        raise ValueError("Fichier attendu")
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    
    if path.suffix == ".txt":
        return read_commande_txt(path)
    elif path.suffix in (".xlsx", ".xls"):
        return read_commande_excel(path)
    else:
        raise ValueError(f"Format non supporté: {path.suffix}")
