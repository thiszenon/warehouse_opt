
import numpy as np
import time
import random
from .base_solver import WarehouseTSPSolver
from typing import List, Tuple, Dict, Optional

class StructuralInsertionSolver(WarehouseTSPSolver):
    """
    Insertion heuristique exploitant la structure géométrique du hangar
    selon la modélisation mathématique (Théorèmes 0.8.2 et 0.8.3)
    """
    
    def __init__(self, hangar=None, commande=None, points_complets=None,
                seed=None, use_structure=True, level_priority=None):
        """
        Args:
            hangar: Référence au hangar (pour accéder aux allées et sens)
            commande: Liste des points de collecte (allee, n)
            points_complets: Liste complète [dépôt] + commande + [arrivée]
            seed: Seed pour reproductibilité
            use_structure: True pour exploiter la structure géométrique
            level_priority: Priorité des niveaux [N1, N2, N3] pour les transitions
        """
        name = "Structural Insertion Solver"
        super().__init__(name)
        self.hangar = hangar
        self.commande = commande
        self.points_complets = points_complets
        self.seed = seed
        self.use_structure = use_structure
        #verifier si hangar existe avant d'acceder à Longueur
        if level_priority is None:
            if hangar is not None and hasattr(hangar,'Longueur'):
                self.level_priority =[0, hangar.Longueur/2, hangar.Longueur]  # N1, N2, N3
            else:
                self.level_priority = [0,50,100]
        else:
            self.level_priority = level_priority
        if seed is not None:
            random.seed(seed)
    
    def solve(self, distance_matrix: np.ndarray, 
            depot_idx: int = 0,
            arrival_idx: Optional[int] = None) -> Dict:
        """
        Résout avec stratégie structurelle
        """
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
                'optimal': True,
                'solver': self.name
            }
        
        # PHASE 1: REGROUPEMENT PAR ALLÉE (si structure disponible)
        if self.use_structure and self.hangar and self.points_complets:
            grouped_points = self._group_points_by_alley(points_to_visit)
            ordered_groups = self._order_groups_strategically(grouped_points, 
                                                            depot_idx, arrival_idx, 
                                                            distance_matrix)
        else:
            # Fallback: ordre aléatoire
            random.shuffle(points_to_visit)
            ordered_groups = [points_to_visit]
        
        # PHASE 2: CONSTRUCTION DU TOUR AVEC INSERTION GUIDÉE
        tour = self._build_tour_with_guided_insertion(
            ordered_groups, distance_matrix, depot_idx, arrival_idx
        )
        
        if not tour:
            return None
        
        # PHASE 3: POST-OPTIMISATION LOCALE (basée sur structure)
        if self.use_structure:
            tour = self._local_optimization(tour, distance_matrix)
        
        # Validation et calcul
        if not self.validate_solution(tour, distance_matrix, depot_idx, arrival_idx):
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return {
            'tour': tour,
            'distance': distance,
            'time': time.time() - start_time,
            'optimal': False,
            'solver': self.name,
            'method': 'structural' if self.use_structure else 'standard'
        }
    
    def _group_points_by_alley(self, point_indices: List[int]) -> Dict[str, List[int]]:
        """
        Regroupe les points par allée selon la modélisation
        """
        groups = {}
        
        for idx in point_indices:
            if idx >= len(self.points_complets):
                continue
                
            point = self.points_complets[idx]
            
            # Identifier l'allée
            if point == 'DEPOT' or point == 'ARRIVEE':
                alley = 'SPECIAL'
            else:
                alley, _ = point
            
            if alley not in groups:
                groups[alley] = []
            groups[alley].append(idx)
        
        # Ordonner les points dans chaque allée selon le sens
        for alley, points in groups.items():
            if alley == 'SPECIAL' or alley not in self.hangar.sens:
                continue
            
            # Trier selon la coordonnée y et le sens
            points.sort(key=lambda idx: self._get_point_y(idx))
            
            # Si sens descendant, inverser pour visiter du haut vers le bas
            if self.hangar.sens[alley] == -1:
                points.reverse()
        
        return groups
    
    def _get_point_y(self, idx: int) -> float:
        """Récupère la coordonnée y d'un point"""
        if self.points_complets is None or idx >= len(self.points_complets):
            return 0
        
        
        point = self.points_complets[idx]
        
        if point in ['DEPOT', 'ARRIVEE']:
            if point == 'DEPOT':
                return self.hangar.depot_position[1] if self.hangar else 0
            else:
                return self.hangar.arrival_position[1] if self.hangar else 0
        
        if self.hangar and point in self.hangar.points:
            return self.hangar.points[point][1]
        
        return 0
    
    def _order_groups_strategically(self, groups: Dict[str, List[int]],
                                  depot_idx: int, arrival_idx: int,
                                  distance_matrix: np.ndarray) -> List[List[int]]:
        """
        Ordonne stratégiquement les groupes d'allées
        selon la structure du hangar
        """
        if not groups:
            return []
        
        # Extraire les allées réelles (exclure SPECIAL)
        alleys = [a for a in groups.keys() if a != 'SPECIAL']
        
        if not alleys:
            return [groups.get('SPECIAL', [])]
        
        #calculer la position x moyenne pour chaque allée
        
        alley_positions = {}
        for alley in alleys:
            #calculer la position x moyenne des points
            x_coords = []
            for idx in groups[alley]:
                point  =self.points_complets[idx] if idx < len(self.points_complets) else None
                if (isinstance(point,tuple) and self.hangar and point in self.hangar.points):
                    coords = self.hangar.points[point]
                    if isinstance(coords, (tuple,list)) and len(coords)>=1:
                        x_coords.append(coords[0])
            if x_coords:
                alley_positions[alley]= sum(x_coords)/ len(x_coords)
            else:
                #valeur par defauts
                if alley in self.hangar.allees:
                    pos = self.hangar.allees.index(alley)
                    alley_positions[alley] = pos * self.hangar.largeur_allee + self.hangar.largeur/2
                else:
                    alley_positions[alley] = 0
        #Trier les allees par position x (de gauche à droite)
        sorted_alleys = sorted(alleys, key=lambda a: alley_positions.get(a,0))

        #construire la liste ordonnée des groupes
        ordered_groups = []
        for alley in sorted_alleys:
            ordered_groups.append(groups[alley])
        return ordered_groups

        
        
    
    def _build_tour_with_guided_insertion(self, ordered_groups: List[List[int]],
                                        distance_matrix: np.ndarray,
                                        depot_idx: int,
                                        arrival_idx: int) -> List[int]:
        """
        Construit le tour avec insertion guidée par la structure
        """
        # Initialisation: dépôt → premier point du premier groupe → arrivée
        if not ordered_groups or not ordered_groups[0]:
            return [depot_idx, arrival_idx]
        
        # Choisir le premier point stratégiquement
        first_group = ordered_groups[0]
        first_point = self._choose_best_start_point(first_group, depot_idx, 
                                                  arrival_idx, distance_matrix)
        
        tour = [depot_idx, first_point, arrival_idx]
        inserted = set([first_point])
        
        # Insérer les points restants groupe par groupe
        for group in ordered_groups:
            for point in group:
                if point in inserted:
                    continue
                
                # GUIDAGE PAR STRUCTURE: Essayer d'abord les insertions "cohérentes"
                best_position = self._find_guided_insertion_position(
                    point, tour, distance_matrix
                )
                
                if best_position != -1:
                    tour.insert(best_position, point)
                    inserted.add(point)
                else:
                    # Fallback: insertion standard
                    best_position = self._find_standard_insertion_position(
                        point, tour, distance_matrix
                    )
                    if best_position != -1:
                        tour.insert(best_position, point)
                        inserted.add(point)
        
        return tour
    
    def _choose_best_start_point(self, group: List[int],
                               depot_idx: int, arrival_idx: int,
                               distance_matrix: np.ndarray) -> int:
        """
        Choisit le meilleur point de départ dans un groupe
        selon la structure géométrique
        """
        if not group:
            return -1
        
        # Critère: minimiser distance totale dépôt→point→arrivée
        best_point = group[0]
        best_cost = float('inf')
        
        for point in group:
            cost = (distance_matrix[depot_idx, point] + 
                   distance_matrix[point, arrival_idx])
            
            # Bonus si le point est "bien placé" dans son allée
            if self.use_structure:
                # Préférer les points proches des niveaux de transition
                y = self._get_point_y(point)
                level_proximity = min(abs(y - level) for level in self.level_priority)
                cost_adjusted = cost - (level_proximity * 0.1)  # Petit bonus
                
                if cost_adjusted < best_cost:
                    best_cost = cost_adjusted
                    best_point = point
            else:
                if cost < best_cost:
                    best_cost = cost
                    best_point = point
        
        return best_point
    
    def _find_guided_insertion_position(self, point: int,
                                      tour: List[int],
                                      distance_matrix: np.ndarray) -> int:
        """
        Trouve une position d'insertion guidée par la structure
        """
        if not self.use_structure or not self.hangar:
            return -1
        
        # Récupérer l'allée du point à insérer
        point_info = self.points_complets[point] if point < len(self.points_complets) else None
        
        # GUIDELINE 1: Essayer d'insérer près des points de même allée
        same_alley_positions = []
        for i in range(1, len(tour) - 1):  # Exclure dépôt et arrivée
            tour_point = self.points_complets[tour[i]] if tour[i] < len(self.points_complets) else None
            
            if (isinstance(point_info, tuple) and isinstance(tour_point, tuple) and
                point_info[0] == tour_point[0]):  # Même allée
                same_alley_positions.append(i)
        
        # Si trouvé, choisir la meilleure position parmi celles-ci
        if same_alley_positions:
            return self._find_best_in_positions(point, tour, same_alley_positions, distance_matrix)
        
        # GUIDELINE 2: Essayer près des points avec des coordonnées y similaires
        point_y = self._get_point_y(point)
        similar_y_positions = []
        
        for i in range(1, len(tour) - 1):
            tour_y = self._get_point_y(tour[i])
            if abs(tour_y - point_y) < 20:  # Seuil de similarité
                similar_y_positions.append(i)
        
        if similar_y_positions:
            return self._find_best_in_positions(point, tour, similar_y_positions, distance_matrix)
        
        return -1  # Aucune position guidée trouvée
    
    def _find_best_in_positions(self, point: int, tour: List[int],
                              positions: List[int],
                              distance_matrix: np.ndarray) -> int:
        """
        Trouve la meilleure position parmi une liste de positions candidates
        """
        best_position = -1
        best_cost = float('inf')
        
        for pos in positions:
            if pos < 1 or pos >= len(tour):
                continue
            
            prev = tour[pos-1]
            next_node = tour[pos]
            
            current_cost = distance_matrix[prev, next_node]
            new_cost = distance_matrix[prev, point] + distance_matrix[point, next_node]
            
            if not np.isinf(current_cost) and not np.isinf(new_cost):
                cost_increase = new_cost - current_cost
                if cost_increase < best_cost:
                    best_cost = cost_increase
                    best_position = pos
        
        return best_position
    
    def _find_standard_insertion_position(self, point: int,
                                        tour: List[int],
                                        distance_matrix: np.ndarray) -> int:
        """
        Insertion standard (cheapest) comme fallback
        """
        best_position = -1
        best_cost_increase = float('inf')
        
        for i in range(1, len(tour) - 1):
            prev = tour[i-1]
            next_node = tour[i]
            
            current_cost = distance_matrix[prev, next_node]
            new_cost = distance_matrix[prev, point] + distance_matrix[point, next_node]
            
            if np.isinf(current_cost) or np.isinf(new_cost):
                continue
            
            cost_increase = new_cost - current_cost
            if cost_increase < best_cost_increase:
                best_cost_increase = cost_increase
                best_position = i
        
        return best_position
    
    def _local_optimization(self, tour: List[int],
                          distance_matrix: np.ndarray) -> List[int]:
        """
        Post-optimisation locale basée sur la structure
        """
        if len(tour) <= 3:
            return tour
        
        improved = True
        iterations = 0
        
        while improved and iterations < 10:
            improved = False
            iterations += 1
            
            # Optimisation spécifique: réorganiser les points de même allée
            for i in range(1, len(tour) - 2):
                for j in range(i + 1, len(tour) - 1):
                    # Vérifier si les points sont dans la même allée
                    if not self._same_alley(tour[i], tour[j]):
                        continue
                    
                    # Essayer d'échanger pour respecter l'ordre dans l'allée
                    if self._should_swap(tour[i], tour[j]):
                        tour[i], tour[j] = tour[j], tour[i]
                        improved = True
                        break
                
                if improved:
                    break
        
        return tour
    
    def _same_alley(self, idx1: int, idx2: int) -> bool:
        """Vérifie si deux points sont dans la même allée"""
        if (self.points_complets is None or idx1 >= len(self.points_complets) or idx2 >= len(self.points_complets)):
            return False
        
        p1 = self.points_complets[idx1]
        p2 = self.points_complets[idx2]
        
        if not isinstance(p1, tuple) or not isinstance(p2, tuple):
            return False
        
        return p1[0] == p2[0]
    
    def _should_swap(self, idx1: int, idx2: int) -> bool:
        """
        Détermine si deux points dans la même allée devraient être échangés
        pour respecter l'ordre selon le sens de circulation
        """
        if not self.hangar or not self._same_alley(idx1, idx2):
            return False
        
        p1 = self.points_complets[idx1]
        p2 = self.points_complets[idx2]
        
        if not isinstance(p1, tuple) or not isinstance(p2, tuple):
            return False
        
        alley = p1[0]
        y1 = self._get_point_y(idx1)
        y2 = self._get_point_y(idx2)
        
        # Selon le sens: les points doivent être visités dans l'ordre croissant de y
        # pour les allées montantes, décroissant pour les descendantes
        if self.hangar.sens.get(alley, 1) == 1:  # Montée
            return y1 > y2  # On devrait avoir y1 < y2
        else:  # Descente
            return y1 < y2  # On devrait avoir y1 > y2