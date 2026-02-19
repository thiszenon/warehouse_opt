# graph/graph_collect_depot.py
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Tuple
from src.geometry.hangar_with_depot import HangarWithDepot
from src.data.commandes import get_commandes


class GraphCollectWithDepot:
    """
    Graphe orienté avec gestion du dépôt et de l'arrivée
    """
    
    def __init__(self, hangar_with_depot, commande: List[Tuple[str, int]]):
        self.hangar = hangar_with_depot
        self.commande_reelle = commande
        
        # Construire la liste complète des points
        self.points_complets = [hangar_with_depot.depot_label] + commande
        if hangar_with_depot.arrival_label != hangar_with_depot.depot_label:
            self.points_complets.append(hangar_with_depot.arrival_label)
        
        self.n_total = len(self.points_complets)
        self.depot_idx = 0
        self.arrival_idx = len(self.points_complets) - 1
        
        # Construire la matrice
        self.matrice = self._construire_matrice()
        
        # Construire le graphe NetworkX
        self.graph_nx = self._construire_graphe()
    
    def _construire_matrice(self) -> np.ndarray:
        """Construit la matrice des distances complète"""
        matrice = np.full((self.n_total, self.n_total), float('inf'), dtype=float)
        
        for i in range(self.n_total):
            for j in range(self.n_total):
                if i == j:
                    matrice[i][j] = 0.0
                else:
                    p = self.points_complets[i]
                    q = self.points_complets[j]
                    matrice[i][j] = self.hangar.distance_special(p, q)
        
        return matrice
    
    #TODO: Afficher la mtrice des distances 
    def afficher_matrice(self,matrice):
        print("Afficher la matrice des distances: \n")
        print(matrice)
    #end afficher_matrice
    
    def _construire_graphe(self) -> nx.DiGraph:
        """Construit le graphe NetworkX"""
        G = nx.DiGraph()
        
        # Ajouter les nœuds
        for i, point in enumerate(self.points_complets):
            if point == self.hangar.depot_label:
                x, y = self.hangar.depot_position
                label = "DÉPÔT"
                couleur = 'green'
            elif point == self.hangar.arrival_label:
                x, y = self.hangar.arrival_position
                label = "ARRIVÉE"
                couleur = 'orange'
            else:
                allee, n = point
                x, y = self.hangar.points[point]
                label = f"{allee}{n}"
                couleur = 'red' if self.hangar.sens.get(allee[0], 1) == 1 else 'blue'
            
            G.add_node(i,
                      label=label,
                      point=point,
                      x=x,
                      y=y,
                    couleur=couleur,
                    is_depot=(point == self.hangar.depot_label),
                    is_arrival=(point == self.hangar.arrival_label))
        
        # Ajouter les arcs
        for i in range(self.n_total):
            for j in range(self.n_total):
                if i != j and self.matrice[i][j] < float('inf'):
                    G.add_edge(i, j,
                            weight=self.matrice[i][j],
                            distance=self.matrice[i][j])
        
        return G
    
    def afficher_infos(self):
        """Affiche les informations du graphe"""
        print("\n" + "="*50)
        print("INFORMATIONS DU GRAPHE AVEC DÉPÔT")
        print("="*50)
        print(f"Nombre total de points: {self.n_total}")
        print(f"Points de collecte: {len(self.commande_reelle)}")
        print(f"Dépôt: {self.hangar.depot_label} (index {self.depot_idx})")
        print(f"Arrivée: {self.hangar.arrival_label} (index {self.arrival_idx})")
        
        # Compter les arcs possibles
        arcs_possibles = np.sum(self.matrice < float('inf')) - self.n_total
        arcs_totaux = self.n_total * (self.n_total - 1)
        
        print(f"Arcs possibles: {arcs_possibles}/{arcs_totaux}")
        print(f"Taux de connectivité: {arcs_possibles/arcs_totaux*100:.1f}%")
        
        # Afficher quelques distances
        print("\nExemples de distances:")
        print(f"  Dépôt → Premier point: {self.matrice[0][1]:.1f}m")
        print(f"  Dernier point → Arrivée: {self.matrice[-2][-1]:.1f}m")
        
        # Vérifier la faisabilité
        if self._est_faisable():
            print("\n✅ Le graphe semble faisable (cycle possible)")
        else:
            print("\n⚠️  Le graphe pourrait ne pas être faisable")
    
    def _est_faisable(self):
        """Vérifie si un cycle hamiltonien est possible"""
        # Vérifier que chaque point a au moins un successeur et un prédécesseur
        for i in range(self.n_total):
            if all(self.matrice[i][j] == float('inf') for j in range(self.n_total) if j != i):
                return False
            if all(self.matrice[j][i] == float('inf') for j in range(self.n_total) if j != i):
                return False
        return True
    
    def _dessiner_graphe_oriented(self, ax):
        """Dessine le graphe orienté (pour compatibilité)"""
        if self.n_total == 0:
            ax.text(0.5, 0.5, "Aucun point", ha='center', va='center')
            return
        
        # Positions
        pos = {i: (self.graph_nx.nodes[i]['x'], self.graph_nx.nodes[i]['y']) 
            for i in range(self.n_total)}
        
        # Couleurs
        couleurs = [self.graph_nx.nodes[i]['couleur'] for i in range(self.n_total)]
        
        # Dessiner les nœuds
        nx.draw_networkx_nodes(self.graph_nx, pos, ax=ax,
                            node_size=400,
                            node_color=couleurs,
                            edgecolors='black',
                            linewidths=2)
        
        # Labels
        labels = {i: self.graph_nx.nodes[i]['label'] for i in range(self.n_total)}
        nx.draw_networkx_labels(self.graph_nx, pos, labels, ax=ax, 
                            font_size=11, font_weight='bold')
        
        # Arcs
        edges = [(i, j) for i in range(self.n_total) for j in range(self.n_total)
                if i != j and self.matrice[i][j] < float('inf')]
        
        nx.draw_networkx_edges(self.graph_nx, pos, edgelist=edges,
                            ax=ax, arrowstyle='->', arrowsize=15,
                            edge_color='gray', width=1.5, alpha=0.7)
        
        ax.set_title("Graphe orienté avec Dépôt/Arrivée")
        ax.set_xlabel("Position x (m)")
        ax.set_ylabel("Position y (m)")
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

    ####Méthodes Utilitaires 
    
if __name__ == "__main__":
    hangar = HangarWithDepot(
        Longueur=90, 
        largeur_allee=5, 
        r=2,
        depot_position=(25, -5),   # Devant à droite
        arrival_position=(15, -5)  # Devant à gauche
    )
    commande = get_commandes()

    #graphe 
    graphe = GraphCollectWithDepot(hangar,commande)
    matrice = graphe.matrice


    graphe.afficher_matrice(matrice)

