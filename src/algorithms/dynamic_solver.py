# src/algorithms/dynamic_structure_solver.py
import numpy as np
import time
import itertools
from typing import List, Dict, Optional, Tuple, Set
from .base_solver import WarehouseTSPSolver

class DynamicStructureSolver(WarehouseTSPSolver):
    """
    Algorithme DynamicStructure : utilise la programmation dynamique
    pour optimiser les sous-structures (allées/segments) avec contraintes
    de sens et de niveaux.
    """
    
    def __init__(self, hangar=None, points_complets=None,
                max_structures_for_bruteforce=6,
                use_heuristic_for_large_k=True):
        """
        Args:
            hangar: Référence au hangar (doit avoir .sens, .points, .niveaux)
            points_complets: Liste complète des points
            max_structures_for_bruteforce: Seuil pour force brute sur structures
            use_heuristic_for_large_k: Utiliser heuristique si beaucoup de structures
        """
        name = "DynamicStructure Solver"
        super().__init__(name)
        self.hangar = hangar
        self.points_complets = points_complets
        self.max_structures_for_bruteforce = max_structures_for_bruteforce
        self.use_heuristic_for_large_k = use_heuristic_for_large_k
        
        # Constantes pour niveaux (basé sur document Carglass)
        """self.NIVEAUX = {
            'N1': 0,     # Bas (y=0m)
            'N2': 50,    # Milieu (y=50m)
            'N3': 100    # Haut (y=100m)
        }
        """
        self.NIVEAUX = hangar.niveaux

        
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
                'optimal': False,
                'solver': self.name
            }
        
        # Si pas d'infos sur le hangar, fallback
        if self.hangar is None or self.points_complets is None:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 0 : Préparation des données
        # Regrouper points par allée et déterminer les segments
        alley_segments = self._identify_alley_segments(points_to_visit)
        
        if not alley_segments:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 1 : Déterminer les sous-structures S_i (segments d'allées)
        structures = self._build_structures(alley_segments, points_to_visit)
        
        if not structures:
            return self._fallback_solution(distance_matrix, depot_idx, arrival_idx)
        
        # PHASE 2 : Calcul des coûts internes C_i(e,x) pour chaque structure
        self._compute_internal_costs(structures, distance_matrix)
        
        # PHASE 3 : Calcul des coûts de transition T(x,e) entre structures
        self._compute_transition_costs(structures, distance_matrix)
        
        # PHASE 4 : Programmation Dynamique pour l'ordre des structures
        structure_order = self._optimize_structure_order(structures, distance_matrix, 
                                                        depot_idx, arrival_idx)
        
        if not structure_order:
            return None
        
        # PHASE 5 : Construire le tour complet
        tour = self._build_complete_tour(structures, structure_order, 
                                        distance_matrix, depot_idx, arrival_idx)
        
        if not tour:
            return None
        
        # PHASE 6 : Valider et retourner
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name,
            'structures_used': len(structure_order),
            'method': 'dynamic_structure'
        }
    
    def _identify_alley_segments(self, point_indices: List[int]) -> Dict[str, Dict]:
        """
        Identifie les segments d'allées (bas→milieu, milieu→haut)
        à partir des points à visiter.
        
        Retourne: Dict[alley_name, Dict[segment_info]]
        """
        segments = {}
        
        for idx in point_indices:
            if idx >= len(self.points_complets):
                continue
                
            point = self.points_complets[idx]
            
            if not isinstance(point, tuple):
                continue  # Ignorer points spéciaux
            
            alley, point_id = point
            
            # Obtenir coordonnées y du point
            y_coord = self._get_y_coordinate(idx)
            if y_coord is None:
                continue
            
            # Déterminer le segment basé sur le niveau
            if y_coord < 50:
                segment_name = f"{alley}_N1_N2"  # Bas → Milieu
            else:
                segment_name = f"{alley}_N2_N3"  # Milieu → Haut
            
            if segment_name not in segments:
                # Récupérer sens de l'allée
                sens = self.hangar.sens.get(alley, 1)  # +1 montée, -1 descente
                
                segments[segment_name] = {
                    'alley': alley,
                    'segment': segment_name,
                    'sens': sens,
                    'start_level': 'N1' if y_coord < 50 else 'N2',
                    'end_level': 'N2' if y_coord < 50 else 'N3',
                    'start_y': self.NIVEAUX['N1'] if y_coord < 50 else self.NIVEAUX['N2'],
                    'end_y': self.NIVEAUX['N2'] if y_coord < 50 else self.NIVEAUX['N3'],
                    'points': [],          # Indices des points
                    'entry_points': {},    # Points d'entrée par niveau
                    'exit_points': {},     # Points de sortie par niveau
                    'internal_costs': {},  # C_i(e,x) pour chaque paire (e,x)
                }
            
            segments[segment_name]['points'].append(idx)
        
        return segments
    
    def _get_y_coordinate(self, point_idx: int) -> Optional[float]:
        """Retourne la coordonnée y d'un point"""
        if point_idx >= len(self.points_complets):
            return None
        
        point = self.points_complets[point_idx]
        
        if isinstance(point, tuple) and point in self.hangar.points:
            return self.hangar.points[point][1]
        
        return None
    
    def _build_structures(self, alley_segments: Dict[str, Dict], 
                         points_to_visit: List[int]) -> List[Dict]:
        """
        Construit la liste des sous-structures S_i à partir des segments
        """
        structures = []
        
        # Convertir segments dict en liste ordonnée
        for segment_name, segment_info in alley_segments.items():
            structures.append(segment_info)
        
        # Trier les structures par position horizontale (x)
        structures.sort(key=lambda s: self._get_alley_x_position(s['alley']))
        
        return structures
    
    def _get_alley_x_position(self, alley: str) -> float:
        """Retourne la position x centrale d'une allée"""
        # Basé sur le document: x_H = 2.5m, x_G = 7.5m, etc.
        alley_positions = {
            'H': 2.5, 'G': 7.5, 'F': 12.5, 'E': 17.5,
            'D': 22.5, 'C': 27.5, 'B': 32.5, 'A': 37.5
        }
        return alley_positions.get(alley, 0.0)
    
    def _compute_internal_costs(self, structures: List[Dict], 
                               distance_matrix: np.ndarray):
        """
        Calcule C_i(e,x) = coût minimal pour visiter tous les points
        de la structure S_i, entrant par e et sortant par x.
        """
        for structure in structures:
            points = structure['points']
            if not points:
                continue
            
            # Trier les points selon le sens et la coordonnée y
            sorted_points = self._sort_points_for_structure(points, structure['sens'])
            
            if not sorted_points:
                continue
            
            # Déterminer les points d'entrée/sortie possibles
            self._identify_entry_exit_points(structure, sorted_points, distance_matrix)
            
            # Calculer les coûts internes pour chaque paire (entrée, sortie)
            self._calculate_pairwise_costs(structure, sorted_points, distance_matrix)
    
    def _sort_points_for_structure(self, point_indices: List[int], 
                                  sens: int) -> List[int]:
        """Trie les points d'une structure selon le sens"""
        points_with_y = []
        
        for idx in point_indices:
            y = self._get_y_coordinate(idx)
            if y is not None:
                points_with_y.append((idx, y))
        
        if not points_with_y:
            return point_indices
        
        # Trier selon le sens
        if sens == 1:  # Montée
            points_with_y.sort(key=lambda x: x[1])
        else:  # Descente
            points_with_y.sort(key=lambda x: x[1], reverse=True)
        
        return [idx for idx, _ in points_with_y]
    
    def _identify_entry_exit_points(self, structure: Dict, 
                                   sorted_points: List[int],
                                   distance_matrix: np.ndarray):
        """
        Identifie les points d'entrée et sortie possibles pour une structure.
        Basé sur les niveaux et le sens.
        """
        alley = structure['alley']
        sens = structure['sens']
        start_y = structure['start_y']
        end_y = structure['end_y']
        
        # Points potentiels d'entrée (les plus proches du début)
        entry_candidates = []
        for idx in sorted_points:
            y = self._get_y_coordinate(idx)
            if y is None:
                continue
            
            # Vérifier compatibilité avec sens
            if sens == 1 and y >= start_y and y <= end_y:
                entry_candidates.append(idx)
            elif sens == -1 and y <= start_y and y >= end_y:
                entry_candidates.append(idx)
        
        # Points potentiels de sortie (les plus proches de la fin)
        exit_candidates = []
        for idx in reversed(sorted_points):
            y = self._get_y_coordinate(idx)
            if y is None:
                continue
            
            # Vérifier compatibilité avec sens
            if sens == 1 and y >= start_y and y <= end_y:
                exit_candidates.append(idx)
            elif sens == -1 and y <= start_y and y >= end_y:
                exit_candidates.append(idx)
        
        # Sélectionner les meilleurs candidats (1-2 par niveau)
        structure['entry_points'] = self._select_best_entry_points(entry_candidates, 
                                                                   structure, 
                                                                   distance_matrix)
        structure['exit_points'] = self._select_best_exit_points(exit_candidates,
                                                                structure,
                                                                distance_matrix)
    
    def _select_best_entry_points(self, candidates: List[int], 
                                 structure: Dict,
                                 distance_matrix: np.ndarray) -> Dict[str, int]:
        """Sélectionne les meilleurs points d'entrée par niveau"""
        best_points = {}
        
        # Pour chaque niveau possible (N1 ou N2 selon segment)
        for level in [structure['start_level']]:
            # Filtrer candidats proches de ce niveau
            level_y = self.NIVEAUX[level]
            
            closest = None
            min_distance = float('inf')
            
            for idx in candidates:
                y = self._get_y_coordinate(idx)
                if y is None:
                    continue
                
                # Distance verticale au niveau
                vertical_dist = abs(y - level_y)
                
                # Préférer les points les plus proches du niveau
                if vertical_dist < min_distance:
                    min_distance = vertical_dist
                    closest = idx
            
            if closest is not None:
                best_points[level] = closest
        
        return best_points
    
    def _select_best_exit_points(self, candidates: List[int],
                                structure: Dict,
                                distance_matrix: np.ndarray) -> Dict[str, int]:
        """Sélectionne les meilleurs points de sortie par niveau"""
        best_points = {}
        
        # Pour chaque niveau possible (N2 ou N3 selon segment)
        for level in [structure['end_level']]:
            level_y = self.NIVEAUX[level]
            
            closest = None
            min_distance = float('inf')
            
            for idx in candidates:
                y = self._get_y_coordinate(idx)
                if y is None:
                    continue
                
                vertical_dist = abs(y - level_y)
                if vertical_dist < min_distance:
                    min_distance = vertical_dist
                    closest = idx
            
            if closest is not None:
                best_points[level] = closest
        
        return best_points
    
    def _calculate_pairwise_costs(self, structure: Dict,
                                 sorted_points: List[int],
                                 distance_matrix: np.ndarray):
        """
        Calcule C_i(e,x) pour chaque paire (entrée, sortie) possible
        """
        internal_costs = {}
        entry_points = structure['entry_points']
        exit_points = structure['exit_points']
        
        # Pour chaque niveau d'entrée possible
        for entry_level, entry_idx in entry_points.items():
            # Pour chaque niveau de sortie possible
            for exit_level, exit_idx in exit_points.items():
                
                # Vérifier contrainte de sens
                if not self._check_direction_constraint(structure, entry_level, exit_level):
                    internal_costs[(entry_level, exit_level)] = float('inf')
                    continue
                
                # Calculer coût pour parcourir tous les points de l'entrée à la sortie
                cost = self._compute_path_cost(structure, entry_idx, exit_idx, 
                                              sorted_points, distance_matrix)
                
                internal_costs[(entry_level, exit_level)] = cost
        
        structure['internal_costs'] = internal_costs
    
    def _check_direction_constraint(self, structure: Dict,
                                   entry_level: str, exit_level: str) -> bool:
        """Vérifie que le parcours respecte le sens de circulation"""
        sens = structure['sens']
        entry_y = self.NIVEAUX[entry_level]
        exit_y = self.NIVEAUX[exit_level]
        
        if sens == 1:  # Montée
            return entry_y < exit_y  # Doit monter
        else:  # Descente
            return entry_y > exit_y  # Doit descendre
    
    def _compute_path_cost(self, structure: Dict, entry_idx: int, exit_idx: int,
                          sorted_points: List[int], 
                          distance_matrix: np.ndarray) -> float:
        """
        Calcule le coût pour visiter tous les points de la structure
        de l'entrée à la sortie.
        """
        # Trouver les indices dans la liste triée
        try:
            entry_pos = sorted_points.index(entry_idx)
            exit_pos = sorted_points.index(exit_idx)
        except ValueError:
            return float('inf')
        
        # S'assurer que entry_pos < exit_pos pour le sens
        if structure['sens'] == 1:  # Montée
            if entry_pos > exit_pos:
                return float('inf')
            # Parcourir dans l'ordre
            sub_points = sorted_points[entry_pos:exit_pos + 1]
        else:  # Descente
            if entry_pos < exit_pos:
                return float('inf')
            # Parcourir dans l'ordre inverse
            sub_points = sorted_points[exit_pos:entry_pos + 1]
            sub_points = list(reversed(sub_points))
        
        # Calculer la distance
        total_cost = 0.0
        for i in range(len(sub_points) - 1):
            dist = distance_matrix[sub_points[i], sub_points[i + 1]]
            if dist == float('inf'):
                return float('inf')
            total_cost += dist
        
        return total_cost
    
    def _compute_transition_costs(self, structures: List[Dict],
                                 distance_matrix: np.ndarray):
        """
        Calcule T(x,e) = coût de transition entre sortie x de S_i
        et entrée e de S_{i+1}.
        """
        # Initialiser les coûts de transition
        for i, structure in enumerate(structures):
            structure['transition_costs'] = {}
        
        # Pour chaque paire de structures consécutives
        for i in range(len(structures) - 1):
            struct_i = structures[i]
            struct_j = structures[i + 1]
            
            # Pour chaque niveau de sortie de S_i
            for exit_level_i, exit_idx_i in struct_i['exit_points'].items():
                # Pour chaque niveau d'entrée de S_j
                for entry_level_j, entry_idx_j in struct_j['entry_points'].items():
                    
                    # Vérifier que les niveaux sont identiques (changement au même niveau)
                    if exit_level_i != entry_level_j:
                        struct_i['transition_costs'][(exit_level_i, entry_level_j)] = float('inf')
                        continue
                    
                    # Distance entre les points de sortie et d'entrée
                    dist = distance_matrix[exit_idx_i, entry_idx_j]
                    
                    # Ajouter coût de déplacement horizontal si nécessaire
                    if dist < float('inf'):
                        # Distance horizontale entre allées
                        x_i = self._get_alley_x_position(struct_i['alley'])
                        x_j = self._get_alley_x_position(struct_j['alley'])
                        horizontal_dist = abs(x_j - x_i)
                        
                        # Le coût de transition inclut le déplacement horizontal
                        struct_i['transition_costs'][(exit_level_i, entry_level_j)] = dist
                    else:
                        struct_i['transition_costs'][(exit_level_i, entry_level_j)] = float('inf')
    
    def _optimize_structure_order(self, structures: List[Dict],
                                 distance_matrix: np.ndarray,
                                 depot_idx: int, arrival_idx: int) -> List[int]:
        """
        Programme dynamique pour trouver l'ordre optimal des structures.
        Retourne la liste des indices des structures dans l'ordre optimal.
        """
        n = len(structures)
        
        if n == 1:
            return [0]
        
        if n <= self.max_structures_for_bruteforce:
            # Force brute pour petit nombre de structures
            return self._bruteforce_structure_order(structures, distance_matrix, 
                                                   depot_idx, arrival_idx)
        else:
            # Heuristique pour grand nombre de structures
            return self._heuristic_structure_order(structures, distance_matrix,
                                                  depot_idx, arrival_idx)
    
    def _bruteforce_structure_order(self, structures: List[Dict],
                                   distance_matrix: np.ndarray,
                                   depot_idx: int, arrival_idx: int) -> List[int]:
        """Force brute pour l'ordre des structures"""
        n = len(structures)
        best_order = None
        best_cost = float('inf')
        
        # Tester toutes les permutations
        for perm in itertools.permutations(range(n)):
            cost = self._compute_order_cost(structures, perm, distance_matrix,
                                           depot_idx, arrival_idx)
            
            if cost < best_cost:
                best_cost = cost
                best_order = perm
        
        return list(best_order) if best_order else list(range(n))
    
    def _compute_order_cost(self, structures: List[Dict], order: Tuple[int, ...],
                           distance_matrix: np.ndarray,
                           depot_idx: int, arrival_idx: int) -> float:
        """Calcule le coût d'un ordre spécifique de structures"""
        total_cost = 0.0
        
        # État DP: (structure_idx, niveau_sortie) -> coût
        dp = [{} for _ in range(len(order))]
        
        # Initialisation: depuis le dépôt vers la première structure
        first_struct = structures[order[0]]
        
        for exit_level, exit_idx in first_struct['exit_points'].items():
            # Chercher la meilleure entrée pour cette sortie
            min_entry_cost = float('inf')
            
            for entry_level, entry_idx in first_struct['entry_points'].items():
                # Coût: dépôt → entrée + coût interne
                entry_cost = distance_matrix[depot_idx, entry_idx]
                if entry_cost == float('inf'):
                    continue
                
                internal_cost = first_struct['internal_costs'].get((entry_level, exit_level), 
                                                                   float('inf'))
                if internal_cost == float('inf'):
                    continue
                
                cost = entry_cost + internal_cost
                if cost < min_entry_cost:
                    min_entry_cost = cost
            
            if min_entry_cost < float('inf'):
                dp[0][exit_level] = min_entry_cost
        
        if not dp[0]:
            return float('inf')
        
        # Récursion: pour les structures suivantes
        for i in range(1, len(order)):
            prev_struct = structures[order[i - 1]]
            curr_struct = structures[order[i]]
            
            dp[i] = {}
            
            # Pour chaque niveau de sortie de la structure courante
            for curr_exit_level, curr_exit_idx in curr_struct['exit_points'].items():
                min_cost = float('inf')
                
                # Pour chaque niveau de sortie de la structure précédente
                for prev_exit_level, prev_cost in dp[i - 1].items():
                    # Coût de transition
                    transition_key = (prev_exit_level, '?')  # On cherche l'entrée correspondante
                    transition_cost = float('inf')
                    
                    # Chercher la meilleure entrée pour cette transition
                    for entry_level, entry_idx in curr_struct['entry_points'].items():
                        if prev_exit_level != entry_level:
                            continue
                        
                        trans_dist = distance_matrix[prev_struct['exit_points'][prev_exit_level], 
                                                     entry_idx]
                        if trans_dist == float('inf'):
                            continue
                        
                        # Coût interne pour cette entrée/sortie
                        internal_cost = curr_struct['internal_costs'].get((entry_level, curr_exit_level),
                                                                          float('inf'))
                        if internal_cost == float('inf'):
                            continue
                        
                        total = prev_cost + trans_dist + internal_cost
                        if total < min_cost:
                            min_cost = total
                
                if min_cost < float('inf'):
                    dp[i][curr_exit_level] = min_cost
        
        if not dp[-1]:
            return float('inf')
        
        # Coût final: vers l'arrivée
        final_cost = float('inf')
        last_struct = structures[order[-1]]
        
        for exit_level, exit_cost in dp[-1].items():
            exit_idx = last_struct['exit_points'][exit_level]
            arrival_cost = distance_matrix[exit_idx, arrival_idx]
            
            if arrival_cost < float('inf'):
                total = exit_cost + arrival_cost
                if total < final_cost:
                    final_cost = total
        
        return final_cost
    
    def _heuristic_structure_order(self, structures: List[Dict],
                                  distance_matrix: np.ndarray,
                                  depot_idx: int, arrival_idx: int) -> List[int]:
        """Heuristique nearest-neighbor pour l'ordre des structures"""
        n = len(structures)
        ordered = []
        remaining = set(range(n))
        
        # Sélectionner la structure la plus proche du dépôt
        current_point = depot_idx
        current_level = 'N2'  # Niveau de départ arbitraire
        
        while remaining:
            best_struct = None
            best_cost = float('inf')
            
            for struct_idx in remaining:
                struct = structures[struct_idx]
                
                # Chercher la meilleure entrée pour cette structure
                for entry_level, entry_idx in struct['entry_points'].items():
                    # Vérifier accessibilité depuis le point courant
                    if distance_matrix[current_point, entry_idx] == float('inf'):
                        continue
                    
                    # Vérifier compatibilité des niveaux
                    if current_level != entry_level:
                        continue
                    
                    # Coût approximatif: aller à l'entrée + coût interne minimal
                    entry_cost = distance_matrix[current_point, entry_idx]
                    
                    # Chercher le coût interne minimal pour cette structure
                    min_internal = min(struct['internal_costs'].values(), 
                                      default=float('inf'))
                    
                    if min_internal == float('inf'):
                        continue
                    
                    total = entry_cost + min_internal
                    
                    if total < best_cost:
                        best_cost = total
                        best_struct = struct_idx
            
            if best_struct is None:
                # Fallback: ordre naturel
                ordered = list(remaining)
                break
            
            ordered.append(best_struct)
            remaining.remove(best_struct)
            
            # Mettre à jour point courant (approximatif)
            # On utilise la sortie "moyenne" de la structure
            struct = structures[best_struct]
            if struct['exit_points']:
                # Prendre la première sortie disponible
                for exit_idx in struct['exit_points'].values():
                    current_point = exit_idx
                    break
        
        return ordered
    
    def _build_complete_tour(self, structures: List[Dict], 
                           structure_order: List[int],
                           distance_matrix: np.ndarray,
                           depot_idx: int, arrival_idx: int) -> List[int]:
        """
        Construit le tour complet en suivant l'ordre optimal des structures
        et en reconstruisant les chemins optimaux.
        """
        # Pour simplifier, on utilise une approche gloutonne
        # Une implémentation complète reconstruirait le chemin DP
        
        tour = [depot_idx]
        current_point = depot_idx
        
        # Parcourir les structures dans l'ordre
        for struct_idx in structure_order:
            struct = structures[struct_idx]
            
            # Trouver la meilleure entrée depuis le point courant
            best_entry = None
            best_entry_cost = float('inf')
            
            for entry_level, entry_idx in struct['entry_points'].items():
                cost = distance_matrix[current_point, entry_idx]
                if cost < best_entry_cost:
                    best_entry_cost = cost
                    best_entry = (entry_level, entry_idx)
            
            if best_entry is None or best_entry_cost == float('inf'):
                # Chercher un chemin alternatif
                entry_candidates = list(struct['entry_points'].values())
                intermediate = self._find_path_to_any(current_point, entry_candidates,
                                                     distance_matrix, tour)
                if intermediate is None:
                    return None
                
                tour.extend(intermediate)
                current_point = intermediate[-1] if intermediate else current_point
                
                # Réessayer
                for entry_level, entry_idx in struct['entry_points'].items():
                    if entry_idx == current_point:
                        best_entry = (entry_level, entry_idx)
                        break
            
            if best_entry is None:
                return None
            
            entry_level, entry_idx = best_entry
            
            # Ajouter l'entrée si nécessaire
            if entry_idx != current_point:
                tour.append(entry_idx)
                current_point = entry_idx
            
            # Visiter les points de la structure dans l'ordre
            sorted_points = self._sort_points_for_structure(struct['points'], struct['sens'])
            
            for point_idx in sorted_points:
                if point_idx == current_point:
                    continue
                
                # Vérifier accessibilité
                if distance_matrix[current_point, point_idx] == float('inf'):
                    intermediate = self._find_intermediate_path(current_point, point_idx,
                                                               distance_matrix, tour)
                    if intermediate is None:
                        return None
                    
                    tour.extend(intermediate)
                    current_point = intermediate[-1] if intermediate else current_point
                
                tour.append(point_idx)
                current_point = point_idx
        
        # Aller à l'arrivée
        if distance_matrix[current_point, arrival_idx] == float('inf'):
            intermediate = self._find_intermediate_path(current_point, arrival_idx,
                                                       distance_matrix, tour)
            if intermediate is None:
                return None
            
            tour.extend(intermediate)
            current_point = intermediate[-1] if intermediate else current_point
        
        tour.append(arrival_idx)
        
        return tour
    
    def _find_path_to_any(self, from_idx: int, to_indices: List[int],
                         distance_matrix: np.ndarray,
                         current_tour: List[int]) -> Optional[List[int]]:
        """Trouve un chemin vers n'importe lequel des points cibles"""
        n = distance_matrix.shape[0]
        
        for to_idx in to_indices:
            # Essayer direct
            if distance_matrix[from_idx, to_idx] < float('inf'):
                return [] if to_idx in current_tour else [to_idx]
            
            # Chercher avec 1 intermédiaire
            for k in range(n):
                if (k != from_idx and k != to_idx and k not in current_tour and
                    distance_matrix[from_idx, k] < float('inf') and
                    distance_matrix[k, to_idx] < float('inf')):
                    return [k, to_idx]
        
        return None
    
    def _find_intermediate_path(self, from_idx: int, to_idx: int,
                               distance_matrix: np.ndarray,
                               current_tour: List[int]) -> Optional[List[int]]:
        """Trouve un chemin alternatif entre deux points"""
        n = distance_matrix.shape[0]
        
        # Chercher un seul point intermédiaire
        for k in range(n):
            if (k != from_idx and k != to_idx and k not in current_tour and
                distance_matrix[from_idx, k] < float('inf') and
                distance_matrix[k, to_idx] < float('inf')):
                return [k]
        
        # Chercher deux points intermédiaires
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
        # Essayer AlleyFirst comme fallback
        try:
            from .alley_first_solver import AlleyFirstSolver
            solver = AlleyFirstSolver(self.hangar, self.points_complets)
            result = solver.solve(distance_matrix, depot_idx, arrival_idx)
            if result:
                result['solver'] = self.name + " (AlleyFirst fallback)"
                return result
        except:
            pass
        
        # Fallback simple
        from .insertion import InsertionSolver
        solver = InsertionSolver()
        result = solver.solve(distance_matrix, depot_idx, arrival_idx)
        
        if result:
            result['solver'] = self.name + " (Insertion fallback)"
        
        return result