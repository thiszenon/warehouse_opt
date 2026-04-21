
"""
Docstring pour graph.graph_collect
Module : GraphCollect 

"""
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Tuple, Dict, Optional, Set
import json

from backend.src.geometry import Hangar
from backend.src.data.commandes import get_commandes
from backend.src.geometry.hangar_with_depot import HangarWithDepot
from backend.src.graph.graph_collect_depot import GraphCollectWithDepot


class GraphCollect:
    """
    Classe representant le graphe orienté pondéré pour notre systeme TSP asymetric
    """

    def __init__(self, hangar, commande: List[Tuple[str,int]]):

        self.hangar = hangar
        self.commande = commande
        self.sommets = commande
        self.n = len(commande) # pour le nombre des points à collecter

        #construire la matrice
        self.matrice = self._construire_matrice()

        #Graphe NetworkX orienté
        self.graph_nx = self._construire_graphe()

    #end __init__

    def _construire_matrice(self) -> np.ndarray:
        """
        Construit la matrice asymétrique des distances.
        """
        matrice = np.full(
            (self.n,self.n),
            float('inf'),
            dtype=float
        )
        for i in range(self.n):
            for j in range(self.n):
                if i==j :
                    matrice[i][j] = 0.0
                else:
                    p= self.sommets[i]
                    q=self.sommets[j]
                    matrice[i][j] = self.hangar.distance(p,q)
            #end for
        #end for
        return matrice
    #end __construire_matrice

    def afficher_matrice(self,matrice):
        print("Affichage de la matrice...\n")
        print(matrice)

    def _construire_graphe(self) -> nx.DiGraph:
        """
        Construit un graphe Orient NetworkX
        """
        Graph = nx.DiGraph()

        #Ajouter les sommets
        for i, (allee,numero) in enumerate(self.sommets):
            coords = self.hangar.points.get((allee,numero),(0,0))
            Graph.add_node(i, 
                        label = f"{allee}{numero}",
                        allee = allee,
                        numero = numero,
                        x=coords[0],
                        y=coords[1],
                        sens= self.hangar.sens[allee]
                        )
        #Ajouter les arcs orientés
        for i in range(self.n):
            for j in range(self.n):
                if i!= j and self.matrice[i][j] < float('inf'):
                    Graph.add_edge(i,j,
                                    weight = self.matrice[i][j],
                                    asymetric = abs(self.matrice[i][j] - self.matrice[j][i])> 0.1 if self.matrice[j][i] < float('inf') else True)
        #end for
        return Graph
    
    def visualiser(self):
        """
        Visulisation simple du graphe
        """
        fig, (ax1, ax2) = plt.subplots(1,2,figsize=(14,7))

        # graphique 
        self.hangar.dessiner("Points dans le hangar")

        # visualiser le graphe orienté
        self._dessiner_graphe_oriented(ax2)

        plt.suptitle(f"Graphe de collecte - {self.n} points", fontsize=14)
        plt.tight_layout()
        plt.show()
    #end visualiser
    def visualiser_graphe_schematique(self):
        """
        Visualise le graphe avec un layout circulaire pour plus de clarté
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
        
        # 1. Hangar avec points réels (optionnel)
        self.hangar.dessiner("Points dans le hangar")
        
        # 2. Graphe schématique
        ax2.set_title("Graphe schématique - Layout circulaire")
        
        # Layout circulaire pour éviter les superpositions
        pos = nx.circular_layout(self.graph_nx)
        
        # 2.1 Dessiner les nœuds
        couleurs = []
        labels = {}
        for i in range(self.n):
            # Couleur selon type d'allée
            if self.graph_nx.nodes[i]['sens'] == 1:
                couleurs.append('red')  # Montante
            else:
                couleurs.append('blue')  # Descendante
            
            # Label avec informations
            labels[i] = f"{self.graph_nx.nodes[i]['label']}"
        
        nx.draw_networkx_nodes(self.graph_nx, pos, ax=ax2,
                            node_size=600,
                            node_color=couleurs,
                            edgecolors='black',
                            linewidths=2)
        
        # 2.2 Dessiner les labels
        nx.draw_networkx_labels(self.graph_nx, pos, labels, ax=ax2,
                            font_size=11, font_weight='bold')
        
        # 2.3 Dessiner les arcs
        arcs_a_dessiner = []
        poids_arcs = {}
        
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.matrice[i][j] < float('inf'):
                    arcs_a_dessiner.append((i, j))
                    poids_arcs[(i, j)] = f"{self.matrice[i][j]:.1f}m"
        
        # Dessiner les arcs avec flèches
        nx.draw_networkx_edges(self.graph_nx, pos,
                            edgelist=arcs_a_dessiner,
                            ax=ax2,
                            arrowstyle='->',
                            arrowsize=20,
                            edge_color='gray',
                            width=1.5,
                            alpha=0.7,
                            connectionstyle='arc3,rad=0.1')  # Légère courbure
        
        # Afficher les poids (seulement quelques-uns pour lisibilité)
        if len(poids_arcs) <= 15:  # Si peu d'arcs, tous les afficher
            nx.draw_networkx_edge_labels(self.graph_nx, pos,
                                        edge_labels=poids_arcs,
                                        ax=ax2, font_size=9)
        else:
            # Sinon, afficher seulement les poids des arcs les plus courts
            edge_labels_select = {}
            for i in range(self.n):
                # Trouver l'arc le plus court partant de chaque nœud
                distances = [(j, self.matrice[i][j]) 
                            for j in range(self.n) 
                            if i != j and self.matrice[i][j] < float('inf')]
                if distances:
                    j, dist = min(distances, key=lambda x: x[1])
                    edge_labels_select[(i, j)] = f"{dist:.1f}m"
            
            nx.draw_networkx_edge_labels(self.graph_nx, pos,
                                        edge_labels=edge_labels_select,
                                        ax=ax2, font_size=9)
        
        # 2.4 Informations
        info_text = f"Points: {self.n}\n"
        info_text += f"Arcs possibles: {len(arcs_a_dessiner)}/{self.n*(self.n-1)}\n"
        info_text += f"● Rouge: allées montantes\n"
        info_text += f"● Bleu: allées descendantes"
        
        ax2.text(0.02, 0.02, info_text, transform=ax2.transAxes,
                fontsize=10, verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        ax2.axis('on')
        ax2.grid(True, alpha=0.2)
        
        plt.tight_layout()
        plt.show()

    def _dessiner_graphe_oriented(self,ax):
        """
        Dessine le graphe orienté sur l'axe donné
        """
        if self.n == 0:
            ax.text(0.5,0.5, "aucun point", ha='center',va='center')
            return
        #positions des noeuds selon leurs coordonnées reelles
        pos={}
        for i in range(self.n):
            node_data = self.graph_nx.nodes[i]
            pos[i] = (node_data['x'], node_data['y'])
        
        #1. dessiner les noeuds
        couleurs = []
        for i in range(self.n):
            #rouge pour les allées montantes et bleu pour les descente
            if self.graph_nx.nodes[i]['sens']==1:
                couleurs.append('red')
            else:
                couleurs.append('blue')
        nx.draw_networkx_nodes(self.graph_nx, pos, ax=ax,
                               node_size=400,
                               node_color=couleurs,
                               edgecolors='black',
                               linewidths=2)
        #2. dessiner les labels
        labels = {i: self.graph_nx.nodes[i]['label'] for i in range(self.n)}
        nx.draw_networkx_labels(self.graph_nx, pos, labels,ax=ax, font_size=11,font_weight='bold')

         
        # Dessiner les arcs avec courbure
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.matrice[i][j] < float('inf'):
                    # Courbure différente selon la direction
                    if self.matrice[j][i] < float('inf'):  # Arc dans les deux sens
                        # Arc aller : courbure positive
                        nx.draw_networkx_edges(
                            self.graph_nx, pos,
                            edgelist=[(i, j)],
                            ax=ax,
                            arrowstyle='->',
                            arrowsize=15,
                            edge_color='red',
                            width=1.5,
                            alpha=0.7,
                            connectionstyle='arc3,rad=0.2'  # Courbure
                        )
                        # Arc retour : courbure négative
                        nx.draw_networkx_edges(
                            self.graph_nx, pos,
                            edgelist=[(j, i)],
                            ax=ax,
                            arrowstyle='->',
                            arrowsize=15,
                            edge_color='blue',
                            width=1.5,
                            alpha=0.7,
                            connectionstyle='arc3,rad=-0.2'  # Courbure opposée
                        )
                    else:  # Arc dans un seul sens
                        nx.draw_networkx_edges(
                            self.graph_nx, pos,
                            edgelist=[(i, j)],
                            ax=ax,
                            arrowstyle='->',
                            arrowsize=15,
                            edge_color='gray',
                            width=1.5,
                            alpha=0.7
                        )
            #configuration
            ax.set_title("graphe orienté des distances")
            ax.set_xlabel("Position x (m)")
            ax.set_ylabel("Position y (m)")
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal')
    #end __dessiner_graphe_oriented

    def visualiser_avec_details(self, point1, point2):
        """
        Visualiser le hangar avec un chemin spécifique détaillé
        
        :param self: Description
        :param point1: Description
        :param point2: Description
        """
        fig, (ax1,ax2,ax3)= plt.subplots(1,3, figsize=(18,6))
        #1 Hangar avec le chemin tracé
        self.hangar.dessiner("Hangar avec chemin")
        #Tracer le chemin spécifique
        resultat = self.hangar.tracer_chemin(point1,point2,ax1, couleur='red',style='-', alpha=0.8)
        #2. Graphe orienté
        self._dessiner_graphe_oriented(ax2)

        #3. Détails du chemin
        ax3.axis('off')

        if resultat['distance'] == float('inf'):
            ax3.text(0.5,0.5, f"IMPOSSIBLE\n{point1} -> {point2}", ha='center', va='center', fontsize=16,color='red')
        else:
            details = f"Chemin: {point1}->{point2}\n"
            details += f"Distance: {resultat['distance']:.1f}m\n"
            details += f"Type: {resultat.get('type', 'via_niveau')}\n"

            if 'niveau' in resultat:
                details += f"Niveau utilisé: {resultat['niveau']} (y={resultat['y_niveau']}m)\n"
                details += "\nEtapes: \n"
                for i, segment in enumerate(resultat['segments'],1):
                    details +=f"{i}. {segment}\n"
                ax3.text(0.05, 0.95, details, transform=ax3.transAxes, fontsize=11, verticalalignment='top',bbox=dict(boxstyle='round', facecolor='lightyellow',alpha=0.8))
        #Ajouter les points selectionnés en surbrillance
        for i, point in enumerate([point1, point2]):
            if point in self.hangar.points:
                x,y = self.hangar.points[point]
                for ax in [ax1,ax2]:
                    ax.plot(x,y,'o', markersize=15,color='yellow' if i==0 else 'orange', markeredgecolor='black', markeredgewidth=2, zorder=20)
                    ax.text(x,y+3, f"{point[0]}{point[1]}",ha='center', va='bottom', fontsize=12, fontweight='bold',bbox=dict(boxstyle='round', facecolor='white',alpha=0.8))
                    plt.suptitle(f"Détails du chemin entre {point1} et {point2}", fontsize=14)
                    plt.tight_layout()
                    plt.show()
                    return resultat
    def visuliser_tous_chemins(self):
        """
        Visualise tous les chemins possibles entre les points
        """
        fig ,axes = plt.subplots(self.n, self.n, figsize=(self.n*4, self.n*4))
        for i in range(self.n):
            for j in range(self.n):
                ax = axes[i,j] if self.n > 1 else axes
                ax.clear()

                if i == j:
                    ax.text(0.5,0.5, f"Même point\n{self.commande[i]}", ha='center', va='center')
                    ax.set_title(f"{self.commande[i]} -> {self.commande[j]}")
                    continue
                p= self.commande[i]
                q=self.commande[j]

                #dessiner le hangar de maniere minimale
                ax.set_xlim(-5, self.hangar.largeur_totale +5)
                ax.set_ylim(-5, self.hangar.Longueur +5)
                ax.grid(True, alpha=0.3)

                #Tracer le chemin
                resultat = self.hangar.tracer_chemin(p,q,ax,couleur='blue' if self.matrice[i][j] < float('inf') else 'red',
                    style = '-' if self.matrice[i][j] < float('inf') else ':')
                #Marquer les points
                for point, couleur in [(p,'green'), (q,'red')]:
                    if point in self.hangar.points:
                        x,y = self.hangar.points[point]
                        ax.plot(x,y, 'o', markersize=10, color=couleur)
                        ax.text(x,y+2, f"{point[0]}{point[1]}", ha='center', fontsize=9)

                        #titre avec la distance
                        if resultat['distance'] < float('inf'):
                            ax.set_title(f"{p}->{q}: {resultat['distance']:.1f}m", color='green', fontsize=10)
                        else:
                            ax.set_title(f"{p}->{q}: Impossible", color='red', fontsize=10)
        plt.suptitle("Tous les chemins possibles", fontsize=16)
        plt.tight_layout()
        plt.show()
    
    def visualiser_chemin_sur_hangar(self, point_depart, point_arrivee):
        """
        Affiche 2 figures séparées :
        1. Le hangar avec le chemin tracé
        2. Le graphe orienté
        """
        # FIGURE 1 : Hangar avec chemin
        fig1, ax1 = plt.subplots(figsize=(10, 8))
        
        # Utiliser votre méthode dessiner existante
        self.hangar.dessiner(f"Chemin: {point_depart} → {point_arrivee}", ax=ax1)
        
        # Tracer le chemin spécifique
        resultat = self.hangar.tracer_chemin(point_depart, point_arrivee, 
                                            ax=ax1, couleur='red', 
                                            style='-', alpha=0.8, linewidth=3)
        
        # Mettre en évidence les points de départ/arrivée
        for point, couleur, label in [(point_depart, 'green', 'Départ'),
                                    (point_arrivee, 'orange', 'Arrivée')]:
            if point in self.hangar.points:
                x, y = self.hangar.points[point]
                ax1.plot(x, y, 'o', markersize=15, color=couleur,
                        markeredgecolor='black', markeredgewidth=2, zorder=20)
                ax1.text(x, y + 3, f"{label}\n{point[0]}{point[1]}", 
                        ha='center', va='bottom', fontsize=11, fontweight='bold',
                        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # FIGURE 2 : Graphe orienté
        fig2, ax2 = plt.subplots(figsize=(10, 8))
        self._dessiner_graphe_oriented(ax2)
        
        # Mettre en évidence le même chemin dans le graphe
        i = self.commande.index(point_depart) if point_depart in self.commande else -1
        j = self.commande.index(point_arrivee) if point_arrivee in self.commande else -1
        
        if i != -1 and j != -1:
            # Dessiner l'arc correspondant en surbrillance
            pos = {idx: (self.graph_nx.nodes[idx]['x'], 
                        self.graph_nx.nodes[idx]['y']) 
                for idx in range(self.n)}
            
            if self.matrice[i][j] < float('inf'):
                nx.draw_networkx_edges(
                    self.graph_nx, pos,
                    edgelist=[(i, j)],
                    ax=ax2,
                    arrowstyle='->',
                    arrowsize=25,
                    edge_color='red',
                    width=3,
                    alpha=0.9
                )
        
        plt.tight_layout()
        plt.show()
        
        return resultat

    def visualiser_tous_chemins_sur_hangar(self):
        """
        Trace tous les chemins possibles sur un seul hangar
        avec des couleurs différentes
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 1. Hangar avec tous les chemins
        self.hangar.dessiner("Tous les chemins possibles", ax=ax1)
        
        couleurs = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'gray']
        couleur_idx = 0
        
        # Tracer tous les chemins possibles
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.matrice[i][j] < float('inf'):
                    p = self.commande[i]
                    q = self.commande[j]
                    
                    couleur = couleurs[couleur_idx % len(couleurs)]
                    
                    # Tracer le chemin
                    self.hangar.tracer_chemin(p, q, ax=ax1,
                                            couleur=couleur,
                                            style='-',
                                            alpha=0.4,
                                            linewidth=1.5)
                    
                    # Ajouter une légère étiquette
                    if i < j:  # Pour éviter les doublons
                        x_mid = (self.hangar.points[p][0] + self.hangar.points[q][0]) / 2
                        y_mid = (self.hangar.points[p][1] + self.hangar.points[q][1]) / 2
                        
                        ax1.text(x_mid, y_mid, f"{p[0]}{p[1]}→{q[0]}{q[1]}",
                                fontsize=7, ha='center', va='center',
                                bbox=dict(boxstyle='round', facecolor='white', alpha=0.6))
                    
                    couleur_idx += 1
        
        # 2. Graphe orienté normal
        self._dessiner_graphe_oriented(ax2)
        
        plt.suptitle(f"{self.n} points - {np.sum(self.matrice < float('inf')) - self.n} chemins possibles", 
                    fontsize=14)
        plt.tight_layout()
        plt.show()

    def visualiser_chemins_par_paires(self):
        """
        Visualise chaque paire sur un hangar séparé
        """
        total_paires = self.n * (self.n - 1)
        paires_possibles = np.sum(self.matrice < float('inf')) - self.n
        
        print(f"Total paires: {total_paires}")
        print(f"Paires possibles: {paires_possibles}")
        print(f"Paires impossibles: {total_paires - paires_possibles}")
        
        # Créer une figure pour chaque paire possible
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.matrice[i][j] < float('inf'):
                    p = self.commande[i]
                    q = self.commande[j]
                    
                    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
                    
                    # Hangar avec le chemin
                    self.hangar.dessiner(f"Chemin: {p} → {q}", ax=ax1)
                    
                    # Tracer le chemin
                    resultat = self.hangar.tracer_chemin(p, q, ax1, 
                                                        couleur='red',
                                                        style='-',
                                                        alpha=0.8,
                                                        linewidth=2)
                    
                    # Graphe orienté
                    self._dessiner_graphe_oriented(ax2)
                    
                    # Surbrillance dans le graphe
                    pos = {idx: (self.graph_nx.nodes[idx]['x'], 
                                self.graph_nx.nodes[idx]['y']) 
                        for idx in range(self.n)}
                    
                    nx.draw_networkx_edges(
                        self.graph_nx, pos,
                        edgelist=[(i, j)],
                        ax=ax2,
                        arrowstyle='->',
                        arrowsize=25,
                        edge_color='red',
                        width=3,
                        alpha=0.9
                    )
                    
                    # Informations
                    info = f"Distance: {resultat['distance']:.1f}m\n"
                    for segment in resultat['segments']:
                        info += f"• {segment}\n"
                    
                    plt.figtext(0.02, 0.02, info, fontsize=10,
                            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
                    
                    plt.tight_layout()
                    plt.show()
                    plt.close(fig)  # Fermer la figure pour éviter la superposition

    def afficher_infos(self):
        """Affiche certaines informations"""
        print("\n" + "="*50)
        print("INFORMATIONS DU GRAPHE")
        print("="*50)
        print(f"Nombre de points : {self.n}")
        print(f"Points : {self.commande}")
        #compter les arcs possibles
        arcs_possibles = 0
        arcs_totaux =self.n * (self.n - 1)

        for i in range(self.n):
            for j in range(self.n):
                if i!=j and self.matrice[i][j] < float('inf'):
                    arcs_possibles +=1
        print(f"Arcs possibles : {arcs_possibles}/{arcs_totaux}")

        #exemple de distances
        if self.n >=2:
            print("\nExemple de distances : ")
            for i in range(self.n):
                for j in range(self.n):
                    if i!= j :
                        p = self.commande[i]
                        q = self.commande[j]
                        d = self.matrice[i][j]
                        if d < float('inf'):
                            print(f" {p} -> {q} : {d:.1f} m ")
                        else:
                            print(f" {p} -> {q} : IMPOSSIBLE")
    def est_faisable(self):
        """
        Verifie si un cycle hamiltonien existe dans le graphe 
        (si on peut visiter tous les points en respectant les contraintes)

        """
        n= self.n
        #chaque point doit avoir au moins un successeur et un predecesseur accessible
        for i in range(n):
            #verifier les successeurs
            if all(self.matrice[i][j] == float('inf') for j in range(n) if j!=i):
                return False
            #verifier les predecesseurs
            if all(self.matrice[j][i] == float('inf') for j in range(n) if j!=i):
                return False
        return True
    



    def __str__(self):
        return f"GraphCollect({self.n} points: {self.commande})"
    


if __name__ == "__main__":

    warehouse = Hangar(
        90,
        5,
        2
    )
    warehouse_depot = HangarWithDepot(90,5,2)


    commande = get_commandes()
    warehouse.placer_commande(commande)
    


    graphe = GraphCollect(warehouse,commande)
    grapheDepot =GraphCollectWithDepot(warehouse_depot,commande)


    matrice = graphe.matrice
    graphe.afficher_matrice(matrice)
    #HANGAR AVEC UN DEPOT
    print("\n Utilisation de la classe Hangar Avec un depot")
    pointsDepot = [p for p in grapheDepot.points_complets]
    print(pointsDepot,end="\n")
    matriceDepot = grapheDepot.matrice
    grapheDepot.afficher_matrice(matriceDepot)


