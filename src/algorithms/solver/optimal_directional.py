
from typing import List,Tuple,Dict,Optional
import numpy as np
import heapq 
import time
#inclure les chemins general si erreur
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
        ...



    
