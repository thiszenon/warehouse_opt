# src/algorithms/alley_first_solver.py
import numpy as np
import time
import itertools
from typing import List, Dict, Optional, Tuple
from .base_solver import WarehouseTSPSolver

class AlleyFirstSolver(WarehouseTSPSolver):
    """
    Algorithme AlleyFirst : visite chaque allée complètement, une seule fois.
    Optimise l'ordre des allées avec TSP réduit.
    """
    
    def __init__(self, hangar=None, points_complets=None, 
                 max_alleys_for_bruteforce=6, use_heuristic_for_large_k=True):
        """
        Args:
            hangar: Référence au hangar
            points_complets: Liste complète des points
            max_alleys_for_bruteforce: Seuil pour force brute (k ≤)
            use_heuristic_for_large_k: Utiliser heuristique si k > max_alleys_for_bruteforce
        """
        name = "AlleyFirst Solver"
        super().__init__(name)
        self.hangar = hangar
        self.points_complets = points_complets
        self.max_alleys_for_bruteforce = max_alleys_for_bruteforce
        self.use_heuristic_for_large_k = use_heuristic_for_large_k
        
    def solve(self, distance_matrix: np.ndarray, 
              depot_idx: int = 0,
              arrival_idx: Optional[int] = None) -> Dict:
        start_time = time.time()
        
        n_total = distance_matrix.shape[0]
        
        if arrival_idx is None:
            arrival_idx = depot_idx
        
        # Cas trivial : pas de points à visiter
        points_to_visit = list(set(range(n_total)) - {depot_idx, arrival_idx})
        if not points_to_visit:
            tour = [depot_idx, arrival_idx]
            distance = distance_matrix[depot_idx, arrival_idx]
            return {
                'tour': tour,
                'distance': distance,
                'time': time.time() - start_time,
                'optimal': False,
                'solver': self.name
            }
        
        # Si pas d'infos sur le hangar, fallback simple
        if self.hangar is None or self.points_complets is None:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 1 : Regrouper les points par allée
        alley_info = self._group_points_by_alley(points_to_visit)
        
        # Extraire les allées avec points
        alleys_with_points = [a for a, info in alley_info.items() 
                            if info['points'] and a != 'SPECIAL' and a != 'UNKNOWN']
        
        if not alleys_with_points:
            # Pas d'allées normales, seulement points spéciaux
            return self._handle_special_points_only(points_to_visit, distance_matrix, 
                                                   depot_idx, arrival_idx)
        
        # PHASE 2 : Optimiser chaque allée individuellement
        self._optimize_each_alley(alley_info, distance_matrix)
        
        # PHASE 3 : Ordonner les allées (TSP réduit)
        alley_order = self._order_alleys(alleys_with_points, alley_info, 
                                        distance_matrix, depot_idx, arrival_idx)
        
        if not alley_order:
            return None
        
        # PHASE 4 : Construire le tour complet
        tour = self._build_complete_tour(alley_order, alley_info, 
                                        distance_matrix, depot_idx, arrival_idx)
        
        if not tour:
            return None
        
        # PHASE 5 : Valider et retourner
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name,
            'alleys_visited': len(alleys_with_points),
            'method': 'alley_first'
        }
    
    def _group_points_by_alley(self, point_indices: List[int]) -> Dict[str, Dict]:
        """
        Regroupe les points par allée et calcule les informations de base
        """
        groups = {}
        
        for idx in point_indices:
            if idx >= len(self.points_complets):
                continue
                
            point = self.points_complets[idx]
            
            # Identifier l'allée
            if isinstance(point, tuple):
                alley, _ = point
            elif point in ['DEPOT', 'ARRIVEE']:
                alley = 'SPECIAL'
            else:
                alley = 'UNKNOWN'
            
            if alley not in groups:
                groups[alley] = {
                    'points': [],        # Indices des points
                    'sorted_points': [], # Points triés selon sens
                    'entry_point': -1,   # Premier point accessible
                    'exit_point': -1,    # Dernier point
                    'intra_cost': 0.0,   # Coût intra-allée
                }
            
            groups[alley]['points'].append(idx)
        
        return groups
    
    def _optimize_each_alley(self, alley_info: Dict[str, Dict], 
                           distance_matrix: np.ndarray):
        """
        Pour chaque allée, trie les points selon le sens et calcule le coût
        """
        for alley, info in alley_info.items():
            if alley == 'SPECIAL' or alley == 'UNKNOWN':
                continue
            
            points = info['points']
            if not points:
                continue
            
            # Trier les points selon le sens de circulation
            sorted_points = self._sort_points_in_alley(points, alley)
            
            if not sorted_points:
                continue
            
            info['sorted_points'] = sorted_points
            info['entry_point'] = sorted_points[0]
            info['exit_point'] = sorted_points[-1]
            
            # Calculer le coût intra-allée
            cost = 0.0
            for i in range(len(sorted_points) - 1):
                cost += distance_matrix[sorted_points[i], sorted_points[i + 1]]
            info['intra_cost'] = cost
    
    def _sort_points_in_alley(self, point_indices: List[int], alley: str) -> List[int]:
        """
        Trie les points dans une allée selon le sens de circulation
        """
        if not point_indices or alley not in self.hangar.sens:
            return point_indices
        
        # Récupérer les coordonnées y des points
        points_with_y = []
        for idx in point_indices:
            if idx < len(self.points_complets):
                point = self.points_complets[idx]
                if isinstance(point, tuple) and point in self.hangar.points:
                    y = self.hangar.points[point][1]
                    points_with_y.append((idx, y))
        
        if not points_with_y:
            return point_indices
        
        # Trier selon le sens
        sens = self.hangar.sens[alley]
        if sens == 1:  # Montée
            points_with_y.sort(key=lambda x: x[1])
        else:  # Descente
            points_with_y.sort(key=lambda x: x[1], reverse=True)
        
        return [idx for idx, _ in points_with_y]
    
    def _order_alleys(self, alleys: List[str], alley_info: Dict[str, Dict],
                     distance_matrix: np.ndarray, depot_idx: int, arrival_idx: int) -> List[str]:
        """
        Trouve le meilleur ordre pour visiter les allées (TSP réduit)
        """
        k = len(alleys)
        
        if k == 1:
            return alleys
        
        if k <= self.max_alleys_for_bruteforce:
            # Force brute pour petit k
            return self._bruteforce_alley_order(alleys, alley_info, 
                                               distance_matrix, depot_idx, arrival_idx)
        elif self.use_heuristic_for_large_k:
            # Heuristique nearest neighbor pour k plus grand
            return self._nearest_neighbor_alley_order(alleys, alley_info,
                                                     distance_matrix, depot_idx, arrival_idx)
        else:
            # Pour k trop grand, ordre simple
            return self._simple_alley_order(alleys)
    
    def _bruteforce_alley_order(self, alleys: List[str], alley_info: Dict[str, Dict],
                               distance_matrix: np.ndarray, depot_idx: int, 
                               arrival_idx: int) -> List[str]:
        """
        Force brute pour trouver l'ordre optimal des allées (k ≤ max_alleys_for_bruteforce)
        """
        best_order = None
        best_cost = float('inf')
        
        # Tester toutes les permutations
        for perm in itertools.permutations(alleys):
            cost = self._compute_alley_order_cost(perm, alley_info, 
                                                 distance_matrix, depot_idx, arrival_idx)
            
            if cost < best_cost:
                best_cost = cost
                best_order = perm
        
        return list(best_order) if best_order else alleys
    
    def _compute_alley_order_cost(self, alley_order: Tuple[str, ...], 
                                 alley_info: Dict[str, Dict],
                                 distance_matrix: np.ndarray, 
                                 depot_idx: int, arrival_idx: int) -> float:
        """
        Calcule le coût d'un ordre spécifique d'allées
        """
        total_cost = 0.0
        current_point = depot_idx
        
        for i, alley in enumerate(alley_order):
            info = alley_info[alley]
            
            # Coût pour aller à l'entrée de l'allée
            entry_cost = distance_matrix[current_point, info['entry_point']]
            if entry_cost == float('inf'):
                return float('inf')
            total_cost += entry_cost
            
            # Coût intra-allée
            total_cost += info['intra_cost']
            current_point = info['exit_point']
        
        # Coût pour aller à l'arrivée
        arrival_cost = distance_matrix[current_point, arrival_idx]
        if arrival_cost == float('inf'):
            return float('inf')
        total_cost += arrival_cost
        
        return total_cost
    
    def _nearest_neighbor_alley_order(self, alleys: List[str], alley_info: Dict[str, Dict],
                                     distance_matrix: np.ndarray, depot_idx: int,
                                     arrival_idx: int) -> List[str]:
        """
        Heuristique nearest neighbor pour l'ordre des allées
        """
        if not alleys:
            return []
        
        ordered = []
        remaining = set(alleys)
        current_point = depot_idx
        
        while remaining:
            # Trouver l'allée la plus proche
            best_alley = None
            best_cost = float('inf')
            best_entry = -1
            
            for alley in remaining:
                info = alley_info[alley]
                cost = distance_matrix[current_point, info['entry_point']]
                
                if cost < best_cost:
                    best_cost = cost
                    best_alley = alley
                    best_entry = info['entry_point']
            
            if best_alley is None or best_cost == float('inf'):
                # Échec, utiliser ordre simple
                return self._simple_alley_order(alleys)
            
            ordered.append(best_alley)
            remaining.remove(best_alley)
            
            # Mettre à jour le point courant
            info = alley_info[best_alley]
            current_point = info['exit_point']
        
        return ordered
    
    def _simple_alley_order(self, alleys: List[str]) -> List[str]:
        """
        Ordre simple des allées (basé sur la position)
        """
        # Définir l'ordre approximatif des allées
        alley_positions = {
            'H': 0, 'G': 1, 'F': 2, 'E': 3, 'D': 4, 'C': 5, 'B': 6, 'A': 7,
            'HH': 0, 'GG': 1, 'FF': 2, 'EE': 3, 'DD': 4, 'CC': 5, 'BB': 6, 'AA': 7
        }
        
        # Trier par position (de gauche à droite)
        alleys_with_pos = [(alley, alley_positions.get(alley, 50)) for alley in alleys]
        alleys_with_pos.sort(key=lambda x: x[1])
        
        return [alley for alley, _ in alleys_with_pos]
    
    def _build_complete_tour(self, alley_order: List[str], alley_info: Dict[str, Dict],
                           distance_matrix: np.ndarray, depot_idx: int, 
                           arrival_idx: int) -> List[int]:
        """
        Construit le tour complet en visitant les allées dans l'ordre donné
        """
        tour = [depot_idx]
        current_point = depot_idx
        
        for alley in alley_order:
            info = alley_info[alley]
            
            # 1. Aller à l'entrée de l'allée
            entry_point = info['entry_point']
            
            if distance_matrix[current_point, entry_point] == float('inf'):
                # Chercher un chemin alternatif
                intermediate = self._find_intermediate_path(current_point, entry_point,
                                                          distance_matrix, tour)
                if intermediate is None:
                    return None
                
                if isinstance(intermediate, list):
                    tour.extend(intermediate)
                    current_point = intermediate[-1]
                else:
                    tour.append(intermediate)
                    current_point = intermediate
            
            # 2. Visiter tous les points de l'allée
            for point_idx in info['sorted_points']:
                # Vérifier si l'arc est possible
                if distance_matrix[current_point, point_idx] == float('inf'):
                    intermediate = self._find_intermediate_path(current_point, point_idx,
                                                              distance_matrix, tour)
                    if intermediate is None:
                        return None
                    
                    if isinstance(intermediate, list):
                        tour.extend(intermediate)
                        current_point = intermediate[-1]
                    else:
                        tour.append(intermediate)
                        current_point = intermediate
                
                tour.append(point_idx)
                current_point = point_idx
        
        # 3. Aller à l'arrivée
        if distance_matrix[current_point, arrival_idx] == float('inf'):
            intermediate = self._find_intermediate_path(current_point, arrival_idx,
                                                      distance_matrix, tour)
            if intermediate is None:
                return None
            
            if isinstance(intermediate, list):
                tour.extend(intermediate)
                current_point = intermediate[-1]
            else:
                tour.append(intermediate)
                current_point = intermediate
        
        tour.append(arrival_idx)
        
        return tour
    
    def _find_intermediate_path(self, from_idx: int, to_idx: int,
                              distance_matrix: np.ndarray, 
                              current_tour: List[int]) -> Optional[List[int]]:
        """
        Trouve un chemin alternatif entre deux points (1-2 intermédiaires)
        """
        n = distance_matrix.shape[0]
        
        # Chercher un seul point intermédiaire
        for k in range(n):
            if (k != from_idx and k != to_idx and k not in current_tour and
                distance_matrix[from_idx, k] < float('inf') and
                distance_matrix[k, to_idx] < float('inf')):
                return [k]
        
        # Chercher deux points intermédiaires
        for k1 in range(n):
            if (k1 != from_idx and k1 != to_idx and k1 not in current_tour and
                distance_matrix[from_idx, k1] < float('inf')):
                for k2 in range(n):
                    if (k2 != from_idx and k2 != to_idx and k2 != k1 and 
                        k2 not in current_tour and
                        distance_matrix[k1, k2] < float('inf') and
                        distance_matrix[k2, to_idx] < float('inf')):
                        return [k1, k2]
        
        return None
    
    def _handle_special_points_only(self, points_to_visit: List[int],
                                  distance_matrix: np.ndarray,
                                  depot_idx: int, arrival_idx: int) -> Optional[Dict]:
        """
        Gère le cas où il n'y a que des points spéciaux (pas d'allées normales)
        """
        # Solution simple : visiter dans l'ordre
        tour = [depot_idx] + points_to_visit + [arrival_idx]
        
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time(),
            'optimal': False,
            'solver': self.name + " (special points only)",
            'method': 'simple'
        }
    
    def _fallback_solution(self, distance_matrix: np.ndarray,
                          depot_idx: int, arrival_idx: int) -> Optional[Dict]:
        """
        Solution de secours quand pas d'info hangar
        """
        from .insertion import InsertionSolver
        
        solver = InsertionSolver(insertion_strategy='cheapest')
        result = solver.solve(distance_matrix, depot_idx, arrival_idx)
        
        if result:
            result['solver'] = self.name + " (fallback)"
        
        return result