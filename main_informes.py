# main_informes.py

from fpdf import FPDF
from PyPDF2 import PdfMerger
import os

class PDFInforme(FPDF):
    def header(self):
        # Títol dalt de cada pàgina
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, text):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, text)
        self.ln()

    def add_image(self, image_path, w=180):
        if os.path.exists(image_path):
            self.image(image_path, w=w)
            self.ln(10)

def generar_informe_escenari(nom_escenari, figures_folder):
    """
    Crea un informe PDF per a un escenari, amb títol i figures.
    """
    informe_path = f"reports/informe_{nom_escenari}.pdf"
    pdf = PDFInforme()
    pdf.set_title(f"Informe Escenari: {nom_escenari}")
    pdf.add_page()

    # Introducció
    pdf.chapter_title(f"Escenari: {nom_escenari}")
    pdf.chapter_body(f"Aquest informe recull els resultats de la simulació per l'escenari '{nom_escenari}'. Inclou heatmaps i gràfiques de captures consecutives.")

    # Afegir figures
    heatmap_path = os.path.join(figures_folder, "heatmap_captures_consecutives_final.png")
    bars_path = os.path.join(figures_folder, "stacked_grouped_bar_percentatges_separat.png")

    pdf.chapter_title("Heatmap Captures Consecutives")
    pdf.add_image(heatmap_path)

    pdf.chapter_title("Comparativa Modalitat A vs B")
    pdf.add_image(bars_path)

    # Crear carpeta de reports si no existeix
    os.makedirs('reports', exist_ok=True)
    pdf.output(informe_path)
    print(f"✅ Informe {nom_escenari} generat a {informe_path}")

def combinar_informes(noms_escenaris):
    """
    Combina múltiples informes PDF en un sol PDF final.
    """
    merger = PdfMerger()
    for nom in noms_escenaris:
        informe_path = f"reports/informe_{nom}.pdf"
        if os.path.exists(informe_path):
            merger.append(informe_path)
        else:
            print(f"⚠️ No s'ha trobat {informe_path}, saltant...")

    final_path = "reports/informe_complet.pdf"
    merger.write(final_path)
    merger.close()
    print(f"🎯 Informe complet creat: {final_path}")
