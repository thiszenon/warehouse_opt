# test_integre.py
"""
Test d'intégration de GraphCollect avec votre Hangar
"""
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from geometry.hangar import Hangar
from graph import GraphCollect

from src.data.commandes import get_commandes

def main():
    # 1. Créer le hangar 
    hangar = Hangar(Longueur=90, largeur_allee=5, r=2)
    
    # 2. Définir une commande
    commande =get_commandes()
    hangar.placer_commande(commande=commande)
    
    # 3. Créer le graphe
    print("Construction du graphe...")
    graphe = GraphCollect(hangar, commande)

    #version schématique du graphe
    graphe.visualiser_graphe_schematique()

    # Visualiser un chemin spécifique
    print("visualisation d'un chemin spécifique...")
    graphe.visualiser_chemin_sur_hangar(('DD',18), ('F',41))

    # visualiser tous les chemins sur le meme hangar
    print("\nVisualisation de tous les chemins...")
    #graphe.visualiser_tous_chemins_sur_hangar()

    #visualisation par paires
    print("\nVisualisation par paires...")
    #graphe.visualiser_chemins_par_paires()

    
    # 4. Afficher les infos
    graphe.afficher_infos()
    
    """# 5. Visualiser
    print("\nVisualisation...")
    graphe.visualiser()
    """
    #voir tous les chemins
    #graphe.visuliser_tous_chemins()

if __name__ == "__main__":
    main()