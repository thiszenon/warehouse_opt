# src/algorithms/dynamic_structure_solver.py
import numpy as np
import time
import itertools
from typing import List, Dict, Optional, Tuple, Set
from .base_solver import WarehouseTSPSolver

class DynamicStructureSolver(WarehouseTSPSolver):
    """
    Algorithme DynamicStructure : version simplifiée mais fonctionnelle
    """
    
    def __init__(self, hangar=None, points_complets=None,
                 max_bruteforce_allies=8):
        """
        Args:
            hangar: Référence au hangar
            points_complets: Liste complète des points
            max_bruteforce_allies: Seuil pour force brute sur allées
        """
        name = "DynamicStructure Solver"
        super().__init__(name)
        self.hangar = hangar
        self.points_complets = points_complets
        self.max_bruteforce_allies = max_bruteforce_allies
        
        # Niveaux CARGLASS
        self.NIVEAUX = hangar.niveaux
        
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
                'optimal': False,
                'solver': self.name
            }
        
        # Si pas d'infos hangar, fallback
        if self.hangar is None or self.points_complets is None:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 1 : Grouper points par allée
        alley_points = self._group_points_by_alley(points_to_visit)
        
        if not alley_points:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 2 : Pour chaque allée, trouver les meilleurs points d'entrée/sortie
        alley_info = self._compute_alley_info(alley_points, distance_matrix)
        
        # PHASE 3 : Optimiser l'ordre des allées (DP simplifiée)
        alley_order = self._optimize_alley_order(alley_info, distance_matrix, 
                                                depot_idx, arrival_idx)
        
        if not alley_order:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 4 : Construire le tour
        tour = self._build_tour_from_order(alley_order, alley_info, 
                                          distance_matrix, depot_idx, arrival_idx)
        
        if not tour:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # Valider
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name,
            'method': 'dynamic_structure'
        }
    
    def _group_points_by_alley(self, point_indices: List[int]) -> Dict[str, List[int]]:
        """Groupe les points par allée"""
        groups = {}
        
        for idx in point_indices:
            if idx >= len(self.points_complets):
                continue
                
            point = self.points_complets[idx]
            
            # Identifier l'allée
            if isinstance(point, tuple):
                alley, _ = point
            elif hasattr(point, '__getitem__') and len(point) > 0:
                # Gestion des points spéciaux
                alley = 'SPECIAL'
            else:
                alley = 'UNKNOWN'
            
            if alley not in groups:
                groups[alley] = []
            groups[alley].append(idx)
        
        # Nettoyer : enlever groupes vides ou spéciaux
        valid_groups = {}
        for alley, points in groups.items():
            if alley not in ['SPECIAL', 'UNKNOWN'] and points:
                valid_groups[alley] = points
        
        return valid_groups
    
    def _compute_alley_info(self, alley_points: Dict[str, List[int]],
                           distance_matrix: np.ndarray) -> Dict[str, Dict]:
        """Calcule les infos pour chaque allée"""
        alley_info = {}
        
        for alley, points in alley_points.items():
            if not points:
                continue
            
            # Sens de l'allée
            sens = self.hangar.sens.get(alley, 1) if hasattr(self.hangar, 'sens') else 1
            
            # Trier points selon le sens
            sorted_points = self._sort_points_in_alley(points, alley)
            
            if not sorted_points:
                continue
            
            # Déterminer points d'entrée/sortie possibles
            entry_candidates = []
            exit_candidates = []
            
            for idx in sorted_points:
                y = self._get_y_coordinate(idx)
                if y is None:
                    continue
                
                # Points proches des niveaux
                for level_name, level_y in self.NIVEAUX.items():
                    if abs(y - level_y) <= 10:  # Tolérance 10m
                        if sens == 1 and y <= level_y:  # Montée : entrée en bas
                            entry_candidates.append((idx, level_name))
                        elif sens == -1 and y >= level_y:  # Descente : entrée en haut
                            entry_candidates.append((idx, level_name))
                        
                        if sens == 1 and y >= level_y:  # Montée : sortie en haut
                            exit_candidates.append((idx, level_name))
                        elif sens == -1 and y <= level_y:  # Descente : sortie en bas
                            exit_candidates.append((idx, level_name))
            
            # Prendre les meilleurs candidats
            entry_points = self._select_best_candidates(entry_candidates, distance_matrix)
            exit_points = self._select_best_candidates(exit_candidates, distance_matrix)
            
            # Calculer coût intra-allée
            intra_cost = 0.0
            if len(sorted_points) > 1:
                for i in range(len(sorted_points) - 1):
                    dist = distance_matrix[sorted_points[i], sorted_points[i + 1]]
                    if dist == float('inf'):
                        intra_cost = float('inf')
                        break
                    intra_cost += dist
            
            alley_info[alley] = {
                'points': sorted_points,
                'sens': sens,
                'entry_points': entry_points,  # Dict {niveau: point_idx}
                'exit_points': exit_points,    # Dict {niveau: point_idx}
                'intra_cost': intra_cost,
                'first_point': sorted_points[0],
                'last_point': sorted_points[-1]
            }
        
        return alley_info
    
    def _sort_points_in_alley(self, point_indices: List[int], alley: str) -> List[int]:
        """Trie les points selon le sens"""
        points_with_y = []
        
        for idx in point_indices:
            y = self._get_y_coordinate(idx)
            if y is not None:
                points_with_y.append((idx, y))
        
        if not points_with_y:
            return point_indices
        
        # Sens de l'allée
        sens = self.hangar.sens.get(alley, 1) if hasattr(self.hangar, 'sens') else 1
        
        # Trier
        if sens == 1:  # Montée
            points_with_y.sort(key=lambda x: x[1])
        else:  # Descente
            points_with_y.sort(key=lambda x: x[1], reverse=True)
        
        return [idx for idx, _ in points_with_y]
    
    def _get_y_coordinate(self, point_idx: int) -> Optional[float]:
        """Retourne coordonnée y"""
        if point_idx >= len(self.points_complets):
            return None
        
        point = self.points_complets[point_idx]
        
        # Si point est un tuple (alley, point_id)
        if isinstance(point, tuple):
            if hasattr(self.hangar, 'points') and point in self.hangar.points:
                return self.hangar.points[point][1]
        
        return None
    
    def _select_best_candidates(self, candidates: List[Tuple[int, str]],
                               distance_matrix: np.ndarray) -> Dict[str, int]:
        """Sélectionne le meilleur point par niveau"""
        best_by_level = {}
        
        for idx, level in candidates:
            if level not in best_by_level:
                best_by_level[level] = idx
            else:
                # Préférer les points plus accessibles (arbitraire)
                # On pourrait raffiner ici
                best_by_level[level] = idx
        
        return best_by_level
    
    def _optimize_alley_order(self, alley_info: Dict[str, Dict],
                             distance_matrix: np.ndarray,
                             depot_idx: int, arrival_idx: int) -> List[str]:
        """Optimise l'ordre des allées (DP simplifiée)"""
        alleys = list(alley_info.keys())
        
        if not alleys:
            return []
        
        if len(alleys) <= self.max_bruteforce_allies:
            # Force brute
            return self._bruteforce_alley_order(alleys, alley_info, 
                                               distance_matrix, depot_idx, arrival_idx)
        else:
            # Heuristique nearest-neighbor
            return self._nearest_neighbor_order(alleys, alley_info,
                                               distance_matrix, depot_idx, arrival_idx)
    
    def _bruteforce_alley_order(self, alleys: List[str], alley_info: Dict[str, Dict],
                               distance_matrix: np.ndarray,
                               depot_idx: int, arrival_idx: int) -> List[str]:
        """Force brute pour l'ordre des allées"""
        best_order = None
        best_cost = float('inf')
        
        for perm in itertools.permutations(alleys):
            cost = self._compute_alley_sequence_cost(perm, alley_info, 
                                                    distance_matrix, depot_idx, arrival_idx)
            
            if cost < best_cost:
                best_cost = cost
                best_order = perm
        
        return list(best_order) if best_order else alleys
    
    def _compute_alley_sequence_cost(self, alley_order: Tuple[str, ...],
                                    alley_info: Dict[str, Dict],
                                    distance_matrix: np.ndarray,
                                    depot_idx: int, arrival_idx: int) -> float:
        """Calcule coût d'une séquence d'allées"""
        total_cost = 0.0
        current_point = depot_idx
        
        for alley in alley_order:
            info = alley_info[alley]
            
            # Trouver la meilleure entrée depuis le point courant
            best_entry = None
            best_entry_cost = float('inf')
            
            for entry_level, entry_idx in info['entry_points'].items():
                cost = distance_matrix[current_point, entry_idx]
                if cost < best_entry_cost:
                    best_entry_cost = cost
                    best_entry = entry_idx
            
            if best_entry is None or best_entry_cost == float('inf'):
                return float('inf')
            
            total_cost += best_entry_cost
            
            # Coût intra-allée
            if info['intra_cost'] == float('inf'):
                return float('inf')
            total_cost += info['intra_cost']
            
            # Mettre à jour point courant (dernier point de l'allée)
            current_point = info['last_point']
        
        # Coût vers l'arrivée
        arrival_cost = distance_matrix[current_point, arrival_idx]
        if arrival_cost == float('inf'):
            return float('inf')
        
        total_cost += arrival_cost
        return total_cost
    
    def _nearest_neighbor_order(self, alleys: List[str], alley_info: Dict[str, Dict],
                               distance_matrix: np.ndarray,
                               depot_idx: int, arrival_idx: int) -> List[str]:
        """Heuristique nearest-neighbor"""
        if not alleys:
            return []
        
        ordered = []
        remaining = set(alleys)
        current_point = depot_idx
        
        while remaining:
            # Trouver l'allée la plus proche
            best_alley = None
            best_cost = float('inf')
            
            for alley in remaining:
                info = alley_info[alley]
                
                # Chercher meilleure entrée
                min_entry_cost = float('inf')
                for entry_idx in info['entry_points'].values():
                    cost = distance_matrix[current_point, entry_idx]
                    if cost < min_entry_cost:
                        min_entry_cost = cost
                
                if min_entry_cost < best_cost:
                    best_cost = min_entry_cost
                    best_alley = alley
            
            if best_alley is None:
                break
            
            ordered.append(best_alley)
            remaining.remove(best_alley)
            
            # Mettre à jour point courant
            current_point = alley_info[best_alley]['last_point']
        
        return ordered
    
    def _build_tour_from_order(self, alley_order: List[str], alley_info: Dict[str, Dict],
                              distance_matrix: np.ndarray,
                              depot_idx: int, arrival_idx: int) -> List[int]:
        """Construit le tour depuis l'ordre des allées"""
        tour = [depot_idx]
        current_point = depot_idx
        
        for alley in alley_order:
            info = alley_info[alley]
            
            # Trouver la meilleure entrée
            best_entry = None
            best_entry_cost = float('inf')
            
            for entry_idx in info['entry_points'].values():
                cost = distance_matrix[current_point, entry_idx]
                if cost < best_entry_cost:
                    best_entry_cost = cost
                    best_entry = entry_idx
            
            if best_entry is None:
                return None
            
            # Ajouter chemin vers l'entrée si nécessaire
            if best_entry != current_point:
                # Vérifier accessibilité directe
                if distance_matrix[current_point, best_entry] == float('inf'):
                    # Chercher chemin intermédiaire
                    path = self._find_path(current_point, best_entry, 
                                         distance_matrix, tour)
                    if path is None:
                        return None
                    tour.extend(path)
                    current_point = path[-1] if path else current_point
                
                if best_entry != current_point:
                    tour.append(best_entry)
                    current_point = best_entry
            
            # Ajouter tous les points de l'allée (déjà dans le bon ordre)
            for point_idx in info['points']:
                if point_idx == current_point:
                    continue
                
                # Vérifier accessibilité
                if distance_matrix[current_point, point_idx] == float('inf'):
                    path = self._find_path(current_point, point_idx,
                                         distance_matrix, tour)
                    if path is None:
                        return None
                    tour.extend(path)
                    current_point = path[-1] if path else current_point
                
                tour.append(point_idx)
                current_point = point_idx
        
        # Aller à l'arrivée
        if distance_matrix[current_point, arrival_idx] == float('inf'):
            path = self._find_path(current_point, arrival_idx,
                                 distance_matrix, tour)
            if path is None:
                return None
            tour.extend(path)
            current_point = path[-1] if path else current_point
        
        tour.append(arrival_idx)
        
        return tour
    
    def _find_path(self, from_idx: int, to_idx: int,
                  distance_matrix: np.ndarray,
                  current_tour: List[int]) -> Optional[List[int]]:
        """Trouve un chemin entre deux points"""
        n = distance_matrix.shape[0]
        
        # Essayer direct
        if distance_matrix[from_idx, to_idx] < float('inf'):
            return []
        
        # Chercher 1 intermédiaire
        for k in range(n):
            if (k != from_idx and k != to_idx and k not in current_tour and
                distance_matrix[from_idx, k] < float('inf') and
                distance_matrix[k, to_idx] < float('inf')):
                return [k]
        
        # Chercher 2 intermédiaires
        for k1 in range(n):
            if (k1 != from_idx and k1 != to_idx and k1 not in current_tour and
                distance_matrix[from_idx, k1] < float('inf')):
                for k2 in range(n):
                    if (k2 != from_idx and k2 != to_idx and k2 != k1 and
                        k2 not in current_tour and
                        distance_matrix[k1, k2] < float('inf') and
                        distance_matrix[k2, to_idx] < float('inf')):
                        return [k1, k2]
        
        return None
    
    def _fallback_solution(self, distance_matrix: np.ndarray,
                          depot_idx: int, arrival_idx: int) -> Optional[Dict]:
        """Solution de secours"""
        from .insertion import InsertionSolver
        
        solver = InsertionSolver()
        result = solver.solve(distance_matrix, depot_idx, arrival_idx)
        
        if result:
            result['solver'] = self.name + " (Insertion fallback)"
        
        return result