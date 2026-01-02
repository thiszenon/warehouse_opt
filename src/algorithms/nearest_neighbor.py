
# src/algorithms/depot_nearest_neighbor.py
import numpy as np
import time
from .base_solver import WarehouseTSPSolver

class NearestNeighborSolver(WarehouseTSPSolver):
    """Plus Proche Voisin adapté pour le problème avec dépôt/arrivée"""
    
    def __init__(self, start_at_nearest=True):
        """
        Args:
            start_at_nearest: Si True, commence au point le plus proche du dépôt
                            Si False, commence par visiter dans l'ordre
        """
        name = "Depot Nearest Neighbor"
        if not start_at_nearest:
            name += " (ordre fixe)"
        super().__init__(name)
        self.start_at_nearest = start_at_nearest
    
    def solve(self, distance_matrix, depot_idx=0, arrival_idx=None):
        start_time = time.time()
        
        n_total = distance_matrix.shape[0]
        
        # Déterminer l'index d'arrivée
        if arrival_idx is None:
            arrival_idx = depot_idx
        
        # Points à visiter (exclure dépôt et arrivée)
        points_to_visit = set(range(n_total))
        points_to_visit.discard(depot_idx)
        if arrival_idx != depot_idx:
            points_to_visit.discard(arrival_idx)
        
        # Initialiser le tour
        tour = [depot_idx]
        current = depot_idx
        
        # Choisir le premier point
        if self.start_at_nearest and points_to_visit:
            # Trouver le point le plus proche du dépôt
            nearest = min(points_to_visit, 
                        key=lambda x: distance_matrix[depot_idx, x])
            tour.append(nearest)
            points_to_visit.remove(nearest)
            current = nearest
        
        # Visiter les points restants avec nearest neighbor
        while points_to_visit:
            # Trouver le point non-visité le plus proche
            min_dist = float('inf')
            next_point = -1
            
            for point in points_to_visit:
                dist = distance_matrix[current, point]
                if dist < min_dist:
                    min_dist = dist
                    next_point = point
            
            if next_point == -1 or min_dist == float('inf'):
                # Aucun point accessible
                return None
            
            # Ajouter au tour
            tour.append(next_point)
            points_to_visit.remove(next_point)
            current = next_point
        
        # Ajouter l'arrivée
        tour.append(arrival_idx)
        
        # Valider la solution
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        # Calculer la distance
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name
        }