import pandas as pd
import numpy as np
import random
import os
import math

def generate_colla_sizes(total, min_size=8, max_size=20):
    """Genera una llista de mides de colla que sumen exactament 'total',
    assegurant que almenys el 30% de les colles són de mida mínima."""
    
    sizes = []

    # 1) Primer pas: assegurar 30% de colles amb mida mínima
    estimated_total_collas = math.ceil(total / ((min_size + max_size) / 2))  # estimació més real
    min_collas = math.ceil(estimated_total_collas * 0.3)
    min_total = min_collas * min_size

    if min_total > total:
        min_collas = total // min_size
        min_total = min_collas * min_size

    sizes.extend([min_size] * min_collas)
    rem = total - min_total

    # 2) Segon pas: completar aleatòriament la resta
    while rem >= min_size:
        max_possible = min(max_size, rem)
        size = random.randint(min_size, max_possible)
        sizes.append(size)
        rem -= size

    # 3) Tercer pas: si queda rem < min_size, repartir-lo entre colles existents
    if rem > 0:
        # Ordenem de més petit a més gran perquè no passem max_size
        sizes.sort(reverse=True)
        for i in range(len(sizes)):
            if sizes[i] + 1 <= max_size:
                sizes[i] += 1
                rem -= 1
                if rem == 0:
                    break
        if rem > 0:
            raise ValueError("No s'ha pogut repartir el remanent sense superar el max_size.")

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
    print(sizes)

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
