from typing import List,Tuple,Dict,Set,Optional
import numpy as np
import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from geometry.hangar import Hangar
from algorithms.base_solver import WarehouseTSPSolver

import matplotlib.pyplot as plt
import matplotlib.patches as patches 
#from graph.graph_collect_depot import GraphCollectWithDepot


class OptParcoursSolver(WarehouseTSPSolver):
    """
    Algorithme d'optimisation du parcours de collecte
    """

    def __init__(self,hangar=None, points_complets=None):
        name= "OptParcours Solver"
        super().__init__(name)
        self.hangar = hangar
        self.points_complets = points_complets
        #DEBUG 
        print(f"\n=== INIT Opt parcours")
        print(f"Points complets: {self.points_complets}")
        print(f"Dépot label: {self.hangar.depot_label}")
        print(f"Arrivée label: {self.hangar.arrival_label}")
    
        self.NIVEAUX = hangar.niveaux
        #placer la commande dans le hangar
        #self.hangar.placer_commande(commande)
        self.groupes_by_allee = self._grouper_by_allee()
        print(f"Groupes par allée: {self.groupes_by_allee.keys()}")
        print("=============================")

        self.graphe_partitons = self.construire_graphe_partitions()
        self.matrice_distances, self.noeuds, self.points_acces = self._matrice_distances_partitions()
        self.afficher_partitions()
    #end if

    def solve(self, distance_matrix: np.ndarray, depot_idx:int =0, arrival_idx: Optional[int] = None) -> Dict:
        """ Implémentation du solver
        """
        start_time = time.time()
        if arrival_idx is None:
            arrival_idx = depot_idx


        #1. Essayer l'algorithme amélioré
        depart = self._point_from_index(depot_idx)
        arrivee = self._point_from_index(arrival_idx)

        resultat = self._parcours_glouton_ameliore(depart,arrivee)
        if resultat['success']:
            # Construire tour
            tour = [depot_idx]
            for point in resultat['ordre_points']:
                idx = self._point_to_index(point)
                if idx is not None:
                    tour.append(idx)
            tour.append(arrival_idx)
            distance = self.calculate_tour_distance(tour,distance_matrix)
            return self._creer_resultat(tour,distance,start_time,optimal=False)
        
        #2. FALLBACK1
        print("⚠️  Échec glouton → Fallback ATSP simple")
        fallback_result = self._fallback_atsp_simple(distance_matrix, depot_idx, arrival_idx)
        if fallback_result:
            return fallback_result
        
        #3. FALLBACK: 
        print("⚠️  Utilisation du fallback simple")
        n = distance_matrix.shape[0]
        tour = [depot_idx]
        
        # Ajouter tous les points dans l'ordre
        for i in range(1, n):
            if i != arrival_idx:
                tour.append(i)
        
        tour.append(arrival_idx)
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return self._creer_resultat(tour, distance, start_time, optimal=False)
    #end solve
    def _fallback_atsp_simple(self, distance_matrix,depot_idx, arrival_idx):
        """Fallback intelligent : ATSP simple sur les points réels"""
        n = distance_matrix.shape[0]
        
        # Algorithme du plus proche voisin adapté à l'asymétrie
        visited = [False] * n
        visited[depot_idx] = True
        
        tour = [depot_idx]
        current = depot_idx
        
        while len(tour) < n:
            # Trouver le point non visité le plus proche
            next_idx = None
            min_dist = float('inf')
            
            for j in range(n):
                if not visited[j] and distance_matrix[current][j] < min_dist:
                    min_dist = distance_matrix[current][j]
                    next_idx = j
            
            if next_idx is None:
                # Plus de point accessible
                break
            
            tour.append(next_idx)
            visited[next_idx] = True
            current = next_idx
        
        # Ajouter l'arrivée
        if arrival_idx != depot_idx and arrival_idx not in tour:
            tour.append(arrival_idx)
        
        # Vérifier que tous les points sont visités
        points_manquants = [i for i in range(n) if not visited[i] and i != arrival_idx]
        if points_manquants:
            print(f"Points non visités: {points_manquants}")
            return None
        
        distance = self.calculate_tour_distance(tour, distance_matrix)
        
        return self._creer_resultat(
            tour, distance, # À ajuster
            optimal=False
        )


    # ====================== Méthodes d'interface ===============
    #TODO: 
    def _parcours_glouton_ameliore(self, depart, arrivee):
        """Teste plusieurs options d'accès par partition"""
        if not self.noeuds:
            return {'success': False, 'message': "Aucune partition"}
        
        # Pour chaque partition, préparer plusieurs options
        toutes_options = []
        for noeud in self.noeuds:
            options = self._points_acces_realistes(noeud)
            toutes_options.append(options)
        
        # Algorithme amélioré
        position = depart
        visitees = []
        ordre_points = []
        distance_totale = 0
        non_visitees = list(range(len(self.noeuds)))
        
        while non_visitees:
            meilleur_idx = None
            meilleure_option = None
            meilleure_distance = float('inf')
            
            # Chercher la partition + option la plus accessible
            for idx in non_visitees:
                for option in toutes_options[idx]:
                    dist = self._distance_contrainte(position, option['entree'][1])
                    
                    # Choisir la meilleure option accessible
                    if dist < meilleure_distance and dist != float('inf'):
                        meilleure_distance = dist
                        meilleur_idx = idx
                        meilleure_option = option
            
            if meilleur_idx is None:
                # Si aucune option n'est accessible, échec
                break
            
            # Visiter avec l'option choisie
            visitees.append(meilleur_idx)
            non_visitees.remove(meilleur_idx)
            
            noeud = self.noeuds[meilleur_idx]
            distance_totale += meilleure_distance + meilleure_option['distance_interne']
            position = meilleure_option['sortie'][1]
            ordre_points.extend(noeud['points'])

            #DEBUG----
            print(f"  Test {noeud['id']}: {position} → {option['entree'][1]}")
            print(f"    Distance réelle: {dist} {'(IMPOSSIBLE)' if dist == float('inf') else ''}")
        
        # Résultat
        return {
            'success': len(visitees) > 0,
            'ordre_points': ordre_points,
            'distance': distance_totale
        }
    
    def _parcours_glouton_ameliore_2(self, depart, arrivee):
        """Version améliorée avec backtracking limité"""
        if not self.noeuds:
            return {'success': False, 'message': "Aucune partition"}
        
        # Préparer toutes les options
        toutes_options = []
        for noeud in self.noeuds:
            options = self._points_acces_realistes(noeud)
            toutes_options.append(options)
        
        # ALGORITHME AMÉLIORÉ : essayer plusieurs points de départ
        meilleur_resultat = None
        meilleure_distance = float('inf')
        
        # Essayer chaque partition comme première (si petit nombre)
        if len(self.noeuds) <= 10:
            for first_idx in range(len(self.noeuds)):
                resultat = self._parcours_glouton_from_first(
                    depart, arrivee, first_idx, toutes_options
                )
                if resultat['success'] and resultat['distance'] < meilleure_distance:
                    meilleure_distance = resultat['distance']
                    meilleur_resultat = resultat
        
        # Si échec ou trop grand, utiliser la version simple
        if meilleur_resultat is None:
            meilleur_resultat = self._parcours_glouton_simple(
                depart, arrivee, toutes_options
            )
        
        return meilleur_resultat

    def _parcours_glouton_simple(self, depart, arrivee, toutes_options):
        """Version simple (votre original amélioré)"""
        position = depart
        visitees = []
        ordre_points = []
        distance_totale = 0
        non_visitees = list(range(len(self.noeuds)))
        
        # Trier les partitions par accessibilité initiale
        access_initiale = []
        for idx in non_visitees:
            best_dist = float('inf')
            for option in toutes_options[idx]:
                dist = self._distance_contrainte(position, option['entree'][1])
                if dist < best_dist:
                    best_dist = dist
            access_initiale.append((idx, best_dist))
        
        # Trier par distance croissante
        access_initiale.sort(key=lambda x: x[1])
        non_visitees = [idx for idx, _ in access_initiale]
        
        # Parcours glouton
        for idx in non_visitees:
            # Trouver la meilleure option pour cette partition
            meilleure_option = None
            meilleure_distance = float('inf')
            
            for option in toutes_options[idx]:
                dist = self._distance_contrainte(position, option['entree'][1])
                if dist < meilleure_distance:
                    meilleure_distance = dist
                    meilleure_option = option
            
            if meilleure_option and meilleure_distance != float('inf'):
                # Visiter cette partition
                noeud = self.noeuds[idx]
                distance_totale += meilleure_distance + meilleure_option['distance_interne']
                position = meilleure_option['sortie'][1]
                ordre_points.extend(noeud['points'])
                visitees.append(idx)
            else:
                # Impossible d'atteindre cette partition
                print(f"⚠️ Partition {self.noeuds[idx]['id']} inaccessible")
        
        return {
            'success': len(visitees) == len(self.noeuds),
            'ordre_points': ordre_points,
            'distance': distance_totale
        }
    def _parcours_glouton_from_first(self, depart, arrivee, first_idx, toutes_options):
        """
        Parcours glouton en partant d'une partition spécifique comme première
        
        Args:
            depart: point de départ (coordonnées)
            arrivee: point d'arrivée (coordonnées)
            first_idx: index de la partition à visiter en premier
            toutes_options: liste des options d'accès pour chaque partition
        
        Returns:
            Dictionnaire avec success, ordre_points, distance
        """
        if first_idx < 0 or first_idx >= len(self.noeuds):
            return {'success': False, 'message': f"Index {first_idx} invalide"}
        
        position = depart
        visitees = []
        ordre_points = []
        distance_totale = 0
        
        # Liste des partitions non visitées (sauf la première)
        non_visitees = list(range(len(self.noeuds)))
        non_visitees.remove(first_idx)  # Retirer la première
        
        # 1. VISITER LA PREMIÈRE PARTITION (forcée)
        noeud_first = self.noeuds[first_idx]
        
        # Trouver la meilleure option pour cette première partition
        meilleure_option_first = None
        meilleure_distance_first = float('inf')
        
        for option in toutes_options[first_idx]:
            dist = self._distance_contrainte(position, option['entree'][1])
            if dist < meilleure_distance_first:
                meilleure_distance_first = dist
                meilleure_option_first = option
        
        if meilleure_option_first is None or meilleure_distance_first == float('inf'):
            # Impossible d'atteindre même la première partition
            return {'success': False, 'message': f"Partition {noeud_first['id']} inaccessible depuis le départ"}
        
        # Visiter cette première partition
        distance_totale += meilleure_distance_first + meilleure_option_first['distance_interne']
        position = meilleure_option_first['sortie'][1]
        ordre_points.extend(noeud_first['points'])
        visitees.append(first_idx)
        
        # 2. VISITER LES AUTRES PARTITIONS (glouton)
        while non_visitees:
            meilleur_idx = None
            meilleure_option = None
            meilleure_distance = float('inf')
            
            # Chercher la partition la plus proche
            for idx in non_visitees:
                for option in toutes_options[idx]:
                    dist = self._distance_contrainte(position, option['entree'][1])
                    if dist < meilleure_distance:
                        meilleure_distance = dist
                        meilleur_idx = idx
                        meilleure_option = option
            
            if meilleur_idx is None or meilleure_distance == float('inf'):
                # Plus aucune partition accessible
                print(f"  ⚠️ Plus de partitions accessibles après {len(visitees)} visites")
                break
            
            # Visiter cette partition
            noeud = self.noeuds[meilleur_idx]
            distance_totale += meilleure_distance + meilleure_option['distance_interne']
            position = meilleure_option['sortie'][1]
            ordre_points.extend(noeud['points'])
            visitees.append(meilleur_idx)
            non_visitees.remove(meilleur_idx)
        
        # 3. AJOUTER LA DISTANCE VERS L'ARRIVÉE
        distance_arrivee = self._distance_contrainte(position, arrivee)
        if distance_arrivee != float('inf'):
            distance_totale += distance_arrivee
        else:
            # Estimation si chemin impossible
            dx = arrivee[0] - position[0]
            dy = arrivee[1] - position[1]
            distance_arrivee = np.sqrt(dx*dx + dy*dy) * 1.5
            distance_totale += distance_arrivee
            print(f"  ⚠️ Chemin vers arrivée impossible, estimation: {distance_arrivee:.1f}")
        
        # 4. RETOURNER LE RÉSULTAT
        succes_complet = len(visitees) == len(self.noeuds)
        
        return {
            'success': succes_complet,
            'message': f"Visited {len(visitees)}/{len(self.noeuds)} partitions" if not succes_complet else "Toutes partitions visitées",
            'ordre_points': ordre_points,
            'distance': distance_totale,
            'premiere_partition': noeud_first['id'],
            'partitions_visitees': visitees
        }

    #TODO:
    def _point_from_index(self,idx):
        """ convertir un index en coordonnée (x,y)"""
        if 0 <= idx < len(self.points_complets):
            point = self.points_complets[idx]

            if point == self.hangar.depot_label:
                return self.hangar.depot_position
            elif point == self.hangar.arrival_label:
                return self.hangar.arrival_position
            elif point in self.hangar.points:
                return self.hangar.points[point]
        print(f" _point_from_index: idx={idx} non trouvé dans points_complets")
        return (0, 0)
    #TODO:
    def _point_to_index(self,point):
        """ convertir un point en index"""
        try:
            if point in self.points_complets:
                return self.points_complets.index(point)
            else:
                #chercher par tuple
                for i,p in enumerate(self.points_complets):
                    if isinstance(p,tuple) and p == point:
                        return i
        except Exception as ex:
            print(f"Erreur _point_to_index: {ex}, point={point}")
        return None
    
    #================ QUELQUES METHODES UTILITAIRES=======
    def _solution_erreur(self,message):
        """ créer une reponse d'erreur standarisée """
        return {
            'tour':[],
            'distance':float('inf'),
            'time': 0,
            'optimal':False,
            'solver': self.name,
            'error':True,
            'message': message
        }
    #end _solution_erreur
    #TODO:
    def _creer_resultat(self,tour,distance,start_time,optimal):
        """ standarisé le resultat """
        return {
            'tour':tour,
            'distance':distance,
            'time': time.time() - start_time,
            'optimal': optimal,
            'solver':self.name,
            'error': False,
            'message':"succès"
        }
    




    #Construction de l'algorithme d'optimisation du parcours lors de la collecte
    ##ETAPE 1:
    #    - grouper les n points de chaque allées
    #    - ordonner les groupes  de maniere alternées montée,descente . et en combien de facons
    def _grouper_by_allee(self):
        """ Groupe les points de la commande par allée """
        if not self.points_complets:
            print("commande vide")
            return {}
        #extraire les lables comme strings
        depot_str = self.hangar.depot_label[0] if isinstance(self.hangar.depot_label,tuple) else str(self.hangar.depot_label)
        arrival_str = self.hangar.arrival_label[0] if isinstance(self.hangar.arrival_label,tuple) else str(self.hangar.arrival_label)

        print(f"DEBUG: depot_str='{depot_str}', arrival_str='{arrival_str}'")

        groupes = {}
        for point in self.points_complets:
            #extraire l'allée et sa position
            if isinstance(point,tuple) and len(point)==2:
                allee, position = point
                allee_str = str(allee)
                print(f"DEBUG: Point {allee_str}{position} - allee_str='{allee_str}'")
                
                #EXCLURE LES POINTS SPECIAUX
                if allee in [depot_str, arrival_str]:
                    print(f"DEBUG: Exclu (point spécial)")
                    continue
                #DEBUG
                if allee in ['AB','BB']:
                    allee_finale = 'B'
                    print(f"DEBUG: {allee} transformé en B")
                else:
                    allee_finale = allee_str

                if allee_finale not in groupes:
                    groupes[allee_finale] = [] # si l'allée n'est pas encore dans le groupe on la crée
                groupes[allee_finale].append((allee_str,position)) # on  garde le code original pour réference
            else:
                print(f"DEBUG: Format de point inattendu: {point}")
        print(f"DEBUG: Groupes après filtrage: {list(groupes.keys())}")

        #trier les points dans chaque allée par leur positon y
        for allee in groupes:
            #determoiner le sens de l'allée
            if len(allee) == 2:
                if allee in ['BB','DD','FF','HH']:
                    base = allee[1]
                else:
                    base = allee[0]
                #sens = self.hangar.sens.get(base,1)
            else:
                base = allee
                #sens = self.hangar.sens.get(base,1)
            sens = self.hangar.sens.get(base,1)
            #Trier selon le sens
            if sens ==1:
                groupes[allee].sort(key = lambda p: self.hangar.points[p][1]) #croissant
            else:
                groupes[allee].sort(key = lambda p: self.hangar.points[p][1], reverse=True)
        return groupes

    def alterner_allee(self, groupes:Dict[str,List[Tuple[str,int]]], hangar: Hangar) -> List[str]:
        """
        Alterneé de maniere : premier montant, dernier descendant, alternance entre les deux     
        """
        # un dictionnaire en entrée des allées deja grouper
        #retourne une alternance montée -descente de sorte que le premier element du groupe soit une allée montante et le dernier une allée descente.
        if not groupes:
            return []
        #separer les montantes et les descendantes
        montantes = []
        descendantes = []

        for allee in groupes.keys():
            #determiner le sens
            if len(allee) == 2:
                if allee in ['BB','DD','FF','HH','AB']: # les descentes speciciales
                    base = allee[1]
                else:
                    base = allee[0]
            else:
                base = allee
            
            sens = hangar.sens.get(base,1)
            if sens ==1:
                montantes.append(allee)
            else:
                descendantes.append(allee)
        #Trier les allées
        montantes.sort()
        descendantes.sort()
        #si pas de montante, retourner toutes les descendantes
        if not montantes:
            return descendantes
        
        #si pas de descendante, retourne toutes les montantes
        if not descendantes:
            return montantes
        
        #creer l'alternance
        ordre = []
        min_len = min(len(montantes),len(descendantes))
        for i in range(min_len):
            ordre.append(montantes[i])
            ordre.append(descendantes[i])
        #ajouter les restes
        if len(montantes) > len(descendantes):
            for i in range(min_len, len(montantes)):
                ordre.append(montantes[i])
        elif len(descendantes) > len(montantes):
            for i in range(min_len, len(descendantes)):
                ordre.append(descendantes[i])
        
        #obligation: premier = montante et dernier = descendantes
        if ordre:
            #verifier la premiere allée
            premier = ordre[0]
            if len(premier)==2 and premier in ['BB','DD','FF','HH','AB']:
                base_premier = premier[1]
            elif len(premier)==2 :
                base_premier = premier[0]
            else:
                base_premier = premier
            
            if hangar.sens.get(base_premier,1) != 1:
                #premier n'est pas montante, trouver un montant pour echanger
                for i in range(1,len(ordre)):
                    alle_test = ordre[i]
                    if len(alle_test) == 2 and alle_test in ['BB','DD','FF','HH','AB']:
                        base_test = alle_test[1]
                    elif len(alle_test)==2 :
                        base_test= alle_test[0]
                    else:
                        base_test = alle_test
                    
                    if hangar.sens.get(base_test,1) == 1:
                        ordre[0],ordre[i] = ordre[i],ordre[0]
                        break

            #verifier la derniere allée
            dernier = ordre[-1]
            if len(dernier)==2 and dernier in ['BB','DD','FF','HH','AB']:
                base_dernier = dernier[1]
            elif len(dernier)==2 :
                base_dernier = dernier[0]
            else:
                base_dernier = dernier
            if hangar.sens.get(base_dernier,1) != -1:
                # dernier n'est pas descendanat, trouver un descendant pour echanger
                for i in range(len(ordre)-2,-1,-1):
                    alle_test = ordre[i]
                    if len(alle_test)==2 and alle_test in ['BB','DD','FF','HH','AB']:
                        base_test = alle_test[1]
                    elif len(alle_test)==2:
                        base_test = alle_test[0]
                    else:
                        base_test = alle_test
                    if hangar.sens.get(base_test,1) == -1:
                        ordre[-1], ordre[i] = ordre[i], ordre[-1]
                        break
        return ordre
    
    ##ETAPE 2:
    #    - Partitionner une allée en 2 niveau: niveau haut et bas. 
    #    - organiniser les points dans chaque partie du niveau
    #    - définir combien des points dans chaque partie.
    def _analyser_parties_allee(self,allee:str)-> Dict:
        """
        Analyse dans quelle(s) partie(s) se trouvent les points d'une allée

        :param allee: code de l'allée (ex: 'A','B')
        :type allee: str
        :return: dictionnaire avec analyse des parties
        :rtype: Dict
        """
        #verifier que l'allée existe dans les groupes
        if allee not in self.groupes_by_allee:
            return {}
        
        #recuperer les points de cette allée
        points = self.groupes_by_allee[allee]

        # DEBUG
        print(f"\nDEBUG _analyser_parties_allee pour '{allee}':")
        print(f"  Total points: {len(points)}")
        for p in points:
            code, num = p
            x,y = self.hangar.points[p]
            print(f"    {code}{num}: y={y}")
        
        # Déterminer le sens
        if len(allee) == 2:
            if allee in ['BB','DD','FF','HH']:
                base = allee[1]
            else:
                base = allee[0]
        else:
            base = allee        
        
        sens = self.hangar.sens.get(base,1)
        
        # CORRECTION IMPORTANTE : Trier TOUS les points d'abord selon le sens
        if sens == 1:  # montée
            points_tries = sorted(points, key=lambda p: self.hangar.points[p][1])  # croissant
        else:  # descente
            points_tries = sorted(points, key=lambda p: self.hangar.points[p][1], reverse=True)  # décroissant
        
        print(f"  Points triés (sens={'montée' if sens==1 else 'descente'}):")
        for p in points_tries:
            code, num = p
            x,y = self.hangar.points[p]
            print(f"    {code}{num}: y={y}")


        #determiner le milieu de l'allée
        milieu = self.hangar.Longueur/2

        #séparer les points en parties basse et haute
        partie_basse = []
        partie_haute = []

        for point in points_tries:
            x,y = self.hangar.points[point]
            if y <= milieu:
                partie_basse.append(point)
            else:
                partie_haute.append(point)

        return {
            'allee':allee,
            'sens':'montée' if sens == 1 else 'descente',
            'partie_basse': partie_basse,
            'partie_haute': partie_haute,
            'a_partie_basse': len(partie_basse) > 0,
            'a_partie_haute': len(partie_haute) > 0,
            'total_points': len(points),
            'points_basse': len(partie_basse),
            'points_haute': len(partie_haute)
        }

    def afficher_partitions(self):
        """
        Affiche l'analyse des parties pour toutes les allées

        :param self: Description
        """
        print("\n" + "="*60)
        print("Etape 2 - ANALYZE DES PARTIES HAUTE/BASSE PAR allée")
        print("="*60)

        for allee in self.groupes_by_allee.keys():
            analyse = self._analyser_parties_allee(allee)
            print(f"\nAllée {allee} ({analyse['sens']}):")
            print(f" Total points: {analyse['total_points']}")

            if analyse['a_partie_basse']:
                points_str = ",".join([f"{p[0]}{p[1]}(y={self.hangar.points[p][1]:.0f})" for p in analyse['partie_basse']])
                print(f"Partie basse : {analyse['points_basse']} point(s) -> {points_str}")
            if analyse['a_partie_haute']:
                points_str = ",".join([f"{p[0]}{p[1]}(y={self.hangar.points[p][1]:.0f})" for p in analyse['partie_haute']])
                print(f"Partie haute : {analyse['points_haute']} point(s) -> {points_str}")


    ## ETAPE 3:
    #    - Construire le graphe des partitions
    #    - pacourir ou passer par chaque partition une et une seule fois en respectant le sens
    def construire_graphe_partitions(self):
        """
        Etape 3: construire le graphe des partitions 
        
        Returns:
            Dictionnaire avec deux clés: 'noeuds' et 'aretes'
        """
        noeuds = []
        for allee in self.groupes_by_allee.keys():
            analyse = self._analyser_parties_allee(allee)

            #créer un noeud pour la partie basse si elle existe
            if analyse['a_partie_basse']:
                id_noeud = f"{allee}_basse"
                noeud_basse = {
                    'id':id_noeud,
                    'allee':allee,
                    'type':'basse',
                    'sens':analyse['sens'],
                    'points':analyse['partie_basse'],
                    'nb_points':analyse['points_basse'],
                    'is_partie_basse':True,
                    'is_partie_haute': False
                }
                noeuds.append(noeud_basse)
            #créer un noeud pour la partie haute si elle existe
            if analyse['a_partie_haute']:
                id_noeud = f"{allee}_haute"
                noeud_haute = {
                    'id':id_noeud,
                    'allee':allee,
                    'type':'haute',
                    'sens':analyse['sens'],
                    'points':analyse['partie_haute'],
                    'nb_points':analyse['points_haute'],
                    'is_partie_basse':False,
                    'is_partie_haute': True
                }
                noeuds.append(noeud_haute)
        #Graphe initial :
        graphe = {
            'noeuds': noeuds,
            'aretes': [],
            'nb_noeuds': len(noeuds),
            'nb_aretes':0
        }
        return graphe
    
    def affiche_graphe_partitions(self, graphe=None):
        """Affiche le graphe des partitions"""
        if graphe is None:
            graphe = self.construire_graphe_partitions()
        
        print("\n" + "="*60)
        print("ÉTAPE 3 - GRAPHE DES PARTITIONS (sans arêtes)")
        print("="*60)
        
        print(f"\nNombre total de partitions (nœuds): {graphe['nb_noeuds']}")
        
        print("\nDétail des nœuds:")
        for i, noeud in enumerate(graphe['noeuds'], 1):
            points_str = ", ".join([f"{p[0]}{p[1]}" for p in noeud['points']])
            print(f"  {i}. {noeud['id']}:")
            print(f"     Allée: {noeud['allee']}, Type: {noeud['type']}, Sens: {noeud['sens']}")
            print(f"     Points: {points_str} ({noeud['nb_points']} points)")
        
        print(f"\nArêtes: {graphe['nb_aretes']} (à définir à l'étape 4)")
    
    def visualiser_graphe_partitions(self, graphe=None):
        """
        Ultra simple: juste des ronds colorés
        """
        if graphe is None:
            graphe = self.construire_graphe_partitions()
        
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Disposer en cercle
        n = len(graphe['noeuds'])
        
        for i, noeud in enumerate(graphe['noeuds']):
            angle = 2 * np.pi * i / n
            x = np.cos(angle) * 3
            y = np.sin(angle) * 3
            
            # Couleur
            couleur = 'blue' if noeud['type'] == 'basse' else 'red'
            
            # Rond
            cercle = plt.Circle((x, y), 0.4, 
                            facecolor=couleur, 
                            edgecolor='black', 
                            linewidth=2)
            ax.add_patch(cercle)
            
            # Texte
            ax.text(x, y, f"{noeud['id']}\n{noeud['nb_points']}p", 
                ha='center', va='center', 
                fontsize=9, color='white', fontweight='bold')
        
        # Cadre invisible
        ax.set_xlim(-4, 4)
        ax.set_ylim(-4, 4)
        ax.set_aspect('equal')
        ax.axis('off')
        
        plt.tight_layout()
        return fig, ax

    ## ETAPE 4:
    #    - definir les points d'entrée et de sortie d'une partition
    #    - calcule de la distance interne de chaque partitions (calcul pouvant se faire une fois)
    #    - trouver un ordre de parcours de ces partitions en minimisant la distance .
    #    - deployer les élements de chaque partition equivaut à l'ordre du parcours de tous les points. 

    def _points_acces_partition(self,noeud:Dict):
        """
        Définir les points d'entée et de sortie d'une partition
        Règles: 
            - partie basse : entrée en Niveau 1(0), sortie en Niveau 2 (L/2)
            - partie haute : entrée en Niveau 3(L), sortie en Niveau 2 (L/2)
        """
        allee = noeud['allee']
        #coordonnée x du centre de l'allée
        if len(allee)==2:
            if allee in ['BB','DD','FF','HH','AB']:
                allee_base = allee[1]
            else:
                allee_base = allee[0]
        else:
            allee_base= allee
        
        sens = self.hangar.sens.get(allee_base,1)
        #coordonnée x du centre de l'allée
        x_centre = self.hangar.centres.get(allee_base)
        if x_centre is None:
            x_centre = self.hangar.centres.get(allee[0],0)
        
        #RECUPERER LES POINTS REELS DE LA PARTITION
        points = noeud['points']

        if not points:
            #Fallback si les partitions sont vides(ne devrait pas arriver)
            if noeud['type'] == 'basse':
                if sens == 1:
                    entree = ('ENTREE_FALLBACK',(x_centre,1))
                    sortie = ('SORTIE_FALLBACK',(x_centre, self.hangar.Longueur/2))
                else:
                    entree = ('ENTREE_FALLBACK', (x_centre,self.hangar.Longueur/2))
                    sortie = ('SORTIE_FALLBACK',(x_centre,1))
            else:
                if sens == 1:
                    entree = ('ENTREE_FALLBACK',(x_centre,self.hangar.Longueur/2))
                    sortie = ('SORTIE_FALLBACK',(x_centre,self.hangar.Longueur))

                else:
                    entree = ('ENTREE_FALLBACK',(x_centre,self.hangar.Longueur))
                    sortie = ('SORTIE_FALLBACK',(x_centre,self.hangar.Longueur/2))
        else:
            #Points Réels. premier et dernier selon le sens
            if sens == 1:
                premier_point = points[0]
                dernier_point = points[-1]
            else:
                premier_point = points[-1]
                dernier_point = points[0]
            
            coord_premier = self.hangar.points[premier_point]
            coord_dernier = self.hangar.points[dernier_point]

            entree = ('ENTREE_REEL',coord_premier)
            sortie = ('SORTIE_REEL',coord_dernier)
        return {
            'entree':entree,
            'sortie':sortie,
            'distance_interne': self._calculer_distance_interne(entree[1], sortie[1], noeud)
        }
    
    #TODO:
    def _points_acces_realistes(self, noeud):
        """
        Points d'accès réalistes - au lieu de seulement (0, L/2, L)
        """
        options = []
        
        # Option 1 : Points fixes originaux (gardée)
        fixe = self._points_acces_partition(noeud)
        options.append(fixe)
        
        # Option 2 : Points RÉELS de la partition comme alternatives
        points = noeud['points']
        
        if points:
            # ENTRÉE : Premier point si proche du début
            premier = points[0]
            coord_premier = self.hangar.points[premier]
            y_premier = coord_premier[1]
            
            # SORTIE : Dernier point si proche de la fin  
            dernier = points[-1]
            coord_dernier = self.hangar.points[dernier]
            y_dernier = coord_dernier[1]
            
            L = self.hangar.Longueur
            sens = noeud['sens']
            
            # Alternative réaliste selon le contexte
            if sens == 'montée':
                if y_premier < L/3:  # Point proche du bas
                    option_alt = {
                        'entree': ('ENTREE_REAL', coord_premier),
                        'sortie': fixe['sortie'],
                        'distance_interne': abs(y_dernier - y_premier)  # Estimation simple
                    }
                    options.append(option_alt)
            else:  # descente
                if y_dernier > 2*L/3:  # Point proche du haut
                    option_alt = {
                        'entree': fixe['entree'],
                        'sortie': ('SORTIE_REAL', coord_dernier),
                        'distance_interne': abs(y_dernier - y_premier)
                    }
                    options.append(option_alt)
        
        return options
    
    def _calculer_distance_interne(self, point_entree:Tuple[float,float],point_sortie:Tuple[float,float],noeud:Dict) -> float:
        """
        Calcule la distance pour traverser la partition
        (distance d'entrée à sortie selon le sens)
        """
        #créer des points factices pour utiliser la méthode distance du hangar
        allee = noeud['allee']
        #on crée des identifiants factices pour les points d'entrée/sortie
        id_entree = (allee,-1)
        id_sortie = (allee,-2)

        #ajouter ces points temporairement au hangar
        self.hangar.points[id_entree] = point_entree
        self.hangar.points[id_sortie] = point_sortie

        #calculer la distance selon le sens
        distance = self.hangar.distance(id_entree,id_sortie)

        #nettoyage des points temporaires
        del self.hangar.points[id_entree]
        del self.hangar.points[id_sortie]

        return distance
    
    def _matrice_distances_partitions(self):
        """
        Calcule la matrice des distances entre toutes les partitions
        returns:
            tuple:(matrice,liste_noeuds,points_acces)

        """
        if self.graphe_partitons is None:
            return None
        
        noeuds = self.graphe_partitons['noeuds']
        n = len(noeuds)
        #definir les points d'accès pour chaque partition
        points_acces = []
        for noeud in noeuds:
            acces = self._points_acces_partition(noeud)
            points_acces.append(acces)
        #initialiser la matrice
        matrice = np.full((n,n), float('inf'))

        #remplir la matrice
        for i in range(n):
            for j in range(n):
                if i == j:
                    matrice[i][j]=0.0
                else:
                    #distance = distance(sortie_i -> entrée_j) + distance_interne_j
                    point_sortie_i = points_acces[i]['sortie'][1]
                    point_entree_j = points_acces[j]['entree'][1]

                    #utiliser les vraies allées
                    allee_i = noeuds[i]['allee']
                    allee_j = noeuds[j]['allee']


                    #Créer des points factices
                    id_sortie_i = (allee_i,-10-i)
                    id_entree_j = (allee_j,-20-j)


                    self.hangar.points[id_sortie_i] = point_sortie_i
                    self.hangar.points[id_entree_j] = point_entree_j

                    #calculer la distance externe
                    dist_externe = self.hangar.distance(id_sortie_i,id_entree_j)

                    #nettoyer
                    del self.hangar.points[id_sortie_i]
                    del self.hangar.points[id_entree_j]

                    #distance totale
                    matrice[i][j] = dist_externe + points_acces[j]['distance_interne']
        return matrice, noeuds, points_acces
    
    def tester_matrice_distances(self, graphe=None):
        """
        Test complet de la matrice des distances
        """
        print("\n" + "="*60)
        print("TEST ÉTAPE 4 - MATRICE DES DISTANCES ENTRE PARTITIONS")
        print("="*60)
        
        if graphe is None:
            graphe = self.construire_graphe_partitions()
        
        # 1. Afficher les partitions
        print(f"\nNombre de partitions: {len(graphe['noeuds'])}")
        for i, noeud in enumerate(graphe['noeuds']):
            print(f"  {i}. {noeud['id']} (Allée: {noeud['allee']}, Type: {noeud['type']}, Sens: {noeud['sens']})")
        
        # 2. Calculer la matrice
        matrice, noeuds, points_acces = self.matrice_distances_partitions(graphe)
        
        # 3. Afficher les points d'accès
        print("\nPoints d'accès des partitions:")
        for i, (noeud, acces) in enumerate(zip(noeuds, points_acces)):
            print(f"\n  Partition {noeud['id']}:")
            print(f"    Entrée: ({acces['entree'][1][0]:.1f}, {acces['entree'][1][1]:.1f})")
            print(f"    Sortie: ({acces['sortie'][1][0]:.1f}, {acces['sortie'][1][1]:.1f})")
            print(f"    Distance interne: {acces['distance_interne']:.1f} m")
        
        # 4. Afficher la matrice
        print(f"\nMatrice des distances ({len(matrice)}x{len(matrice)}):")
        print("     ", end="")
        for j in range(len(matrice)):
            print(f"{noeuds[j]['id']:>10}", end="")
        print()
        
        for i in range(len(matrice)):
            print(f"{noeuds[i]['id']:5}", end="")
            for j in range(len(matrice)):
                if matrice[i][j] == float('inf'):
                    print(f"{'INF':>10}", end="")
                elif i == j:
                    print(f"{'0':>10}", end="")
                else:
                    print(f"{matrice[i][j]:>10.1f}", end="")
            print()
        
        # 5. Analyser la connexité
        print("\nAnalyse de connexité:")
        n = len(matrice)
        for i in range(n):
            inf_count = sum(1 for j in range(n) if j != i and matrice[i][j] == float('inf'))
            if inf_count > 0:
                print(f"  Partition {noeuds[i]['id']}: {inf_count} partitions inaccessibles")
            else:
                print(f"  Partition {noeuds[i]['id']}: accessible à toutes les autres partitions")
        
        return matrice, noeuds, points_acces

        ## ETAPE 4: ALGORITHME GLOUTON
    
    #TODO:
    def _distance_contrainte(self, point1, point2):
        """
        Distance avec estimation si chemin impossible
        """
        id1 = ("TEMP", 9991)
        id2 = ("TEMP", 9992)
        
        self.hangar.points[id1] = point1
        self.hangar.points[id2] = point2
        
        dist = self.hangar.distance(id1, id2)
        
        del self.hangar.points[id1]
        del self.hangar.points[id2]
        
        # Si chemin impossible, ESTIMER au lieu de inf
        
        if dist == float('inf'):
            # Estimation euclidienne + pénalité
            dx = point2[0] - point1[0]
            dy = point2[1] - point1[1]
            distance_euclid = np.sqrt(dx*dx + dy*dy)
            
            #pénalité selon la configuration (voir le document)
            #Si changement d'allée nécessaire: pénalité forte
            allee1 = self._trouver_allee_plus_proche(point1)
            allee2 = self._trouver_allee_plus_proche(point2)

            if allee1 != allee2:
                #changement d'allée : nécessite un niveau intermédiaire
                penalite = 2.0 #100% de pénalité
            else:
                # meme allée mais sens incompatible
                penalite = 1.5 # 50% de pénalité
            estimer = distance_euclid * penalite

            #DEBUG
            print(f" Estimation: {distance_euclid:.1f} x {penalite} = {estimer:.1f}")

            return estimer
        
        return dist
    def _trouver_allee_plus_proche(self,point):
        """Trouver l'allée la plus proche d'un point """
        x,y = point
        allee_proche = None
        dist_min = float('inf')

        for allee, x_centre in self.hangar.centres.items():
            distance_laterale = abs(x - x_centre)
            if distance_laterale < dist_min:
                dist_min = distance_laterale
                allee_proche = allee
        return allee_proche
    
        

