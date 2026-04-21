# src/algorithms/s_shape_solver.py
import numpy as np
import time
from .base_solver import WarehouseTSPSolver
from typing import List, Dict, Optional

class SShapeSolver(WarehouseTSPSolver):
    """
    Parcours en S-shape (serpent) adapté aux contraintes du hangar.
    Visite chaque allée complètement avant de passer à la suivante.
    """
    
    def __init__(self, hangar=None, commande=None, points_complets=None,
                 start_from='left', transition_level='optimal'):
        """
        Args:
            hangar: Référence au hangar
            commande: Liste des points de collecte
            points_complets: Liste complète des points
            start_from: 'left' (allée H) ou 'right' (allée A)
            transition_level: 'N1' (bas), 'N2' (milieu), 'N3' (haut), 'optimal' (choix auto)
        """
        name = f"S-Shape ({start_from}, {transition_level})"
        super().__init__(name)
        self.hangar = hangar
        self.commande = commande
        self.points_complets = points_complets
        self.start_from = start_from
        self.transition_level = transition_level
        
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
                'optimal': True,
                'solver': self.name
            }
        
        # Si pas d'infos sur le hangar, utiliser une version simplifiée
        if self.hangar is None or self.points_complets is None:
            return self._solve_simple(distance_matrix, depot_idx, arrival_idx)
        
        # 1. Grouper les points par allée
        points_by_alley = self._group_points_by_alley(points_to_visit)
        
        # 2. Déterminer l'ordre des allées (serpent)
        alley_order = self._get_alley_order()
        
        # 3. Construire le parcours S-shape
        tour = self._build_s_shape_tour(points_by_alley, alley_order, 
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
            
            # Identifier l'allée
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
    
    def _get_alley_order(self) -> List[str]:
        """Détermine l'ordre de visite des allées (serpent)"""
        # Allées principales (H à A)
        main_alleys = ['H', 'G', 'F', 'E', 'D', 'C', 'B', 'A']
        
        # Allées spéciales
        special_alleys = ['BB', 'CC', 'DD', 'EE', 'FF', 'GG', 'HH', 'AA']
        
        # Toutes les allées disponibles dans le hangar
        available_alleys = []
        for alley in main_alleys + special_alleys:
            if alley in self.hangar.allees_toutes:
                available_alleys.append(alley)
        
        # Ordonner selon le type de parcours
        if self.start_from == 'left':
            # De gauche à droite
            return available_alleys
        else:
            # De droite à gauche
            return list(reversed(available_alleys))
    
    def _build_s_shape_tour(self, points_by_alley: Dict[str, List[int]],
                          alley_order: List[str],
                          depot_idx: int, arrival_idx: int,
                          distance_matrix: np.ndarray) -> List[int]:
        """Construit le parcours en S-shape"""
        tour = [depot_idx]
        current_point = depot_idx
        
        for i, alley in enumerate(alley_order):
            if alley not in points_by_alley or not points_by_alley[alley]:
                continue
            
            # Points de cette allée
            alley_points = points_by_alley[alley]
            
            # Trier les points selon le sens de circulation
            sorted_points = self._sort_points_in_alley(alley_points, alley)
            
            # Ajouter les points au tour
            for point_idx in sorted_points:
                # Vérifier si l'arc est possible
                if distance_matrix[current_point, point_idx] == float('inf'):
                    # Essayer de trouver un chemin indirect
                    intermediate = self._find_intermediate_point(current_point, point_idx, 
                                                               distance_matrix)
                    if intermediate:
                        tour.append(intermediate)
                        current_point = intermediate
                
                tour.append(point_idx)
                current_point = point_idx
        
        # Ajouter l'arrivée
        tour.append(arrival_idx)
        
        return tour
    
    def _sort_points_in_alley(self, point_indices: List[int], alley: str) -> List[int]:
        """Trie les points dans une allée selon le sens de circulation"""
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
        
        # Trier selon le sens
        sens = self.hangar.sens[alley]
        
        # Montée : du bas vers le haut (y croissant)
        # Descente : du haut vers le bas (y décroissant)
        if sens == 1:  # Montée
            points_with_y.sort(key=lambda x: x[1])
        else:  # Descente
            points_with_y.sort(key=lambda x: x[1], reverse=True)
        
        return [idx for idx, _ in points_with_y]
    
    def _find_intermediate_point(self, from_idx: int, to_idx: int,
                               distance_matrix: np.ndarray) -> Optional[int]:
        """Trouve un point intermédiaire si l'arc direct est impossible"""
        n = distance_matrix.shape[0]
        
        # Chercher un point intermédiaire qui connecte les deux
        for k in range(n):
            if (k != from_idx and k != to_idx and
                distance_matrix[from_idx, k] < float('inf') and
                distance_matrix[k, to_idx] < float('inf')):
                return k
        
        return None
    
    def _solve_simple(self, distance_matrix: np.ndarray,
                     depot_idx: int, arrival_idx: int) -> Optional[Dict]:
        """Version simplifiée sans info sur le hangar"""
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
        
        # Parcours simple : dépôt → points dans l'ordre → arrivée
        tour = [depot_idx] + points_to_visit + [arrival_idx]
        
        # Valider
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