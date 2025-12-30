
def solve_exact(graphe, timeout=30):
    """
    Solution exacte par recherche exhaustive
    Utilisable seulement pour n <= 8
    """
    if graphe.n > 8:
        return None
    n = graphe.n
    best_tour = None
    best_dist = float('inf')

    from itertools import permutations
    import time
    start_time = time.time()

    #fixer le point 0 comme depart
    for perm in permutations(range(1,n)):
        if time.time() - start_time > timeout:
            break
        tour = [0] + list(perm) + [0] #cycle complet
        #calculer distance
        dist=0
        valid = True
        for i in range(n):
            d= graphe.matrice[tour[i]][tour[i+1]]
            if d == float('inf'):
                valid =False
                break
            dist+=d
        if valid and dist < best_dist:
            best_dist = dist
            best_tour = tour
    if best_tour:
        return {
            'tour': [graphe.commande[i] for i in best_tour],
            'distance': best_dist,
            'optimal': True
        }
    return None

