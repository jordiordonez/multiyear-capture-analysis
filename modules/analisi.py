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
    streak = None
    for idx, row in data.iterrows():
        current_id = row['ID']
        adjudicat = row['adjudicats']
        if current_id != previous_id:
            streak = 1 if adjudicat == 1 else 0
        else:
            streak = streak + 1 if adjudicat == 1 else (0 if streak > 0 else streak - 1)
        data.at[idx, 'captures_consecutives'] = streak
        previous_id = current_id

    # Clamp captures consecutives
    data['captures_consecutives_clamped'] = data['captures_consecutives'].clip(lower=-3, upper=3)

    pivot_A = data[data['Modalitat'] == 'A'].pivot(index='ID', columns='any', values='captures_consecutives_clamped').fillna(0)
    pivot_B = data[data['Modalitat'] == 'B'].pivot(index='ID', columns='any', values='captures_consecutives_clamped').fillna(0)
    empty_row = pd.DataFrame(np.nan, index=['', '', ''], columns=pivot_A.columns)
    pivot_heatmap = pd.concat([pivot_A, empty_row, pivot_B])

    # Colors fixos
    valors_fixos = [-3, -2, -1, 0, 1, 2, 3]
    valor_to_color = {
        -3: "#8B0000",  # Vermell fosc
        -2: "#FF6347",  # Vermell clar
        -1: "#FFA500",  # Taronja
         0: "#FFD700",  # Groc
         1: "#87CEFA",  # Blau clar
         2: "#0000CD",  # Blau fosc
         3: "#4B0082",  # Violeta fosc
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

    separacio_index = len(pivot_A) + 1.5
    plt.hlines(y=separacio_index, xmin=0, xmax=pivot_heatmap.shape[1], colors='black', linewidth=8)

    plt.text(-0.2, (len(pivot_A)-1)/2, 'Modalitat A', va='center', ha='center', rotation=90, fontsize=18, fontweight='bold')
    plt.text(-0.2, len(pivot_A)+2+(len(pivot_B)-1)/2, 'Modalitat B', va='center', ha='center', rotation=90, fontsize=18, fontweight='bold')

    plt.suptitle('Adjudicacions Consecutives per ID\\nSeparat per Modalitat A i B', fontsize=26, fontweight='bold', y=.95)
    plt.xlabel('Any', fontsize=20, fontweight='bold')
    plt.ylabel('ID', fontsize=20, fontweight='bold')
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=12)
    plt.tight_layout(rect=[0, 0, 0.9, 0.95])

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

    # Inicialitzar bottom
    bottom_A = np.zeros(len(x))
    bottom_B = np.zeros(len(x))

    # Comprovem quins valors existeixen realment
    valors_reals = sorted(set(percent_A.columns).union(percent_B.columns))

    # Pintem valor per valor, any per any
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

    # Etiqueta Modalitat A/B
    for i in range(len(x)):
        ax.text(x[i] - bar_width/2 - separacio/2, 101, 'A', ha='center', fontsize=14, fontweight='bold')
        ax.text(x[i] + bar_width/2 + separacio/2, 101, 'B', ha='center', fontsize=14, fontweight='bold')

    ax.set_xlabel('Any', fontsize=18, fontweight='bold')
    ax.set_ylabel('Percentatge (%)', fontsize=18, fontweight='bold')
    ax.set_title('Comparació Modalitat A vs B\\nRepartició Percentual Adjudicacions Consecutives per Any', fontsize=24, fontweight='bold', pad=30)
    ax.set_xticks(x)
    ax.set_xticklabels(anys, fontsize=16)

    # Llegenda: només valors reals que han aparegut
    handles = [plt.Rectangle((0,0),1,1,color=valor_to_color[v]) for v in valors_fixos if v in valors_reals]
    labels = [str(v) for v in valors_fixos if v in valors_reals]
    ax.legend(handles, labels, title='Adjudicacions Consecutives', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14, title_fontsize=16)

    ax.set_ylim(-10, 110)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    plt.savefig(os.path.join(output_folder, "stacked_grouped_bar_percentatges_separat.png"), dpi=300)
    plt.close()
