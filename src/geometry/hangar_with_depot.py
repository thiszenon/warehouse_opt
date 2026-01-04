import numpy as np
from .hangar import Hangar

class HangarWithDepot(Hangar):
    """
    Hangar étendu avec gestion des points hors hangar :
    - Dépôt (point de départ)
    - Arrivée (point de retour, peut être différent du dépôt)
    """
    
    def __init__(self, Longueur=100, largeur_allee=5, r=2, 
                depot_position=(20, -10), arrival_position=None):
        """
        Args:
            depot_position: (x, y) du point de départ hors hangar
            arrival_position: (x, y) du point d'arrivée (None = même que dépôt)
        """
        super().__init__(Longueur=Longueur, largeur_allee=largeur_allee, r=r)
        
        self.depot_position = depot_position
        self.arrival_position = arrival_position if arrival_position else depot_position
        
        # Labels spéciaux pour les points hors hangar
        self.depot_label = ('DEPOT', 0)
        self.arrival_label = ('ARRIVEE', 0) if arrival_position else ('DEPOT', 0)
        
        # Ajouter ces points au dictionnaire de points
        self.points[self.depot_label] = depot_position
        if arrival_position:
            self.points[self.arrival_label] = arrival_position
    
    def distance_special(self, from_point, to_point):
        """
        Version simplifiée mais qui respecte mieux les contraintes.
        """
        
        # CAS 1 : DÉPÔT/ARRIVÉE → DÉPÔT/ARRIVÉE
        if (from_point in [self.depot_label, self.arrival_label] and 
            to_point in [self.depot_label, self.arrival_label]):
            
            x1, y1 = self.depot_position if from_point == self.depot_label else self.arrival_position
            x2, y2 = self.depot_position if to_point == self.depot_label else self.arrival_position
            
            return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # CAS 2 : Un des points est hors hangar
        if from_point in [self.depot_label, self.arrival_label] or to_point in [self.depot_label, self.arrival_label]:
            
            # Déterminer le point hors hangar et le point dans le hangar
            if from_point in [self.depot_label, self.arrival_label]:
                point_hors = from_point
                point_dans = to_point
                sens = "vers_hangar"
            else:
                point_hors = to_point
                point_dans = from_point
                sens = "depuis_hangar"
            
            # Coordonnées du point hors hangar
            if point_hors == self.depot_label:
                x_hors, y_hors = self.depot_position
            else:
                x_hors, y_hors = self.arrival_position
            
            # Coordonnées du point dans le hangar
            if point_dans not in self.points:
                allee, n = point_dans
                self._ajouter_point(allee, n)
            x_dans, y_dans = self.points[point_dans]
            
            # Trouver l'allée du point dans le hangar
            allee_dans, _ = point_dans
            
            # Créer un point d'entrée dans cette allée au niveau 0
            point_entree = (allee_dans, 0)
            if point_entree not in self.points:
                self._ajouter_point(allee_dans, 0)
            
            # Distance hors hangar → entrée (ligne droite)
            dist_externe = np.sqrt(
                (self.points[point_entree][0] - x_hors)**2 + 
                (self.points[point_entree][1] - y_hors)**2
            )
            
            # Distance dans le hangar : entrée → point
            dist_interne = super().distance(point_entree, point_dans)
            
            # Si pas de chemin direct, chercher un chemin via un autre niveau
            if dist_interne == float('inf'):
                # Essayer différents niveaux
                for y_n in self.niveaux.values():
                    point_niveau = (allee_dans, y_n)
                    if point_niveau not in self.points:
                        continue
                    
                    # Entrée → niveau
                    d1 = super().distance(point_entree, point_niveau)
                    if d1 == float('inf'):
                        continue
                    
                    # Niveau → point
                    d2 = super().distance(point_niveau, point_dans)
                    if d2 == float('inf'):
                        continue
                    
                    dist_interne = min(dist_interne, d1 + d2)
            
            # Si toujours inf, utiliser estimation
            if dist_interne == float('inf'):
                # Estimation conservatrice
                dist_interne = abs(y_dans - 0) * 2  # Aller-retour dans l'allée
            
            return dist_externe + dist_interne
        
        # CAS 3 : Les deux points sont dans le hangar
        return super().distance(from_point, to_point)
    
    def calculer_tous_chemins(self, commande):
        """
        Calcule toutes les distances entre les points d'une commande,
        incluant le dépôt et l'arrivée.
        
        Returns:
            dict: {
                'points': [dépôt] + commande + [arrivée],
                'matrice': matrice des distances (n+2 x n+2)
            }
        """
        # Liste de tous les points à considérer
        tous_points = [self.depot_label] + commande
        if self.arrival_position != self.depot_position:
            tous_points.append(self.arrival_label)
        else:
            tous_points.append(self.depot_label)  # Même point
        
        n_total = len(tous_points)
        matrice = np.full((n_total, n_total), float('inf'), dtype=float)
        
        # Remplir la matrice
        for i in range(n_total):
            for j in range(n_total):
                if i == j:
                    matrice[i][j] = 0.0
                else:
                    matrice[i][j] = self.distance_special(tous_points[i], tous_points[j])
        
        return {
            'points': tous_points,
            'matrice': matrice,
            'depot_idx': 0,
            'arrival_idx': n_total - 1 if self.arrival_position != self.depot_position else 0
        }
    
    def dessiner_avec_depot(self, commande, titre="Hangar avec Dépôt", ax=None):
        """Dessine le hangar avec le dépôt et les points de collecte"""
        if ax is None:
            fig, ax = super().dessiner(titre, ax=None)
            retourner_fig = True
        else:
            retourner_fig = False
        
        # Tracer le dépôt
        x_depot, y_depot = self.depot_position
        ax.plot(x_depot, y_depot, 's', markersize=15, 
                color='green', markeredgecolor='black',
                markeredgewidth=2, zorder=20, label='Dépôt')
        ax.text(x_depot, y_depot - 5, 'DÉPÔT', 
                ha='center', va='top', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Tracer l'arrivée si différente
        if self.arrival_position != self.depot_position:
            x_arr, y_arr = self.arrival_position
            ax.plot(x_arr, y_arr, 's', markersize=15,
                    color='orange', markeredgecolor='black',
                    markeredgewidth=2, zorder=20, label='Arrivée')
            ax.text(x_arr, y_arr - 5, 'ARRIVÉE',
                    ha='center', va='top', fontsize=10, fontweight='bold',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Tracer les chemins vers le niveau N1
        ax.plot([x_depot, x_depot], [y_depot, 0], 'g--', alpha=0.5, linewidth=1)
        ax.plot([x_depot, self.largeur_totale/2], [0, 0], 'g--', alpha=0.5, linewidth=1)
        
        if retourner_fig:
            return fig, ax
    
    def tracer_chemin_special(self, p, q, ax=None, couleur='red', style='-', 
                            alpha=0.8, linewidth=2):
        """
        Version adaptée pour tracer des chemins incluant dépôt/arrivée
        """
        # Si l'un des points est le dépôt/arrivée
        if p == self.depot_label or p == self.arrival_label or \
        q == self.depot_label or q == self.arrival_label:
            
            # Obtenir les coordonnées
            if p == self.depot_label:
                x_p, y_p = self.depot_position
            elif p == self.arrival_label:
                x_p, y_p = self.arrival_position
            else:
                x_p, y_p = self.points[p]
            
            if q == self.depot_label:
                x_q, y_q = self.depot_position
            elif q == self.arrival_label:
                x_q, y_q = self.arrival_position
            else:
                x_q, y_q = self.points[q]
            
            # Chemin simplifié via niveau N1
            chemin = [
                (x_p, y_p),       # Point de départ
                (x_p, 0),         # Niveau N1 (vertical)
                (x_q, 0),         # Niveau N1 (horizontal)
                (x_q, y_q)        # Point d'arrivée
            ]
            
            distance = (abs(y_p - 0) + abs(x_q - x_p) + abs(0 - y_q))
            
            if ax is not None:
                x_vals = [point[0] for point in chemin]
                y_vals = [point[1] for point in chemin]
                ax.plot(x_vals, y_vals, style, color=couleur, 
                    linewidth=linewidth, alpha=alpha, 
                    marker='o', markersize=4, markerfacecolor=couleur)
            
            return {
                'distance': distance,
                'chemin': chemin,
                'type': 'via_niveau_N1'
            }
        
        # Si les deux points sont dans le hangar, utiliser la méthode parent
        return super().tracer_chemin(p, q, ax, couleur, style, alpha, linewidth)