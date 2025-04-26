import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.colorbar import ColorbarBase

def generar_heatmaps_i_grafics(file_path='data/historial_6_anys.csv', output_folder='figures'):

    # Crear la carpeta de figures si no existeix
    os.makedirs(output_folder, exist_ok=True)

    # Carregar el fitxer
    data = pd.read_csv(file_path)

    # Inicialitzar nova columna
    data['captures_consecutives'] = 0

    # Ordenar per ID i any
    data = data.sort_values(by=['ID', 'any'])

    # Definició captures consecutives
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

    # Crear pivot taules Modalitat A i B
    pivot_A = data[data['Modalitat'] == 'A'].pivot(index='ID', columns='any', values='captures_consecutives').fillna(0)
    pivot_B = data[data['Modalitat'] == 'B'].pivot(index='ID', columns='any', values='captures_consecutives').fillna(0)

    # Afegir files buides per separació
    empty_row = pd.DataFrame(np.nan, index=['', '', ''], columns=pivot_A.columns)
    pivot_heatmap = pd.concat([pivot_A, empty_row, pivot_B])

    # Crear Heatmap
    valors_discrets = sorted(data['captures_consecutives'].unique())
    valor_to_idx = {v: i for i, v in enumerate(valors_discrets)}
    indexed_matrix = pivot_heatmap.replace(valor_to_idx)

    colors = sns.color_palette("RdYlGn_r", n_colors=len(valors_discrets))
    cmap = ListedColormap(colors)

    plt.figure(figsize=(22, 16))
    ax = sns.heatmap(indexed_matrix, cmap=cmap, linewidths=0.5, linecolor='gray', cbar=False)

    separacio_index = len(pivot_A) + 1.5
    plt.hlines(y=separacio_index, xmin=0, xmax=pivot_heatmap.shape[1], colors='black', linewidth=8)

    plt.text(-0.2, (len(pivot_A)-1)/2, 'Modalitat A', va='center', ha='center', rotation=90, fontsize=18, fontweight='bold')
    plt.text(-0.2, len(pivot_A)+2+(len(pivot_B)-1)/2, 'Modalitat B', va='center', ha='center', rotation=90, fontsize=18, fontweight='bold')

    plt.suptitle('Adjudicacions Consecutives per ID\nSeparat per Modalitat A i B', fontsize=26, fontweight='bold', y=.95)
    plt.xlabel('Any', fontsize=20, fontweight='bold')
    plt.ylabel('ID', fontsize=20, fontweight='bold')
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=12)
    plt.tight_layout(rect=[0, 0, 0.9, 0.95])

    cbar_ax = plt.gcf().add_axes([0.93, 0.25, 0.02, 0.5])
    norm = BoundaryNorm(boundaries=[v - 0.5 for v in range(min(valors_discrets), max(valors_discrets) + 2)], ncolors=len(valors_discrets))
    cb = ColorbarBase(cbar_ax, cmap=cmap, norm=norm, ticks=valors_discrets)
    cb.ax.set_yticklabels(valors_discrets, fontsize=18)
    cb.set_label('Adjudicacions Consecutives', fontsize=18, fontweight='bold')

    plt.savefig(os.path.join(output_folder, "heatmap_captures_consecutives_final.png"), dpi=300)

    plt.close()

    # Crear stacked grouped bar chart
    data_A = data[data['Modalitat'] == 'A']
    data_B = data[data['Modalitat'] == 'B']

    def crear_taules_modalitat(data_modalitat):
        counts_table = data_modalitat.groupby(['any', 'captures_consecutives']).size().unstack(fill_value=0)
        percent_table = counts_table.div(counts_table.sum(axis=1), axis=0) * 100
        return counts_table, percent_table

    counts_A, percent_A = crear_taules_modalitat(data_A)
    counts_B, percent_B = crear_taules_modalitat(data_B)

    anys = percent_A.index
    valors = sorted(set(percent_A.columns).union(percent_B.columns))
    x = np.arange(len(anys))
    bar_width = 0.35
    separacio = 0.15

    fig, ax = plt.subplots(figsize=(20, 10))
    colors = sns.color_palette("tab20", n_colors=len(valors))

    bottom_A = np.zeros(len(x))
    bottom_B = np.zeros(len(x))

    for idx, v in enumerate(valors):
        data_A_pct = percent_A.get(v, pd.Series(0, index=anys))
        data_B_pct = percent_B.get(v, pd.Series(0, index=anys))
        data_A_count = counts_A.get(v, pd.Series(0, index=anys))
        data_B_count = counts_B.get(v, pd.Series(0, index=anys))

        bars_A = ax.bar(x - bar_width/2 - separacio/2, data_A_pct, bottom=bottom_A, width=bar_width, color=colors[idx])
        bars_B = ax.bar(x + bar_width/2 + separacio/2, data_B_pct, bottom=bottom_B, width=bar_width, color=colors[idx])

        for i, bar in enumerate(bars_A):
            height = bar.get_height()
            if height > 5:
                ax.text(bar.get_x() + bar.get_width()/2, bottom_A[i] + height/2, f"{round(height)}%\n({int(data_A_count.iloc[i])})", ha='center', va='center', fontsize=10)
        for i, bar in enumerate(bars_B):
            height = bar.get_height()
            if height > 5:
                ax.text(bar.get_x() + bar.get_width()/2, bottom_B[i] + height/2, f"{round(height)}%\n({int(data_B_count.iloc[i])})", ha='center', va='center', fontsize=10)

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

    handles = [plt.Rectangle((0,0),1,1,color=colors[i]) for i in range(len(valors))]
    labels = [str(v) for v in valors]
    ax.legend(handles, labels, title='Adjudicacions Consecutives', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14, title_fontsize=16)

    ax.set_ylim(-10, 100)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    plt.savefig(os.path.join(output_folder, "stacked_grouped_bar_percentatges_separat.png"), dpi=300)

    plt.close()
