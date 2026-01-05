# src/algorithms/robust_s_shape_solver.py
import numpy as np
import time
from .base_solver import WarehouseTSPSolver
from typing import List, Dict, Optional, Tuple

class RobustSShapeSolver(WarehouseTSPSolver):
    """
    S-shape robuste qui gère les arcs impossibles (∞)
    """
    
    def __init__(self, hangar=None, commande=None, points_complets=None,
                 max_attempts=3, fallback_to_simple=True):
        name = "Robust S-Shape"
        super().__init__(name)
        self.hangar = hangar
        self.commande = commande
        self.points_complets = points_complets
        self.max_attempts = max_attempts
        self.fallback_to_simple = fallback_to_simple
    
    def solve(self, distance_matrix: np.ndarray, 
              depot_idx: int = 0,
              arrival_idx: Optional[int] = None) -> Dict:
        start_time = time.time()
        
        n_total = distance_matrix.shape[0]
        
        if arrival_idx is None:
            arrival_idx = depot_idx
        
        points_to_visit = list(set(range(n_total)) - {depot_idx, arrival_idx})
        
        if not points_to_visit:
            tour = [depot_idx, arrival_idx]
            distance = distance_matrix[depot_idx, arrival_idx]
            return {
                'tour': tour,
                'distance': distance,
                'time': time.time() - start_time,
                'optimal': True,
                'solver': self.name
            }
        
        # Essayer plusieurs stratégies
        for attempt in range(self.max_attempts):
            strategy = self._get_strategy(attempt)
            tour = self._build_tour_with_strategy(
                points_to_visit, distance_matrix, depot_idx, arrival_idx, strategy
            )
            
            if tour and self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
                distance = self.calculate_tour_distance(tour, distance_matrix)
                return {
                    'tour': tour,
                    'distance': distance,
                    'time': time.time() - start_time,
                    'optimal': False,
                    'solver': self.name,
                    'strategy': strategy
                }
        
        # Fallback : solution simple
        if self.fallback_to_simple:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        return None
    
    def _get_strategy(self, attempt: int) -> str:
        """Différentes stratégies de parcours"""
        strategies = [
            'left_to_right',      # H → G → F → ... → A
            'right_to_left',      # A → B → C → ... → H  
            'middle_out',         # Milieu vers les bords
            'closest_first',      # Plus proche du dépôt d'abord
            'alternating'         # Alterner gauche/droite
        ]
        return strategies[attempt % len(strategies)]
    
    def _build_tour_with_strategy(self, points_to_visit: List[int],
                                distance_matrix: np.ndarray,
                                depot_idx: int, arrival_idx: int,
                                strategy: str) -> Optional[List[int]]:
        """Construit un tour selon la stratégie"""
        
        # Grouper par allée si possible
        if self.hangar and self.points_complets:
            points_by_alley = self._group_points_by_alley(points_to_visit)
            alley_order = self._get_alley_order_by_strategy(points_by_alley, strategy)
            
            # Construire le tour allée par allée
            return self._build_alley_by_alley(
                points_by_alley, alley_order, distance_matrix, depot_idx, arrival_idx
            )
        else:
            # Version simple sans info hangar
            return self._build_simple_tour(points_to_visit, distance_matrix, 
                                         depot_idx, arrival_idx, strategy)
    
    def _group_points_by_alley(self, point_indices: List[int]) -> Dict[str, List[int]]:
        """Regroupe les points par allée"""
        groups = {}
        
        for idx in point_indices:
            if idx >= len(self.points_complets):
                continue
                
            point = self.points_complets[idx]
            
            if isinstance(point, tuple):
                alley, _ = point
            elif point in ['DEPOT', 'ARRIVEE']:
                alley = 'SPECIAL'
            else:
                alley = 'UNKNOWN'
            
            if alley not in groups:
                groups[alley] = []
            groups[alley].append(idx)
        
        return groups
    
    def _get_alley_order_by_strategy(self, points_by_alley: Dict[str, List[int]],
                                   strategy: str) -> List[str]:
        """Ordonne les allées selon la stratégie"""
        alleys = [a for a in points_by_alley.keys() 
                 if a != 'SPECIAL' and a != 'UNKNOWN' and points_by_alley[a]]
        
        if not alleys:
            return []
        
        # Définir l'ordre des allées (approximatif)
        alley_positions = {
            'H': 0, 'G': 1, 'F': 2, 'E': 3, 'D': 4, 'C': 5, 'B': 6, 'A': 7,
            'HH': 0, 'GG': 1, 'FF': 2, 'EE': 3, 'DD': 4, 'CC': 5, 'BB': 6, 'AA': 7
        }
        
        # Trier par position
        alleys_with_pos = []
        for alley in alleys:
            pos = alley_positions.get(alley, 50)  # 50 = position par défaut
            alleys_with_pos.append((alley, pos))
        
        alleys_with_pos.sort(key=lambda x: x[1])
        sorted_alleys = [a for a, _ in alleys_with_pos]
        
        # Appliquer la stratégie
        if strategy == 'left_to_right':
            return sorted_alleys  # Déjà trié de gauche à droite
        elif strategy == 'right_to_left':
            return list(reversed(sorted_alleys))
        elif strategy == 'middle_out':
            # Milieu d'abord, puis alterner gauche/droite
            middle = len(sorted_alleys) // 2
            result = [sorted_alleys[middle]]
            for i in range(1, max(middle, len(sorted_alleys) - middle)):
                if middle - i >= 0:
                    result.append(sorted_alleys[middle - i])
                if middle + i < len(sorted_alleys):
                    result.append(sorted_alleys[middle + i])
            return result
        elif strategy == 'alternating':
            # Alterner gauche/droite
            result = []
            left, right = 0, len(sorted_alleys) - 1
            while left <= right:
                if left <= right:
                    result.append(sorted_alleys[left])
                    left += 1
                if left <= right:
                    result.append(sorted_alleys[right])
                    right -= 1
            return result
        else:
            return sorted_alleys
    
    def _build_alley_by_alley(self, points_by_alley: Dict[str, List[int]],
                            alley_order: List[str],
                            distance_matrix: np.ndarray,
                            depot_idx: int, arrival_idx: int) -> Optional[List[int]]:
        """Construit le tour allée par allée avec gestion des ∞"""
        tour = [depot_idx]
        current = depot_idx
        
        for alley in alley_order:
            if alley not in points_by_alley:
                continue
            
            # Trier les points de cette allée
            alley_points = self._sort_alley_points(points_by_alley[alley], alley)
            
            # Ajouter les points un par un avec vérification
            for point in alley_points:
                # Vérifier si l'arc est possible
                if distance_matrix[current, point] == float('inf'):
                    # Chercher un chemin via un point intermédiaire
                    intermediate = self._find_path(current, point, distance_matrix, tour)
                    if intermediate is None:
                        # Skip ce point pour l'instant
                        continue
                    elif isinstance(intermediate, list):
                        # Plusieurs points intermédiaires
                        for inter in intermediate:
                            tour.append(inter)
                            current = inter
                    else:
                        # Un seul point intermédiaire
                        tour.append(intermediate)
                        current = intermediate
                
                tour.append(point)
                current = point
        
        # Ajouter l'arrivée
        if distance_matrix[current, arrival_idx] < float('inf'):
            tour.append(arrival_idx)
            return tour
        else:
            # Chercher un chemin vers l'arrivée
            path_to_arrival = self._find_path(current, arrival_idx, distance_matrix, tour)
            if path_to_arrival:
                if isinstance(path_to_arrival, list):
                    tour.extend(path_to_arrival)
                else:
                    tour.append(path_to_arrival)
                tour.append(arrival_idx)
                return tour
        
        return None
    
    def _sort_alley_points(self, point_indices: List[int], alley: str) -> List[int]:
        """Trie les points dans une allée"""
        if not self.hangar or alley not in self.hangar.sens:
            return point_indices
        
        # Récupérer les coordonnées y
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
        sens = self.hangar.sens.get(alley, 1)
        if sens == 1:  # Montée
            points_with_y.sort(key=lambda x: x[1])
        else:  # Descente
            points_with_y.sort(key=lambda x: x[1], reverse=True)
        
        return [idx for idx, _ in points_with_y]
    
    def _find_path(self, from_idx: int, to_idx: int,
                  distance_matrix: np.ndarray,
                  current_tour: List[int]) -> Optional[List[int]]:
        """Trouve un chemin entre deux points (peut être multiple)"""
        n = distance_matrix.shape[0]
        
        # Chercher un chemin direct à 1 intermédiaire
        for k in range(n):
            if (k not in current_tour and k != from_idx and k != to_idx and
                distance_matrix[from_idx, k] < float('inf') and
                distance_matrix[k, to_idx] < float('inf')):
                return k
        
        # Chercher un chemin à 2 intermédiaires
        for k1 in range(n):
            if (k1 not in current_tour and k1 != from_idx and k1 != to_idx and
                distance_matrix[from_idx, k1] < float('inf')):
                for k2 in range(n):
                    if (k2 not in current_tour and k2 != from_idx and k2 != to_idx and k2 != k1 and
                        distance_matrix[k1, k2] < float('inf') and
                        distance_matrix[k2, to_idx] < float('inf')):
                        return [k1, k2]
        
        return None
    
    def _build_simple_tour(self, points_to_visit: List[int],
                         distance_matrix: np.ndarray,
                         depot_idx: int, arrival_idx: int,
                         strategy: str) -> Optional[List[int]]:
        """Version simple sans info hangar"""
        # Trier selon la stratégie
        if strategy == 'closest_first':
            # Trier par distance au dépôt
            points_to_visit.sort(key=lambda x: distance_matrix[depot_idx, x])
        elif strategy == 'right_to_left':
            points_to_visit.sort(reverse=True)
        else:  # left_to_right par défaut
            points_to_visit.sort()
        
        # Construire pas à pas avec vérification
        tour = [depot_idx]
        current = depot_idx
        
        for point in points_to_visit:
            if distance_matrix[current, point] == float('inf'):
                # Chercher un point intermédiaire
                found = False
                for other in points_to_visit:
                    if (other != point and other not in tour and
                        distance_matrix[current, other] < float('inf') and
                        distance_matrix[other, point] < float('inf')):
                        tour.append(other)
                        current = other
                        found = True
                        break
                
                if not found:
                    # Skip ce point
                    continue
            
            tour.append(point)
            current = point
        
        # Ajouter l'arrivée
        if distance_matrix[current, arrival_idx] < float('inf'):
            tour.append(arrival_idx)
            return tour
        
        return None
    
    def _fallback_solution(self, distance_matrix: np.ndarray,
                          depot_idx: int, arrival_idx: int) -> Optional[Dict]:
        """Solution de secours très simple"""
        from .insertion import InsertionSolver
        
        solver = InsertionSolver(insertion_strategy='cheapest')
        result = solver.solve(distance_matrix, depot_idx, arrival_idx)
        
        if result:
            result['solver'] = self.name + " (fallback)"
        
        return result


