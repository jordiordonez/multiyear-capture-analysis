# main_pipeline.py

import os
import random
from modules.generador import generar_dades_inicials
from modules.simulacio import simular_6_anys_variable
from modules.analisi import generar_heatmaps_i_grafics
from modules.config_escenaris import escenaris
from main_informes import generar_informe_escenari, combinar_informes

# Crear carpetes si no existeixen
os.makedirs('data', exist_ok=True)
os.makedirs('figures', exist_ok=True)
os.makedirs('reports', exist_ok=True)

noms_escenaris = []

for escenari in escenaris:
    nom = escenari["nom"]
    print(f"🏹 Simulant: {nom}...")
    noms_escenaris.append(nom)

    # Generar estructura inicial de caçadors
    generar_dades_inicials(
        total_cacadors_colla=175,
        total_individuals=190,
        min_colla_size=escenari["min_colla"],
        max_colla_size=escenari["max_colla"],
        output_path='data/sorteig.csv'
    )

    # Decideix el tipus de simulació
    if isinstance(escenari["captures_per_any"], list):
        # Captures variables
        captures = [random.randint(escenari["captures_per_any"][0], escenari["captures_per_any"][1]) for _ in range(6)]
        simular_6_anys_variable('sorteig.csv', captures, seed=42)
    else:
        # Captures fixes
        simular_6_anys('sorteig.csv', escenari["captures_per_any"], years=6, seed=42,
                       new_hunters_range=escenari.get('new_hunters_per_year', 0),
                       retired_hunters_range=escenari.get('retired_hunters_per_year', 0),
                       min_colla_size=escenari["min_colla"])

    # Crear carpeta específica de figures
    figures_folder = os.path.join('figures', nom)
    os.makedirs(figures_folder, exist_ok=True)

    # Generar figures
    generar_heatmaps_i_grafics(output_folder=figures_folder)

    # Generar informe individual
    generar_informe_escenari(nom_escenari=nom, figures_folder=figures_folder)

# Finalment, combinar tots els informes
combinar_informes(noms_escenaris)
