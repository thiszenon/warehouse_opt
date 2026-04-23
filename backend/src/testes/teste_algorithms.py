
# test_integre.py
"""
Test d'intégration complet avec les algorithmes de benchmark
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from backend.src.geometry.hangar_with_depot import HangarWithDepot
from backend.src.graph.graph_collect_depot import GraphCollectWithDepot
from backend.src.algorithms import (
    NearestNeighborSolver,
    InsertionSolver,
    TwoOptSolver,
    StructuralInsertionSolver,
    SShapeSolver,
    UShapeSolver,
    RobustSShapeSolver,
    RobustUShapeSolver,
    AlleyFirstSolver,
    RobustAlleySolver,
    DynamicStructureSolver
)
from backend.src.algorithms.solver.opt_parcours import OptParcoursSolver
from backend.src.algorithms.solver.optimal_directional import OptimalDirectionalSolver
from backend.src.data.commandes import get_commandes

def test_avec_depot_fixe():
    """Test avec un dépôt fixe et arrivée identique"""
    print("=" * 70)
    print("🚀 TEST AVEC DÉPÔT FIXE (Dépôt = Arrivée)")
    print("=" * 70)
    
    # 1. Créer le hangar avec dépôt
    hangar = HangarWithDepot(
        Longueur=90, 
        largeur_allee=5, 
        r=2,
        depot_position=(14, -10),  # Devant le hangar à gauche
        arrival_position=None      # Même que dépôt
    )
    #Les points DEPART/ARRIVE
    depot=hangar.depot_position
    
    # 2. Définir une commande réelle
    commande = get_commandes()
    print(f"\n Commande à collecter ({len(commande)} points):")
    for i, (allee, n) in enumerate(commande):
        print(f"   {i+1}. {allee}{n}")

    #3. Placer les points dans le hangar
    print("placement des points dans le hangar...")
    hangar.placer_commande(commande)

    
    # 4. Créer le graphe avec dépôt
    print("\n🔧 Construction du graphe avec dépôt...")
    graphe = GraphCollectWithDepot(hangar, commande)
    
    # 5. Afficher les infos
    graphe.afficher_infos()

    
    
    # 6. Tester les algorithmes de benchmark
    print("\n🎯 TEST DES ALGORITHMES DE BENCHMARK")
    print("-" * 50)
    
    solvers = [
        NearestNeighborSolver(start_at_nearest=True),
        #InsertionSolver(seed=42, insertion_strategy='cheapest'),
        #InsertionSolver(seed=42, insertion_strategy='farthest'),
        #TwoOptSolver(),
        #StructuralInsertionSolver(hangar=hangar,commande=commande,points_complets=graphe.points_complets,use_structure=True),
        #SShapeSolver(hangar=hangar,commande=commande,points_complets=graphe.points_complets,start_from='left',transition_level='optimal'),
        #UShapeSolver(hangar=hangar,commande=commande,points_complets=graphe.points_complets,strategy='alternating',return_level='optimal'),
        #RobustUShapeSolver(hangar=hangar,commande=commande, points_complets=graphe.points_complets,fallback_to_simple=False),
        #RobustSShapeSolver(hangar=hangar,commande=commande,points_complets=graphe.points_complets,fallback_to_simple=False),
        #AlleyFirstSolver(hangar=hangar,points_complets=graphe.points_complets),
        #RobustAlleySolver(hangar=hangar,points_complets=graphe.points_complets,consolidation_enabled=True),
        #DynamicStructureSolver(hangar=hangar,points_complets=graphe.points_complets),
        #OptParcoursSolver(hangar=hangar,points_complets=graphe.points_complets),
        OptimalDirectionalSolver(hangar=hangar)


    ]
    
    best_solution = None
    best_distance = float('inf')
    
    for solver in solvers:
        print(f"\n Testing {solver.name}...")
        
        try:
            # Résoudre
            result = solver.solve(
                graphe.matrice,
                depot_idx=graphe.depot_idx,
                arrival_idx=graphe.arrival_idx
            )
            
            if result:
                print(f"    Solution trouvée!")
                print(f"    Distance: {result['distance']:.1f}m")
                print(f"     Temps: {result['time']:.4f}s")
                print(f"     Tour: ", end="")
                
                # Afficher le tour de manière lisible
                tour_points = []
                for idx in result['tour']:
                    if idx == graphe.depot_idx:
                        tour_points.append("DÉPÔT")
                    elif idx == graphe.arrival_idx:
                        tour_points.append("ARRIVÉE")
                    else:
                        point_idx = idx - 1  # Ajuster pour les points réels
                        if 0 <= point_idx < len(commande):
                            allee, n = commande[point_idx]
                            tour_points.append(f"{allee}{n}")
                        else:
                            tour_points.append(f"Point{idx}")
                
                print(" → ".join(tour_points))
                
                # Garder la meilleure solution
                if result['distance'] < best_distance:
                    best_distance = result['distance']
                    best_solution = result
                    best_solver = solver.name
            else:
                print(f"   ❌ Aucune solution trouvée")
                
        except Exception as e:
            print(f"   ⚠️  Erreur: {e}")
    #afficher le chemin
    
    
    # 7. Afficher la meilleure solution
    if best_solution:
        print("\n" + "=" * 70)
        print("🏆 MEILLEURE SOLUTION TROUVÉE")
        print("=" * 70)
        print(f"Algorithme: {best_solver}")
        print(f"Distance totale: {best_distance:.1f}m")
        print(f"Temps d'exécution: {best_solution['time']:.4f}s")
        visualiser_chemins_parcours(hangar,commande=commande,solution=best_solution,graphe=graphe)
        
        
        # Calculer la distance si on faisait naïvement
        print(f"\n📊 Comparaison avec approche naïve:")
        
        # Approche naïve: ordre d'apparition dans la commande
        naive_tour = [graphe.depot_idx] + list(range(1, len(commande)+1)) + [graphe.arrival_idx]
        naive_distance = 0
        for i in range(len(naive_tour)-1):
            naive_distance += graphe.matrice[naive_tour[i], naive_tour[i+1]]
        
        print(f"   Distance naïve (ordre commande): {naive_distance:.1f}m")
        print(f"   Gain avec optimisation: {naive_distance - best_distance:.1f}m ({((naive_distance - best_distance)/naive_distance*100):.1f}%)")
    
    # 7. Visualiser la meilleure solution sur le hangar
    if best_solution:
        print("\n🎨 Visualisation du meilleur parcours...")
        visualiser_parcours_optimal(hangar, commande, best_solution, graphe)
    
    return best_solution

def test_avec_depot_arrivee_differents(algorithm_type='farthest', display_plot=True):
    """
    Test avec dépôt et arrivée différents - version simplifiée pour tester un algorithme
    
    Args:
        algorithm_type: 'nearest', 'cheapest', 'farthest', 'two_opt'
        display_plot: True pour afficher les visualisations
    """
    print("\n" + "=" * 70)
    print(f"🚀 TEST AVEC DÉPÔT ≠ ARRIVÉE - Algorithme: {algorithm_type}")
    print("=" * 70)
    
    # 1. Créer le hangar avec dépôt et arrivée différents
    hangar = HangarWithDepot(
        Longueur=90, 
        largeur_allee=5, 
        r=2,
        depot_position=(25, -5),   # Devant à droite
        arrival_position=(15, -5)  # Devant à gauche
    )
    
    # 2. Définir une commande réelle
    commande = get_commandes()
    print(f"\n📦 Commande à collecter ({len(commande)} points):")
    for i, (allee, n) in enumerate(commande):
        print(f"   {i+1}. {allee}{n}")
    
    # Placer les points dans le hangar
    hangar.placer_commande(commande)
    
    # 3. Créer le graphe
    print("\n🔧 Construction du graphe...")
    graphe = GraphCollectWithDepot(hangar, commande)

    # Dans test_avec_depot_arrivee_differents(), APRÈS avoir créé graphe :

    """ 
    print("\n🔍 DEBUG MATRICE COMPLÈTE POUR OPTIMAL_DIR")

    # Trouver les indices de BB14 et B10 dans la matrice
    points = graphe.points_complets
    for i, pt in enumerate(points):
        if pt == ('BB', 14):
            idx_BB14 = i
        if pt == ('B', 10):
            idx_B10 = i

    print(f"Indices dans la matrice: BB14={idx_BB14}, B10={idx_B10}")

    print(f"\nValeurs dans la matrice:")
    print(f"  BB14→B10 = {graphe.matrice[idx_BB14][idx_B10]}")
    print(f"  B10→BB14 = {graphe.matrice[idx_B10][idx_BB14]}")

    print(f"\nTest direct avec hangar.distance_special():")
    d1 = hangar.distance_special(('BB', 14), ('B', 10))
    d2 = hangar.distance_special(('B', 10), ('BB', 14))
    print(f"  distance_special(BB14, B10) = {d1}")
    print(f"  distance_special(B10, BB14) = {d2}")

    print(f"\nVérification de tous les arcs depuis/vers BB14:")
    for j, pt in enumerate(points):
        if j != idx_BB14:
            dist = graphe.matrice[idx_BB14][j]
            if dist == float('inf'):
                print(f"  BB14 → {pt} = inf (PROBLÈME!)")
            else:
                print(f"  BB14 → {pt} = {dist:.1f}")

    print(f"\nVérification de tous les arcs depuis/vers B10:")
    for j, pt in enumerate(points):
        if j != idx_B10:
            dist = graphe.matrice[idx_B10][j]
            if dist == float('inf'):
                print(f"  B10 → {pt} = inf (PROBLÈME!)")
            else:
                print(f"  B10 → {pt} = {dist:.1f}")
    """
    # 4. Vérifier que le point dépôt ≠ arrivée
    if hangar.depot_position == hangar.arrival_position:
        print("⚠️ Attention: dépôt et arrivée sont identiques!")
    else:
        print("✅ Dépôt et arrivée sont différents")
    
    print(f"📍 Dépôt position: {hangar.depot_position}")
    print(f"📍 Arrivée position: {hangar.arrival_position}")
    
    # 5. Afficher les informations du graphe
    graphe.afficher_infos()
    
    # 6. Initialiser l'algorithme choisi
    print(f"\n🎯 CONFIGURATION DE L'ALGORITHME: {algorithm_type.upper()}")
    
    if algorithm_type == 'nearest':
        solver = NearestNeighborSolver(start_at_nearest=True)
        print("   - Plus proche voisin")
        print("   - Commence au point le plus proche du dépôt")
        
    elif algorithm_type == 'cheapest':
        solver = InsertionSolver(seed=42, insertion_strategy='cheapest')
        print("   - Insertion la moins chère")
        print("   - Insère les points là où ça coûte le moins")
        
    elif algorithm_type == 'farthest':
        solver = InsertionSolver(seed=42, insertion_strategy='farthest')
        print("   - Insertion la plus éloignée")
        print("   - Commence par les points les plus éloignés")
        
    elif algorithm_type == 'two_opt':
        solver = TwoOptSolver()
        print("   - 2-opt amélioration")
        print("   - Améliore une solution existante")
    elif algorithm_type == 'structural_insertion':
        solver = StructuralInsertionSolver(
            hangar=hangar,
            commande=commande,
            points_complets=graphe.points_complets,
            use_structure=True
        )
        print(" - structural insertion")
    elif algorithm_type == 's_shape':
        solver = SShapeSolver(
            hangar=hangar,
            commande=commande,
            points_complets=graphe.points_complets,
            start_from='left',
            transition_level='optimal'
        )
        print("- s_shape heuristique")
    elif algorithm_type =='u_shape':
        solver = UShapeSolver(
            hangar=hangar,
            commande=commande,
            points_complets= graphe.points_complets,
            strategy='alternating'
        )
        print("- u_shape heuristique")
    elif algorithm_type =='rob_s_shape':
        solver =RobustSShapeSolver(
            hangar=hangar,
            commande=commande,
            points_complets=graphe.points_complets,
            fallback_to_simple=False
        )
        print("- rob S_Shape")
    elif algorithm_type == 'rob_u_shape':
        solver = RobustUShapeSolver(
            hangar=hangar,
            commande=commande,
            points_complets=graphe.points_complets,
            fallback_to_simple=False
        )
        print("- rob U_Shape")
    elif algorithm_type == 'first_solver':
        solver = AlleyFirstSolver(
            hangar=hangar,
            points_complets=graphe.points_complets
        )
        print("- first Solver")
    elif algorithm_type == 'robust_solver':
        solver = RobustAlleySolver(
            hangar=hangar,
            points_complets=graphe.points_complets,
            consolidation_enabled=False
        )
        print("- robust solver")
    elif algorithm_type == 'dynamic_solver':
        solver = DynamicStructureSolver(
            hangar=hangar,
            points_complets= graphe.points_complets
        )
    elif algorithm_type == 'opt_parcours':
        solver = OptParcoursSolver(
            hangar=hangar,
            points_complets=graphe.points_complets
        )
        print("- opt_parcours ")
    elif algorithm_type =='optimal_dir':

        solver = OptimalDirectionalSolver(hangar=hangar)
        solution = solver.solve(
            distance_matrix=graphe.matrice,
            depot_idx=graphe.depot_idx,
            arrival_idx=graphe.arrival_idx
        )

        

    else:
        raise ValueError(f"Algorithme inconnu: {algorithm_type}")
    
    # 7. Résoudre avec l'algorithme choisi
    print(f"\n⚙️  RÉSOLUTION EN COURS...")
    
    try:
        result = solver.solve(
            graphe.matrice,
            depot_idx=graphe.depot_idx,
            arrival_idx=graphe.arrival_idx
        )
        
        if result:
            print(f"✅ SOLUTION TROUVÉE!")
            print(f"📏 Distance totale: {result['distance']:.1f}m")
            print(f"⏱️  Temps de calcul: {result['time']:.4f}s")
            
            # Afficher le parcours détaillé
            print(f"\n🛣️  PARCOURS DÉTAILLÉ:")
            for i, idx in enumerate(result['tour']):
                if idx == graphe.depot_idx:
                    nom = "DÉPÔT"
                elif idx == graphe.arrival_idx:
                    nom = "ARRIVÉE"
                else:
                    point_idx = idx - 1
                    if 0 <= point_idx < len(commande):
                        allee, n = commande[point_idx]
                        nom = f"{allee}{n}"
                    else:
                        nom = f"Point {idx}"
                
                print(f"   {i+1}. {nom}")
            
            # Calculer les distances segment par segment
            print(f"\n📊 DÉTAIL DES SEGMENTS:")
            total_distance = 0
            for i in range(len(result['tour']) - 1):
                idx_from = result['tour'][i]
                idx_to = result['tour'][i+1]
                distance = graphe.matrice[idx_from, idx_to]
                total_distance += distance
                
                # Noms des points
                if idx_from == graphe.depot_idx:
                    nom_from = "DÉPÔT"
                elif idx_from == graphe.arrival_idx:
                    nom_from = "ARRIVÉE"
                else:
                    point_idx = idx_from - 1
                    if 0 <= point_idx < len(commande):
                        allee, n = commande[point_idx]
                        nom_from = f"{allee}{n}"
                    else:
                        nom_from = f"Point {idx_from}"
                
                if idx_to == graphe.depot_idx:
                    nom_to = "DÉPÔT"
                elif idx_to == graphe.arrival_idx:
                    nom_to = "ARRIVÉE"
                else:
                    point_idx = idx_to - 1
                    if 0 <= point_idx < len(commande):
                        allee, n = commande[point_idx]
                        nom_to = f"{allee}{n}"
                    else:
                        nom_to = f"Point {idx_to}"
                
                print(f"   Segment {i+1}: {nom_from} → {nom_to} ({distance:.1f}m)")
            
            # Vérifier la cohérence
            if abs(total_distance - result['distance']) > 0.1:
                print(f"⚠️  Attention: différence entre somme des segments ({total_distance:.1f}m) et distance totale ({result['distance']:.1f}m)")
            
            # 8. Visualiser le résultat si demandé
            if display_plot:
                print(f"\n🎨 GÉNÉRATION DES VISUALISATIONS...")
                visualiser_chemins_parcours(hangar, commande, result, graphe)
            
            return {
                'hangar': hangar,
                'commande': commande,
                'graphe': graphe,
                'solution': result,
                'solver': solver
            }
            
        else:
            print(f"❌ AUCUNE SOLUTION TROUVÉE")
            return None
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None


# Fonction pour tester tous les algorithmes successivement
def comparer_tous_algorithmes():
    """Teste tous les algorithmes successivement et compare les résultats"""
    print("\n" + "=" * 70)
    print("📊 COMPARAISON DE TOUS LES ALGORITHMES")
    print("=" * 70)
    
    algorithms = ['nearest', 'cheapest', 'farthest', 'two_opt']
    results = []
    
    for algo in algorithms:
        print(f"\n▶️  TEST DE L'ALGORITHME: {algo.upper()}")
        result = test_avec_depot_arrivee_differents(
            algorithm_type=algo,
            display_plot=False  # Pas de visualisation pour la comparaison
        )
        
        if result and 'solution' in result:
            results.append({
                'algorithm': algo,
                'distance': result['solution']['distance'],
                'time': result['solution']['time'],
                'solution': result
            })
    
    # Afficher le tableau comparatif
    if results:
        print("\n" + "=" * 70)
        print("📈 RÉSULTATS COMPARATIFS")
        print("=" * 70)
        
        # Trouver la meilleure distance
        best_distance = min(r['distance'] for r in results)
        
        print(f"\n{'Algorithme':<15} {'Distance (m)':<15} {'Temps (s)':<12} {'Performance':<10}")
        print("-" * 52)
        
        for r in results:
            performance = f"{((best_distance / r['distance']) * 100):.1f}%" if r['distance'] > 0 else "N/A"
            diff_percent = f"+{((r['distance'] - best_distance) / best_distance * 100):.1f}%" if r['distance'] > best_distance else "MEILLEUR"
            
            print(f"{r['algorithm']:<15} {r['distance']:<15.1f} {r['time']:<12.4f} {diff_percent:<10}")
        
        # Afficher le meilleur résultat
        print(f"\n🏆 MEILLEUR ALGORITHME: {min(results, key=lambda x: x['distance'])['algorithm']}")
        
        # Demander si on veut visualiser le meilleur
        best_algo = min(results, key=lambda x: x['distance'])['algorithm']
        response = input(f"\nVoulez-vous visualiser le résultat du meilleur algorithme ({best_algo}) ? (o/n): ")
        if response.lower() == 'o':
            test_avec_depot_arrivee_differents(
                algorithm_type=best_algo,
                display_plot=True
            )
    
    return results




def visualiser_parcours_optimal(hangar, commande, solution, graphe):
    """Visualise le parcours optimal sur le hangar"""
    import matplotlib.pyplot as plt
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 1. Hangar avec tous les points et le parcours
    hangar.dessiner_avec_depot(commande, "Parcours optimal de collecte", ax=ax1)
    
    # Tracer le parcours
    tour = solution['tour']
    points_complets = graphe.points_complets  # [dépôt] + commande + [arrivée]
    
    for i in range(len(tour) - 1):
        idx_from = tour[i]
        idx_to = tour[i+1]
        
        if 0 <= idx_from < len(points_complets) and 0 <= idx_to < len(points_complets):
            # Obtenir les coordonnées réelles
            point_from = points_complets[idx_from]
            point_to = points_complets[idx_to]
            
            x1, y1 = hangar.points.get(point_from, point_from if isinstance(point_from, tuple) and len(point_from) == 2 else (0, 0))
            x2, y2 = hangar.points.get(point_to, point_to if isinstance(point_to, tuple) and len(point_to) == 2 else (0, 0))
            
            # Tracer la ligne
            ax1.plot([x1, x2], [y1, y2], 'r-', linewidth=2, alpha=0.7, 
                    marker='o', markersize=6, markerfacecolor='red')
    
    # 2. Graphique du graphe orienté
    graphe._dessiner_graphe_oriented(ax2)
    
    # Mettre en évidence le parcours optimal dans le graphe
    for i in range(len(tour) - 1):
        idx_from = tour[i]
        idx_to = tour[i+1]
        
        if idx_from < len(points_complets) and idx_to < len(points_complets):
            # Dessiner l'arc en surbrillance
            x_from = graphe.graph_nx.nodes[idx_from]['x'] if idx_from in graphe.graph_nx.nodes else 0
            y_from = graphe.graph_nx.nodes[idx_from]['y'] if idx_from in graphe.graph_nx.nodes else 0
            x_to = graphe.graph_nx.nodes[idx_to]['x'] if idx_to in graphe.graph_nx.nodes else 0
            y_to = graphe.graph_nx.nodes[idx_to]['y'] if idx_to in graphe.graph_nx.nodes else 0
            
            ax2.plot([x_from, x_to], [y_from, y_to], 'r-', linewidth=3, alpha=0.9)
    
    plt.suptitle(f"Parcours optimal - {solution['distance']:.1f}m - {len(commande)} points", 
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.show()

def analyser_resultats_detaille(hangar, commande, solution, graphe):
    """Analyse détaillée des résultats"""
    print("\n" + "=" * 70)
    print("🔍 ANALYSE DÉTAILLÉE DU PARCOURS")
    print("=" * 70)
    
    if not solution:
        print("Aucune solution à analyser")
        return
    
    tour = solution['tour']
    points_complets = graphe.points_complets
    
    print(f"\n📊 ÉTAPES DU PARCOURS ({len(tour)-1} segments):")
    print("-" * 60)
    
    total_distance = 0
    segment_details = []
    
    for i in range(len(tour) - 1):
        idx_from = tour[i]
        idx_to = tour[i+1]
        
        point_from = points_complets[idx_from]
        point_to = points_complets[idx_to]
        
        # Nom des points
        if point_from == hangar.depot_label:
            nom_from = "DÉPÔT"
        elif point_from == hangar.arrival_label:
            nom_from = "ARRIVÉE"
        else:
            allee, n = point_from
            nom_from = f"{allee}{n}"
        
        if point_to == hangar.depot_label:
            nom_to = "DÉPÔT"
        elif point_to == hangar.arrival_label:
            nom_to = "ARRIVÉE"
        else:
            allee, n = point_to
            nom_to = f"{allee}{n}"
        
        # Distance
        distance = graphe.matrice[idx_from, idx_to]
        total_distance += distance
        
        # Type de mouvement
        if point_from == hangar.depot_label or point_to == hangar.depot_label or \
        point_from == hangar.arrival_label or point_to == hangar.arrival_label:
            mouvement = "Entrée/Sortie hangar"
        elif point_from[0] == point_to[0]:  # Même allée
            mouvement = f"Déplacement vertical (allée {point_from[0]})"
        else:
            mouvement = f"Changement d'allée ({point_from[0]} → {point_to[0]})"
        
        segment_details.append({
            'étape': i+1,
            'de': nom_from,
            'à': nom_to,
            'distance': distance,
            'mouvement': mouvement
        })
    
    # Afficher le tableau
    print(f"{'Étape':<6} {'De':<10} {'À':<10} {'Distance':<10} {'Type':<30}")
    print("-" * 66)
    for detail in segment_details:
        print(f"{detail['étape']:<6} {detail['de']:<10} {detail['à']:<10} "
            f"{detail['distance']:<10.1f} {detail['mouvement']:<30}")
    
    print("-" * 66)
    print(f"{'TOTAL':<26} {total_distance:<10.1f} m")
    
    # Statistiques
    print(f"\n📈 STATISTIQUES:")
    print(f"   • Nombre de points collectés: {len(commande)}")
    print(f"   • Nombre total d'étapes: {len(segment_details)}")
    print(f"   • Distance moyenne par étape: {total_distance/len(segment_details):.1f} m")
    
    # Analyse des types de mouvements
    changements_allee = sum(1 for d in segment_details if "Changement" in d['mouvement'])
    deplacements_verticaux = sum(1 for d in segment_details if "vertical" in d['mouvement'].lower())
    
    print(f"   • Changements d'allée: {changements_allee}")
    print(f"   • Déplacements verticaux: {deplacements_verticaux}")
    print(f"   • Entrées/sorties: {len(segment_details) - changements_allee - deplacements_verticaux}")


def visualiser_chemin_sur_hangar_depot(self, point_depart, point_arrivee):
        """
        Version adaptée pour GraphCollectWithDepot
        
        Affiche 2 figures séparées :
        1. Le hangar avec le chemin tracé (inclut dépôt/arrivée si besoin)
        2. Le graphe orienté complet
        """
        # FIGURE 1 : Hangar avec chemin
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        
        # Titre adapté
        if point_depart == self.hangar.depot_label:
            nom_depart = "DÉPÔT"
        elif point_depart == self.hangar.arrival_label:
            nom_depart = "ARRIVÉE"
        else:
            nom_depart = f"{point_depart[0]}{point_depart[1]}"
        
        if point_arrivee == self.hangar.depot_label:
            nom_arrivee = "DÉPÔT"
        elif point_arrivee == self.hangar.arrival_label:
            nom_arrivee = "ARRIVÉE"
        else:
            nom_arrivee = f"{point_arrivee[0]}{point_arrivee[1]}"
        
        # Dessiner le hangar
        self.hangar.dessiner_avec_depot(
            self.commande_reelle, 
            f"Chemin: {nom_depart} → {nom_arrivee}", 
            ax=ax1
        )
        
        # Tracer le chemin spécifique
        resultat = self.hangar.tracer_chemin_special(point_depart, point_arrivee, 
                                                    ax=ax1, couleur='red', 
                                                    style='-', alpha=0.8, linewidth=3)
        
        # Mettre en évidence les points
        for point, couleur, label in [(point_depart, 'green', 'Départ'),
                                    (point_arrivee, 'orange', 'Arrivée')]:
            # Déterminer les coordonnées
            if point == self.hangar.depot_label:
                x, y = self.hangar.depot_position
                nom_point = "DÉPÔT"
            elif point == self.hangar.arrival_label:
                x, y = self.hangar.arrival_position
                nom_point = "ARRIVÉE"
            else:
                x, y = self.hangar.points.get(point, (0, 0))
                nom_point = f"{point[0]}{point[1]}"
            
            # Tracer le point
            ax1.plot(x, y, 'o', markersize=15, color=couleur,
                    markeredgecolor='black', markeredgewidth=2, zorder=20)
            ax1.text(x, y + 3, f"{label}\n{nom_point}", 
                    ha='center', va='bottom', fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
            # FIGURE 2 : Graphe orienté complet
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            self._dessiner_graphe_oriented(ax2)
            
            # Trouver les indices dans le graphe complet
            i = -1
            j = -1
            
            for idx, node_data in self.graph_nx.nodes(data=True):
                if node_data['point'] == point_depart:
                    i = idx
                if node_data['point'] == point_arrivee:
                    j = idx
            
            # Mettre en évidence l'arc dans le graphe
            if i != -1 and j != -1:
                # Dessiner l'arc correspondant en surbrillance
                pos = {idx: (self.graph_nx.nodes[idx]['x'], 
                            self.graph_nx.nodes[idx]['y']) 
                    for idx in range(self.n_total)}
                
                if self.matrice[i][j] < float('inf'):
                    nx.draw_networkx_edges(
                        self.graph_nx, pos,
                        edgelist=[(i, j)],
                        ax=ax2,
                        arrowstyle='->',
                        arrowsize=25,
                        edge_color='red',
                        width=3,
                        alpha=0.9
                    )
                    
                    # Ajouter le poids de l'arc
                    ax2.text((pos[i][0] + pos[j][0]) / 2,
                            (pos[i][1] + pos[j][1]) / 2,
                            f"{self.matrice[i][j]:.1f}m",
                            fontsize=10, fontweight='bold',
                            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
                else:
                    # Arc impossible
                    ax2.text(0.5, 0.5, f"ARC IMPOSSIBLE\n{nom_depart} → {nom_arrivee}",
                            ha='center', va='center', fontsize=14, color='red',
                            transform=ax2.transAxes,
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
            
            plt.tight_layout()
            plt.show()
            
            return resultat
    



def visualiser_chemins_parcours(hangar, commande, solution, graphe):
    """
    Affiche 2 figures séparées :
    1. Le hangar avec le chemin complet tracé
    2. Le graphe orienté avec le parcours complet ET l'ordre de visite clairement indiqué
    """
    import matplotlib.pyplot as plt
    
    if not solution:
        print("⚠️  Aucune solution à visualiser")
        return
    
    tour = solution['tour']
    points_complets = graphe.points_complets
    
    print(f"\n🎨 VISUALISATION DU PARCOURS COMPLET")
    print(f"   {len(tour)-1} segments, distance totale: {solution['distance']:.1f}m")
    
    # Identifier les points de départ et d'arrivée
    depart_idx = tour[0]
    arrivee_idx = tour[-1]
    depart_point = points_complets[depart_idx]
    arrivee_point = points_complets[arrivee_idx]
    
    # Noms pour l'affichage
    if depart_point == hangar.depot_label:
        nom_depart = "DÉPÔT"
    elif depart_point == hangar.arrival_label:
        nom_depart = "ARRIVÉE"
    else:
        allee, n = depart_point
        nom_depart = f"{allee}{n}"
    
    if arrivee_point == hangar.depot_label:
        nom_arrivee = "DÉPÔT"
    elif arrivee_point == hangar.arrival_label:
        nom_arrivee = "ARRIVÉE"
    else:
        allee, n = arrivee_point
        nom_arrivee = f"{allee}{n}"
    
    # ========== FIGURE 1 : Hangar avec chemin ==========
    fig1, ax1 = plt.subplots(figsize=(12, 10))
    
    # Dessiner le hangar avec le dépôt
    hangar.dessiner_avec_depot(commande, f"Chemin: {nom_depart} → {nom_arrivee}", ax=ax1)
    
    # Tracer tous les segments du parcours
    for i in range(len(tour) - 1):
        idx_from = tour[i]
        idx_to = tour[i+1]
        
        point_from = points_complets[idx_from]
        point_to = points_complets[idx_to]
        
        # Tracer le chemin avec la méthode spéciale
        hangar.tracer_chemin_special(point_from, point_to, 
                                    ax=ax1, couleur='red', 
                                    style='-', alpha=0.8, linewidth=3)
    
    # Mettre en évidence TOUS les points du parcours avec NUMÉROS d'ordre
    for idx_pos, idx in enumerate(tour):
        point = points_complets[idx]
        
        # Déterminer la couleur
        if idx == depart_idx:
            couleur = 'green'
            etiquette = "DÉPÔT"
        elif idx == arrivee_idx:
            couleur = 'orange'
            etiquette = "ARRIVÉE"
        else:
            couleur = 'blue'
            if isinstance(point, tuple):
                etiquette = f"{point[0]}{point[1]}"
            else:
                etiquette = str(point)
        
        # Coordonnées du point
        if point == hangar.depot_label:
            x, y = hangar.depot_position
        elif point == hangar.arrival_label:
            x, y = hangar.arrival_position
        else:
            x, y = hangar.points[point]
        
        # Taille différente pour départ/arrivée
        taille = 20 if couleur in ['green', 'orange'] else 15
        
        ax1.plot(x, y, 'o', markersize=taille, color=couleur,
                markeredgecolor='black', markeredgewidth=3, zorder=30)
        
        # Ajouter le NUMÉRO D'ORDRE en grand au centre du point
        ax1.text(x, y, str(idx_pos + 1), 
                ha='center', va='center', fontsize=11, fontweight='bold',
                color='white', zorder=31)
        
        # Annotation avec le nom du point
        offset_y = 7 if couleur in ['green', 'orange'] else 5
        ax1.text(x, y + offset_y, etiquette, 
                ha='center', va='bottom', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Légende
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', edgecolor='black', label='Départ (1)'),
        Patch(facecolor='orange', edgecolor='black', label=f'Arrivée ({len(tour)})'),
        Patch(facecolor='blue', edgecolor='black', label='Points de collecte'),
        Patch(facecolor='red', edgecolor='red', alpha=0.8, linewidth=3, label='Chemin parcouru')
    ]
    ax1.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.05, 1))
    
    # ========== FIGURE 2 : Graphe orienté avec ORDRE DE VISITE ==========
    fig2, ax2 = plt.subplots(figsize=(14, 10))
    
    # Dessiner le graphe de base
    graphe._dessiner_graphe_oriented(ax2)
    
    # Position des nœuds du graphe
    pos = {}
    for idx in range(graphe.n_total):
        if idx in graphe.graph_nx.nodes:
            pos[idx] = (graphe.graph_nx.nodes[idx]['x'], 
                       graphe.graph_nx.nodes[idx]['y'])
    
    # Tracer le parcours sur le graphe avec annotations d'ordre
    for i in range(len(tour) - 1):
        idx_from = tour[i]
        idx_to = tour[i+1]
        
        if idx_from in pos and idx_to in pos:
            # Ligne principale du segment
            ax2.plot([pos[idx_from][0], pos[idx_to][0]],
                    [pos[idx_from][1], pos[idx_to][1]],
                    'red', linewidth=5, alpha=0.9, zorder=10)
            
            # Flèche directionnelle
            ax2.arrow(pos[idx_from][0], pos[idx_from][1],
                     (pos[idx_to][0] - pos[idx_from][0]) * 0.8,
                     (pos[idx_to][1] - pos[idx_from][1]) * 0.8,
                     head_width=4, head_length=5, fc='red', ec='red',
                     alpha=0.9, zorder=11)
            
            # NUMÉRO DU SEGMENT au milieu
            mid_x = (pos[idx_from][0] + pos[idx_to][0]) / 2
            mid_y = (pos[idx_from][1] + pos[idx_to][1]) / 2
            
            # Cercle avec numéro du segment
            circle = plt.Circle((mid_x, mid_y), 8, color='yellow', alpha=0.9, zorder=12)
            ax2.add_patch(circle)
            
            # Numéro du segment (i+1 car les segments commencent à 1)
            ax2.text(mid_x, mid_y, str(i+1),
                    ha='center', va='center', fontsize=10, fontweight='bold',
                    zorder=13)
            
            # Distance du segment (plus petit en dessous)
            distance = graphe.matrice[idx_from, idx_to]
            ax2.text(mid_x, mid_y - 10, f"{distance:.0f}m",
                    ha='center', va='top', fontsize=8,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Marquer les nœuds du parcours avec NUMÉROS D'ORDRE DE VISITE
    for ordre, idx in enumerate(tour):
        if idx in pos:
            x, y = pos[idx]
            
            # Couleur selon le type de point
            point = points_complets[idx]
            if point == hangar.depot_label:
                couleur = 'green'
                etiquette = "DÉPÔT"
                taille_cercle = 30
                taille_texte = 12
            elif point == hangar.arrival_label:
                couleur = 'orange'
                etiquette = "ARRIVÉE"
                taille_cercle = 30
                taille_texte = 12
            else:
                couleur = 'blue'
                if isinstance(point, tuple):
                    etiquette = f"{point[0]}{point[1]}"
                else:
                    etiquette = str(point)
                taille_cercle = 25
                taille_texte = 10
            
            # Cercle extérieur plus grand
            cercle_exterieur = plt.Circle((x, y), taille_cercle/2, 
                                        color=couleur, alpha=0.9, zorder=20)
            ax2.add_patch(cercle_exterieur)
            
            # Cercle intérieur blanc pour le numéro
            cercle_interieur = plt.Circle((x, y), taille_cercle/3, 
                                        color='white', alpha=0.9, zorder=21)
            ax2.add_patch(cercle_interieur)
            
            # NUMÉRO D'ORDRE au centre (très visible)
            ax2.text(x, y, str(ordre + 1), 
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    color=couleur, zorder=22)
            
            # Nom du point en dessous
            ax2.text(x, y - taille_cercle/2 - 5, etiquette,
                    ha='center', va='top', fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
    
    # Titre du graphe avec séquence
    sequence = " → ".join([str(i+1) for i in range(len(tour))])
    ax2.set_title(f"PARCOURS COMPLET - Séquence: {sequence}", 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Légende détaillée à droite
    legend_text = "LÉGENDE:\n"
    legend_text += "• Cercles numérotés = ordre de visite\n"
    legend_text += "• Cercles jaunes = numéros des segments\n"
    legend_text += f"• Distance totale: {solution['distance']:.1f}m\n"
    legend_text += f"• Nombre de segments: {len(tour)-1}\n\n"
    
    # Détail de la séquence
    legend_text += "SÉQUENCE DÉTAILLÉE:\n"
    for ordre, idx in enumerate(tour):
        point = points_complets[idx]
        if point == hangar.depot_label:
            nom = "DÉPÔT"
        elif point == hangar.arrival_label:
            nom = "ARRIVÉE"
        elif isinstance(point, tuple):
            nom = f"{point[0]}{point[1]}"
        else:
            nom = str(point)
        
        legend_text += f"{ordre+1}. {nom}\n"
    
    # Ajouter la légende textuelle
    ax2.text(1.02, 0.98, legend_text,
            transform=ax2.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    # Tableau récapitulatif des segments
    if len(tour) <= 10:  # Seulement si pas trop de segments
        segment_text = "\nDÉTAIL DES SEGMENTS:\n"
        for i in range(len(tour) - 1):
            idx_from = tour[i]
            idx_to = tour[i+1]
            point_from = points_complets[idx_from]
            point_to = points_complets[idx_to]
            
            # Noms
            if point_from == hangar.depot_label:
                nom_from = "DÉPÔT"
            elif point_from == hangar.arrival_label:
                nom_from = "ARRIVÉE"
            elif isinstance(point_from, tuple):
                nom_from = f"{point_from[0]}{point_from[1]}"
            else:
                nom_from = str(point_from)
                
            if point_to == hangar.depot_label:
                nom_to = "DÉPÔT"
            elif point_to == hangar.arrival_label:
                nom_to = "ARRIVÉE"
            elif isinstance(point_to, tuple):
                nom_to = f"{point_to[0]}{point_to[1]}"
            else:
                nom_to = str(point_to)
            
            distance = graphe.matrice[idx_from, idx_to]
            segment_text += f"Segment {i+1}: {nom_from} → {nom_to} ({distance:.0f}m)\n"
        
        ax2.text(1.02, 0.4, segment_text,
                transform=ax2.transAxes, fontsize=8,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    plt.show()
    
    # Afficher aussi la séquence dans la console
    print(f"\n📋 SÉQUENCE DE VISITE ({len(tour)} points):")
    for ordre, idx in enumerate(tour):
        point = points_complets[idx]
        if point == hangar.depot_label:
            nom = "DÉPÔT"
        elif point == hangar.arrival_label:
            nom = "ARRIVÉE"
        elif isinstance(point, tuple):
            nom = f"{point[0]}{point[1]}"
        else:
            nom = str(point)
        
        print(f"  {ordre+1}. {nom}")
    
    print(f"\n📏 DISTANCE TOTALE: {solution['distance']:.1f}m")
    
    return solution

def main():
    """Fonction principale"""
    print("=" * 70)
    print("🧪 TEST D'INTÉGRATION COMPLET - ALGORITHMES DE COLLECTE")
    print("=" * 70)
    
    # Test 1: Dépôt = Arrivée
    #solution1 = test_avec_depot_fixe()
    
    # Test 2: Dépôt ≠ Arrivée
    solution2 = test_avec_depot_arrivee_differents(algorithm_type='first_solver',display_plot=True)
    
    """# Analyse comparative
    print("\n" + "=" * 70)
    print("📊 COMPARAISON DES DEUX SCÉNARIOS")
    print("=" * 70)
    
    if solution1 and solution2:
        print(f"Scénario Dépôt = Arrivée:    {solution1['distance']:.1f} m")
        print(f"Scénario Dépôt ≠ Arrivée:    {solution2['distance']:.1f} m")
        print(f"Différence:                  {abs(solution1['distance'] - solution2['distance']):.1f} m")
        
        if solution1['distance'] < solution2['distance']:
            print("\n✅ Le scénario avec même dépôt/arrivée est plus court")
        else:
            print("\n✅ Le scénario avec dépôt/arrivée différents est plus court")
    else:
        print("Certains scénarios n'ont pas de solution")
    
    print("\n" + "=" * 70)
    print("✅ TEST D'INTÉGRATION TERMINÉ")
    print("=" * 70)
    """

if __name__ == "__main__":
    main()