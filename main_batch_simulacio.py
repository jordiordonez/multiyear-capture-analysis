from modules.generador import generar_dades_inicials
from modules.simulacio import simular_6_anys
from modules.analisi import generar_heatmaps_i_grafics
import os

# Crear carpeta de figures si no existeix
os.makedirs('figures', exist_ok=True)

# Llista d'escenaris
escenaris = [
    {
        'nom': 'base_8',
        'total_cacadors_colla': 175,
        'total_individuals': 190,
        'min_colla_size': 8,
        'max_colla_size': 20,
        'captures_per_any': 150,
        'anys': 6
    },
    {
        'nom': 'base_6',
        'total_cacadors_colla': 175,
        'total_individuals': 190,
        'min_colla_size': 6,
        'max_colla_size': 20,
        'captures_per_any': 150,
        'anys': 6
    },
    {
        'nom': 'captures_variants_8',
        'total_cacadors_colla': 175,
        'total_individuals': 190,
        'min_colla_size': 8,
        'max_colla_size': 20,
        'captures_per_any': [60, 100, 150, 200, 250, 300],
        'anys': 6
    },
    {
        'nom': 'captures_variants_6',
        'total_cacadors_colla': 175,
        'total_individuals': 190,
        'min_colla_size': 6,
        'max_colla_size': 20,
        'captures_per_any': [60, 100, 150, 200, 250, 300],
        'anys': 6
    },
]

# Processar cada escenari
for escenari in escenaris:
    print(f"🛠️ Processant escenari: {escenari['nom']}")

    # 1. Generar dades inicials
    generar_dades_inicials(
        total_cacadors_colla=escenari['total_cacadors_colla'],
        total_individuals=escenari['total_individuals'],
        min_colla_size=escenari['min_colla_size'],
        max_colla_size=escenari['max_colla_size'],
        output_file='sorteig.csv'
    )

    # 2. Simular captures
    if isinstance(escenari['captures_per_any'], list):
        # Simulació amb captures variables
        from modules.simulacio import simular_6_anys_variable
        simular_6_anys_variable(
            initial_csv='sorteig.csv',
            captures_per_year_list=escenari['captures_per_any'],
            seed=42
        )
    else:
        # Simulació clàssica captures fixes
        simular_6_anys(
            initial_csv='sorteig.csv',
            total_captures=escenari['captures_per_any'],
            years=escenari['anys'],
            seed=42
        )

    # 3. Crear carpeta de figures per l'escenari
    figures_path = os.path.join('figures', escenari['nom'])
    os.makedirs(figures_path, exist_ok=True)

    # 4. Generar gràfics
    generar_heatmaps_i_grafics(
        file_path=os.path.join('data', 'historial_6_anys.csv'),
        figures_dir=figures_path
    )

    print(f"✅ Escenari {escenari['nom']} completat!\n")

print("🎯 Totes les simulacions han estat completades.")