def visualiser_graphe_partitions(self, graphe=None):
    """
    Visualise les partitions (version simple)
    """
    if graphe is None:
        graphe = self.construire_graphe_partitions()
    
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Tracer le hangar
    self.hangar.dessiner("Partitions du hangar", ax=ax)
    
    # Tracer les partitions
    for noeud in graphe['noeuds']:
        # Obtenir les points d'accès
        acces = self.points_acces_partition(noeud)
        entree = acces['entree'][1]
        sortie = acces['sortie'][1]
        
        # Couleur selon le type
        couleur = 'blue' if noeud['type'] == 'basse' else 'red'
        
        # Tracer entrée et sortie
        ax.plot(entree[0], entree[1], '^', markersize=15, 
                color=couleur, markeredgecolor='black', zorder=15, label=f"Entrée {noeud['type']}")
        ax.plot(sortie[0], sortie[1], 'v', markersize=15,
                color=couleur, markeredgecolor='black', zorder=15, label=f"Sortie {noeud['type']}")
        
        # Tracer la ligne entre entrée et sortie
        ax.plot([entree[0], sortie[0]], [entree[1], sortie[1]], 
                '--', color=couleur, alpha=0.5, linewidth=2)
        
        # Texte avec l'ID
        ax.text((entree[0] + sortie[0])/2, (entree[1] + sortie[1])/2,
                noeud['id'], ha='center', va='center',
                fontsize=9, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    # Titre
    ax.set_title(f"Partitions: {len(graphe['noeuds'])} partitions", fontsize=12)
    
    # Légende
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='^', color='w', markerfacecolor='blue', 
               markersize=10, label='Entrée partie basse'),
        Line2D([0], [0], marker='v', color='w', markerfacecolor='blue', 
               markersize=10, label='Sortie partie basse'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='red', 
               markersize=10, label='Entrée partie haute'),
        Line2D([0], [0], marker='v', color='w', markerfacecolor='red', 
               markersize=10, label='Sortie partie haute'),
    ]
    ax.legend(handles=legend_elements, loc='upper left')
    
    plt.tight_layout()
    return fig, ax
    
