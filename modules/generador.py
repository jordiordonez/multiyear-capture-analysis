import pandas as pd
import numpy as np
import random
import os

def generate_colla_sizes(total, min_size=8, max_size=20):
    """Genera una llista de mides de colla que sumen exactament 'total'."""
    while True:
        sizes = []
        rem = total
        while rem > max_size:
            size = random.randint(min_size, max_size)
            sizes.append(size)
            rem -= size
        if min_size <= rem <= max_size:
            sizes.append(rem)
            return sizes

def generar_dades_inicials(
    total_cacadors_colla: int,
    total_individuals: int,
    min_colla_size: int = 8,
    max_colla_size: int = 20,
    output_path: str = 'data/sorteig.csv'  # ✨ Nou paràmetre flexible
):
    """Genera un CSV amb estructura de caçadors modalitat A i B."""
    # Generar colles
    sizes = generate_colla_sizes(total_cacadors_colla, min_size=min_colla_size, max_size=max_colla_size)
    data = []
    pid = 1

    # Assignar participants Modalitat A (colla)
    for i, size in enumerate(sizes, start=1):
        for _ in range(size):
            data.append({
                'ID': pid,
                'Modalitat': 'A',
                'Prioritat': 3,
                'Colla_ID': f'Colla_{i}',
                'anys_sense_captura': 0
            })
            pid += 1

    # Assignar participants Modalitat B (individual)
    for _ in range(total_individuals):
        data.append({
            'ID': pid,
            'Modalitat': 'B',
            'Prioritat': 3,
            'Colla_ID': np.nan,
            'anys_sense_captura': 0
        })
        pid += 1

    df = pd.DataFrame(data)

    # Assegurar que existeix la carpeta del path
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Només crear si existeix un directori!
        os.makedirs(output_dir, exist_ok=True)

    # Guardar CSV
    df.to_csv(output_path, index=False, sep=';')
    print(f"✅ Dades inicials generades i desades a {output_path}")

    return df
