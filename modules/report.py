import os

def generar_report_escenari(
    nom_escenari: str,
    num_anys: int,
    total_inicial: int,
    num_colla: int,
    num_indiv: int,
    captures_per_any: int,
    new_hunters_per_year: int,
    retired_hunters_per_year: int,
    output_dir: str = 'reports'
):
    """
    Genera un informe resum d'un escenari en format Markdown.
    """

    report_path = os.path.join(output_dir, f"{nom_escenari}.md")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 📄 Informe de l'Escenari: {nom_escenari.replace('_', ' ').title()}\n\n")
        f.write(f"**Anys simulats:** {num_anys}\n\n")
        f.write(f"**Total inicial de caçadors:** {total_inicial} (Colla: {num_colla}, Individuals: {num_indiv})\n\n")
        f.write(f"**Captures adjudicables per any:** {captures_per_any}\n\n")
        f.write(f"**Nous caçadors/any:** {new_hunters_per_year}\n\n")
        f.write(f"**Caçadors que pleguen/any:** {retired_hunters_per_year}\n\n")

        f.write("\n---\n\n")

        f.write("## 📊 Heatmap de Captures Consecutives\n\n")
        f.write(f"![Heatmap](../figures/{nom_escenari}/heatmap_captures_consecutives_final.png)\n\n")

        f.write("## 📊 Barres Apilades Comparatives\n\n")
        f.write(f"![Barres Apilades](../figures/{nom_escenari}/stacked_grouped_bar_percentatges_separat.png)\n\n")

    print(f"✅ Report de l'escenari '{nom_escenari}' generat a {report_path}")
