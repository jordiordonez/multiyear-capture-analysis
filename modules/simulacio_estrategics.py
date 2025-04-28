import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sorteig import assignar_isards_sorteig_csv


def simular_6_anys_tracking(
    initial_csv: str,
    captures_per_year_list: list = None,
    seed: int = None,
    min_colla_size: int = 8,
    max_colla_size: int = 20,
    tracked_count: int = 10,
    output_folder_data: str = 'data'
) -> (pd.DataFrame, list):
    """
    Simula 6 anys amb captures i tracking segons si han guanyat l'any anterior.
    Retorna el dataframe complet i els tracked_ids utilitzats.
    """

    if captures_per_year_list is None:
        captures_per_year_list = [150] * 6

    rng = np.random.RandomState(seed) if seed is not None else np.random
    df = pd.read_csv(os.path.join(output_folder_data, initial_csv), sep=';')
    historial = []
    pid = int(df['ID'].max()) + 1

    tracked_ids = []       # IDs dels caçadors que seguim
    last_winners = set()   # Guanyadors de l'any anterior

    for anyo, captures in enumerate(captures_per_year_list, start=1):
        print(f"🛠️ Preparant any {anyo} amb {captures} captures...")

        if anyo > 1 and tracked_ids:
            df_any_anterior = historial[-1]

            tracked_won_last = set(df_any_anterior.loc[
                (df_any_anterior['ID'].isin(tracked_ids)) &
                (df_any_anterior['adjudicats'] > 0),
                'ID'
            ])

            if tracked_won_last:
                all_winners_last = set(df_any_anterior.loc[df_any_anterior['adjudicats'] > 0, 'ID'])
                candidats = df[df['ID'].isin(all_winners_last)]
                permanents_tracked = df[df['ID'].isin(tracked_won_last)]

                n_permanents = permanents_tracked['ID'].nunique()
                n_needed = max(0, min_colla_size - n_permanents)
                altres_candidats = candidats[~candidats['ID'].isin(permanents_tracked['ID'])]

                if n_needed > 0 and not altres_candidats.empty:
                    seleccionats = altres_candidats.sample(min(n_needed, len(altres_candidats)), random_state=rng)
                    membres_colla = pd.concat([permanents_tracked, seleccionats])
                else:
                    membres_colla = permanents_tracked

                nom_nova_colla = f'TrackedColla_{anyo}'
                df.loc[df['ID'].isin(membres_colla['ID']), ['Modalitat', 'Colla_ID']] = ['A', nom_nova_colla]
                print(f"🔗 Creada nova colla '{nom_nova_colla}' amb {len(membres_colla)} caçadors per any {anyo}")

        temp_in = os.path.join(output_folder_data, f"temp_any_{anyo}.csv")
        df.to_csv(temp_in, sep=';', index=False)

        df_out = assignar_isards_sorteig_csv(
            file_csv=temp_in,
            total_captures=captures,
            output_csv=os.path.join(output_folder_data, f"resultats_any_{anyo}.csv"),
            seed=(seed + anyo * 100) if seed is not None else anyo * 100
        )
        df_out['any'] = anyo

        winners = df_out.loc[df_out['adjudicats'] > 0, 'ID'].tolist()
        if anyo == 1:
            if len(winners) < tracked_count:
                raise ValueError(f"No hi ha prou guanyadors per fer tracking (n={len(winners)})")
            tracked_ids = rng.choice(winners, size=tracked_count, replace=False).tolist()
            print(f"🎯 Caçadors seguits (fixos durant 6 anys): {tracked_ids}")

        last_winners = set(winners)
        historial.append(df_out)

        df = (
            df_out[['ID', 'Modalitat', 'Colla_ID', 'nova_prioritat', 'nou_anys_sense_captura', 'adjudicats']]
            .rename(columns={'nova_prioritat': 'Prioritat', 'nou_anys_sense_captura': 'anys_sense_captura'})
        )

        os.remove(temp_in)

    df_hist = pd.concat(historial, ignore_index=True)
    historial_file = os.path.join(output_folder_data, f'historial_6_anys_tracking_colles_min_{min_colla_size}.csv')
    df_hist.to_csv(historial_file, index=False)
    print(f"✅ Simulació completa i desada a {historial_file}")

    return df_hist, tracked_ids


def graficar_tracked_vs_altres(df_hist: pd.DataFrame, tracked_ids: list, min_size: int, output_folder_figures: str = 'figures'):
    """
    Genera gràfica sumant adjudicats dels tracked_ids vs. la mitjana dels altres.
    """

    target_sums = df_hist[df_hist['ID'].isin(tracked_ids)].groupby('ID')['adjudicats'].sum()
    other_sums = df_hist[~df_hist['ID'].isin(tracked_ids)].groupby('ID')['adjudicats'].sum()
    mean_other_sum = other_sums.mean()
    mean_target_sum = target_sums.mean()
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(target_sums.index.astype(str), target_sums.values)
    plt.axhline(mean_other_sum, color='red', linestyle='--', label=f'Mitjana altres caçadors ({mean_other_sum:.2f})')
    plt.axhline(mean_target_sum, color='black', linestyle='--', label=f'Mitjana caçadors estratègics({mean_target_sum:.2f})')
    plt.title(f'Suma d\'Adjudicats per Tracked IDs vs Altres (Colla mínima {min_size})')
    plt.xlabel('ID')
    plt.ylabel('Suma adjudicats')
    plt.legend()
    plt.grid(axis='y')

    if not os.path.exists(output_folder_figures):
        os.makedirs(output_folder_figures)

    output_path = os.path.join(output_folder_figures, f"Estrategics_vs_Aleatoris_colles_min_{min_size}.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"📈 Gràfica desada a {output_path}")


if __name__ == "__main__":
    initial_csv = 'sorteig.csv'
    captures_per_year = [150] * 6
    seed = 42
    max_colla_size = 20
    tracked_count = 10
    output_folder_data = 'data'
    output_folder_figures = 'figures'

    # --- Primera simulació (colla min 6)
    min_colla_size = 6
    df_hist_6, tracked_ids_6 = simular_6_anys_tracking(
        initial_csv,
        captures_per_year,
        seed,
        min_colla_size,
        max_colla_size,
        tracked_count,
        output_folder_data
    )
    graficar_tracked_vs_altres(df_hist_6, tracked_ids_6, min_colla_size, output_folder_figures)

    # --- Segona simulació (colla min 8)
    min_colla_size = 8
    df_hist_8, tracked_ids_8 = simular_6_anys_tracking(
        initial_csv,
        captures_per_year,
        seed,
        min_colla_size,
        max_colla_size,
        tracked_count,
        output_folder_data
    )
    graficar_tracked_vs_altres(df_hist_8, tracked_ids_8, min_colla_size, output_folder_figures)
