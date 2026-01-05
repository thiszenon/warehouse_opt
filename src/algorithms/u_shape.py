# src/algorithms/u_shape_solver.py
import numpy as np
import time
from .base_solver import WarehouseTSPSolver
from typing import List, Dict, Optional

class UShapeSolver(WarehouseTSPSolver):
    """
    Parcours en U-shape (peigne) adapté aux contraintes du hangar.
    Visite chaque allée en aller-retour.
    """
    
    def __init__(self, hangar=None, commande=None, points_complets=None,
                 strategy='alternating', return_level='optimal'):
        """
        Args:
            hangar: Référence au hangar
            commande: Liste des points de collecte
            points_complets: Liste complète des points
            strategy: 'alternating' (alterné), 'one_way' (toujours même sens)
            return_level: Niveau pour le retour 'N1', 'N2', 'N3', 'optimal'
        """
        name = f"U-Shape ({strategy}, {return_level})"
        super().__init__(name)
        self.hangar = hangar
        self.commande = commande
        self.points_complets = points_complets
        self.strategy = strategy
        self.return_level = return_level
        
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
                'optimal': True,
                'solver': self.name
            }
        
        # Si pas d'infos sur le hangar
        if self.hangar is None or self.points_complets is None:
            return self._solve_simple(distance_matrix, depot_idx, arrival_idx)
        
        # 1. Grouper les points par allée
        points_by_alley = self._group_points_by_alley(points_to_visit)
        
        # 2. Déterminer l'ordre des allées
        alley_order = self._get_alley_order(points_by_alley)
        
        # 3. Construire le parcours U-shape
        tour = self._build_u_shape_tour(points_by_alley, alley_order,
                                       depot_idx, arrival_idx, distance_matrix)
        
        if not tour:
            return None
        
        # 4. Valider et calculer
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name
        }
    
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
                continue
            
            if alley not in groups:
                groups[alley] = []
            groups[alley].append(idx)
        
        return groups
    
    def _get_alley_order(self, points_by_alley: Dict[str, List[int]]) -> List[str]:
        """Détermine l'ordre de visite des allées"""
        # Filtrer les allées qui ont des points
        alleys_with_points = [a for a in points_by_alley.keys() 
                            if a != 'SPECIAL' and points_by_alley[a]]
        
        # Trier par position (approximative)
        if not alleys_with_points:
            return []
        
        # Trier alphabétiquement pour une première approximation
        # (A=à droite, H=à gauche)
        sorted_alleys = sorted(alleys_with_points, reverse=True)  # A, B, C, ..., H
        
        # Ajuster selon la stratégie
        if self.strategy == 'alternating':
            # Alterner pour minimiser les retours
            return self._alternate_alleys(sorted_alleys)
        else:
            # Ordre simple
            return sorted_alleys
    
    def _alternate_alleys(self, alleys: List[str]) -> List[str]:
        """Ordonne les allées en alternant les côtés"""
        if len(alleys) <= 2:
            return alleys
        
        # Séparer les allées "paires" et "impaires" (approximation)
        # En réalité, il faudrait les positions réelles
        return alleys  # Simplifié pour l'instant
    
    def _build_u_shape_tour(self, points_by_alley: Dict[str, List[int]],
                          alley_order: List[str],
                          depot_idx: int, arrival_idx: int,
                          distance_matrix: np.ndarray) -> List[int]:
        """Construit le parcours en U-shape"""
        tour = [depot_idx]
        current_point = depot_idx
        direction = 1  # 1 = avant, -1 = retour
        
        for alley in alley_order:
            if alley not in points_by_alley or not points_by_alley[alley]:
                continue
            
            alley_points = points_by_alley[alley]
            
            # Trier les points selon la direction
            sorted_points = self._sort_points_for_u_shape(alley_points, alley, direction)
            
            # Ajouter les points
            for point_idx in sorted_points:
                # Vérifier la connectivité
                if distance_matrix[current_point, point_idx] == float('inf'):
                    intermediate = self._find_intermediate_point(current_point, point_idx,
                                                               distance_matrix)
                    if intermediate:
                        tour.append(intermediate)
                        current_point = intermediate
                
                tour.append(point_idx)
                current_point = point_idx
            
            # Changer de direction pour l'allée suivante (si alterné)
            if self.strategy == 'alternating':
                direction *= -1
        
        # Ajouter l'arrivée
        tour.append(arrival_idx)
        
        return tour
    
    def _sort_points_for_u_shape(self, point_indices: List[int], 
                               alley: str, direction: int) -> List[int]:
        """Trie les points pour un parcours U-shape"""
        if not point_indices:
            return []
        
        # Récupérer les coordonnées
        points_with_data = []
        for idx in point_indices:
            if idx < len(self.points_complets):
                point = self.points_complets[idx]
                if isinstance(point, tuple) and point in self.hangar.points:
                    x, y = self.hangar.points[point]
                    points_with_data.append((idx, x, y))
        
        if not points_with_data:
            return point_indices
        
        # Trier selon plusieurs critères
        # 1. Par coordonnée y selon le sens et la direction
        sens = self.hangar.sens.get(alley, 1)
        
        # Dans un U-shape, on peut aller dans les deux sens dans la même allée
        # Donc on trie simplement pour minimiser le chemin
        points_with_data.sort(key=lambda p: p[2])  # Trier par y
        
        # Si direction -1, inverser
        if direction == -1:
            points_with_data.reverse()
        
        return [idx for idx, _, _ in points_with_data]
    
    def _find_intermediate_point(self, from_idx: int, to_idx: int,
                               distance_matrix: np.ndarray) -> Optional[int]:
        """Trouve un point intermédiaire si besoin"""
        n = distance_matrix.shape[0]
        
        for k in range(n):
            if (k != from_idx and k != to_idx and
                distance_matrix[from_idx, k] < float('inf') and
                distance_matrix[k, to_idx] < float('inf')):
                return k
        
        return None
    
    def _solve_simple(self, distance_matrix: np.ndarray,
                     depot_idx: int, arrival_idx: int) -> Optional[Dict]:
        """Version simplifiée"""
        n_total = distance_matrix.shape[0]
        points_to_visit = list(set(range(n_total)) - {depot_idx, arrival_idx})
        
        if not points_to_visit:
            tour = [depot_idx, arrival_idx]
            distance = distance_matrix[depot_idx, arrival_idx]
            return {
                'tour': tour,
                'distance': distance,
                'time': time.time(),
                'optimal': True,
                'solver': self.name
            }
        
        # Parcours simple
        tour = [depot_idx] + points_to_visit + [arrival_idx]
        
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time(),
            'optimal': False,
            'solver': self.name
        }