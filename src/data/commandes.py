import csv
from typing import List, Tuple, Dict
from pathlib import Path

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
