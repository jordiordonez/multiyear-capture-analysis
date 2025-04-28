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
    Simula l'assignació de captures durant diversos anys.
    Aplica retirades i nous caçadors *abans* de cada sorteig (excepte any 1),
    i sempre manté la mida mínima de colla.
    """

    rng = np.random.RandomState(seed) if seed is not None else np.random
    df = pd.read_csv(os.path.join('data', initial_csv), sep=';')
    historial = []
    pid = int(df['ID'].max()) + 1  # següent ID disponible

    for anyo, captures in enumerate(captures_per_year_list, start=1):
        print(f"🛠️ Preparant any {anyo} amb {captures} captures...")

        # 1) Retirades i incorporacions *abans* del sorteig (excepte any 1)
        if anyo > 1:
            # --- Retirades ---
            if isinstance(retired_hunters_range, tuple) and retired_hunters_range != (0, 0):
                n_retire = rng.randint(retired_hunters_range[0],
                                       retired_hunters_range[1] + 1)
                if n_retire > 0 and len(df) > n_retire:
                    drop_ids = rng.choice(df['ID'], size=n_retire, replace=False)
                    df = df[~df['ID'].isin(drop_ids)]
                    print(f"🚪 {n_retire} caçadors retirats en l'any {anyo}")

            # --- Nous caçadors ---
            if isinstance(new_hunters_range, tuple) and new_hunters_range != (0, 0):
                n_new = rng.randint(new_hunters_range[0],
                                    new_hunters_range[1] + 1)
                if n_new > 0:
                    new_hunters = []
                    # 30% a colles existents, 30% a colles noves, 40% individus
                    to_exist = int(n_new * 0.3)
                    to_new   = int(n_new * 0.3)
                    to_ind   = n_new - to_exist - to_new

                    # a) Afegir a colles EXISTENTS
                    exist_collas = df.loc[df['Modalitat']=='A','Colla_ID'] \
                                    .dropna().unique()
                    for _ in range(to_exist):
                        if not len(exist_collas):
                            break
                        cid = rng.choice(exist_collas)
                        new_hunters.append({
                            'ID': pid,
                            'Modalitat': 'A',
                            'Prioritat': 3,
                            'Colla_ID': cid,
                            'anys_sense_captura': 0
                        })
                        pid += 1

                    # b) Crear colles NOVES (mida mínima)
                    n_colles = int(np.ceil(to_new / min_colla_size))
                    for _ in range(n_colles):
                        cname = f'NovaColla_{pid}'
                        for _ in range(min_colla_size):
                            if to_new <= 0:
                                break
                            new_hunters.append({
                                'ID': pid,
                                'Modalitat': 'A',
                                'Prioritat': 3,
                                'Colla_ID': cname,
                                'anys_sense_captura': 0
                            })
                            pid += 1
                            to_new -= 1

                    # c) Afegir individus
                    for _ in range(to_ind):
                        new_hunters.append({
                            'ID': pid,
                            'Modalitat': 'B',
                            'Prioritat': 3,
                            'Colla_ID': np.nan,
                            'anys_sense_captura': 0
                        })
                        pid += 1

                    df = pd.concat([df, pd.DataFrame(new_hunters)],
                                   ignore_index=True)
                    print(f"🧑‍🌾 {len(new_hunters)} nous caçadors afegits en l'any {anyo}")

            # --- Requilibrar colles perquè tinguin mínim de membres ---
            col_counts = df.loc[df['Modalitat']=='A', 'Colla_ID'].value_counts()
            for cid, cnt in col_counts.items():
                if cnt < min_colla_size:
                    need = min_colla_size - cnt
                    indiv = df[df['Modalitat']=='B']
                    if len(indiv) >= need:
                        move_idx = indiv.sample(need, random_state=rng).index
                        df.loc[move_idx, 'Modalitat'] = 'A'
                        df.loc[move_idx, 'Colla_ID']   = cid
                        print(f"🛠️ Reassignats {need} caçadors a {cid} per mantenir mida mínima")

        # 2) Desa estat actual abans del sorteig
        temp_in = f"data/temp_any_{anyo}.csv"
        df.to_csv(temp_in, sep=';', index=False)

        # 3) Assignar captures
        df_out = assignar_isards_sorteig_csv(
            file_csv=temp_in,
            total_captures=captures,
            output_csv=f"data/resultats_any_{anyo}.csv",
            seed=(seed + anyo * 100) if seed is not None else anyo * 100
        )
        df_out['any'] = anyo
        historial.append(df_out)

        # 4) Prepara df per al pròxim any
        df = (df_out[['ID', 'Modalitat', 'Colla_ID',
                      'nova_prioritat', 'nou_anys_sense_captura']]
              .rename(columns={
                  'nova_prioritat': 'Prioritat',
                  'nou_anys_sense_captura': 'anys_sense_captura'
              }))

        # 5) Neteja fitxer temporal
        os.remove(temp_in)

    # 6) Concatena i desa l'historial complet
    df_hist = pd.concat(historial, ignore_index=True)
    df_hist.to_csv('data/historial_6_anys.csv', index=False)
    print("✅ Simulació completa i desada a data/historial_6_anys.csv")
    return df_hist
