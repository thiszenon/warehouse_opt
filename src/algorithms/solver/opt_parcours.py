
#Construction de l'algorithme d'optimisation du parcours lors de la collecte

##ETAPE 1:
#    - grouper les n points de chaque allées
#    - ordonner les groupes  de maniere alternées montée,descente . et en combien de facons
def grouper_by_allee(commande):
    if commande is None:
        print("commande  vide")
        return {} # dictionnaire vide 
    groupes = {}
    for allee,position in commande:
        if allee not in groupes:
            groupes[allee]= [] # si l'allée n'est pas encore dans le groupe on la crée
        groupes[allee].append((allee,position))
    return groupes


##ETAPE 2:
#    - Partitionner une allée en 2 niveau: niveau haut et bas. 
#    - organiniser les points dans chaque partie du niveau
#    - définir combien des points dans chaque partie.

## ETAPE 3:
#    - Construire le graphe des partitions
#    - pacourir ou passer par chaque partition une et une seule fois en respectant le sens
# 
## ETAPE 4:
#    - trouver un ordre de parcours de ces partitions en minimisant la distance .
#    - deployer les élements de chaque partition equivaut à l'ordre du parcours de tous les points. 