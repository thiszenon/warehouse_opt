import matplotlib.pyplot as plt
import matplotlib.patches as patches 
import numpy as np


class Hangar:
    """Class for modeling and visualizing a hangar"""
    def __init__(self, Longueur=100,largeur_allee=5, r=2):
        """
        Initialise un hangar avec les paramètres.
        
        :param Longueur: Longueur des allées (m)
        :param largeur_allee: Largeur d'une allée (m)
        :param r: Espacement vertical entre de points (m)
        """
        self.Longueur = Longueur
        self.largeur_allee = largeur_allee
        self.r = r

        #Allées de gauche à droite
        self.allees = ['H','G','F','E','D','C','B','A']

        #sens de circulation (-1: descente, +1: montée)
        self.sens = {'H':-1, 'G':1, 'F':-1, 'E':1,'D':-1,'C':1,'B':-1,'A':1}

        #Niveaux horizontaux
        self.niveaux = {'N1': 0, 'N2': 50, 'N3':100}

        #Calcul des centres d'allées
        self.centres = {}
        for k, allee in enumerate(self.allees):
            self.centres[allee] = largeur_allee * (k + 0.5)
        
        #Largeur totale
        self.largeur_totale = len(self.allees) * largeur_allee

        #Points vides pour l'instant
        self.points = {}
    #end __init__

    def genere_tous_points(self):
        """Genere tous les points possibles dans le hangar"""
        n_paires = int(self.Longueur // self.r) # nombre de paires par allée

        for allee in self.allees:
            x_centre = self.centres[allee]
            x_droit = x_centre + self.largeur_allee/2
            x_gauche = x_centre - self.largeur_allee/2

            for p in range(1, n_paires + 1): #p= numéro de paire
                #calcul de y selon le sens
                if self.sens[allee] == 1 : #montée
                    y = self.r * p- self.r /2
                else: #descente
                    y = self.Longueur - (self.r *p - self.r /2)

                #points impair (coté droit)
                n_impair = 2 * p - 1
                self.points[(allee,n_impair)] = (x_droit, y)

                #point pair (coté gauche)
                n_pair = 2*p
                self.points[(allee, n_pair)] = (x_gauche,y)

        return self.points
    #end generer_tous_points

    def placer_commande(self, commande):
        """
        Place les points d'une commande dans le hangar.
        
        :param commande: Liste de tuples (allée, numéro)
        """
        for allee, n in commande:
            if(allee,n) not in self.points:
                self._ajouter_point(allee,n)
            #end if
    #end palcer_commande

    def calculer_coordonnees(self, allee, n):
        """Nouvelle méthode : calcule les coordonnées exactes d'un point."""
        if allee not in self.allees:
            raise ValueError(f"Allée {allee} invalide")
        
        k = self.allees.index(allee)
        largeur_couloir = self.largeur_allee*0.8 
        marge = (self.largeur_allee - largeur_couloir)/2
        
        # NOUVEAU CALCUL : Points sur les BORDS, pas au centre ± largeur/2
        if n % 2 == 1:  # Point impair → bord DROIT
            x = (k * self.largeur_allee + marge) + largeur_couloir  # Bord droit de l'allée
        else:  # Point pair → bord GAUCHE
            x = k * self.largeur_allee + marge # Bord gauche de l'allée
        
        # Calcul de y (inchangé mais clarifié)
        p = (n + 1) // 2  # Numéro de la paire
        
        if self.sens[allee] == 1:  # Montée
            y = self.r * p - self.r / 2  # 1, 3, 5, ..., 99
        else:  # Descente
            # CORRECTION : Commence en haut (99) et descend
            y = self.Longueur- (self.r * p - self.r / 2)  # 99, 97, 95, ..., 1
        return x, y

    def _ajouter_point(self, allee, n):
        """Nouvelle version : utilise calculer_coordonnees."""
        x, y = self.calculer_coordonnees(allee, n)
        self.points[(allee, n)] = (x, y)
    #end _ajouter_point

    def dessiner(self, titre="hangar avec points de collecte"):
        """Dessine le hangar avec ses points."""
        fig, ax = plt.subplots(figsize=(14,8))

        #offset par allée pour eviter les superpositions
        offsets = {'H':0.0, 'G':0.1,'F':0.2,'E':0.3,'D':0.4,'C':0.5,'B':0.6,'A':0.7}

        #Dessiner les allées (rectangles)
        for k, allee in enumerate(self.allees):
            x_min = k * self.largeur_allee
            x_max = (k+1) * self.largeur_allee

            #rectangle de l'allée 
            rect = patches.Rectangle(
                (x_min,0), self.largeur_allee, self.Longueur,linewidth=1,
                edgecolor='gray', facecolor = 'lightblue' if k%2==0 else 'lightyellow', alpha=0.2, linestyle='--'
            )
            ax.add_patch(rect)

            #nom de l'allée au centre
            ax.text((x_min + x_max)/2 , -5, allee, ha='center', va='center',fontsize=12, fontweight='bold')


            #Flèche de sens
            y_fleche = self.Longueur + 5 
            if self.sens[allee] == 1: #montée
                ax.arrow(
                    x_min + self.largeur_allee/2,
                    y_fleche - 10, 
                    0,
                    8, 
                    head_width=0.5, 
                    head_length=3,
                    fc='red',
                    ec='red'
                )
                ax.text(
                    x_min + self.largeur_allee/2,
                    y_fleche, 
                    '↑',
                    ha='center',
                    va='center',
                    fontsize=14,
                    color='red'
                )
            else: #descente
                ax.arrow(
                    x_min + self.largeur_allee/2,
                    y_fleche + 2,
                    0,
                    -8,
                    head_width=0.5,
                    head_length=3,
                    fc='blue',
                    ec='blue'
                )
                ax.text(
                    x_min + self.largeur_allee/2,
                    y_fleche,
                    '↓',
                    ha='center',
                    va='center',
                    fontsize=14,
                    color='blue'
                )

            #dessiner les niveaux horizontaux
            for nom, y in self.niveaux.items():
                ax.axhline(y=y,color='orange', linestyle='--',alpha=0.7,linewidth=2)
                ax.text(
                    self.largeur_totale + 2, 
                    y, 
                    nom,
                    ha='left',
                    va='center',
                    fontsize=11,
                    color='orange',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow",alpha=0.5)
                )
            
            #dessiner les bords verticaux
            for i in range(len(self.allees) + 1):
                x_bord = i * self.largeur_allee
                ax.plot([x_bord, x_bord], [0, self.Longueur], 'k-', linewidth=2, alpha=0.7)
            #dessiner les points
            for (allee,n),(x,y) in self.points.items():
                offset = offsets[allee]*0.8 

                #ajouter x avec offset
                if n % 2 == 1: #point impair (droite)
                    x_adj = x - offset 
                else:
                    x_adj = x + offset 
                couleur = 'red' if self.sens[allee] == 1 else 'blue'

                #Point principal
                ax.plot(x_adj,y, 'o', markersize=12,
                        markerfacecolor = couleur, markeredgecolor='black',
                        markeredgewidth=1.5, zorder=10, alpha=0.9
                )

                #ligne pointillée vers la position réelle 
                ax.plot([x,x_adj], [y,y], 'k:', alpha=0.3, linewidth=1)

                #etiquette avec informations
                label = f"{allee}{n}\n({x:.1f},{y:.1f})"
                ax.text(x_adj + 0.5, y +1, label,fontsize=9, fontweight='bold',
                        bbox=dict(boxstyle="round, pad=0.2",facecolor="white",alpha=0.8))
                
                

                

            

            #Configuration du graphique
            ax.set_xlim(-2, self.largeur_totale + 2)
            ax.set_ylim(-10, self.Longueur + 20)
            ax.set_xlabel('Position horizontale (m)', fontsize=8)
            ax.set_ylabel('Hauteur (m)', fontsize=8)
            ax.set_title(titre, fontsize=10, fontweight='bold')
            ax.grid(True,alpha=0.2)
            ax.set_aspect('auto')

            #Légende
            """ 
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='o',color='w',markerfacecolor='blue',markersize=10, label='Allées descente (H,F,D,B)'),
                Line2D([0], [0], marker='o',color='w',markerfacecolor='red',markersize=10, label='Allées montée (G,E,C,A)'),
                Line2D([0], [0], color='orange', linestyle='--', linewidth=2, label='Niveaux horizontaux'),
            ]
            ax.legend(handles=legend_elements, loc='upper left', fontsize=10)
            """

            plt.tight_layout()
            return fig, ax
    
#################### Calcul distances 
    def _accessible_verticalement(self, y_start, y_end, allee):
        """Cette methode verifie si le deplacement vertical respecte le sens de circulation"""
        sens = self.sens[allee]
        return (y_end - y_start)*sens >=0 
    #end _accessible_verticalement

    def distance(self,p,q):
        """
        Distance admissible entre deux points p et q en
        respectant les contraintes du hangar
        :p,q : tuples(allee, n)
        """
        if p == q :
            return 0.0
        #coordonnées 
        x_p, y_p = self.points[p]
        x_q, y_q = self.points[q]

        allee_p, _ = p
        allee_q, _ = q
        distances = []

        #cas 1: même allée
        if allee_p == allee_q:
            if self._accessible_verticalement(y_p, y_q,allee_p):
                distances.append(abs(y_q - y_p))
        #end if
        #cas 2: passage par niveaux horizontaux
        for y_n in self.niveaux.values():
            #p -> niveau
            if not self._accessible_verticalement(y_p,y_n,allee_p):
                continue
            #niveau -> q
            if not self._accessible_verticalement(y_n, y_q, allee_q):
                continue
            d_vertical_1 = abs(y_n - y_p)
            d_horizontal = abs(x_q - x_p)
            d_vertical_2 = abs(y_q - y_n)

            distances.append(d_vertical_1 + d_horizontal + d_vertical_2)
        #end for
        if not distances:
            return float('inf')
        return min(distances)





if __name__ == "__main__":
    # 1. Créer le hangar
    hangar = Hangar(Longueur=90, largeur_allee=5, r=2)
    
    print(f"=== CONSTRUCTION DU HANGAR ===")
    print(f"Longueur: {hangar.Longueur} m")
    print(f"Largeur par allée: {hangar.largeur_allee} m")
    print(f"Largeur totale: {hangar.largeur_totale} m")
    print(f"Espacement vertical: {hangar.r} m")
    print(f"Allées: {hangar.allees}")
    print(f"Sens: {hangar.sens}")
    print(f"Centres: {hangar.centres}")
    print(f"Niveaux: {hangar.niveaux}")
    
    # 2. Générer quelques points pour la démonstration
    # (Au lieu de tous les points, juste quelques-uns pour la clarté)
    points_demo = [
        ('A', 1), ('A', 8),   # Paire 1 dans A (montée)
        ('B', 47), ('D', 68), # Paire 50 dans A (haut)
        ('H', 45), ('H', 24),   # Paire 1 dans H (descente, en haut)
        ('C', 3), ('C', 19), # Point milieu dans C (montée)
    ]
    commande = [
        ('A',1),
        ('A',8),
        ('B',47),
        ('C',3),
        ('H',24)
    ]
    
    # 3. Placer ces points
    hangar.placer_commande(commande)
    
    
    print(f"\n=== POINTS PLACÉS ===")
    for (allee, n), (x, y) in sorted(hangar.points.items()):
        print(f"{allee}{n}: ({x:.1f}, {y:.1f}) m")

    p = ('C',3)
    q= ('A',1)
    print("Distance A1 -> C3: ", hangar.distance(p,q))
    print("Distance A1 -> C3: ", hangar.distance(q,p))

    
    # 4. Visualiser
    fig, ax = hangar.dessiner("Hangar avec points de collecte (démonstration)")
    
    # Ajouter des annotations pour expliquer
    """ 
    ax.text(20, 110, "Sens de circulation:", fontsize=11, fontweight='bold')
    ax.text(20, 105, "• Flèches rouges ↑ : Montée seulement", color='red', fontsize=10)
    ax.text(20, 100, "• Flèches bleues ↓ : Descente seulement", color='blue', fontsize=10)
    
    ax.text(20, 90, "Points:", fontsize=11, fontweight='bold')
    ax.text(20, 85, "• A1 et A2: même hauteur (y=1)", color='red', fontsize=10)
    ax.text(20, 80, "• H1 et H2: même hauteur (y=99)", color='blue', fontsize=10)
    ax.text(20, 75, "• Niveaux N1,N2,N3: couloirs horizontaux", color='orange', fontsize=10)
    """
    plt.tight_layout()
    plt.show()
    