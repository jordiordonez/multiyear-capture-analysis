# modules/simulacio.py

import pandas as pd
import numpy as np
import os
import random
from modules.sorteig import assignar_isards_sorteig_csv
from modules.generador import generate_colla_sizes

def simular_6_anys_variable(
    initial_csv: str,
    captures_per_year_list: list,
    seed: int = None,
    min_colla_size: int = 8,
    max_colla_size: int = 20,
    new_hunters_range: tuple = (0, 0),
    retired_hunters_range: tuple = (0, 0)
) -> pd.DataFrame:
    """
    Simula l'assignació de captures durant diversos anys, amb captures, nous caçadors i retirades variables.

    Args:
        initial_csv: Fitxer CSV inicial.
        captures_per_year_list: Nombre de captures per any.
        seed: Semilla aleatòria.
        min_colla_size, max_colla_size: Rang de mida per les colles.
        new_hunters_range: Tuple (min, max) nous caçadors per any.
        retired_hunters_range: Tuple (min, max) caçadors que pleguen per any.
    """

    rng = np.random.RandomState(seed) if seed is not None else np.random

    df = pd.read_csv(os.path.join('data', initial_csv), sep=';')
    historial = []
    pid = df['ID'].max() + 1  # ID següent

    for anyo, captures in enumerate(captures_per_year_list, start=1):
        print(f"🛠️ Simulant temporada {anyo} amb {captures} captures...")

        # Desa estat temporal
        temp_in = f"data/temp_any_{anyo}.csv"
        df.to_csv(temp_in, sep=';', index=False)

        # Assignar captures
        df_res = assignar_isards_sorteig_csv(
            file_csv=temp_in,
            total_captures=captures,
            output_csv=f"data/resultats_any_{anyo}.csv",
            seed=seed + anyo * 100 if seed is not None else anyo * 100
        )

        df_res['any'] = anyo
        historial.append(df_res)

        # Prepara estat pel següent any
        df = df_res[['ID', 'Modalitat', 'Colla_ID', 'nova_prioritat', 'nou_anys_sense_captura']].rename(
            columns={'nova_prioritat': 'Prioritat', 'nou_anys_sense_captura': 'anys_sense_captura'}
        )

        # --- Simulació de retirades ---
        if isinstance(retired_hunters_range, tuple) and retired_hunters_range != (0, 0):
            n_retire = rng.randint(retired_hunters_range[0], retired_hunters_range[1] + 1)
            if n_retire > 0 and len(df) > n_retire:
                ids_to_remove = rng.choice(df['ID'], size=n_retire, replace=False)
                df = df[~df['ID'].isin(ids_to_remove)]
                print(f"🚪 {n_retire} caçadors retirats en l'any {anyo}")

        # --- Simulació de nous caçadors ---
        if isinstance(new_hunters_range, tuple) and new_hunters_range != (0, 0):
            n_new = rng.randint(new_hunters_range[0], new_hunters_range[1] + 1)
            if n_new > 0:
                new_hunters = []

                # Percentatge de distribució
                n_to_existing = int(n_new * 0.30)
                n_to_new_colles = int(n_new * 0.30)
                n_to_individuals = n_new - n_to_existing - n_to_new_colles

                # 1. Nous a colles EXISTENTS
                colles_existents = df[df['Modalitat'] == 'A']['Colla_ID'].dropna().unique()
                for _ in range(n_to_existing):
                    if len(colles_existents) == 0:
                        break
                    colla_id = rng.choice(colles_existents)
                    new_hunters.append({
                        'ID': pid,
                        'Modalitat': 'A',
                        'Prioritat': 3,
                        'Colla_ID': colla_id,
                        'anys_sense_captura': 0
                    })
                    pid += 1

                # 2. Nous a colles NOVES
                n_colles = int(np.ceil(n_to_new_colles / min_colla_size))
                for i in range(n_colles):
                    colla_size = min_colla_size
                    colla_name = f'NovaColla_{pid}'
                    for _ in range(colla_size):
                        if n_to_new_colles <= 0:
                            break
                        new_hunters.append({
                            'ID': pid,
                            'Modalitat': 'A',
                            'Prioritat': 3,
                            'Colla_ID': colla_name,
                            'anys_sense_captura': 0
                        })
                        pid += 1
                        n_to_new_colles -= 1

                # 3. Nous INDIVIDUALS
                for _ in range(n_to_individuals):
                    new_hunters.append({
                        'ID': pid,
                        'Modalitat': 'B',
                        'Prioritat': 3,
                        'Colla_ID': np.nan,
                        'anys_sense_captura': 0
                    })
                    pid += 1

                df_new = pd.DataFrame(new_hunters)
                df = pd.concat([df, df_new], ignore_index=True)
                print(f"🧑‍🌾 {len(new_hunters)} nous caçadors afegits en l'any {anyo}")

        # --- Mantenir coherència de colles ---
        # Si una colla cau per sota de mida mínima, reassignar-hi individuals
        colles_counts = df[df['Modalitat'] == 'A'].groupby('Colla_ID').size()
        colles_deficients = colles_counts[colles_counts < min_colla_size].index.tolist()
        
        for colla_id in colles_deficients:
            needed = min_colla_size - colles_counts[colla_id]
            individus = df[df['Modalitat'] == 'B']
            if len(individus) >= needed:
                ids_to_move = individus.sample(needed, random_state=rng).index
                df.loc[ids_to_move, 'Modalitat'] = 'A'
                df.loc[ids_to_move, 'Colla_ID'] = colla_id
                print(f"🛠️ {needed} caçadors individuals reassignats a {colla_id} per mantenir la mida mínima.")

        # Netejar fitxer temporal
        os.remove(temp_in)

    # Guardar historial
    df_hist = pd.concat(historial, ignore_index=True)
    df_hist.to_csv('data/historial_6_anys.csv', index=False)
    print("✅ Simulació completa i desada a data/historial_6_anys.csv")

    return df_hist
