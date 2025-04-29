import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from sorteig import assignar_isards_sorteig_csv
from generador import generar_dades_inicials


def simular_6_anys_tracking(
    initial_filename: str,
    captures_per_year_list: list = None,
    seed: int = None,
    min_colla_size: int = 8,
    max_colla_size: int = 20,
    tracked_count: int = 10,
    output_folder_data: str = 'data'
) -> (pd.DataFrame, list):
    """
    Simula 6 anys amb captures i tracking segons si han guanyat l'any anterior.
    Per any >1, crea tantes "colles" com cal per encabir tots els tracked_winners
    en grups de mida entre min_colla_size i max_colla_size, utilitzant només
    guanyadors de l'any anterior.

    Retorna el dataframe complet i els tracked_ids utilitzats.
    """

    if captures_per_year_list is None:
        captures_per_year_list = [150] * 6

    rng = np.random.RandomState(seed) if seed is not None else np.random
    csv_path = os.path.join(output_folder_data, initial_filename)
    df = pd.read_csv(csv_path, sep=';')
    historial = []
    tracked_ids = []

    for anyo, captures in enumerate(captures_per_year_list, start=1):
        print(f"🛠️ Preparant any {anyo} amb {captures} captures...")

        if anyo > 1 and tracked_ids:
            # Obtenir IDs dels guanyadors de l'any anterior
            df_any_anterior = historial[-1]
            winners_last = df_any_anterior.loc[df_any_anterior['adjudicats'] > 0, 'ID'].tolist()

            # Tracked winners
            tracked_won_last = [i for i in winners_last if i in tracked_ids]
            others = [i for i in winners_last if i not in tracked_won_last]

            colla_groups = []
            # 1) Particiona tracked_won_last en trossos de max_colla_size
            for i in range(0, len(tracked_won_last), max_colla_size):
                group = tracked_won_last[i:i+max_colla_size]
                colla_groups.append(group)

            # 2) Per cada grup, si < min_colla_size, top-up amb "others"
            for idx, group in enumerate(colla_groups):
                if len(group) < min_colla_size and others:
                    need = min_colla_size - len(group)
                    pick = rng.choice(others, size=min(need, len(others)), replace=False).tolist()
                    group.extend(pick)
                    # treure els seleccionats d'others
                    others = [o for o in others if o not in pick]

            # 3) Ara assignem cada grup com una colla separada
            for j, group in enumerate(colla_groups, start=1):
                colla_name = f"TrackedColla_{anyo}_{j}"
                df.loc[df['ID'].isin(group), ['Modalitat','Colla_ID']] = ['A', colla_name]
                print(f"🔗 Creada colla '{colla_name}' amb {len(group)} caçadors")

        # Estat intermitjà per al sorteig
        temp_in = os.path.join(output_folder_data, f"temp_any_{anyo}.csv")
        df.to_csv(temp_in, sep=';', index=False)

        # Assignació de captures
        df_out = assignar_isards_sorteig_csv(
            file_csv=temp_in,
            total_captures=captures,
            output_csv=os.path.join(output_folder_data, f"resultats_any_{anyo}.csv"),
            seed=(seed + anyo * 100) if seed is not None else anyo * 100
        )
        df_out['any'] = anyo

        # Primer any: triar tracked_ids inicials
        winners = df_out.loc[df_out['adjudicats'] > 0, 'ID'].tolist()
        if anyo == 1:
            if len(winners) < tracked_count:
                raise ValueError(f"No hi ha prou guanyadors per fer tracking (n={len(winners)})")
            tracked_ids = rng.choice(winners, size=tracked_count, replace=False).tolist()
            print(f"🎯 Tracked IDs (6 anys): {tracked_ids}")

        historial.append(df_out)

        # Prepara per al següent any
        df = (
            df_out[['ID','Modalitat','Colla_ID','nova_prioritat','nou_anys_sense_captura','adjudicats']]
            .rename(columns={'nova_prioritat':'Prioritat','nou_anys_sense_captura':'anys_sense_captura'})
        )
        os.remove(temp_in)

    # Concatena i desa l'historial
    df_hist = pd.concat(historial, ignore_index=True)
    out_file = os.path.join(output_folder_data, f"historial_6_anys_tracking_colles_min_{min_colla_size}.csv")
    df_hist.to_csv(out_file, index=False)
    print(f"✅ Simulació desada a {out_file}")

    return df_hist, tracked_ids


def graficar_tracked_vs_altres(
    df_hist: pd.DataFrame,
    tracked_ids: list,
    min_size: int,
    output_folder_figures: str = 'figures'
):
    """
    Genera gràfica comparant suma d'adjudicats dels tracked_ids vs. mitjana altres.
    """
    target_sums = df_hist[df_hist['ID'].isin(tracked_ids)].groupby('ID')['adjudicats'].sum()
    other_sums = df_hist[~df_hist['ID'].isin(tracked_ids)].groupby('ID')['adjudicats'].sum()
    mean_other = other_sums.mean()
    mean_target = target_sums.mean()

    plt.figure(figsize=(10,6))
    plt.bar(target_sums.index.astype(str), target_sums.values)
    plt.axhline(mean_other, linestyle='--', color= 'black', label=f'Mitjana altres ({mean_other:.2f})')
    plt.axhline(mean_target, linestyle='--', color= 'red', label=f'Mitjana estratègics ({mean_target:.2f})')
    plt.title(f'Suma adjudicats: estratègics vs altres (min colla {min_size})')
    plt.xlabel('ID')
    plt.ylabel('Total adjudicats')
    plt.legend()
    plt.grid(axis='y')

    os.makedirs(output_folder_figures, exist_ok=True)
    fig_path = os.path.join(output_folder_figures, f"Estrategics_vs_Aleatoris_colles_min_{min_size}.png")
    plt.savefig(fig_path, dpi=300)
    plt.close()
    print(f"📈 Gràfica desada a {fig_path}")

if __name__ == "__main__":
    total_cacadors_colla, total_individuals = 17500, 19000
    captures_per_year, seed = [15000]*6, 1000
    max_colla_size, tracked_count = 20, 100
    data_folder = 'data'; os.makedirs(data_folder, exist_ok=True)
    initial_filename = 'sorteig.csv'

    for min_colla_size in (6,8):
        print(f"\n=== Simulació per a colla min {min_colla_size} ===")
        generar_dades_inicials(
            total_cacadors_colla=total_cacadors_colla,
            total_individuals=total_individuals,
            min_colla_size=min_colla_size,
            max_colla_size=max_colla_size,
            output_path=os.path.join(data_folder,initial_filename)
        )
        df_hist, tracked_ids = simular_6_anys_tracking(
            initial_filename, captures_per_year, seed,
            min_colla_size, max_colla_size, tracked_count,
            output_folder_data=data_folder
        )
        graficar_tracked_vs_altres(df_hist, tracked_ids, min_colla_size, 'figures')

