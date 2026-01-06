# src/algorithms/robust_alley_solver.py
import numpy as np
import time
from typing import List, Dict, Optional, Tuple, Set
from .base_solver import WarehouseTSPSolver

class RobustAlleySolver(WarehouseTSPSolver):
    """
    Algorithme RobustAlley : Flexible, autorise des retours dans les allées
    pour garantir une solution même avec beaucoup de ∞.
    """
    
    def __init__(self, hangar=None, points_complets=None,
                 score_points_weight=100.0,
                 max_backtrack_attempts=3,
                 consolidation_enabled=True):
        """
        Args:
            hangar: Référence au hangar
            points_complets: Liste complète des points
            score_points_weight: Poids du nombre de points dans le score
            max_backtrack_attempts: Nombre max de tentatives de backtrack
            consolidation_enabled: Activer la phase de consolidation
        """
        name = "RobustAlley Solver"
        super().__init__(name)
        self.hangar = hangar
        self.points_complets = points_complets
        self.score_points_weight = score_points_weight
        self.max_backtrack_attempts = max_backtrack_attempts
        self.consolidation_enabled = consolidation_enabled
        
    def solve(self, distance_matrix: np.ndarray, 
              depot_idx: int = 0,
              arrival_idx: Optional[int] = None) -> Dict:
        start_time = time.time()
        
        n_total = distance_matrix.shape[0]
        
        if arrival_idx is None:
            arrival_idx = depot_idx
        
        # Cas trivial
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
        
        # Si pas d'infos sur le hangar, fallback
        if self.hangar is None or self.points_complets is None:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 0 : Préparation des données
        alley_points = self._group_points_by_alley(points_to_visit)
        remaining_points = set(points_to_visit)
        
        # PHASE 1 : Construction gloutonne adaptative
        tour = self._adaptive_greedy_construction(
            alley_points, remaining_points, distance_matrix, 
            depot_idx, arrival_idx
        )
        
        if not tour:
            return None
        
        # PHASE 2 : Consolidation (si activée)
        if self.consolidation_enabled and len(tour) > 3:
            tour = self._consolidate_groups(tour, distance_matrix)
        
        # PHASE 3 : Réparation des arcs ∞
        tour = self._repair_infinite_arcs(tour, distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 4 : Validation finale
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            # Dernier recours : méthode simple
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name,
            'method': 'robust_alley'
        }
    
    def _group_points_by_alley(self, point_indices: List[int]) -> Dict[str, Set[int]]:
        """Regroupe les points par allée (ensembles pour accès rapide)"""
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
                groups[alley] = set()
            groups[alley].add(idx)
        
        return groups
    
    def _adaptive_greedy_construction(self, alley_points: Dict[str, Set[int]],
                                    remaining_points: Set[int],
                                    distance_matrix: np.ndarray,
                                    depot_idx: int, arrival_idx: int) -> List[int]:
        """
        Construction gloutonne adaptative avec gestion des ∞
        """
        tour = [depot_idx]
        current_point = depot_idx
        current_alley = None
        visited_alleys = []  # Historique des allées visitées
        backtrack_count = 0
        
        while remaining_points:
            # Option A : Continuer dans l'allée courante si possible
            if current_alley and current_alley in alley_points:
                same_alley_points = alley_points[current_alley] & remaining_points
                
                if same_alley_points:
                    # Chercher le point le plus proche accessible
                    closest = self._find_closest_accessible(
                        current_point, list(same_alley_points), distance_matrix
                    )
                    
                    if closest is not None:
                        tour.append(closest)
                        remaining_points.remove(closest)
                        current_point = closest
                        continue  # Continuer dans la même allée
            
            # Option B : Changer d'allée (avec score)
            best_alley, best_point = self._find_best_next_alley(
                current_point, alley_points, remaining_points, distance_matrix,
                visited_alleys
            )
            
            if best_point is not None:
                tour.append(best_point)
                remaining_points.remove(best_point)
                current_point = best_point
                
                # Mettre à jour l'allée courante
                if best_alley != current_alley:
                    current_alley = best_alley
                    visited_alleys.append(best_alley)
                    backtrack_count = 0  # Reset backtrack count
                continue
            
            # Option C : Backtrack limité
            if backtrack_count < self.max_backtrack_attempts and len(tour) > 2:
                # Retirer le dernier point et réessayer
                backtrack_count += 1
                last_point = tour.pop()
                remaining_points.add(last_point)
                current_point = tour[-1]
                
                # Mettre à jour l'allée courante
                if len(tour) > 1:
                    current_alley = self._get_alley_of_point(tour[-1])
                continue
            
            # Option D : Échec - fallback
            print(f"  ⚠️  RobustAlley: Échec de construction, {len(remaining_points)} points restants")
            return None
        
        # Ajouter l'arrivée
        if distance_matrix[current_point, arrival_idx] < float('inf'):
            tour.append(arrival_idx)
        else:
            # Chercher un chemin vers l'arrivée
            path = self._find_path_to_arrival(current_point, arrival_idx, 
                                            distance_matrix, tour)
            if path:
                tour.extend(path)
            tour.append(arrival_idx)
        
        return tour
    
    def _find_closest_accessible(self, from_point: int, to_points: List[int],
                               distance_matrix: np.ndarray) -> Optional[int]:
        """Trouve le point le plus proche accessible"""
        closest = None
        min_distance = float('inf')
        
        for point in to_points:
            dist = distance_matrix[from_point, point]
            if dist < min_distance and dist < float('inf'):
                min_distance = dist
                closest = point
        
        return closest
    
    def _find_best_next_alley(self, current_point: int,
                            alley_points: Dict[str, Set[int]],
                            remaining_points: Set[int],
                            distance_matrix: np.ndarray,
                            visited_alleys: List[str]) -> Tuple[Optional[str], Optional[int]]:
        """
        Trouve la meilleure allée suivante avec système de score
        Score = (nb_points * weight) - distance
        """
        best_score = -float('inf')
        best_alley = None
        best_point = None
        
        for alley, points in alley_points.items():
            if alley == 'SPECIAL' or alley == 'UNKNOWN':
                continue
            
            # Points de cette allée non visités
            alley_remaining = points & remaining_points
            if not alley_remaining:
                continue
            
            # Trouver le point accessible le plus proche
            accessible_point = self._find_first_accessible(
                current_point, list(alley_remaining), distance_matrix
            )
            
            if accessible_point is None:
                continue
            
            # Calcul du score
            distance = distance_matrix[current_point, accessible_point]
            nb_points = len(alley_remaining)
            
            # Bonus si c'est une allée déjà visitée (on favorise les retours)
            alley_bonus = 20 if alley in visited_alleys[-3:] else 0
            
            score = (nb_points * self.score_points_weight) - distance + alley_bonus
            
            if score > best_score:
                best_score = score
                best_alley = alley
                best_point = accessible_point
        
        return best_alley, best_point
    
    def _find_first_accessible(self, from_point: int, to_points: List[int],
                             distance_matrix: np.ndarray) -> Optional[int]:
        """Trouve le premier point accessible"""
        for point in to_points:
            if distance_matrix[from_point, point] < float('inf'):
                return point
        return None
    
    def _get_alley_of_point(self, point_idx: int) -> Optional[str]:
        """Retourne l'allée d'un point"""
        if point_idx >= len(self.points_complets):
            return None
        
        point = self.points_complets[point_idx]
        if isinstance(point, tuple):
            return point[0]
        return None
    
    def _find_path_to_arrival(self, from_point: int, arrival_idx: int,
                            distance_matrix: np.ndarray,
                            current_tour: List[int]) -> Optional[List[int]]:
        """Trouve un chemin vers l'arrivée"""
        n = distance_matrix.shape[0]
        
        # Chercher un point intermédiaire
        for k in range(n):
            if (k != from_point and k != arrival_idx and 
                k not in current_tour and
                distance_matrix[from_point, k] < float('inf') and
                distance_matrix[k, arrival_idx] < float('inf')):
                return [k]
        
        return None
    
    def _consolidate_groups(self, tour: List[int],
                          distance_matrix: np.ndarray) -> List[int]:
        """
        Tente de regrouper les points de même allée qui sont proches
        """
        if len(tour) <= 3:
            return tour
        
        improved = True
        iterations = 0
        
        while improved and iterations < 10:
            improved = False
            iterations += 1
            
            # Analyser le tour pour trouver des points de même allée non consécutifs
            for i in range(1, len(tour) - 2):
                alley_i = self._get_alley_of_point(tour[i])
                if not alley_i:
                    continue
                
                for j in range(i + 2, len(tour) - 1):
                    alley_j = self._get_alley_of_point(tour[j])
                    
                    if alley_i == alley_j:
                        # Essayer d'échanger pour rapprocher
                        if self._should_swap(tour, i, j, distance_matrix):
                            tour[i+1], tour[j] = tour[j], tour[i+1]
                            improved = True
                            break
                
                if improved:
                    break
        
        return tour
    
    def _should_swap(self, tour: List[int], i: int, j: int,
                   distance_matrix: np.ndarray) -> bool:
        """Détermine si un échange améliore la distance"""
        if j <= i + 1:
            return False
        
        # Distance actuelle
        current_dist = (distance_matrix[tour[i], tour[i+1]] +
                       distance_matrix[tour[j-1], tour[j]] +
                       distance_matrix[tour[j], tour[j+1]])
        
        # Distance après échange
        new_dist = (distance_matrix[tour[i], tour[j]] +
                   distance_matrix[tour[j], tour[i+1]] +
                   distance_matrix[tour[j-1], tour[i+1]])
        
        return new_dist < current_dist - 1e-6
    
    def _repair_infinite_arcs(self, tour: List[int],
                            distance_matrix: np.ndarray,
                            depot_idx: int, arrival_idx: int) -> List[int]:
        """
        Répare les arcs ∞ dans le tour
        """
        if len(tour) < 2:
            return tour
        
        repaired_tour = [tour[0]]
        
        for i in range(len(tour) - 1):
            from_point = repaired_tour[-1]
            to_point = tour[i + 1]
            
            if distance_matrix[from_point, to_point] < float('inf'):
                repaired_tour.append(to_point)
            else:
                # Chercher un chemin intermédiaire
                intermediate = self._find_intermediate_path(
                    from_point, to_point, distance_matrix, repaired_tour
                )
                if intermediate:
                    if isinstance(intermediate, list):
                        repaired_tour.extend(intermediate)
                    else:
                        repaired_tour.append(intermediate)
                else:
                    # Essayer de sauter ce point pour l'instant
                    continue
        
        return repaired_tour
    
    def _find_intermediate_path(self, from_idx: int, to_idx: int,
                              distance_matrix: np.ndarray,
                              current_tour: List[int]) -> Optional[List[int]]:
        """Trouve un chemin alternatif"""
        n = distance_matrix.shape[0]
        
        # Chercher un point intermédiaire
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
    
    def _fallback_solution(self, distance_matrix: np.ndarray,
                          depot_idx: int, arrival_idx: int) -> Optional[Dict]:
        """Solution de secours"""
        # Essayer d'abord S-Shape (très robuste)
        try:
            from .s_shape_solver import SShapeSolver
            solver = SShapeSolver()
            result = solver.solve(distance_matrix, depot_idx, arrival_idx)
            if result:
                result['solver'] = self.name + " (S-Shape fallback)"
                return result
        except:
            pass
        
        # Sinon, méthode très simple
        n_total = distance_matrix.shape[0]
        points_to_visit = list(set(range(n_total)) - {depot_idx, arrival_idx})
        
        if not points_to_visit:
            tour = [depot_idx, arrival_idx]
            distance = distance_matrix[depot_idx, arrival_idx]
            return {
                'tour': tour,
                'distance': distance,
                'time': time.time(),
                'optimal': False,
                'solver': self.name + " (simple fallback)"
            }
        
        # Construction linéaire avec vérification
        tour = [depot_idx]
        current = depot_idx
        
        for point in points_to_visit:
            if distance_matrix[current, point] < float('inf'):
                tour.append(point)
                current = point
            else:
                # Chercher un point intermédiaire
                found = False
                for other in points_to_visit:
                    if (other != point and other not in tour and
                        distance_matrix[current, other] < float('inf') and
                        distance_matrix[other, point] < float('inf')):
                        tour.append(other)
                        tour.append(point)
                        current = point
                        found = True
                        break
                if not found:
                    # Skip ce point
                    continue
        
        # Ajouter l'arrivée
        if distance_matrix[current, arrival_idx] < float('inf'):
            tour.append(arrival_idx)
        else:
            return None
        
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time(),
            'optimal': False,
            'solver': self.name + " (simple fallback)"
        }