
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
    hangar._ajouter_point('BB', 14)
    hangar._ajouter_point('B', 10)
    
    # 3. Maintenant récupérer les coordonnées
    x_BB14, y_BB14 = hangar.points[('BB', 14)]
    x_B10, y_B10 = hangar.points[('B', 10)]
    
    print(f"\n📐 COORDONNÉES :")
    print(f"BB14: ({x_BB14:.1f}, {y_BB14:.1f})")
    print(f"B10: ({x_B10:.1f}, {y_B10:.1f})")
    print(f"Différence y: {abs(y_BB14 - y_B10):.1f}m")
    
    # 4. Tester la distance (maintenant ça marche)
    d1 = hangar.distance(('BB', 14), ('B', 10))
    d2 = hangar.distance(('B', 10), ('BB', 14))

    #AUTRES TEST:
    # Après avoir créé le hangar et placé la commande :
    print("\n🔍 TEST distance_special()")
    d_special = hangar.distance_special(('BB', 14), ('B', 10))
    d_normal = hangar.distance(('BB', 14), ('B', 10))
    print(f"  distance_special(BB14, B10) = {d_special}")
    print(f"  distance(BB14, B10) = {d_normal}")
    print(f"  Sont-ils égaux ? {d_special == d_normal}")
    
    print(f"\n📏 DISTANCES :")
    print(f"BB14 → B10 = {d1}")
    print(f"B10 → BB14 = {d2}")
    
    # 5. Vérifier accessibilité verticale
    print(f"\n🔍 ACCESSIBILITÉ VERTICALE :")
    
    # Utiliser la méthode interne
    access_BB14_to_B10 = hangar._accessible_verticalement(y_BB14, y_B10, 'BB')
    access_B10_to_BB14 = hangar._accessible_verticalement(y_B10, y_BB14, 'B')
    
    print(f"BB14 → B10 (descente): {'✓ AUTORISÉ' if access_BB14_to_B10 else '✗ INTERDIT'}")
    print(f"B10 → BB14 (montée): {'✓ AUTORISÉ' if access_B10_to_BB14 else '✗ INTERDIT'}")
    
    # 6. Vérifier les sens
    print(f"\n⚙️  CONFIGURATION :")
    print(f"Sens de 'B': {hangar.sens.get('B')} (1=montée, -1=descente)")
    print(f"Sens de 'BB': {hangar.sens.get('BB')}")
    
    # 7. Vérifier si même allée de base
    print(f"\n🔧 MÊME ALLÉE DE BASE ?")
    allee_base_BB = hangar.get_allee_base('BB') if hasattr(hangar, 'get_allee_base') else '?'
    print(f"Base de 'BB': {allee_base_BB}")
    print(f"Base de 'B': B")

if __name__ == "__main__":
    test_geometrie()