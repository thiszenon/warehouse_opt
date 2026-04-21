# src/algorithms/benchmark/data_generator.py
import random
from typing import List, Tuple, Dict

class WarehouseDataGenerator:
    """Génère des instances de test réalistes pour le benchmark"""
    
    def __init__(self, seed=42):
        random.seed(seed)
        
        # Configuration du hangar
        self.allees = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        self.allees_speciales = [ 'BB', 'CC', 'DD', 'EE', 'FF', 'GG', 'HH']
        
        # Sens des allées
        self.sens_montant = ['A', 'C', 'E', 'G', 'CC', 'EE', 'GG']
        self.sens_descendant = ['B', 'D', 'F', 'H', 'BB', 'DD', 'FF', 'HH']
        
        # Zones de hauteur
        self.zone_bas = (1, 20)      # Proche N1
        self.zone_milieu = (21, 45)  # N1-N2
        self.zone_haut = (46, 90)    # N2-N3
    
    def generate_small_command(self, n_points=3) -> List[Tuple[str, int]]:
        """Petite commande réaliste"""
        command = []
        
        for _ in range(n_points):
            # Choix aléatoire de l'allée
            if random.random() < 0.7:  # 70% allées normales
                allee = random.choice(self.allees)
            else:  # 30% allées spéciales
                allee = random.choice(self.allees_speciales)
            
            # Hauteur selon la zone (plus de points en bas)
            zone = random.choices(
                ['bas', 'milieu', 'haut'],
                weights=[0.6, 0.3, 0.1]
            )[0]
            
            min_h, max_h = getattr(self, f'zone_{zone}')
            hauteur = random.randint(min_h, max_h)
            
            # Assurer un nombre impair ou pair selon le côté de l'allée
            if random.random() < 0.5:
                numero = hauteur if hauteur % 2 == 1 else hauteur + 1
            else:
                numero = hauteur if hauteur % 2 == 0 else hauteur + 1
            
            command.append((allee, numero))
        
        return command
    
    def generate_medium_command(self, n_points=8) -> List[Tuple[str, int]]:
        """Commande moyenne réaliste"""
        command = []
        
        # S'assurer d'avoir une variété d'allées
        allees_utilisees = random.sample(self.allees, min(4, n_points))
        
        for i in range(n_points):
            if i < len(allees_utilisees):
                allee = allees_utilisees[i]
            else:
                if random.random() < 0.7:
                    allee = random.choice(self.allees)
                else:
                    allee = random.choice(self.allees_speciales)
            
            # Distribution plus uniforme sur les zones
            zone = random.choice(['bas', 'milieu', 'haut'])
            min_h, max_h = getattr(self, f'zone_{zone}')
            hauteur = random.randint(min_h, max_h)
            
            # Alterner côté gauche/droit
            if i % 2 == 0:
                numero = hauteur if hauteur % 2 == 1 else hauteur + 1
            else:
                numero = hauteur if hauteur % 2 == 0 else hauteur + 1
            
            command.append((allee, numero))
        
        return command
    
    def generate_large_command(self, n_points=15) -> List[Tuple[str, int]]:
        """Grande commande réaliste"""
        command = []
        
        # Utiliser toutes les allées
        allees_disponibles = self.allees.copy()
        random.shuffle(allees_disponibles)
        
        for i in range(n_points):
            if i < len(allees_disponibles):
                allee = allees_disponibles[i]
            else:
                # Réutiliser les allées
                allee = random.choice(self.allees)
            
            # Priorité aux zones basse et moyenne pour les grandes commandes
            zone = random.choices(
                ['bas', 'milieu', 'haut'],
                weights=[0.5, 0.4, 0.1]
            )[0]
            
            min_h, max_h = getattr(self, f'zone_{zone}')
            hauteur = random.randint(min_h, max_h)
            
            # Mélanger côtés
            if random.random() < 0.5:
                numero = hauteur if hauteur % 2 == 1 else hauteur + 1
            else:
                numero = hauteur if hauteur % 2 == 0 else hauteur + 1
            
            command.append((allee, numero))
        
        return command
    
    def generate_difficult_command(self, n_points=6) -> List[Tuple[str, int]]:
        """Commande difficile (points éloignés)"""
        command = []
        
        # Points extrêmes
        extremes = [
            ('A', 1),    # Bas gauche
            ('H', 90),   # Haut droite
            ('A', 90),   # Haut gauche
            ('H', 1),    # Bas droite
        ]
        
        # Ajouter quelques extrêmes
        n_extremes = min(4, n_points)
        command.extend(extremes[:n_extremes])
        
        # Ajouter des points aléatoires difficiles
        remaining = n_points - n_extremes
        for _ in range(remaining):
            # Choisir des allées opposées
            if random.random() < 0.5:
                allee = random.choice(['A', 'B', 'C'])  # Gauche
            else:
                allee = random.choice(['F', 'G', 'H'])  # Droite
            
            # Points extrêmes en hauteur
            if random.random() < 0.5:
                numero = random.choice([1, 3, 5, 7, 9])  # Très bas
            else:
                numero = random.choice([85, 87, 89, 90])  # Très haut
            
            command.append((allee, numero))
        
        return command
    
    def generate_test_suite(self) -> Dict[str, List]:
        """Génère une suite complète de tests"""
        return {
            'small': [
                self.generate_small_command(3),
                self.generate_small_command(4),
                self.generate_small_command(5),
            ],
            'medium': [
                self.generate_medium_command(6),
                self.generate_medium_command(8),
                self.generate_medium_command(10),
            ],
            'large': [
                self.generate_large_command(12),
                self.generate_large_command(15),
                self.generate_large_command(18),
            ],
            'difficult': [
                self.generate_difficult_command(4),
                self.generate_difficult_command(6),
                self.generate_difficult_command(8),
            ]
        }