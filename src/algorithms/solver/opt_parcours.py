from typing import List,Tuple,Dict,Set
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from geometry.hangar import Hangar
import matplotlib.pyplot as plt
import matplotlib.patches as patches 
#from graph.graph_collect_depot import GraphCollectWithDepot


class OptParcours:
    """
    Algorithme d'optimisation du parcours de collecte
    """

    def __init__(self,hangar,commande:List[Tuple[str,int]]):
        self.hangar = hangar
        self.commande = commande
        #placer la commande dans le hangar
        self.hangar.placer_commande(commande)
        self.groupes_by_allee = self.grouper_by_allee()
        self.afficher_partitions()


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
    def analyser_parties_allee(self,allee:str)-> Dict:
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
            partie_basse.sort(key=lambda p : self.hangar.points[p][1])
            partie_haute.sort(key=lambda p : self.hangar.points[p][1])
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
            analyse = self.analyser_parties_allee(allee)
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
            analyse = self.analyser_parties_allee(allee)

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
    #    - trouver un ordre de parcours de ces partitions en minimisant la distance .
    #    - deployer les élements de chaque partition equivaut à l'ordre du parcours de tous les points. 

    def points_acces_partition(self,noeud:Dict):
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
        L=self.hangar.Longueur
        L2 = L/2

        
        if noeud['type'] == 'basse': # à verifier 
            #partie basse : entrée par N1(0), sortie par N2(L/2)
            if sens == 1:
                entree = ('ENTREE',(x_centre,0))
                sortie = ('SORTIE',(x_centre, L2))
            else:
                entree = ('ENTREE',(x_centre,L2))
                sortie = ('SORTIE',(x_centre, 0))
        else: #partie HAUTE
            if sens == 1:
                entree = ('ENTREE',(x_centre,L2))
                sortie = ('SORTIE',(x_centre,L))
            else:
                entree = ('ENTREE',(x_centre,L))
                sortie = ('SORTIE',(x_centre,L2))
        return{
            'entree':entree,
            'sortie':sortie,
            'distance_interne': self.calculer_distance_interne(entree[1],sortie[1],noeud)
        }
    
    def calculer_distance_interne(self, point_entree:Tuple[float,float],point_sortie:Tuple[float,float],noeud:Dict) -> float:
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
    
    def matrice_distances_partitions(self,graphe=None):
        """
        Calcule la matrice des distances entre toutes les partitions
        returns:
            tuple:(matrice,liste_noeuds,points_acces)

        """
        if graphe is None:
            graphe = self.construire_graphe_partitions()
        noeuds = graphe['noeuds']
        n = len(noeuds)
        #definir les points d'accès pour chaque partition
        points_acces = []
        for noeud in noeuds:
            acces = self.points_acces_partition(noeud)
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

    




