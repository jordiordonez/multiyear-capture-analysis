import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colorbar import ColorbarBase

def generar_heatmaps_i_grafics(file_path='data/historial_6_anys.csv', output_folder='figures'):
    os.makedirs(output_folder, exist_ok=True)
    data = pd.read_csv(file_path)
    data['captures_consecutives'] = 0

    data = data.sort_values(by=['ID', 'any'])

    previous_id = None
    streak = 0
    for idx, row in data.iterrows():
        current_id = row['ID']
        adjudicat = row.get('adjudicats', 0)
        if current_id != previous_id:
            streak = 1 if adjudicat == 1 else 0
        else:
            if adjudicat >0:
                streak = max(1, streak + 1)
            else:
                streak = min(0, streak - 1)
        data.at[idx, 'captures_consecutives'] = streak
        previous_id = current_id

    # Clamp captures consecutives
    data['captures_consecutives_clamped'] = data['captures_consecutives'].clip(lower=-3, upper=3)

    # Create heatmap pivots without filling NaN
    pivot_A = data[data['Modalitat'] == 'A'].pivot(
        index='ID',
        columns='any',
        values='captures_consecutives_clamped'
    )
    pivot_B = data[data['Modalitat'] == 'B'].pivot(
        index='ID',
        columns='any',
        values='captures_consecutives_clamped'
    )

    # Insert empty separator rows
    empty_rows = pd.DataFrame(np.nan, index=["", "", ""], columns=pivot_A.columns)
    pivot_heatmap = pd.concat([pivot_A, empty_rows, pivot_B])

    # Colors mapping
    valors_fixos = [-3, -2, -1, 0, 1, 2, 3]
    valor_to_color = {
        -3: "#8B0000",  # Dark red
        -2: "#FF6347",  # Light red
        -1: "#FFA500",  # Orange
         0: "#FFD700",  # Gold
         1: "#87CEFA",  # Light blue
         2: "#0000CD",  # Dark blue
         3: "#4B0082",  # Indigo
    }
    cmap = ListedColormap([valor_to_color[v] for v in valors_fixos])
    norm = BoundaryNorm(boundaries=[-3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5], ncolors=7)

    # HEATMAP
    plt.figure(figsize=(22, 16))
    ax = sns.heatmap(
        pivot_heatmap,
        cmap=cmap,
        norm=norm,
        linewidths=0.5,
        linecolor='gray',
        cbar=False
    )

    # Draw separation line
    separacio_index = len(pivot_A) + 1.5
    plt.hlines(y=separacio_index, xmin=0, xmax=pivot_heatmap.shape[1], colors='black', linewidth=8)

    # Labels for A/B sections
    plt.text(-0.2, (len(pivot_A)-1)/2, 'Modalitat A', va='center', ha='center', rotation=90, fontsize=18, fontweight='bold')
    plt.text(-0.2, len(pivot_A)+2+(len(pivot_B)-1)/2, 'Modalitat B', va='center', ha='center', rotation=90, fontsize=18, fontweight='bold')

    plt.suptitle('Adjudicacions Consecutives per ID\nSeparat per Modalitat A i B', fontsize=26, fontweight='bold', y=.95)
    plt.xlabel('Any', fontsize=20, fontweight='bold')
    plt.ylabel('ID', fontsize=20, fontweight='bold')
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=12)
    plt.tight_layout(rect=[0, 0, 0.9, 0.95])

    # Colorbar
    cbar_ax = plt.gcf().add_axes([0.93, 0.25, 0.02, 0.5])
    cb = ColorbarBase(cbar_ax, cmap=cmap, norm=norm, ticks=valors_fixos)
    cb.ax.set_yticklabels(valors_fixos, fontsize=18)
    cb.set_label('Adjudicacions Consecutives', fontsize=18, fontweight='bold')

    plt.savefig(os.path.join(output_folder, "heatmap_captures_consecutives_final.png"), dpi=300)
    plt.close()

    # STACKED BARS
    data_A = data[data['Modalitat'] == 'A']
    data_B = data[data['Modalitat'] == 'B']

    def crear_taules_modalitat(data_modalitat):
        counts_table = data_modalitat.groupby(['any', 'captures_consecutives_clamped']).size().unstack(fill_value=0)
        percent_table = counts_table.div(counts_table.sum(axis=1), axis=0) * 100
        return counts_table, percent_table

    counts_A, percent_A = crear_taules_modalitat(data_A)
    counts_B, percent_B = crear_taules_modalitat(data_B)

    anys = sorted(list(set(percent_A.index).union(set(percent_B.index))))
    x = np.arange(len(anys))
    bar_width = 0.35
    separacio = 0.15

    fig, ax = plt.subplots(figsize=(20, 10))
    bottom_A = np.zeros(len(x))
    bottom_B = np.zeros(len(x))

    valors_reals = sorted(set(percent_A.columns).union(percent_B.columns))
    for v in valors_fixos:
        color = valor_to_color[v]
        if v in valors_reals:
            data_A_pct = percent_A.get(v, pd.Series(0, index=anys))
            data_B_pct = percent_B.get(v, pd.Series(0, index=anys))
            data_A_count = counts_A.get(v, pd.Series(0, index=anys))
            data_B_count = counts_B.get(v, pd.Series(0, index=anys))

            bars_A = ax.bar(x - bar_width/2 - separacio/2, data_A_pct, bottom=bottom_A, width=bar_width, color=color, edgecolor='black')
            bars_B = ax.bar(x + bar_width/2 + separacio/2, data_B_pct, bottom=bottom_B, width=bar_width, color=color, edgecolor='black')

            for i, bar in enumerate(bars_A):
                height = bar.get_height()
                if height > 5:
                    ax.text(bar.get_x() + bar.get_width()/2, bottom_A[i] + height/2, f"{round(height)}%\n({int(data_A_count.iloc[i])})",
                            ha='center', va='center', fontsize=10)
            for i, bar in enumerate(bars_B):
                height = bar.get_height()
                if height > 5:
                    ax.text(bar.get_x() + bar.get_width()/2, bottom_B[i] + height/2, f"{round(height)}%\n({int(data_B_count.iloc[i])})",
                            ha='center', va='center', fontsize=10)

            bottom_A += np.array(data_A_pct)
            bottom_B += np.array(data_B_pct)

    for i in range(len(x)):
        ax.text(x[i] - bar_width/2 - separacio/2, 101, 'A', ha='center', fontsize=14, fontweight='bold')
        ax.text(x[i] + bar_width/2 + separacio/2, 101, 'B', ha='center', fontsize=14, fontweight='bold')

    ax.set_xlabel('Any', fontsize=18, fontweight='bold')
    ax.set_ylabel('Percentatge (%)', fontsize=18, fontweight='bold')
    ax.set_title('Comparació Modalitat A vs B\nRepartició Percentual Adjudicacions Consecutives per Any', fontsize=24, fontweight='bold', pad=30)
    ax.set_xticks(x)
    ax.set_xticklabels(anys, fontsize=16)

    handles = [plt.Rectangle((0,0),1,1,color=valor_to_color[v]) for v in valors_fixos if v in valors_reals]
    labels = [str(v) for v in valors_fixos if v in valors_reals]
    ax.legend(handles, labels, title='Adjudicacions Consecutives', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14, title_fontsize=16)

    ax.set_ylim(-10, 110)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    plt.savefig(os.path.join(output_folder, "stacked_grouped_bar_percentatges_separat.png"), dpi=300)
    plt.close()

        # ————————————————————————————————————————————————————————————————
    # Nou gràfic: Modalitat A, col·les petites vs col·les grans (>10),
    #     identificades CADA ANY segons la seva mida AQUELL ANY
    # ————————————————————————————————————————————————————————————————
    data_A = data[data['Modalitat'] == 'A']
    anys = sorted(data_A['any'].unique())

    # valors de captures consecutives i colors ja definits abans:
    # valors_fixos = [-3, -2, -1, 0, 1, 2, 3]
    # valor_to_color = { … }

    # 1) crear taules buides per a counts i pct
    counts_small = pd.DataFrame(0, index=anys, columns=valors_fixos)
    counts_large = pd.DataFrame(0, index=anys, columns=valors_fixos)
    pct_small    = pd.DataFrame(0.0, index=anys, columns=valors_fixos)
    pct_large    = pd.DataFrame(0.0, index=anys, columns=valors_fixos)

    # 2) omplir-les any per any
    for anyo in anys:
        df_y = data_A[data_A['any'] == anyo]
        # mida de cada colla aquell any
        sizes = df_y.groupby('Colla_ID')['ID'].nunique()
        if sizes.empty:
            continue
        min_sz = sizes.min()
        small_ids = sizes[sizes == min_sz].index
        large_ids = sizes[sizes > 10].index

        # comptar captures_consecutives_clamped dins cada grup
        series_s = df_y[df_y['Colla_ID'].isin(small_ids)]['captures_consecutives_clamped']
        series_l = df_y[df_y['Colla_ID'].isin(large_ids)]['captures_consecutives_clamped']
        cnt_s = series_s.value_counts().to_dict()
        cnt_l = series_l.value_counts().to_dict()
        total_s = series_s.size
        total_l = series_l.size

        for v in valors_fixos:
            c_s = cnt_s.get(v, 0)
            c_l = cnt_l.get(v, 0)
            counts_small.at[anyo, v] = c_s
            counts_large.at[anyo, v] = c_l
            pct_small.at[anyo, v]    = (c_s / total_s * 100) if total_s > 0 else 0
            pct_large.at[anyo, v]    = (c_l / total_l * 100) if total_l > 0 else 0

    # 3) dibuixar el gràfic apilat
    x = np.arange(len(anys))
    bar_width = 0.35
    separacio = 0.15

    fig, ax = plt.subplots(figsize=(20, 10))
    bottom_s = np.zeros(len(x))
    bottom_l = np.zeros(len(x))

    for v in valors_fixos:
        color = valor_to_color[v]
        ps = pct_small[v].values
        pl = pct_large[v].values
        cs = counts_small[v].values
        cl = counts_large[v].values

        bars_s = ax.bar(x - bar_width/2 - separacio/2, ps,
                        bottom=bottom_s, width=bar_width,
                        color=color, edgecolor='black')
        bars_l = ax.bar(x + bar_width/2 + separacio/2, pl,
                        bottom=bottom_l, width=bar_width,
                        color=color, edgecolor='black')

        # etiqueta amb % i (n) només si n>0
        for i, b in enumerate(bars_s):
            h = b.get_height()
            if cs[i] > 0:
                ax.text(b.get_x()+b.get_width()/2, bottom_s[i]+h/2,
                        f"{round(h)}%\n({cs[i]})",
                        ha='center', va='center', fontsize=12)
        for i, b in enumerate(bars_l):
            h = b.get_height()
            if cl[i] > 0:
                ax.text(b.get_x()+b.get_width()/2, bottom_l[i]+h/2,
                        f"{round(h)}%\n({cl[i]})",
                        ha='center', va='center', fontsize=12)

        bottom_s += ps
        bottom_l += pl

    # marca “Petites” i “Grans” sobre cada any
    for i in range(len(x)):
        ax.text(x[i] - bar_width/2 - separacio/2, 101, 'Petites',
                ha='center', fontsize=14, fontweight='bold')
        ax.text(x[i] + bar_width/2 + separacio/2, 101, 'Grans',
                ha='center', fontsize=14, fontweight='bold')

    # format del gràfic
    ax.set_xlabel('Any', fontsize=18, fontweight='bold')
    ax.set_ylabel('Percentatge (%)', fontsize=18, fontweight='bold')
    ax.set_title('Modalitat A: Col·les petites vs grans (>10)\n'
                 'Repartició Captures Consecutives per Any',
                 fontsize=24, fontweight='bold', pad=30)
    ax.set_xticks(x)
    ax.set_xticklabels(anys, fontsize=16)

    handles = [plt.Rectangle((0,0),1,1,color=valor_to_color[v])
               for v in valors_fixos]
    labels = [str(v) for v in valors_fixos]
    ax.legend(handles, labels, title='Captures Consecutives',
              bbox_to_anchor=(1.05,1), loc='upper left',
              fontsize=14, title_fontsize=16)

    ax.set_ylim(-10, 110)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder,
                             "stacked_grouped_bar_petites_vs_grans.png"),
                dpi=300)
    plt.close()
