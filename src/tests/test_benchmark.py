
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.benchmark.benchmark import TSPBenchmarker

def main():
    print("🚀 DÉMARRAGE DU BENCHMARK - PARCOURS DE COLLECTE")
    print("=" * 70)
    
    # Créer le benchmarker
    benchmarker = TSPBenchmarker(output_dir="benchmark_results")
    
    # Exécuter le benchmark
    results = benchmarker.run_benchmark(n_runs=3)
    
    # Afficher un résumé
    print("\n" + "=" * 70)
    print("📋 RÉSUMÉ DES RÉSULTATS")
    print("=" * 70)
    
    for scenario in results:
        print(f"\n📊 {scenario['scenario_name']}:")
        print(f"   Nombre d'instances: {len(scenario['instances'])}")
        
        # Calculer les statistiques globales
        for solver_name in ['Nearest Neighbor', 'Insertion', 'Two-Opt']:
            distances = []
            success_rates = []
            
            for instance in scenario['instances']:
                for name, stats in instance['solvers'].items():
                    if solver_name in name:
                        if stats['mean_distance'] < float('inf'):
                            distances.append(stats['mean_distance'])
                        success_rates.append(stats['success_rate'])
            
            if distances:
                avg_dist = sum(distances) / len(distances)
                avg_success = sum(success_rates) / len(success_rates) * 100
                print(f"   {solver_name}: {avg_dist:.1f}m, succès: {avg_success:.1f}%")
    
    print("\n" + "=" * 70)
    print("✅ BENCHMARK TERMINÉ AVEC SUCCÈS!")
    print("=" * 70)
    print("\n📁 Résultats disponibles dans le dossier 'benchmark_final_results':")
    print("   - benchmark_report.html (rapport complet)")
    print("   - benchmark_plots.png (graphiques)")
    print("   - benchmark_results.csv (données brutes)")
    print("   - benchmark_results_*.json (résultats détaillés)")

if __name__ == "__main__":
    main()