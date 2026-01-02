# src/algorithms/depot_two_opt.py
import numpy as np
import time
from .base_solver import WarehouseTSPSolver
from .nearest_neighbor import NearestNeighborSolver

class TwoOptSolver(WarehouseTSPSolver):
    """Recherche locale 2-Opt adaptée pour le problème avec dépôt/arrivée"""
    
    def __init__(self, initial_solver=None, max_iterations=1000):
        """
        Args:
            initial_solver: Solveur pour la solution initiale
            max_iterations: Nombre maximum d'itérations 2-opt
        """
        super().__init__("Depot Two-Opt")
        self.initial_solver = initial_solver or NearestNeighborSolver()
        self.max_iterations = max_iterations
    
    def solve(self, distance_matrix, depot_idx=0, arrival_idx=None):
        start_time = time.time()
        
        # Obtenir une solution initiale
        initial_result = self.initial_solver.solve(
            distance_matrix, depot_idx, arrival_idx
        )
        
        if not initial_result:
            return None
        
        tour = initial_result['tour'].copy()
        best_distance = initial_result['distance']
        initial_distance = best_distance
        
        improved = True
        iterations = 0
        
        # Indices qui peuvent être échangés (exclure dépôt et arrivée)
        start_idx = 1  # Après le dépôt
        end_idx = len(tour) - 2  # Avant l'arrivée
        
        while improved and iterations < self.max_iterations:
            improved = False
            iterations += 1
            
            for i in range(start_idx, end_idx - 1):
                for j in range(i + 1, end_idx + 1):
                    # Évaluer l'échange 2-opt
                    a, b = tour[i-1], tour[i]
                    c, d = tour[j], tour[(j+1) % len(tour)]
                    
                    # Vérifier que nous n'échangeons pas avec l'arrivée
                    if d == arrival_idx and j + 1 >= len(tour) - 1:
                        continue
                    
                    current_cost = distance_matrix[a, b] + distance_matrix[c, d]
                    new_cost = distance_matrix[a, c] + distance_matrix[b, d]
                    
                    if new_cost < current_cost - 1e-6:  # Marge numérique
                        # Effectuer l'échange (inverser la section)
                        tour[i:j+1] = reversed(tour[i:j+1])
                        best_distance = best_distance - current_cost + new_cost
                        improved = True
                        break
                
                if improved:
                    break
        
        # Recalculer la distance pour vérification
        final_distance = self.calculate_tour_distance(tour, distance_matrix)
        
        # Valider
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        improvement = 0
        if initial_distance > 0:
            improvement = ((initial_distance - final_distance) / initial_distance) * 100
        
        return {
            'tour': tour,
            'distance': final_distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name,
            'initial_distance': initial_distance,
            'improvement_pct': improvement,
            'iterations': iterations
        }