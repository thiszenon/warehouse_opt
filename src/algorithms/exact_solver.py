#NOTE: Cet Algorithme ne respecte pas la structure geometrique et les contraintes du Hangar
import time
import itertools
from .base_solver import BaseSolver
from typing import List, Dict

class ExactSolver(BaseSolver):
    """solution exacte par recherche exhaustive"""

    def __init__(self, timeout=30):
        super().__init__("Exact Exhaustive")
        self.timeout = timeout

    def solve(self, graph) -> Dict:
        """utilisable pour n < 9"""
        if graph.n > 8:
            print(f" Trop de points ({graph.n}) pour la recherche exhaustive")
            return None
        n = graph.n
        best_tour = None
        best_dist = float('inf')
        start_time = time.time()
        #fixer le point 0 comme depart
        for perm in itertools.permutations(range(1,n)):
            if time.time() - start_time > self.timeout:
                print(f"Timeout apres {self.timeout} secondes")
                break
            tour  =[0] + list(perm) + [0] #cycle complet
            #calculer distance
            dist=0
            valid = True
            for i in range(n):
                d= graph.matrice[tour[i]][tour[i+1]]
                if d == float('inf'):
                    valid =False
                    break
                dist+=d

            if valid and dist < best_dist:
                best_dist = dist
                best_tour = tour
            if best_tour:
                return {
                    'tour_indices': best_tour,
                    'tour_points': [graph.commande[i] for i in best_tour],
                    'distance': best_dist,
                    'optimal': True,
                    'time': time.time() - start_time
                }
            return None

