
"""
Docstring pour graph.graph_collect
Module : GraphCollect 

"""
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Tuple, Dict, Optional, Set
import json

from geometry import hangar

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
        Visulisation du graphe
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
    
    def __str__(self):
        return f"GraphCollect({self.n} points: {self.commande})"



