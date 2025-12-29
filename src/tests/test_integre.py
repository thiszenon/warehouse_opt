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

def main():
    # 1. Créer le hangar (VOTRE CODE)
    hangar = Hangar(Longueur=90, largeur_allee=5, r=2)
    
    # 2. Définir une commande
    commande = [
        ('A', 1),
        ('A', 8),
        ('B', 47),
        ('C', 3),
        ('H', 24)
    ]
    hangar.placer_commande(commande=commande)
    
    # 3. Créer le graphe
    print("Construction du graphe...")
    graphe = GraphCollect(hangar, commande)
    
    # 4. Afficher les infos
    graphe.afficher_infos()
    
    # 5. Visualiser
    print("\nVisualisation...")
    graphe.visualiser()

if __name__ == "__main__":
    main()