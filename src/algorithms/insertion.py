import numpy as np
import time
import random
from .base_solver import WarehouseTSPSolver

class InsertionSolver(WarehouseTSPSolver):
    """Insertion heuristique adaptée pour le problème avec dépôt/arrivée"""
    
    def __init__(self, seed=None, insertion_strategy='cheapest'):
        """
        Args:
            seed: Seed pour la reproductibilité
            insertion_strategy: 'cheapest' ou 'farthest'
        """
        name = f"Depot Insertion ({insertion_strategy})"
        super().__init__(name)
        self.seed = seed
        self.insertion_strategy = insertion_strategy
        if seed is not None:
            random.seed(seed)
    
    def solve(self, distance_matrix, depot_idx=0, arrival_idx=None):
        start_time = time.time()
        
        n_total = distance_matrix.shape[0]
        
        if arrival_idx is None:
            arrival_idx = depot_idx 
        
        # Points à visiter
        points_to_visit = list(set(range(n_total)) - {depot_idx, arrival_idx})
        
        if not points_to_visit:
            # Cas trivial: dépôt → arrivée
            tour = [depot_idx, arrival_idx]
            distance = distance_matrix[depot_idx, arrival_idx]
            
            return {
                'tour': tour,
                'distance': distance,
                'time': time.time() - start_time,
                'optimal': True,
                'solver': self.name
            }
        
        # Stratégie de sélection initiale
        if self.insertion_strategy == 'farthest':
            # Commencer par les points les plus éloignés
            points_to_visit.sort(
                key=lambda x: distance_matrix[depot_idx, x] + distance_matrix[x, arrival_idx],
                reverse=True
            )
        else:
            # Mélanger aléatoirement
            random.shuffle(points_to_visit)
        
        # Initialiser avec dépôt → premier point → arrivée
        tour = [depot_idx, points_to_visit[0], arrival_idx]
        inserted = {points_to_visit[0]}
        
        # Insérer les points restants
        for point in points_to_visit[1:]:
            best_position = -1
            best_cost_increase = float('inf')
            
            # Essayer toutes les positions d'insertion possibles
            for i in range(1, len(tour) - 1):
                # Coût d'insertion entre tour[i-1] et tour[i]
                prev = tour[i-1]
                next_node = tour[i]
                
                current_cost = distance_matrix[prev, next_node]
                new_cost = (distance_matrix[prev, point] + 
                        distance_matrix[point, next_node])
                
                cost_increase = new_cost - current_cost
                
                if cost_increase < best_cost_increase:
                    best_cost_increase = cost_increase
                    best_position = i
            
            # Insérer à la meilleure position
            tour.insert(best_position, point)
            inserted.add(point)
        
        # Vérifier que tous les points ont été insérés
        if len(inserted) != len(points_to_visit):
            return None
        
        # Valider
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