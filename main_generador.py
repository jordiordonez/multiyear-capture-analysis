from modules.generador import generar_dades_inicials

if __name__ == '__main__':
    generar_dades_inicials(
        total_cacadors_colla=175,
        total_individuals=190,
        min_colla_size=8,
        max_colla_size=20,
        output_path='data/sorteig.csv'  # <--- ara passa la ruta
    )
