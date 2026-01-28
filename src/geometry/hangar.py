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
        self.allees_speciales = ['BB','CC','DD','EE','FF','GG','HH','AA']
        self.allees_toutes = self.allees + self.allees_speciales

        #sens de circulation (-1: descente, +1: montée)
        self.sens = {'H':-1, 'G':1, 'F':-1, 'E':1,'D':-1,'C':1,'B':-1,'A':1,
                    'AB':-1,'BB':-1, 'CC':1, 'DD':-1,'EE':1, 'FF':-1,'GG':1,'HH':-1
        }

        #Niveaux horizontaux
        self.niveaux = {'N1': 0, 'N2': Longueur/2, 'N3':Longueur}

        #Calcul des centres d'allées
        self.centres = {}
        for k, allee in enumerate(self.allees):
            self.centres[allee] = largeur_allee * (k + 0.5)
        
        #Largeur totale du hangar pour en estimer les dimensions
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
        for allee, num in commande:
            if(allee,num) not in self.points:
                self._ajouter_point(allee,num)
            #end if
    #end palcer_commande

    def calculer_coordonnees(self, allee, n):
        """calcule les coordonnées exactes d'un point."""

        #1. Identifier l'allée de base et le type
        allee_base = allee
        is_special = False
        zone = None

        if len(allee) == 2: #code à 2 lettres
            is_special = True
            if allee in ['BB','DD','FF','HH','AB']:
                #descentes spéciales (N3->N2)
                allee_base = allee[1] if allee != 'AB' else 'B'# 'B' pour 'BB' et 'AB'
                zone= 'N3_N2'
            elif allee in ['CC','EE','GG']:
                #Montantes spéciales (N2->N3)
                allee_base = allee[0] # 'C' pour 'cc', etc
                zone = 'N2_N3'
            else:
                raise ValueError(f"Code d'allée inconnu: {allee}")
            
        #validation
        if allee_base not in self.allees:
            raise ValueError(f"Allée {allee} (base: {allee_base}) invalide")
        
        #2. Calcul de x
        k = self.allees.index(allee_base)
        largeur_couloir = self.largeur_allee*0.8 
        marge = (self.largeur_allee - largeur_couloir)/2
        
        # Points sur les BORDS, pas au centre ± largeur/2
        if n % 2 == 1:  # Point impair → bord DROIT
            x = (k * self.largeur_allee + marge) + largeur_couloir  # Bord droit de l'allée
        else:  # Point pair → bord GAUCHE
            x = k * self.largeur_allee + marge # Bord gauche de l'allée
        
        # Calcul de y 
        p = (n + 1) // 2  # Numéro de la paire

        if is_special:
            if zone == 'N3_N2':
                #descente special : commence en haut (N3)
                y = self.Longueur - (self.r*p - self.r/2)
                #limiter à la zone N3->N2 (haut du hangar)
                y= max(y, self.Longueur /2)
            elif zone == 'N2_N3':
                #Montante speciale : commence au milieu (N2)
                y= self.Longueur/2 + (self.r*p - self.r /2)
                #limiter à la zone N2->N3
                y = min(y, self.Longueur)
        else:
            #Point normal
            if self.sens[allee_base] == 1:  # Montée
                y = self.r * p - self.r / 2  # 1, 3, 5, ..., 99
            else:  # Descente
                # CORRECTION : Commence en haut (N3) et descend jusqu'en Bas (N0)
                y = self.Longueur/2 - (self.r * p - self.r / 2)  # 99, 97, 95, ..., 1
        return x, y

    def _ajouter_point(self, allee, n):
        """Nouvelle version : utilise calculer_coordonnees."""
        x, y = self.calculer_coordonnees(allee, n)
        self.points[(allee, n)] = (x, y)
    #end _ajouter_point

    def dessiner(self, titre="hangar avec points de collecte",ax=None):
        """Dessine le hangar avec ses points."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(14,8))
            retourner_fig = True
        else:
            retourner_fig = False


        #offset par allée pour eviter les superpositions
        offsets = {'H':0.0, 'G':0.1,'F':0.2,'E':0.3,'D':0.4,'C':0.5,'B':0.6,'A':0.7,
                'HH':0.0, 'GG':0.1, 'FF':0.2, 'EE':0.3, 'DD':0.4, 'CC':0.5, 'BB':0.6, 'AA':0.7, 'AB':0.6
        }

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
            if retourner_fig:
                return fig, ax
    
#################### Calcul distances 
    def _accessible_verticalement(self, y_start, y_end, allee):
        """Cette methode verifie si le deplacement vertical respecte le sens de circulation"""
        #Si l'allée est None , retourne True : le cas par défaut
        if allee is None:
            return True
        
        #si allee est deja une allée de base (1 caractere)
        if len(allee) == 1:
            allee_base = allee
        elif len(allee) == 2:
        #Trouver l'allée de base
            if allee in ['BB','DD','FF','HH','AB']: 
                allee_base = allee[1] if allee != 'AB' else 'B' #'AB' prendra 'B' puisque 'AB' est dans B est descente
            elif allee in ['CC','EE','GG']: # tu reviendra pour le cas de AA
                allee_base = allee[0]
            else:
                allee_base = allee[0]
        else:
            allee_base = allee

        sens = self.sens.get(allee_base)
        if sens is None:
            return True
        
        #Pour les allées de descente (B,D,F,H), permettre tout mouvement descendant
        if sens == -1:
            return y_end <= y_start #descente
        
        #return (y_end - y_start)*sens >=0 
        return y_end >= y_start #Montée
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


        #cas 1: même allée ou allées speciales liées à la meme allée de base
        def get_allee_base(code_allee):
            if len(code_allee)==2:
                if code_allee in ['BB','DD','FF','HH','AB']:
                    return code_allee[1] if code_allee != 'AB' else 'B'
                elif code_allee in ['CC','EE','GG']:
                    return code_allee[0]
                else:
                    return code_allee
        #end get_allee_base
        allee_base_p = get_allee_base(allee_p)
        allee_base_q = get_allee_base(allee_q)

        #si meme allée de base , aller directement
        
        if allee_base_p == allee_base_q:
            #pour la verification d'accessibilité, utilisation du code de l'allée de base
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
    #end distance

    def tracer_chemin(self, p,q,ax=None, couleur='green', style='-', alpha=0.7, linewidth=2):
        """
        Cette methode trace et retourne le chemin entre deux points p et q
        
        :param self: Description
        :param p: Description
        :param q: Description
        :param ax: Description
        :param couleur: Description
        :param style: Description
        :param alpha: Description
        Returns:
            dict : {'distance': float, 'chemin':list, 'segments': list}
        """
        if p==q:
            return {'distance':0, 'chemin':[], 'segments':[]}
        x_p, y_p = self.points[p]
        x_q, y_q = self.points[q]
        allee_p, _ =p
        allee_q, _ = q
        chemins_possibles = []

        #cas même allée
        if allee_p == allee_q and self._accessible_verticalement(y_p, y_q, allee_p):
            return {
                'distance': abs(y_q - y_p),
                'chemin': [(x_p,y_p), (x_p,y_q)],
                'segments': [f"Allée {allee_p}: ({y_p} -> {y_q})"],
                'type': 'vertical_direct'
            }
        #cas passage par niveaux
        for non_niveau, y_n in self.niveaux.items():
            if (self._accessible_verticalement(y_p, y_n,allee_p) and self._accessible_verticalement(y_n, y_q, allee_q)):
                distance = abs(y_n - y_p) + abs(x_q - x_p) + abs(y_n - y_q)
                chemin = [
                    (x_p, y_p), #point départ
                    (x_p, y_n), #montee/descente au niveau
                    (x_q, y_n),# deplacement horizontal
                    (x_q,y_q) #Montéé /descente au point d'arrivée
                ]

                chemins_possibles.append({
                    'distance':distance,
                    'chemin': chemin,
                    'niveau': non_niveau,
                    'y_niveau': y_n,
                    'segments':[
                        f"Allée {allee_p}: ({y_p} -> {y_n})",
                        f"Niveau {non_niveau}: ({x_p} -> {x_q})",
                        f"Allée {allee_q}: ({y_n} -> {y_q})"
                    ]
                })
        if not chemins_possibles:
            return {'distance': float('inf'), 'chemin':[], 'segments': []}
        #prendre le chemin le plus court jusque là
        meilleur = min(chemins_possibles, key=lambda x : x['distance'])

        #tracer si un axe est fourni
        if ax is not None:
            x_vals = [point[0] for point in meilleur['chemin']]
            y_vals = [point[1] for point in meilleur['chemin']]
            ax.plot(x_vals, y_vals, style, color=couleur, linewidth=2, alpha=alpha, marker='o',markersize=4, markerfacecolor=couleur)
        return meilleur
    






if __name__ == "__main__":
    # 1. Créer le hangar
    hangar = Hangar(Longueur=90, largeur_allee=5, r=2)
    
    print(f"=== CONSTRUCTION DU HANGAR ===")
    """print(f"Longueur: {hangar.Longueur} m")
    print(f"Largeur par allée: {hangar.largeur_allee} m")
    print(f"Largeur totale: {hangar.largeur_totale} m")
    print(f"Espacement vertical: {hangar.r} m")
    print(f"Allées: {hangar.allees}")
    print(f"Sens: {hangar.sens}")
    print(f"Centres: {hangar.centres}")
    print(f"Niveaux: {hangar.niveaux}")
    """
    
    # 2. Générer quelques points pour la démonstration
    # (Au lieu de tous les points, juste quelques-uns pour la clarté)
    commande = [
        ('AB', 7), ('BB', 11), ('B', 23)
    ]
    
    # 3. Placer ces points
    hangar.placer_commande(commande)
    
    
    print(f"\n=== POINTS PLACÉS ===")
    for (allee, n), (x, y) in sorted(hangar.points.items()):
        print(f"{allee}{n}: ({x:.1f}, {y:.1f}) m")

    p = ('AB',7)
    q= ('B',23)
    print("Distance AB 7 -> B23 : ", hangar.distance(p,q))
    print("Distance B23 -> AB 7: ", hangar.distance(q,p))

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