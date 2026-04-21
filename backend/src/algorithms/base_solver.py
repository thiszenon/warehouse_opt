# src/algorithms/base_solver.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
import numpy as np
import time

class WarehouseTSPSolver(ABC):
    """
    Classe de base abstraite pour les solveurs du problème de collecte.
    
    Problème spécifique : 
    - DÉPÔT → Points de collecte → ARRIVÉE
    - DÉPÔT et ARRIVÉE peuvent être le même point
    - Tous les points de collecte doivent être visités exactement une fois
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def solve(self, distance_matrix: np.ndarray, 
            depot_idx: int = 0,
            arrival_idx: Optional[int] = None) -> Dict:
        """
        Résout le problème de collecte.
        
        Args:
            distance_matrix: Matrice (n x n) des distances
            depot_idx: Index du point de départ (dépôt)
            arrival_idx: Index du point d'arrivée (None = même que dépôt)
            
        Returns:
            Dict avec:
                - 'tour': liste des indices visités
                - 'distance': distance totale
                - 'time': temps d'exécution
                - 'optimal': booléen indiquant si la solution est optimale
        """
        pass
    
    def validate_solution(self, tour: List[int], 
                        distance_matrix: np.ndarray,
                        depot_idx: int,
                        arrival_idx: Optional[int]) -> bool:
        """
        Valide qu'une solution est correcte.
        """
        if not tour:
            return False
        
        n_total = distance_matrix.shape[0]
        
        # 1. Doit commencer au dépôt
        if tour[0] != depot_idx:
            return False
        
        # 2. Doit finir à l'arrivée
        expected_end = arrival_idx if arrival_idx is not None else depot_idx
        if tour[-1] != expected_end:
            return False
        
        # 3. Doit visiter tous les points (sauf dépôt/arrivée)
        points_to_visit = set(range(n_total))
        points_to_visit.discard(depot_idx)
        if arrival_idx is not None and arrival_idx != depot_idx:
            points_to_visit.discard(arrival_idx)
        
        visited = set(tour[1:-1])  # Exclure début et fin
        if points_to_visit != visited:
            return False
        
        # 4. Tous les arcs doivent exister (distance < inf)
        total_distance = 0
        for i in range(len(tour) - 1):
            dist = distance_matrix[tour[i], tour[i+1]]
            if dist == float('inf'):
                return False
            total_distance += dist
        
        return True
    
    def calculate_tour_distance(self, tour: List[int], 
                            distance_matrix: np.ndarray) -> float:
        """Calcule la distance totale d'un tour"""
        total = 0
        for i in range(len(tour) - 1):
            total += distance_matrix[tour[i], tour[i+1]]
        return total