# modules/report.py
import os
import pandas as pd

def generar_report_escenari(
    nom_escenari: str,
    captures_per_any,           # int or list[int]
    min_colla_size,              # int or list[int]
    new_hunters_per_year,        # int or (min,max)
    retired_hunters_per_year,    # int or (min,max)
    output_dir: str = 'reports',
    index_escenari: int = None   # <- Nou paràmetre opcional
) -> None:
    """
    Llegeix data/historial_6_anys.csv i genera un .md amb:
      - paràmetres d'escenari
      - taula evolutiva real (captures + colla vs individuals)
      - gràfics (heatmap + barres)
    """
    # 1) llegir historial complet
    hist_path = os.path.join('data', 'historial_6_anys.csv')
    df = pd.read_csv(hist_path)

    # 2) paràmetres text
    def fmt_range(v):
        if isinstance(v, tuple):
            a, b = v
            return str(a) if a == b else f"Entre {a} i {b}"
        return str(v)

    os.makedirs(output_dir, exist_ok=True)
    report_md = os.path.join(output_dir, f"{nom_escenari}.md")
    with open(report_md, 'w', encoding='utf-8') as f:
        # Títol
        titol = nom_escenari.replace('_',' ').title()
        if index_escenari is not None:
            f.write(f"# {index_escenari}. Escenari: {titol}\n\n")
        else:
            f.write(f"# Escenari: {titol}\n\n")

        # Paràmetres
        if isinstance(captures_per_any, list):
            mn, mx = min(captures_per_any), max(captures_per_any)
            caps_txt = str(mn) if mn == mx else f"Variable entre {mn} i {mx}"
        else:
            caps_txt = str(captures_per_any)
        f.write(f"**Captures/any:** {caps_txt}\n\n")
        f.write(f"**Colles mínim de:** {min_colla_size}\n\n")
        f.write(f"**Nous caçadors/any:** {fmt_range(new_hunters_per_year)}\n\n")
        f.write(f"**Retirats/any:** {fmt_range(retired_hunters_per_year)}\n\n")
        f.write("---\n\n")

        # 3) taula d'evolució real
        if index_escenari is not None:
            f.write(f"## {index_escenari}.1. Taula evolució per any\n\n")
        else:
            f.write("## 1.Taula evolució per any\n\n")

        f.write("| Any | Captures | Caçadors Totals | Colla | Individuals |\n")
        f.write("|:--:|:--------:|:---------------:|:-----:|:-----------:|\n")
        anys = sorted(df['any'].astype(int).unique())
        for anyo in anys:
            sub = df[df['any'] == anyo]
            captures = sub['adjudicats'].sum()
            tot = sub['ID'].nunique()
            colla = sub[sub['Modalitat'] == 'A']['ID'].nunique()
            indiv = sub[sub['Modalitat'] == 'B']['ID'].nunique()
            f.write(f"| {anyo} | {captures} | {tot} | {colla} | {indiv} |\n")

        # 4) gràfics
        if index_escenari is not None:
            f.write(f"\n## {index_escenari}.2. Heatmap de Captures Consecutives\n\n")
        else:
            f.write("\n## 2. Heatmap de Captures Consecutives\n\n")
        f.write(f"![Heatmap](../figures/{nom_escenari}/heatmap_captures_consecutives_final.png)\n\n")

        if index_escenari is not None:
            f.write(f"## {index_escenari}.3. Barres Apilades captures consecutives o anys consecutius sense captura\n\n")
        else:
            f.write("## 3.Barres Apilades captures consecutives o anys consecutius sense captura\n\n")
        f.write(f"![Barres](../figures/{nom_escenari}/stacked_grouped_bar_percentatges_separat.png)\n")

        if index_escenari is not None:
            f.write(f"## {index_escenari}.4. Barres Apilades captures consecutives o anys consecutius sense captura Colles petites ({min_colla_size} caçadors) vs Colles grans (11 o més caçadors)\n\n")
        else:
            f.write("## 4 .Barres Apilades captures consecutives o anys consecutius sense captura Colles petites ({min_colla_size} caçadors) vs Colles grans (11 o més caçadors)\n\n")
        f.write(f"![Barres](../figures/{nom_escenari}/stacked_grouped_bar_petites_vs_grans.png)\n")
    print(f"✅ Informe generat: {report_md}")

def combinar_markdowns(noms_escenaris, output_md='reports/final_report.md'):
    """Combina .mds en un sol Markdown amb índex i separadors visualitzats."""
    os.makedirs(os.path.dirname(output_md), exist_ok=True)

    with open(output_md, 'w', encoding='utf-8') as outfile:
        # Índex
        outfile.write("# Índex dels Escenaris Simulats\n\n")
        for i, nom in enumerate(noms_escenaris, 1):
            titol = nom.replace('_',' ').title()
            anchor = titol.lower().replace(' ', '-')
            outfile.write(f"{i}. [{titol}](#{anchor})\n")
        outfile.write("\n---\n\n")

        # Incloure cada informe
        for nom in noms_escenaris:
            path = os.path.join('reports', f"{nom}.md")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as infile:
                    lines = infile.readlines()
                # eliminar títols duplicats
                content = [ln for ln in lines]
                outfile.writelines(content)
                outfile.write("\n---\n\n")
            else:
                print(f"⚠️ No trobat: {path}")
    print(f"✅ Markdown combinat creat a {output_md}")