# Version U-shape robuste
class RobustUShapeSolver(RobustSShapeSolver):
    """U-shape robuste"""
    
    def __init__(self, hangar=None, commande=None, points_complets=None,
                 max_attempts=3, fallback_to_simple=True):
        name = "Robust U-Shape"
        super().__init__(hangar, commande, points_complets, max_attempts, fallback_to_simple)
        self.name = name
    
    def _get_strategy(self, attempt: int) -> str:
        """Stratégies spécifiques à U-shape"""
        strategies = [
            'alternating_u',      # Alterner avec retour
            'double_back',        # Aller-retour systématique
            'zone_by_zone',       # Par zones
            'closest_first',
            'left_to_right'
        ]
        return strategies[attempt % len(strategies)]
    
    def _build_alley_by_alley(self, points_by_alley: Dict[str, List[int]],
                            alley_order: List[str],
                            distance_matrix: np.ndarray,
                            depot_idx: int, arrival_idx: int) -> Optional[List[int]]:
        """U-shape : visiter chaque allée en aller-retour"""
        tour = [depot_idx]
        current = depot_idx
        direction = 'forward'  # forward ou backward
        
        for i, alley in enumerate(alley_order):
            if alley not in points_by_alley:
                continue
            
            alley_points = points_by_alley[alley]
            
            # Pour U-shape, on visite l'allée dans un sens, puis parfois on revient
            if direction == 'forward':
                sorted_points = self._sort_alley_points(alley_points, alley)
            else:
                sorted_points = list(reversed(self._sort_alley_points(alley_points, alley)))
            
            # Ajouter les points
            for point in sorted_points:
                if distance_matrix[current, point] == float('inf'):
                    intermediate = self._find_path(current, point, distance_matrix, tour)
                    if intermediate:
                        if isinstance(intermediate, list):
                            for inter in intermediate:
                                tour.append(inter)
                                current = inter
                        else:
                            tour.append(intermediate)
                            current = intermediate
                
                tour.append(point)
                current = point
            
            # Alterner la direction pour l'allée suivante
            if i % 2 == 1:  # Alterner toutes les 2 allées
                direction = 'backward' if direction == 'forward' else 'forward'
        
        # Ajouter l'arrivée
        if distance_matrix[current, arrival_idx] < float('inf'):
            tour.append(arrival_idx)
            return tour
        
        return None