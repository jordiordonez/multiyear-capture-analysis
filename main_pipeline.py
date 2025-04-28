# main_pipeline.py

import os
import random
import pandas as pd

from modules.generador import generar_dades_inicials
from modules.simulacio import simular_6_anys_variable
from modules.analisi import generar_heatmaps_i_grafics
from modules.report import generar_report_escenari, combinar_markdowns
from modules.config_escenaris import escenaris

# Assegurar carpetes
os.makedirs('data', exist_ok=True)
os.makedirs('figures', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# Anem guardant noms dels escenaris
noms_escenaris = []
index_escenari = 0
# Pipeline principal
for escenari in escenaris:
    print(f"\n🏹 Simulant: {escenari['nom']}...\n")
    index_escenari += 1
    # 1. Generar dades inicials
    generar_dades_inicials(
        total_cacadors_colla=escenari.get('total_cacadors_colla', 175),
        total_individuals=escenari.get('total_individuals', 190),
        min_colla_size=escenari.get('min_colla', 8),
        max_colla_size=escenari.get('max_colla', 20),
        output_path='data/sorteig.csv'
    )

    # 2. Simulació
    captures = escenari['captures_per_any']
    captures_per_year = [random.randint(captures[0], captures[1]) for _ in range(6)]
    simular_6_anys_variable(
        initial_csv='sorteig.csv',
        min_colla_size=escenari.get('min_colla', 8),
        max_colla_size=escenari.get('max_colla', 20),
        captures_per_year_list=captures_per_year,
        seed=42,
        new_hunters_range=escenari['new_hunters_per_year'],
        retired_hunters_range=escenari['retired_hunters_per_year']
    )

    # 3. Crear figures
    carpeta_figures = os.path.join('figures', escenari['nom'])
    generar_heatmaps_i_grafics(output_folder=carpeta_figures)

    # 4. Generar informe per escenari
    df_hist = pd.read_csv('data/historial_6_anys.csv')

    # ➡️ Nova part: construir evolució any a any
    evolucio_anys = []
    for anyo in range(1, 7):
        caçadors_total = len(df_hist[df_hist['any'] == anyo])
        caçadors_colla = len(df_hist[(df_hist['any'] == anyo) & (df_hist['Modalitat'] == 'A')])
        caçadors_individual = len(df_hist[(df_hist['any'] == anyo) & (df_hist['Modalitat'] == 'B')])
        captures_adjudicades = df_hist[(df_hist['any'] == anyo) & (df_hist['adjudicats'] == 1)].shape[0]

        evolucio_anys.append({
            'any': anyo,
            'cacadors_total': caçadors_total,
            'cacadors_colla': caçadors_colla,
            'cacadors_individual': caçadors_individual,
            'captures_adjudicades': captures_adjudicades
        })

    # ➡️ Ara cridem la funció passant evolucio_anys
    generar_report_escenari(
        nom_escenari=escenari['nom'],
        min_colla_size=escenari['min_colla'],
        captures_per_any=captures,
        new_hunters_per_year=escenari.get('new_hunters_per_year', 0),
        retired_hunters_per_year=escenari.get('retired_hunters_per_year', 0),
        index_escenari=index_escenari,
    )
    noms_escenaris.append(escenari['nom'])



# 5. Combinar en un sol Markdown
combinar_markdowns(noms_escenaris)

print("\n✅ Pipeline completat correctament!\n")
