import numpy as np
import time
from .base_solver import WarehouseTSPSolver
from typing import List, Dict, Optional, Tuple

from .rob_s_shape import RobustSShapeSolver
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