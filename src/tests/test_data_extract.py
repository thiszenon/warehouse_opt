from src.data.extract_data import *
from src.data.commandes import create_commandes, sauvegarder_commandes
import csv


def main():
    """tester l'extraction des données """
    path = "src/data/Extracted_text.txt"

    if len(path) > 0:
        try:
            points = load_commande(path)
            commandes = create_commandes(points,size=10)

            sauvegarder_commandes(commandes,"src/data/commandes_10points.csv")
            
            print(f"nombres des points : {len(commandes)} generéé")

        except Exception as ex:
            print(f"probleme: -> {ex}")


if __name__ =="__main__":
    main()
