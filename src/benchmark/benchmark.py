# src/algorithms/benchmark/depot_benchmarker.py
import time
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from src.geometry.hangar_with_depot import HangarWithDepot
from src.algorithms import (
    NearestNeighborSolver,
    InsertionSolver,
    TwoOptSolver
)

class TSPBenchmarker:
    """Benchmarker complet pour le problème de collecte avec dépôt"""
    
    def __init__(self, output_dir="benchmark_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        
    def create_test_scenarios(self):
        """Crée différents scénarios de test"""
        from .data_generator import WarehouseDataGenerator
        
        generator = WarehouseDataGenerator(seed=42)
        test_suite = generator.generate_test_suite()
        
        scenarios = []
        
        # Scénario 1: Même dépôt/arrivée
        scenarios.append({
            'id': 'same_depot_arrival',
            'name': 'Dépôt = Arrivée',
            'depot_position': (20, -10),
            'arrival_position': None,
            'instances': []
        })
        
        # Scénario 2: Dépôt et arrivée différents
        scenarios.append({
            'id': 'different_depot_arrival',
            'name': 'Dépôt ≠ Arrivée',
            'depot_position': (20, -10),
            'arrival_position': (60, -10),
            'instances': []
        })
        
        # Remplir les instances pour chaque scénario
        for scenario in scenarios:
            for category, commands in test_suite.items():
                for i, commande in enumerate(commands):
                    scenario['instances'].append({
                        'id': f"{category}_{i}",
                        'category': category,
                        'commande': commande,
                        'n_points': len(commande)
                    })
        
        return scenarios
    
    def run_benchmark(self, solvers=None, n_runs=3):
        """Exécute le benchmark complet"""
        print("=" * 70)
        print("🚀 BENCHMARK COMPLET - COLLECTE AVEC DÉPÔT")
        print("=" * 70)
        
        # Solveurs par défaut
        if solvers is None:
            solvers = [
                NearestNeighborSolver(start_at_nearest=True),
                NearestNeighborSolver(start_at_nearest=False),
                InsertionSolver(seed=42, insertion_strategy='cheapest'),
                InsertionSolver(seed=42, insertion_strategy='farthest'),
                TwoOptSolver(),
            ]
        
        # Créer les scénarios
        scenarios = self.create_test_scenarios()
        
        all_results = []
        
        for scenario in scenarios:
            print(f"\n📊 SCÉNARIO: {scenario['name']}")
            print(f"   Dépôt: {scenario['depot_position']}")
            print(f"   Arrivée: {scenario.get('arrival_position', 'identique')}")
            
            scenario_results = {
                'scenario_id': scenario['id'],
                'scenario_name': scenario['name'],
                'depot_position': scenario['depot_position'],
                'arrival_position': scenario.get('arrival_position'),
                'instances': []
            }
            
            for instance in scenario['instances']:
                print(f"\n   Instance {instance['id']}: {instance['n_points']} points")
                
                # Créer le hangar
                hangar = HangarWithDepot(
                    Longueur=90,
                    largeur_allee=5,
                    r=2,
                    depot_position=scenario['depot_position'],
                    arrival_position=scenario.get('arrival_position')
                )
                
                # Placer les points
                hangar.placer_commande(instance['commande'])
                
                # Calculer la matrice de distances
                distance_info = hangar.calculer_tous_chemins(instance['commande'])
                distance_matrix = distance_info['matrice']
                depot_idx = distance_info['depot_idx']
                arrival_idx = distance_info['arrival_idx']
                
                instance_result = {
                    'instance_id': instance['id'],
                    'category': instance['category'],
                    'n_points': instance['n_points'],
                    'commande': instance['commande'],
                    'solvers': {}
                }
                
                # Tester chaque solveur
                for solver in solvers:
                    solver_results = []
                    
                    for run in range(n_runs):
                        try:
                            result = solver.solve(
                                distance_matrix, depot_idx, arrival_idx
                            )
                            
                            if result:
                                solver_results.append({
                                    'run': run,
                                    'distance': result['distance'],
                                    'time': result['time'],
                                    'tour': result['tour'],
                                    'success': True
                                })
                            else:
                                solver_results.append({
                                    'run': run,
                                    'success': False,
                                    'error': 'No solution found'
                                })
                                
                        except Exception as e:
                            solver_results.append({
                                'run': run,
                                'success': False,
                                'error': str(e)
                            })
                    
                    # Calculer les statistiques
                    successful_runs = [r for r in solver_results if r['success']]
                    
                    if successful_runs:
                        distances = [r['distance'] for r in successful_runs]
                        times = [r['time'] for r in successful_runs]
                        
                        stats = {
                            'mean_distance': float(np.mean(distances)),
                            'std_distance': float(np.std(distances)),
                            'min_distance': float(np.min(distances)),
                            'max_distance': float(np.max(distances)),
                            'mean_time': float(np.mean(times)),
                            'success_rate': len(successful_runs) / n_runs,
                            'sample_tour': successful_runs[0]['tour'] if successful_runs else None
                        }
                    else:
                        stats = {
                            'mean_distance': float('inf'),
                            'std_distance': 0,
                            'min_distance': float('inf'),
                            'max_distance': float('inf'),
                            'mean_time': 0,
                            'success_rate': 0,
                            'sample_tour': None
                        }
                    
                    instance_result['solvers'][solver.name] = stats
                
                scenario_results['instances'].append(instance_result)
            
            all_results.append(scenario_results)
            self.results.append(scenario_results)
        
        # Calculer les gaps par rapport au meilleur
        self._calculate_gaps(all_results)
        
        # Sauvegarder les résultats
        self._save_results(all_results)
        
        # Générer le rapport
        self._generate_report(all_results)
        
        return all_results
    
    def _calculate_gaps(self, results):
        """Calcule les gaps par rapport à la meilleure solution"""
        for scenario in results:
            for instance in scenario['instances']:
                # Trouver la meilleure distance
                best_distance = float('inf')
                for solver_name, stats in instance['solvers'].items():
                    if stats['mean_distance'] < best_distance:
                        best_distance = stats['mean_distance']
                
                # Calculer les gaps
                for solver_name, stats in instance['solvers'].items():
                    if stats['mean_distance'] < float('inf') and best_distance < float('inf'):
                        gap = ((stats['mean_distance'] - best_distance) / best_distance) * 100
                        stats['gap_to_best'] = gap
                    else:
                        stats['gap_to_best'] = None
    
    def _save_results(self, results):
        """Sauvegarde les résultats bruts"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"benchmark_results_{timestamp}.json"
        
        # Convertir en format JSON sérialisable
        serializable_results = []
        for scenario in results:
            serializable_scenario = {
                'scenario_id': scenario['scenario_id'],
                'scenario_name': scenario['scenario_name'],
                'depot_position': scenario['depot_position'],
                'arrival_position': scenario.get('arrival_position'),
                'instances': []
            }
            
            for instance in scenario['instances']:
                serializable_instance = {
                    'instance_id': instance['instance_id'],
                    'category': instance['category'],
                    'n_points': instance['n_points'],
                    'commande': [[str(a), n] for a, n in instance['commande']],
                    'solvers': {}
                }
                
                for solver_name, stats in instance['solvers'].items():
                    serializable_instance['solvers'][solver_name] = {
                        k: (v if not isinstance(v, float) or not np.isinf(v) else None)
                        for k, v in stats.items()
                        if k != 'sample_tour'  # Ne pas sauvegarder les tours complets
                    }
                
                serializable_scenario['instances'].append(serializable_instance)
            
            serializable_results.append(serializable_scenario)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False,default=str, escape_forward_slashes=False)
        
        print(f"\n💾 Résultats sauvegardés: {filename}")
    
    def _generate_report(self, results):
        """Génère un rapport complet avec graphiques"""
        # 1. Graphiques de performance
        self._generate_plots(results)
        
        # 2. Rapport HTML
        self._generate_html_report(results)
        
        # 3. Rapport CSV pour analyse
        self._generate_csv_report(results)
    
    def _generate_plots(self, results):
        """Génère les graphiques de performance"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Collecter toutes les données
        all_solvers = set()
        for scenario in results:
            for instance in scenario['instances']:
                all_solvers.update(instance['solvers'].keys())
        
        # Graphique 1: Temps vs Nombre de points
        ax1 = axes[0, 0]
        for solver in sorted(all_solvers):
            n_points_list = []
            time_list = []
            
            for scenario in results:
                for instance in scenario['instances']:
                    if solver in instance['solvers']:
                        stats = instance['solvers'][solver]
                        if stats['mean_time'] > 0:
                            n_points_list.append(instance['n_points'])
                            time_list.append(stats['mean_time'])
            
            if n_points_list:
                ax1.scatter(n_points_list, time_list, label=solver, alpha=0.7, s=50)
        
        ax1.set_xlabel('Nombre de points')
        ax1.set_ylabel('Temps moyen (s)')
        ax1.set_title('Performance temporelle')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # Graphique 2: Distribution des gaps
        ax2 = axes[0, 1]
        gap_data = []
        solver_names = []
        
        for solver in sorted(all_solvers):
            gaps = []
            for scenario in results:
                for instance in scenario['instances']:
                    if solver in instance['solvers']:
                        gap = instance['solvers'][solver].get('gap_to_best')
                        if gap is not None:
                            gaps.append(gap)
            
            if gaps:
                gap_data.append(gaps)
                solver_names.append(solver)
        
        if gap_data:
            ax2.boxplot(gap_data, labels=solver_names)
            ax2.set_xlabel('Algorithme')
            ax2.set_ylabel('Gap par rapport au meilleur (%)')
            ax2.set_title('Qualité des solutions')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
        
        # Graphique 3: Taux de succès
        ax3 = axes[1, 0]
        success_rates = []
        colors = []
        
        for solver in sorted(all_solvers):
            rates = []
            for scenario in results:
                for instance in scenario['instances']:
                    if solver in instance['solvers']:
                        rates.append(instance['solvers'][solver]['success_rate'] * 100)
            
            if rates:
                avg_rate = np.mean(rates)
                success_rates.append(avg_rate)
                colors.append('green' if avg_rate > 90 else 'orange' if avg_rate > 70 else 'red')
        
        if success_rates:
            bars = ax3.bar(range(len(solver_names)), success_rates, color=colors)
            ax3.set_xlabel('Algorithme')
            ax3.set_ylabel('Taux de succès moyen (%)')
            ax3.set_title('Robustesse des algorithmes')
            ax3.set_xticks(range(len(solver_names)))
            ax3.set_xticklabels(solver_names, rotation=45, ha='right')
            
            for bar, rate in zip(bars, success_rates):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2, height + 1,
                        f'{rate:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # Graphique 4: Distance vs Temps
        ax4 = axes[1, 1]
        for solver in sorted(all_solvers):
            distances = []
            times = []
            
            for scenario in results:
                for instance in scenario['instances']:
                    if solver in instance['solvers']:
                        stats = instance['solvers'][solver]
                        if stats['mean_distance'] < float('inf'):
                            distances.append(stats['mean_distance'])
                            times.append(stats['mean_time'])
            
            if distances:
                ax4.scatter(times, distances, label=solver, alpha=0.7, s=50)
        
        ax4.set_xlabel('Temps moyen (s)')
        ax4.set_ylabel('Distance moyenne (m)')
        ax4.set_title('Compromis temps/distance')
        ax4.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'benchmark_plots.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    def _generate_html_report(self, results):
        """Génère un rapport HTML complet"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Benchmark Collecte avec Dépôt</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                h1 {{ border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #3498db; color: white; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f8f9fa; }}
                tr:hover {{ background-color: #e9ecef; }}
                .good {{ color: #27ae60; font-weight: bold; }}
                .medium {{ color: #f39c12; font-weight: bold; }}
                .bad {{ color: #e74c3c; font-weight: bold; }}
                .metric {{ background-color: #e8f4f8; padding: 10px; border-radius: 5px; margin: 20px 0; }}
                .summary {{ background-color: #d5f4e6; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 5px; }}
                .scenario {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #3498db; }}
                footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <h1>📊 Benchmark - Optimisation des Parcours de Collecte</h1>
            <p><strong>Date du benchmark:</strong> {timestamp}</p>
            
            <div class="summary">
                <h2>🎯 Résumé Exécutif</h2>
                <p>Ce benchmark compare les algorithmes d'optimisation des parcours de collecte dans un hangar avec contraintes de circulation.</p>
                <p><strong>Problème:</strong> DÉPÔT → Points de collecte → ARRIVÉE (peut être identique au dépôt)</p>
                <p><strong>Objectif:</strong> Identifier les algorithmes les plus performants pour l'optimisation finale.</p>
            </div>
            
            <h2>📈 Graphiques de Performance</h2>
            <img src='benchmark_plots.png' alt="Graphiques de performance">
            
            <h2>🔍 Analyse par Scénario</h2>
        """
        
        # Parcourir chaque scénario
        for scenario_idx, scenario in enumerate(results):
            html += f"""
            <div class="scenario">
                <h3>Scénario {scenario_idx + 1}: {scenario['scenario_name']}</h3>
                <p><strong>Dépôt:</strong> {scenario['depot_position']}</p>
                <p><strong>Arrivée:</strong> {scenario.get('arrival_position', 'identique au dépôt')}</p>
            """
            
            # Tableau récapitulatif par catégorie
            html += """
                <h4>Performance par catégorie d'instances</h4>
                <table>
                    <tr>
                        <th>Catégorie</th>
                        <th>Algorithme</th>
                        <th>Distance moyenne</th>
                        <th>Temps moyen (s)</th>
                        <th>Gap moyen (%)</th>
                        <th>Taux succès</th>
                        <th>Recommandation</th>
                    </tr>
            """
            
            # Collecter les données par catégorie
            categories = {}
            for instance in scenario['instances']:
                cat = instance['category']
                if cat not in categories:
                    categories[cat] = {'instances': [], 'solvers': {}}
                categories[cat]['instances'].append(instance)
            
            # Remplir le tableau
            for cat, data in categories.items():
                first_instance = data['instances'][0]
                first_row = True
                
                for solver_name in sorted(first_instance['solvers'].keys()):
                    # Calculer les moyennes pour cette catégorie
                    distances = []
                    times = []
                    gaps = []
                    success_rates = []
                    
                    for instance in data['instances']:
                        if solver_name in instance['solvers']:
                            stats = instance['solvers'][solver_name]
                            if stats['mean_distance'] < float('inf'):
                                distances.append(stats['mean_distance'])
                                times.append(stats['mean_time'])
                                if stats.get('gap_to_best') is not None:
                                    gaps.append(stats['gap_to_best'])
                                success_rates.append(stats['success_rate'])
                    
                    if distances:
                        avg_dist = np.mean(distances)
                        avg_time = np.mean(times)
                        avg_gap = np.mean(gaps) if gaps else None
                        avg_success = np.mean(success_rates) * 100
                        
                        # Déterminer la recommandation
                        if avg_gap is not None:
                            if avg_gap < 5:
                                reco = "🎯 Excellent"
                                reco_class = "good"
                            elif avg_gap < 15:
                                reco = "👍 Bon"
                                reco_class = "good"
                            elif avg_gap < 30:
                                reco = "⚠️ Acceptable"
                                reco_class = "medium"
                            else:
                                reco = "⏱️ Médiocre"
                                reco_class = "bad"
                        else:
                            reco = "❓ Non mesurable"
                            reco_class = "medium"
                        
                        html += f"""
                        <tr>
                            <td>{cat if first_row else ''}</td>
                            <td>{solver_name}</td>
                            <td>{avg_dist:.1f}m</td>
                            <td>{avg_time:.4f}s</td>
                            <td>{avg_gap:.1f}% if avg_gap is not None else {'N/A'}</td>
                            <td>{avg_success:.1f}%</td>
                            <td class="{reco_class}">{reco}</td>
                        </tr>
                        """
                        
                        first_row = False
            
            html += """
                </table>
            </div>
            """
        
        # Recommandations finales
        html += """
            <div class="metric">
                <h2>🏆 Recommandations Finales</h2>
                <h3>Pour les petites instances (≤ 8 points):</h3>
                <p><strong>Depot Two-Opt</strong> - Offre le meilleur compromis qualité/temps avec une recherche locale.</p>
                
                <h3>Pour les instances moyennes (9-15 points):</h3>
                <p><strong>Depot Insertion (cheapest)</strong> - Bonne qualité de solution avec temps d'exécution raisonnable.</p>
                
                <h3>Pour les grandes instances (≥ 16 points):</h3>
                <p><strong>Depot Nearest Neighbor (start_at_nearest=True)</strong> - Très rapide avec des solutions acceptables.</p>
                
                <h3>Pour la robustesse maximale:</h3>
                <p><strong>Combinaison Depot Nearest Neighbor + Two-Opt</strong> - Garantit toujours une solution avec amélioration locale.</p>
            </div>
            
            <footer>
                <p>Généré automatiquement par DepotTSPBenchmarker</p>
                <p>Projet d'optimisation des parcours de collecte - Hangar Warehouse</p>
            </footer>
        </body>
        </html>
        """
        
        report_path = self.output_dir / 'benchmark_report.html'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"📄 Rapport HTML généré: {report_path}")
    
    def _generate_csv_report(self, results):
        """Génère un rapport CSV pour analyse externe"""
        import csv
        
        csv_path = self.output_dir / 'benchmark_results.csv'
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # En-tête
            writer.writerow([
                'scenario_id', 'scenario_name', 'instance_id', 'category',
                'n_points', 'solver', 'mean_distance', 'mean_time',
                'gap_to_best', 'success_rate', 'std_distance'
            ])
            
            # Données
            for scenario in results:
                for instance in scenario['instances']:
                    for solver_name, stats in instance['solvers'].items():
                        writer.writerow([
                            scenario['scenario_id'],
                            scenario['scenario_name'],
                            instance['instance_id'],
                            instance['category'],
                            instance['n_points'],
                            solver_name,
                            stats['mean_distance'],
                            stats['mean_time'],
                            stats.get('gap_to_best', ''),
                            stats['success_rate'],
                            stats['std_distance']
                        ])
        
        print(f"📊 Rapport CSV généré: {csv_path}")