from typing import List,Tuple,Dict,Set
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from geometry.hangar import Hangar
#from graph.graph_collect_depot import GraphCollectWithDepot


class OptParcours:
    """
    Algorithme d'optimisation du parcours de collecte
    """

    def __init__(self,hangar,commande:List[Tuple[str,int]]):
        self.hangar = hangar
        self.commande = commande
        self.groupes_by_allee = self.groupes_by_allee()




    #Construction de l'algorithme d'optimisation du parcours lors de la collecte
    ##ETAPE 1:
    #    - grouper les n points de chaque allées
    #    - ordonner les groupes  de maniere alternées montée,descente . et en combien de facons
    def grouper_by_allee(self):
        """ Groupe les points de la commande par allée """
        if not self.commande:
            print("commande vide")
            return {}
        
        groupes = {}
        for allee,position in self.commande:
            if allee not in groupes:
                groupes[allee]= [] # si l'allée n'est pas encore dans le groupe on la crée
            groupes[allee].append((allee,position))
        
        #trier les points dans chaque allée par leur positon y
        for allee in groupes:
            groupes[allee].sort(key = lambda p: self.hangar.points[p][1])
        return groupes

    def alterner_allee(groupes:Dict[str,List[Tuple[str,int]]], hangar: Hangar) -> List[str]:
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
    def analyser_parties_allee(self,allee:str)-> Dict:
        """
        Analyse dans quelle(s) partie(s) se trouvent les points d'une allée

        :param allee: code de l'allée (ex: 'A','B')
        :type allee: str
        :return: dictionnaire avec analyse des parties
        :rtype: Dict
        """
        #verifier que l'allée existe dans les groupes
        if allee not in self.grouper_by_allee:
            return {}
        
        #recuperer les points de cette allée
        points = self.grouper_by_allee[allee]

        #determiner le milieu de l'allée
        milieu = self.hangar.Longueur/2

        #séparer les points en parties basse et haute
        partie_basse = []
        partie_haute = []

        for point in points:
            x,y = self.hangar.points[point]
            if y <= milieu:
                partie_basse.append(point)
            else:
                partie_haute.append(point)
        #Trier selon le sens de l'allée
        #déterminer le sens
        if len(allee)==2:
            if allee in ['BB','DD','FF','HH','AB']:
                base = allee[1]
            else:
                base = allee[0]
        else:
            base = allee        
        sens = self.hangar.sens.get(base,1)

        #Pour une montée: du bas vers le haut
        #Pour une descente: du haut vers le bas
        if sens ==1: #cas 1 montée
            partie_basse.sort(key=lambda p:self.hangar.points[p][1]) #croissant
            partie_haute.sort(key=lambda p: self.hangar.points[p][1])
        else:
            partie_basse.sort(key=lambda p : self.hangar.points[p][1], reverse=True)
            partie_haute.sort(key=lambda p : self.hangar.points[p][1], reverse=True)
        return {
            'allee':allee,
            'sens':'montée' if sens == 1 else 'descente',
            'partie_basse': partie_basse,
            'partie_hausse': partie_haute,
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
            analyse = self.analyser_parties_allee(allee)
            print(f"\nAllée {allee} ({analyse['sens']}):")
            print(f" Total points: {analyse['total_points']}")

            if analyse['a_partie_basse']:
                for p in analyse['partie_basse']:
                    points_str = ",".join([f"{p[0]}{p[1]}(y={self.hangar.points[p][1]:.0f})"])
                print(f"Partie basse : {analyse['points_basse']} point(s) -> {points_str}")
            
            if analyse['a_partie_haute']:
                for p in analyse['partie_haute']:
                    points_str = ",".join([f"{p[0]}{p[1]}(y={self.hangar.points[p][1]:.0f})"])
                print(f"Partie basse : {analyse['points_basse']} point(s) -> {points_str}")

## ETAPE 3:
#    - Construire le graphe des partitions
#    - pacourir ou passer par chaque partition une et une seule fois en respectant le sens
# 
## ETAPE 4:
#    - trouver un ordre de parcours de ces partitions en minimisant la distance .
#    - deployer les élements de chaque partition equivaut à l'ordre du parcours de tous les points. 


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
        
        print("=== TEST alterner_allee ===")
        ordre = alterner_allee(groupes_test, hangar_test)
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
        # Afficher les partitions
        
        afficher_partitions()