# Test
if __name__ == "__main__":
    # Créer un hangar de test
    hangar_test = Hangar(Longueur=90, largeur_allee=5, r=2)
    
    # Définir des groupes de test
    groupes_test = {
        'BB': [('BB', 1), ('BB', 8)],      # Montée
        'B': [('B', 47)],                # Descente  
        'D': [('C', 3), ('C', 19)],      # Montée
        'F': [('A', 24), ('A', 45)],     # Descente
        'D': [('D', 12)],                # Descente
        'HH': [('G', 30)],                # Montée
    }
    # Définir une COMMANDE de test (liste de points)
    commande_test = [
        ('BB', 1), ('BB', 8),      # Allée BB
        ('B', 43),                 # Allée B
        ('C', 3), ('C', 19),       # Allée C
        ('A', 24), ('A', 45),      # Allée A
        ('D', 12),                 # Allée D
        ('HH', 30),                # Allée HH
    ]
    #création de l'optimiseur avec la commande
    opt = OptParcours(hangar_test,commande_test)
    
    print("=== TEST alterner_allee ===")
    ordre = opt.alterner_allee(opt.groupes_by_allee, hangar_test)
    print(f"Ordre alterné obtenu: {ordre}")


    # Afficher le sens de chaque allée
    print("\nVérification des sens:")
    for i, allee in enumerate(ordre):
        if len(allee) == 2:
            if allee in ['BB', 'DD', 'FF', 'HH', 'AB']:
                base = allee[1]
            else:
                base = allee[0]
        else:
            base = allee
        
        sens = hangar_test.sens.get(base, 1)
        print(f"  Position {i}: {allee} ({'montée' if sens==1 else 'descente'})")

    # Test Etape 3
    print("\n=== ETAPE 3 - GRAPHE DES PARTITIONS===")
    graphe_partitions = opt.construire_graphe_partitions()
    opt.affiche_graphe_partitions(graphe_partitions)
    #visualisation
    fig, ax = opt.visualiser_graphe_partitions(graphe_partitions)
    plt.show()

    print("\n ETAPE 4 - MATRICE DES DISTANCES")
    matrice, noeuds, points_acces = opt.tester_matrice_distances(graphe_partitions)

    # Test algorithme glouton
    print("\n" + "="*60)
    print("TEST algorithme glouton")
    print("="*60)

    #depart et arrivée 
    depart_test = (20,-10)
    arrivee_test = (20,25)
    parcours = opt.parcours_glouton(depart_test,arrivee_test,graphe_partitions)

    if parcours['complet']:
        print("\n Parcours complet trouvé")
    else:
        print("\n Parcours incomplet")

    




