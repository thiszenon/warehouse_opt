
def nearest_neighbor(graphe, start_idx=0):
    """ Plus proche voison pour ATSP """
    n = graphe.n 
    visited = [False]*n
    tour = [start_idx]
    visited[start_idx] = True

    for _ in range(n-1):
        current  = tour[-1]

        # Trouver le plus proche non visité
        candidates = []
        for j in range(n):
            if not visited[j] and graphe.matrice[current][j] < float('inf'):
                candidates.append((j, graphe.matrice[current][j]))
        if not candidates:
            return None #bloqué
        next_point, _ = min(candidates, key=lambda x:x[1])
        tour.append(next_point)
        visited[next_point]=True
    #verifier retour au depart

    if graphe.matrice[tour[-1]][tour[0]] < float('inf'):
        tour.append(tour[0]) # fermer le cycle
        return {
            'tour': [graphe.commande[i] for i in tour],
            'distance': sum(graphe.matrice[tour[i]][tour[i+1]] for i in range(n))
        }
    return None


def random_insertion(graphe):
    """Insertion aléatoire (baseline simple) """
    import random
    n = graphe.n
    unvisited = list(range(n))
    random.shuffle(unvisited)

    tour = [unvisited.pop()]
    while unvisited:
        best_pos = -1
        best_increase = float('inf')
        point_to_insert = unvisited.pop()

        # Trouver la meilleure position d'insertion
        for i in range(len(tour)):
            #cout d'insertion entre tour[i] et tour[i+1]
            if i==len(tour) -1:
                #insertion à la fin
                cost = (graphe.matrice[tour[i]][point_to_insert] + graphe.matrice[point_to_insert][tour[0]])
            else:
                cost = (graphe.matrice[tour[i]][point_to_insert] +
                        graphe.matrice[point_to_insert][tour[i+1]] - 
                        graphe.matrice[tour[i]][tour[i+1]])
            if cost < best_increase:
                best_increase = cost
                best_pos = i
        #Inserer à la meilleure position
        if best_pos == len(tour) - 1:
            tour.append(point_to_insert)
        else:
            tour.insert(best_pos + 1, point_to_insert)
    #fermer le cycle
    tour.append(tour[0])
    return {
        'tour': [graphe.commande[i] for i in tour],
        'distance': sum(graphe.matrice[tour[i]][tour[i+1]] for i in range(n))
    }
    
    