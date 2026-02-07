
from typing import List,Tuple,Dict,Optional
import numpy as np
import heapq 
import time
import sys
import os
sys.path.append(os.path.join((os.path.dirname(__file__),'..','..')))

from algorithms.base_solver import WarehouseTSPSolver

class OptimalDirectionalSolver(WarehouseTSPSolver):
    """
    C'est Solveur optimal basé sur la modélisation mathématique de l'article.
    Ce solveur implemente l'algorithme ATSP avec contraintes directionnelles selon 
    le théoreme 0.8.3 : chemins optimaux à 3 segments max.

    Compléxité : O(n² log n) avec n= nombre de points
    Garantie: solution optimale (exacte ) pour n <=15,
            heuristique de qualité pour n >=15
    """
    def __init__(self, hangar):
        super().__init__("OptimalDirectional")
        self.hangar = hangar

        #cache pour les distances calculées
        self._distance_cache = {}
    #end __init__

    #------------------------------------------------
    #IMPLEMENTATITON DE LA DISTANCE d_H DE L'ARTICLE
    #------------------------------------------------
    def _compute_dH(self,p:Tuple,q:Tuple)-> float:
        """
        cette méthode calcule la distance d_H(p,q) selon la modélisation de l'article.
        Théorème 0.8.2 : d_H(p,q) = min_{j∈J(p,q)} (|y_p - y_j| + |x_q - x_p| + |y_j - y_q|)
        où J(p,q) = {j ∈ {1,2,3} | (y_j - y_p)·σ(α_p) > 0 et (y_q - y_j)·σ(α_q) > 0}
        
        Complexité : O(1) grâce à la formule explicite
        """
        #Récupérer les coordonnées
        if p not in self.hangar.points:
            self.hangar._ajouter_point(p[0],p[1])
        if q not in self.hangar.points:
            self.hangar._ajouter_point(q[0],q[1])

        x_p, y_p = self.hangar.points[p]
        x_q, y_q = self.hangar.points[q]

        #Allées de base
        allee_p = self._get_base_allee(p[0])
        allee_q = self._get_base_allee(q[0])

        #sens des allées
        sens_p = self.hangar.sens.get(allee_p,1)
        sens_q = self.hangar.sens.get(allee_q,1)

        #CAS 1: les points ont la même allée de base
        if allee_p == allee_q:
            #Vérifier l'accessibilité verticale
            if sens_p == 1 and y_q >=y_p: #montée
                return abs(y_q - y_p)
            elif sens_p == -1 and y_q <= y_p: #descente
                return abs(y_q - y_p)
            else:
                return float('inf')
        
        #CAS 2: allées differentes -> utiliser les niveaux pour changer
        distances =[]

        #niveaux disponibles
        niveaux = list(self.hangar.niveaux.values())
        noms_niveaux  = list(self.hangar.niveaux.keys())

        for j, y_j in enumerate(niveaux):
            #verifier les conditions d'accessibilité (J(p,q))
            condition1 = (y_j - y_p)*sens_p > 0 # p -> niveau j possible
            condition2 = (y_q - y_j)*sens_q > 0 # niveau j -> q possible

            if condition1 and condition2:
                d_vertical1 = abs(y_j - y_p)
                d_horizontal = abs(x_q - x_p)
                d_vertical2 = abs(y_q - y_j)

                distances.append(d_vertical1 + d_horizontal + d_vertical2)
        if not distances:
            #Aucun chemin possible via les niveaux standars
            #Essayer un chemin en deux étapes (passer par le niveau le plus proche)
            return self._compute_fallback_dH(p,q, allee_p,allee_q, y_p,y_q,x_p,x_q)
        return min(distances)
    #end _compute_dH

    def _get_base_allee(self,allee_code:str) -> str:
        """Cette méthode retourne l'allée de base (A,B,C,...) d'un code d'allée"""
        if len(allee_code)== 1:
            return allee_code
        elif allee_code in ['BB','DD','FF','HH','AB']:
            return allee_code[1] if allee_code != 'AB' else 'B'
        elif allee_code in ['CC', 'EE', 'GG']:
            return allee_code[0]
        else:
            return allee_code[0]
    #end _get_base_allee

    def _compute_fallback_dH(self,p,q,allee_p,allee_q, y_p,y_q,x_p,x_q):
        """
        Fallback pour quand un niveau intermédiaire ne fonctionne.
        Utilisation de la structure du Théorème 0.8.3
        
        :param p: le point p
        :param q: le point q
        :param allee_p: le code de l'allée p
        :param allee_q: le code de l'allée q 
        :param y_p: coordonnée en y du point p 
        :param y_q: coordonnée en y du point q
        :param x_p: coordonnée en x du point p 
        :param x_q: coordonnée en x du point q 
        """
        #Distance horizontale fixe
        d_horizontal = abs(x_q - x_p)

        #Trouver les niveaux accessibles depuis q
        niveaux_p = []
        for y_j in self.hangar.niveaux.values():
            if (y_j - y_p)* self.hangar.sens.get(allee_p,1)>0:
                niveaux_p.append(y_j)
        #Trouver les niveaux accessibles vers q
        niveaux_q = []
        for y_k in self.hangar.niveaux.values():
            if (y_q - y_k)* self.hangar.sens.get(allee_q,1)>0:
                niveaux_q.append(y_k)
        #Distances minimale via la combinaison de niveaux
        min_dist = float('inf')
        for y_j in niveaux_p:
            for y_k in niveaux_q:
                #chemin : p -> niveau j -> niveau k -> q
                d1 = abs(y_j - y_p)
                d2= d_horizontal #horizontal entre allées
                d3 = abs(y_k - y_j) #eventuel changement de niveau
                d4 = abs(y_q - y_k)

                dist = d1 + d2 + d3 + d4
                if dist < min_dist:
                    min_dist = dist
        return min_dist if min_dist != float('inf') else float('inf')
    
