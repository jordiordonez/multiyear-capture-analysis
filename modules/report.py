# modules/report.py

import os
import subprocess
import pandoc

def generar_report_escenari(
    nom_escenari: str,
    num_anys: int,
    total_inicial: int,
    num_colla: int,
    num_indiv: int,
    captures_per_any: int or list,
    new_hunters_per_year: int or tuple,
    retired_hunters_per_year: int or tuple,
    evolucio_anys: list,  # [(captures_any, cacadors_any), ...]
    output_dir: str = 'reports'
):
    """
    Genera un informe resum d'un escenari en format Markdown (.md).
    """

    # Assegurar carpeta reports
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, f"{nom_escenari}.md")

    with open(report_path, 'w', encoding='utf-8') as f:
        # Títol i descripció inicial
        f.write(f"# 📄 Informe de l'Escenari: {nom_escenari.replace('_', ' ').title()}\n\n")
        f.write(f"**Anys simulats:** {num_anys}\n\n")
        f.write(f"**Total inicial de caçadors:** {total_inicial} (Colla: {num_colla}, Individuals: {num_indiv})\n\n")
        
        # 📈 Captures adjudicables
        if isinstance(captures_per_any, list):
            min_cap = min(captures_per_any)
            max_cap = max(captures_per_any)
            if min_cap == max_cap:
                f.write(f"**Captures adjudicables per any:** {min_cap}\n\n")
            else:
                f.write(f"**Captures adjudicables per any:** Variable entre {min_cap} i {max_cap}\n\n")
        else:
            f.write(f"**Captures adjudicables per any:** {captures_per_any}\n\n")


       # 🆕 Nous caçadors per any
        if isinstance(new_hunters_per_year, tuple):
            min_new = min(new_hunters_per_year)
            max_new = max(new_hunters_per_year)
            if min_new == max_new:
                f.write(f"**Nous caçadors/any:** {min_new}\n\n")
            else:
                f.write(f"**Nous caçadors/any:** Entre {min_new} i {max_new}\n\n")
        else:
            f.write(f"**Nous caçadors/any:** {new_hunters_per_year}\n\n")

        # 🔻 Caçadors que pleguen per any
        if isinstance(retired_hunters_per_year, tuple):
            min_ret = min(retired_hunters_per_year)
            max_ret = max(retired_hunters_per_year)
            if min_ret == max_ret:
                f.write(f"**Caçadors que pleguen/any:** {min_ret}\n\n")
            else:
                f.write(f"**Caçadors que pleguen/any:** Entre {min_ret} i {max_ret}\n\n")
        else:
            f.write(f"**Caçadors que pleguen/any:** {retired_hunters_per_year}\n\n")


        f.write("\n---\n\n")

        # Nova secció: taula de l'evolució
        f.write("\n## 📈 Evolució per Any\n\n")
        f.write("| Any | Captures Adjudicades | Caçadors Totals | Caçadors Colla | Caçadors Individuals |\n")
        f.write("|:---:|:--------------------:|:---------------:|:--------------:|:---------------------:|\n")

        for any_info in evolucio_anys:
            anyo = any_info['any']
            captures = any_info['captures_adjudicades']
            cacadors_total = any_info['cacadors_total']
            cacadors_colla = any_info['cacadors_colla']
            cacadors_individual = any_info['cacadors_individual']

            f.write(f"| {anyo} | {captures} | {cacadors_total} | {cacadors_colla} | {cacadors_individual} |\n")


        # Gràfics
        f.write("## 📊 Heatmap de Captures Consecutives\n\n")
        f.write(f"![Heatmap](../figures/{nom_escenari}/heatmap_captures_consecutives_final.png)\n\n")

        f.write("## 📊 Barres Apilades Comparatives\n\n")
        f.write(f"![Barres Apilades](../figures/{nom_escenari}/stacked_grouped_bar_percentatges_separat.png)\n\n")

    print(f"✅ Report de l'escenari '{nom_escenari}' generat a {report_path}")



def combinar_markdowns(noms_escenaris, output_md='reports/final_report.md'):
    """Combina .mds en un final markdown amb índex i separadors estètics."""
    os.makedirs(os.path.dirname(output_md), exist_ok=True)

    with open(output_md, 'w', encoding='utf-8') as outfile:
        # ✅ Índex
        outfile.write("# 📑 Índex dels Escenaris\n\n")
        for idx, nom in enumerate(noms_escenaris, 1):
            titol = nom.replace('_', ' ').title()
            anchor = titol.lower().replace(' ', '-')
            outfile.write(f"{idx}. [{titol}](#{anchor})\n")
        outfile.write("\n---\n\n")

        # ✅ Escenaris
        for nom in noms_escenaris:
            file_path = os.path.join('reports', f"{nom}.md")
            if os.path.exists(file_path):
                titol = nom.replace('_', ' ').title()
                outfile.write(f"# 🏹 {titol}\n\n")
                with open(file_path, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    # Evitem repetir títols dins el contingut
                    content = '\n'.join(line for line in content.splitlines() if not line.startswith('# '))
                    outfile.write(content)
                outfile.write('\n\n---\n\n')  # Separador visual
            else:
                print(f"⚠️ {file_path} no trobat, saltant...")
    print(f"✅ Markdown combinat creat a {output_md}")
