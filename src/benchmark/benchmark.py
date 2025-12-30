
import time
from algorithms.exact_solver import solve_exact
from algorithms.heuristic import nearest_neighbor, random_insertion

class Benchmarker:
    def __init__(self):
        self.results = []

    def run_single(self, graphe):
        """Teste tous les algorithmes sur un graphe"""
        result = {
            'n_points': graphe.n,
            'faisable': graphe.est_faisable()
        }
        if not result['faisable']:
            return result

        #1. Solution exacte (si un petit graphe)
        if graphe.n <= 8:
            start = time.time()
            exact = solve_exact(graphe)
            result['exact'] = {
                'solution': exact['tour'] if exact else None,
                'distance': exact['distance'] if exact else None,
                'time': time.time() - start
            }
        #2. Plus proche voisin
        start = time.time()
        nearest_n = nearest_neighbor(graphe)
        result['nearest_neighbor'] = {
            'solution': nearest_n['tour'] if nearest_n else None,
            'distance': nearest_n['distance'] if nearest_n else None,
            'time': time.time() - start,
            'gap': self._calculate_gap(result.get('exact', {}).get('distance'), nearest_n['distance'] if nearest_n else None)
        }

        #3. Insertion  aléatoire
        start = time.time()
        random_i = random_insertion(graphe)
        result['random_insertion'] = {
            'solution': random_i['tour'] if random_i else None,
            'distance': random_i['distance'] if random_i else None,
            'time': time.time() - start,
            'gap': self._calculate_gap(result.get('exact', {}).get('distance'), random_i['distance'] if random_i else None)
        }

        return result
    
    def _calculate_gap(self, optimal, heuristic):
        """Calcule le pourcentage d'écart à l'optimal"""
        if optimal is None or heuristic is None:
            return None
        return ((heuristic - optimal)/optimal)*100
    