#------------------------------------------------
# ALGORITHME ATSP OPTIMAL (Held- Karp adapté)
#------------------------------------------------
    def solve(self,distance_matrix: np.ndarray,depot_idx:int=0,arrival_idx: Optional[int]=None)->Dict:
        """
        Résolution de l'ATSP avec les contraintes directionnelles.

        stratégie:
        1. si n <= 15 : Held-Karp 
        2. si 15 < n <= 30: Lin-kernighan heuristique 
        3. si n >30 : nearest Neighbor + 3-opt  

        Args:
            distance_matrix: matrice pré-calculée
            depot_idx, arrival_idx: indices des points spéciaux
        Returns:
            une solution optimale ou quasi-optimale
        """
        start_time = time.time()

        if arrival_idx is None:
            arrival_idx = depot_idx
        n = distance_matrix.shape[0]

        #vérifier la faisabilité
        if not self._check_feasibility(distance_matrix,depot_idx,arrival_idx):
            return self._solution_erreur("Problème insoluble (contraintes)")
        
        #CHOIX DE L'ALGORITHME SELON LA TAILLE

        if n <=15:
            print(f"[Optimal] n={n} <= 15 -> Held-Karp")
            tour,distance, is_optimal = self._held_karp_astp(distance_matrix,depot_idx,arrival_idx)
        elif n <=30:
            print(f"[Qausi-optimal] 15 < n={n} <= 30 -> Lin-Kernighan heuristique")
            tour,distance = self._lin_kernighan_astp(
                distance_matrix,depot_idx,arrival_idx
            )
            is_optimal = False
        else:
            print(f"[Heuristique] n={n} > 30 -> Nearest Neighbor + 3-opt")
            tour,distance= self._nearest_neighbor_3opt(
                distance_matrix,depot_idx,arrival_idx
            )
            is_optimal = False
        
        return self._creer_resultat(
            tour,distance,time.time() - start_time, is_optimal
        )
    #end solve

    def _held_karp_astp(self,dist_matrix,start,end):
        """
        Algorithme de Help-Karp adapté pour ATSP.
        Complexité : O(n².2^n)
        Utilisation de la programmation dynamique avec un masque de bits
        """
        n = dist_matrix.shape[0]
        #Si départ = arrivée (tour classique)
        if start == end:
            #DP[mask][last] = distance minimale pour visiter les points dans mask et finir à 'last'
            dp = np.full((1 << n,n), float('inf'))
            parent = np.full((1<< n,n), -1, dtype=int)

            # Initialisation : juste le départ
            dp[1 << start][start]=0

            #Parcours des masques croissants
            for mask in range(1<<n):
                for last in range(n):
                    if dp[mask][last] == float('inf'):
                        continue

                    #Essayer d'aller vers chaque point non visité
                    for next_point in range(n):
                        if mask & (1 << next_point):
                            continue #deja visité
                        new_mask = mask | (1 << next_point)
                        new_dist = dp[mask][last] + dist_matrix[last][next_point]

                        if new_dist < dp[new_mask][next_point]:
                            dp[new_mask][next_point] = new_dist
                            parent[new_mask][next_point]= last
                        
            # Reconstruction du tour
            full_mask = (1 << n) - 1
            last_point = np.argmin(dp[full_mask])
            min_dist = dp[full_mask][last_point]

            #Reconstruction
            tour = []
            mask= full_mask
            current = last_point

            while current != -1:
                tour.append(current)
                prev = parent[mask][current]
                mask &= ~(1 << current)
                current = prev
            tour.reverse()
            return tour, min_dist,True
        else:
            #départ != arrivée : problème encore difficile
            #Utilisons une version adaptée

            return self._held_karp_atsp_different_ends(dist_matrix,start,end)
    # _held_karp_astp

    def _held_karp_atsp_different_ends(self, dist_matrix, start, end):
        """
        Held-Karp adapté pour un départ != arrivée
        """
        n= dist_matrix.shape[0]
        nodes = [i for i in range(n) if i not in [start,end]]

        #DP[mask][last]= min distance
        size = len(nodes)
        dp= np.full((1<< size,size), float('inf'))
        parent = np.full((1<< size,size), -1, dtype=int)

        #Initialisation : depuit le départ
        for i , point in enumerate(nodes):
            dp[1<< i][i] = dist_matrix[start][point]
        #DP
        for mask in range(1 << size):
            for i in range(size):
                if dp[mask][i] == float('inf'):
                    continue

                last_point = nodes[i]
                for j in range(size):
                    if mask & (1 << j):
                        continue
                    next_point = nodes[j]
                    new_mask = mask | (1 << j)
                    new_dist = dp[mask][i] + dist_matrix[last_point][next_point]

                    if new_dist < dp[new_mask][j]:
                        dp[new_mask][j] = new_dist
                        parent[new_mask][j]=i
        #Trouver le meilleur chemin vers l'arrivée
        full_mask = (1 << size) -1
        best_dist = float('inf')
        best_last = -1

        for i in range(size):
            last_point = nodes[i]
            total_dist = dp[full_mask][i] + dist_matrix[last_point][end]

            if total_dist < best_dist:
                best_dist = total_dist
                best_last = i
        #Reconstruction
        tour = [start]
        mask = full_mask
        current_idx = best_last

        while current_idx := -1:
            tour.append(nodes[current_idx])
            prev_idx = parent[mask][current_idx]
            mask &=~(1 << current_idx)
            current_idx = prev_idx
        tour.append(end)
        return tour, best_dist,True
    #_held_karp_atsp_different_ends

    def _lin_kernighan_atsp(self,dist_matrix,start,end):
        """ 
        Heuristique Lin-Kernighan adaptée pour ATSP
        Complexité : O(n².k) avec k presque 20-100 iterations.
        """
        #1. Construction initiale (nearest neighbor)
        n= dist_matrix.shape[0]
        visited = [False]*n
        tour = [start]
        current = start
        visited[start] = True

        #Construction du tour initial
        while len(tour) < n - (0 if start == end else 1):
            #Trouver le point le plus proche non visitée
            next_point = -1
            min_dist = float('inf')
            
            for i in range(n):
                if not visited[i] and i != end: #on ajoutera l'arrivée à la fin
                    if dist_matrix[current][i] < min_dist:
                        min_dist = dist_matrix[current][i]
                        next_point = i
            if next_point == -1:
                break

            tour.append(next_point)
            visited[next_point]= True
            current = next_point
        #Ajouter l'arrivée
        if end not in tour:
            tour.append(end)
        
        #2. Optimisation Lin-Kernighan
        improved = True
        max_iterations = min(100, n*5)

        for iteration in range(max_iterations):
            if not improved:
                break
            improved = False

            #Essayer des échanges de k-opt (k=2,3,4)
            for k in [2,3,4]:
                new_tour, new_dist = self._k_opt_move(tour,dist_matrix,k)
                if new_dist < self.calculate_tour_distance(tour,dist_matrix):
                    tour = new_tour
                    improved = True
                    break
        distance = self.calculate_tour_distance(tour,dist_matrix)
        return tour, distance
    #_lin_kernighan_atsp

    def _k_opt_move(self,tour,dist_matrix,k):
        """ Effectue un mouvement k-opt"""
        n= len(tour)
        best_tour = tour.copy()
        best_dist = self.calculate_tour_distance(tour,dist_matrix)

        #Générer des combinaisins d'arêtes à échanger
        indices = list(range(1,n-1))  #Exclusion du départ et de l'arrivée

        #Echantillonnage pour éviter l'explosion combinatoire
        import random
        samples = min(1000,len(indices)** k)
        
        for _ in range(samples):
            #Choisir k arêtes aléatoirement
            edges = random.sample(indices,k)
            edges.sort()

            #Essayer différentes combinaisons d'échange
            new_tour = self._apply_k_opt_swap(tour,edges)
            new_dist = self.calculate_tour_distance(new_tour,dist_matrix)

            if new_dist < best_dist:
                best_tour = new_tour
                best_dist = new_dist
        return best_tour, best_dist
    #_k_opt_move

    def _apply_k_opt_swap(self, tour, edges):
        """ Applique un échange k-opt sur les arêtes données"""
        new_tour = []
        prev = 0

        for i in range(len(edges)):
            start = prev
            end = edges[i]

            # Inverser ou non selon la parité
            if i%2 == 0:
                new_tour.extend(tour[start:end])
            else:
                new_tour.extend(reversed(tour[start:end]))
            prev = end
        # Dernier segment
        new_tour.extend(tour[prev:])
        return new_tour
    #_apply_k_opt_swap

    def _nearest_neighbor_3opt(self,dist_matrix,start,end):
        """
        Nearest Neighbor + optimisation 3-opt
        Complexité: O(n^3)
        """
        n= dist_matrix.shape[0]

        #1. Nearest Neighbor initial
        visited = [False]*n
        tour = [start]
        current = start
        visited[start] = True

        while len(tour) < n - (0 if start == end else 1):
            next_point = -1
            min_dist = float('inf')
            for i in range(n):
                if not visited[i] and i != end:
                    min_dist = dist_matrix[current][i]
                    next_point=i
            if next_point == -1:
                break

            tour.append(next_point)
            visited[next_point]= True
            current = next_point

        if end not in tour:
            tour.append(end)
        
        #2. Optimisation 3-opt
        tour = self._three_opt(tour,dist_matrix)
        distance = self.calculate_tour_distance(tour,dist_matrix)
        return tour, distance
    #_nearest_neighbor_3opt

    def _three_opt(self, tour,dist_matrix):
        """Optimisation 3-opt"""
        n = len(tour)
        best_tour = tour
        best_dist = self.calculate_tour_distance(tour,dist_matrix)
        improved = True

        while improved:
            improved = False

            for i in range(1,n-5):
                for j in range(i+2, n-3):
                    for k in range(j+2,n-1):
                        #Essayer les 7 combinaisons possibles de 3-opt
                        combinaisons = self._three_opt_combinations(best_tour,i,j,k)
                        for new_tour in combinaisons:
                            new_dist = self.calculate_tour_distance(new_tour,dist_matrix)
                            if new_dist < best_dist:
                                best_dist = new_dist
                                improved = True
                                break
                        if improved:
                            break
                    if improved:
                        break
                if improved:
                    break
        return best_tour
    #_three_opt
    def _three_opt_combinations(self,tour,i,j,k):
        """ Génére les 7 combinaisons posssibles de 3-opt"""
        #Les 7 combinaisons standars
        combos = []
        n = len(tour)

        # 0-1-2 (original)
        # 0-2-1
        # 1-0-2
        # 1-2-0
        # 2-0-1
        # 2-1-0

        #Implémentation simplifiée: retourner quelques combinaisons
        combos.append(tour.copy()) #original

        #Quelques combinaisons
        combo1 = tour[:i+1] + tour[j:i:-1] + tour[k:j:-1] + tour[k+1:]
        combos.append(combo1)

        combo2 = tour[:i+1] + tour[k:j:-1] + tour[i+1:j+1] + tour[k+1:]
        combos.append(combo2)

        return combos
    #_three_opt_combinations

    #------------------------------------------
    # METHODES AUXILIAIRES
    #----------------------------------------------
    def _check_feasibility(self,dist_matrix,start,end):
        """ Vérifier si le problème est faisable"""
        n = dist_matrix.shape[0]

        #vérifier que tous les points sont accessibles depuis le départ
        for i in range(n):
            if i!= start and dist_matrix[start][i] == float('inf'):
                return False
        #Vérifier que l'arrivée est accessible depuis tous les points
        for i in range(n):
            if i!= end and dist_matrix[i][end] == float('inf'):
                return False
        return True
    #end _check_feasibility

    def _creer_resultat(self,tour,distance,time_elapsed, is_optimal):
        """ Créer le dictionnaire de résultat standarisés """
        return {
            'tour':tour,
            'distance':distance,
            'time':time_elapsed,
            'optimal': is_optimal,
            'solver': self.name,
            'error':False,
            'message':f"Solution {'optimale' if is_optimal else 'heurisitique'}"
        }
    #_creer_resultat

    def _solution_erreur(self,message):
        """Créer un résultat d'erreur """
        return {
            'tour': [],
            'distance': float('inf'),
            'time':0,
            'optimal':False,
            'solver':self.name,
            'error':True,
            'message':message
        }




    
