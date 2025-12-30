
import matplotlib.pyplot as plt
import pandas as pd

def generate_report(results, filename="benchmark-report.html"):
    """Génère un rapport HTML avec graphiques """

    #convertir en dataFrame
    dataF = pd.DataFrame(results)

    #graphiques
    fig, axes = plt.subplots(2,2, figsize=(12,10))

    #1. Temps de calcul vs nombe de points
    ax1 = axes[0,0]
    for algo in ['nearest_neighbor', 'random_insertion']:
        times = [r[algo]['time'] for r in results if algo in r ]
        points = [r['n_points'] for r in results if algo in r]
        ax1.plot(points, times, 'o-', label=algo)
    ax1.set_xlabel('Nombre de points')
    ax1.set_ylabel('Temps (s)')
    ax1.legend()
    ax1.set_title('Performance tempo')

    #2. Qualité des solutions (gap %)
    ax2 = axes[0,1]
    gaps = []
    for r in results:
        if 'nearest_neighbor' in r and r['nearest_neighbor']['gap']:
            gaps.append(r['nearest_neighbor']['gap'])
    ax2.hist(gaps, bins=20, alpha=0.7)
    ax2.set_xlabel('Gap optimal (%)')
    ax2.set_ylabel('Fréquence')
    ax2.set_title('Distribution de la qualité')

    #sauvegarder
    plt.tight_layout()
    plt.savefig('benchmark_plots.png', dpi=150)

    #Generer HTML
    html = f"""
    <html>
    <head><title>Benchmark ATSP Warehouse</title></head>
    <body>
        <h1>Rapport de Benchmark</h1>
        <img src="benchmark_plots.png" width="800">
        <h2>Résumé</h2>
        <p>Nombre de tests: {len(results)}</p>
        <h2>Données détaillées</h2>
        {dataF.to_html()}
    </body>
    </html>
    """
    with open(filename, 'w') as file:
        file.write(html)
    print(f"rapport généré : {filename}")