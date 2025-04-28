import pandas as pd
import numpy as np
import math
from typing import Optional

"""
Assigna captures d'isard segons el règim de sorteig i exporta un CSV amb el camp 'adjudicats'
i 'nova_prioritat'.

Paràmetres
----------
file_csv : str
Ruta al fitxer CSV d'entrada amb full de dades 'inscrits'. Ha de contenir les columnes:
- ID
- Modalitat (A = colla, B = individual)
- Prioritat (enter > 0; ordinals P2=2, P3=3, P4=4, P4+n=4+n)
- Colla_ID (identificador de la colla; NaN o None per a individuals)
total_captures : int
Nombre total d'isards a distribuir.
output_csv : str
Nom del fitxer CSV de sortida (per defecte "resultats.csv").
seed : int, opcional
Llavors per al generador aleatori (per reproducibilitat).

Retorna
-------
pd.DataFrame
DataFrame ampliat amb les columnes:
- adjudicats: 0 o 1 segons si s'ha assignat captura
- nova_prioritat: prioritat calculada per a futurs sortejos
"""


def assignar_isards_sorteig_csv(
    file_csv: str,
    total_captures: int,
    output_csv: str = "resultats.csv",
    seed: Optional[int] = None
) -> pd.DataFrame:
    rng = np.random.RandomState(seed) if seed is not None else np.random
    df = pd.read_csv(file_csv, sep=';')

    required_cols = {'ID', 'Modalitat', 'Prioritat', 'Colla_ID', 'anys_sense_captura'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Falten columnes obligatòries: {required_cols - set(df.columns)}")

    df['adjudicats'] = 0
    df_colla = df[df['Modalitat'] == 'A'].copy()
    df_indiv = df[df['Modalitat'] == 'B'].copy()
    n_colla_applicants = len(df_colla)
    n_indiv_applicants = len(df_indiv)

    total_applicants = n_colla_applicants + n_indiv_applicants
    ratio = math.ceil(total_applicants / total_captures)

    # --- Proportional distribution of captures
    n_indiv = round(total_captures * n_indiv_applicants / total_applicants)
    n_colla = total_captures - n_indiv

    # --- Distribution per colla
    colles_df = df_colla.groupby('Colla_ID').size().reset_index(name='caçadors')
    colles_df['floor'] = (colles_df['caçadors'] // ratio).astype(int)
    colles_df['assignats'] = colles_df['floor']

    # --- Calculate remaining captures for colles (proportional share of leftovers)
    base_assigned = colles_df['assignats'].sum()
    proportional_remainder = n_colla - base_assigned
    for _ in range(proportional_remainder):
        colles_df['rati'] = colles_df['assignats'] / colles_df['caçadors']
        min_rati = colles_df['rati'].min()
        candidates = colles_df[np.isclose(colles_df['rati'], min_rati, atol=1e-6)]
        selected = candidates.sample(n=1, random_state=rng)
        colla_id = selected['Colla_ID'].values[0]
        colles_df.loc[colles_df['Colla_ID'] == colla_id, 'assignats'] += 1

    # --- Assign inside colles
    for _, row in colles_df.iterrows():
        cid = row['Colla_ID']
        n_assign = int(row['assignats'])

        while n_assign > 0:
            # Troba el mínim d’adjudicacions dins la colla
            adjudicacions_actuals = df[
                (df['Modalitat'] == 'A') & (df['Colla_ID'] == cid)
            ]['adjudicats']
            min_adjud = adjudicacions_actuals.min()

            # Grup amb menys adjudicacions
            group = df[
                (df['Modalitat'] == 'A') &
                (df['Colla_ID'] == cid) &
                (df['adjudicats'] == min_adjud)
            ].copy()

            if group.empty:
                break

            group['rand'] = rng.random(size=len(group))
            sorted_group = group.sort_values(
                by=['Prioritat', 'anys_sense_captura', 'rand'],
                ascending=[True, False, True]
            )

            n_to_assign = min(n_assign, len(sorted_group))
            assign_indices = sorted_group.index[:n_to_assign]
            df.loc[assign_indices, 'adjudicats'] += 1
            n_assign -= n_to_assign


    # --- Assign in modality B (individual)
    if n_indiv > 0:
        remaining_indiv = n_indiv

        while remaining_indiv > 0:
            # Troba el mínim d’adjudicacions actuals entre els individuals
            min_adjud = df[df['Modalitat'] == 'B']['adjudicats'].min()

            group = df[
                (df['Modalitat'] == 'B') &
                (df['adjudicats'] == min_adjud)
            ].copy()

            if group.empty:
                break

            group['rand'] = rng.random(size=len(group))
            sorted_group = group.sort_values(
                by=['Prioritat', 'anys_sense_captura', 'rand'],
                ascending=[True, False, True]
            )

            n_to_assign = min(remaining_indiv, len(sorted_group))
            assign_indices = sorted_group.index[:n_to_assign]
            df.loc[assign_indices, 'adjudicats'] += 1
            remaining_indiv -= n_to_assign


    # --- Compute new priority and history
    df['nova_prioritat'] = df['adjudicats'].apply(lambda x: 4 if x == 1 else 2)
    df['nou_anys_sense_captura'] = df.apply(
        lambda row: 0 if row['adjudicats'] == 1 else row['anys_sense_captura'] + 1,
        axis=1
    )

    df.drop(columns=['rand'], errors='ignore').to_csv(output_csv, index=False)
    return df

