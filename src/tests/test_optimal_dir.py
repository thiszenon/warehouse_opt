
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from geometry.hangar import Hangar
from geometry.hangar_with_depot import HangarWithDepot
from algorithms.solver.optimal_directional import OptimalDirectionalSolver
def test_geometrie():
    """Test spécifique pour BB14 et B10"""
    print("="*60)
    print("TEST GÉOMÉTRIE BB14 vs B10")
    print("="*60)
    
    # 1. Créer un hangar simple
    hangar = HangarWithDepot(Longueur=100, largeur_allee=5, r=2)
    
    # 2. AJOUTER LES POINTS D'ABORD (correction)
    hangar._ajouter_point('C', 29)
    hangar._ajouter_point('B', 10)
    
    # 3. Maintenant récupérer les coordonnées
    x_C29, y_C29 = hangar.points[('C', 29)]
    x_B10, y_B10 = hangar.points[('B', 10)]
    
    print(f"\n📐 COORDONNÉES :")
    print(f"C29: ({x_C29:.1f}, {y_C29:.1f})")
    print(f"B10: ({x_B10:.1f}, {y_B10:.1f})")
    print(f"Différence y: {abs(y_C29 - y_B10):.1f}m")
    
    # 4. Tester la distance (maintenant ça marche)
    d1 = hangar.distance(('C', 29), ('B', 10))
    d2 = hangar.distance(('B', 10), ('C', 29))

    #AUTRES TEST:
    # Après avoir créé le hangar et placé la commande :
    #print("\n🔍 TEST distance_special()")
    #d_special = hangar.distance_special(('C', 29), ('B', 10))
    d_normal = hangar.distance(('C', 29), ('B', 10))
    #print(f"  distance_special(C29, B10) = {d_special}")
    print(f"  distance(C29, B10) = {d_normal}")
    #print(f"  Sont-ils égaux ? {d_special == d_normal}")
    
    print(f"\n📏 DISTANCES :")
    print(f"C29 → B10 = {d1}")
    print(f"B10 → C29 = {d2}")

    
    print("\nTest manuel B10 → BB14")
    dist_n1 = abs(0-41) + hangar.distance_centres_allees('B','BB') + abs(87-0)  # 41 + 5 + 87 = 133
    dist_n2 = abs(50-41) + hangar.distance_centres_allees('B','BB') + abs(87-50)  # 9 + 5 + 37 = 51
    dist_n3 = abs(100-41) + hangar.distance_centres_allees('B','BB') + abs(87-100)  # 59 + 5 + 13 = 77

    print(f"\nB10→BB14: N1={dist_n1}, N2={dist_n2}, N3={dist_n3}")
        

if __name__ == "__main__":
    test_geometrie()