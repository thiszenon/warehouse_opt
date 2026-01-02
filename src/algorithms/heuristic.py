import time
import random
from .base_solver import BaseSolver
from typing import Dict

class NearestNeighborSolver(BaseSolver):
    """Plus proche voisin"""

    def __init__(self, start_idx=0):
        super().__init__(f"Nearest Neighbor (start={start_idx})")
        self.start_idx = start_idx

    def solve(self, graph) -> Dict:
        start_time = time.time()
        n = graph.n
        visited = [False]*n
        tour = [self.start_idx]
        visited[self.start_idx] = True
        for _ in range(n-1):
            current  = tour[-1]

            # Trouver le plus proche non visité
            candidates = []
            for j in range(n):
                if not visited[j] and graph.matrice[current][j] < float('inf'):
                    candidates.append((j, graph.matrice[current][j]))
            if not candidates:
                return None #bloqué
            
            next_point, _ = min(candidates, key=lambda x:x[1])
            tour.append(next_point)
            visited[next_point]=True

        #verifier retour au depart
        if graph.matrice[tour[-1]][tour[0]] < float('inf'):
            tour.append(tour[0]) # fermer le cycle
            distance = sum(graph.matrice[tour[i]][tour[i+1]] for i in range(n))

            return {
                'tour_indices': tour,
                'tour_points': [graph.commande[i] for i in tour],
                'distance':distance,
                'time': time.time() - start_time
            }
        return None
    #end solve

class RandomInsertionSolver(BaseSolver):
    """Insertion aléatoire"""

    def __init__(self,seed=None):
        super().__init__("Random Insertion")
        self.seed = seed
        if seed is not None:
            random.seed(seed)
    
    def solve(self,graph) -> Dict:
        start_time = time.time()
        n = graph.n
        unvisited = list(range(n))
        random.shuffle(unvisited)

        tour = [unvisited.pop()]
        while unvisited:
            best_pos = -1
            best_increase = float('inf')
            point_to_insert = unvisited.pop()

            # Trouver la meilleure position d'insertion
            for i in range(len(tour)):
                #cout d'insertion entre tour[i] et tour[i+1]
                if i==len(tour) -1:
                    #insertion à la fin
                    cost = (graph.matrice[tour[i]][point_to_insert] + graph.matrice[point_to_insert][tour[0]])
                else:
                    cost = (graph.matrice[tour[i]][point_to_insert] +
                            graph.matrice[point_to_insert][tour[i+1]] - 
                            graph.matrice[tour[i]][tour[i+1]])
                if cost < best_increase:
                    best_increase = cost
                    best_pos = i
            #Inserer à la meilleure position
            if best_pos == len(tour)-1:
                tour.append(point_to_insert)
            else:
                tour.insert(best_pos +1, point_to_insert)
        #fermer le cycle
        tour.append(tour[0])
        distance = sum(graph.matrice[tour[i]][tour[i+1]] for i in range(n))

        return {
            'tour_indice': tour,
            'tour_points': [graph.commande[i] for i in tour],
            'distance': distance,
            'optimal': False,
            'time': time.time() - start_time
        }
    
    