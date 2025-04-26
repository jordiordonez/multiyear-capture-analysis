import os

def combinar_reports(directori_reports: str, output_path: str = 'reports/report_final.md'):
    """
    Combina tots els fitxers .md d'un directori en un únic report final.
    """
    files = sorted([
        f for f in os.listdir(directori_reports)
        if f.endswith('.md') and f != os.path.basename(output_path)
    ])

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for fname in files:
            filepath = os.path.join(directori_reports, fname)
            with open(filepath, 'r', encoding='utf-8') as infile:
                outfile.write(f"# 📄 {fname.replace('.md', '').replace('_', ' ').title()}\n\n")
                outfile.write(infile.read())
                outfile.write("\n\n---\n\n")  # separador entre escenaris

    print(f"✅ Report final generat a {output_path}")

if __name__ == '__main__':
    combinar_reports('reports')
