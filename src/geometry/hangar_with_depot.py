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
        Distance entre deux points, avec gestion spéciale des points hors hangar.
        
        Logique simplifiée pour les benchmarks :
        - Pour aller d'un point hors hangar à un point dans le hangar :
          position → niveau N1 → point
        - Pour aller d'un point dans le hangar à un point hors hangar :
          point → niveau N1 → position
        """
        # 1. Départ = DÉPÔT
        if from_point == self.depot_label:
            x_depot, y_depot = self.depot_position
            
            # Si arrivée = DÉPÔT (même point)
            if to_point == self.depot_label:
                return 0.0
            
            # Si arrivée = ARRIVÉE différente
            if to_point == self.arrival_label:
                x_arr, y_arr = self.arrival_position
                return np.sqrt((x_arr - x_depot)**2 + (y_arr - y_depot)**2)
            
            # DÉPÔT → Point dans le hangar
            if to_point not in self.points:
                #placer le point s'il n'existe pas
                allee,n = to_point
                self._ajouter_point(allee,n)

            x_point, y_point = self.points[to_point]
            
            # Chemin: Dépôt → Niveau N1 (y=0) → Point
            # Distance verticale pour atteindre le niveau
            dist_to_level = abs(0 - y_depot)  # y_depot est négatif (-10)
            # Distance horizontale au niveau
            dist_horizontal = abs(x_point - x_depot)
            # Distance verticale dans le hangar
            dist_in_hangar = abs(y_point - 0)
            
            return dist_to_level + dist_horizontal + dist_in_hangar
        
        # 2. Départ = ARRIVÉE (si différente de DÉPÔT)
        if from_point == self.arrival_label:
            x_arr, y_arr = self.arrival_position
            
            # ARRIVÉE → DÉPÔT
            if to_point == self.depot_label:
                x_depot, y_depot = self.depot_position
                return np.sqrt((x_depot - x_arr)**2 + (y_depot - y_arr)**2)
            
            # ARRIVÉE → Point dans le hangar (peu probable mais géré)
            x_point, y_point = self.points[to_point]
            dist_to_level = abs(0 - y_arr)
            dist_horizontal = abs(x_point - x_arr)
            dist_in_hangar = abs(y_point - 0)
            
            return dist_to_level + dist_horizontal + dist_in_hangar
        
        # 3. Départ = Point dans le hangar, Arrivée = DÉPÔT ou ARRIVÉE
        if to_point == self.depot_label or to_point == self.arrival_label:
            
            #Vériication si le point de départ existe
            if from_point not in self.points:
                allee,n = from_point
                self._ajouter_point(allee,n)

            x_point, y_point = self.points[from_point]
            
            if to_point == self.depot_label:
                x_target, y_target = self.depot_position
            else:
                x_target, y_target = self.arrival_position
            
            # Chemin: Point → Niveau N1 (y=0) → Dépôt/Arrivée
            dist_to_level = abs(0 - y_point)
            dist_horizontal = abs(x_target - x_point)
            dist_to_target = abs(y_target - 0)
            
            return dist_to_level + dist_horizontal + dist_to_target
        
        # 4. Départ et Arrivée dans le hangar → utiliser la méthode parent
        #verifier si les points existent
        if from_point not in self.points:
            allee,n = from_point
            self._ajouter_point(allee,n)
        
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