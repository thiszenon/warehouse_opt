import csv
from typing import List, Tuple, Dict
from pathlib import Path
import pandas as pd


def create_commandes(points: List[Tuple[str,int]], size:int) -> Dict[int, List[Tuple[str,int]]]:
    """
    Cette methode organise des commandes distinctes à partir d'une liste de points.
    """
    commandes = {}
    commande_id = 1
    for i in range(0,len(points), size):
        commandes[commande_id] = points[i:i + size]
        commande_id +=1
    return commandes

def sauvegarder_commandes(commandes, file_name_to_save):
    file_name_to_save = Path(file_name_to_save)

    with file_name_to_save.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["commande_id", "allee", "position"])

        for cid, points in commandes.items():
            for allee, pos in points:
                writer.writerow([cid,allee,pos])

def get_commandes(csv_file="src/data/commandes_10points.csv",command_id=2, n_points=13):
    """Recupère n points d'une commande"""
    dataF = pd.read_csv(csv_file)
    command_df=dataF[dataF['commande_id']== command_id].head(n_points)
    return list(zip(command_df['allee'],dataF['position']))
