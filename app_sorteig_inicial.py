import streamlit as st
import pandas as pd
import tempfile
import numpy as np
import math

def assignar_isards_sorteig_csv(
    file_csv: str,
    total_captures: int,
    output_csv: str = "resultats.csv",
    seed: [int] = None
) -> pd.DataFrame:
    rng = np.random.RandomState(seed) if seed is not None else np.random
    df = pd.read_csv(file_csv, sep=';')

    required_cols = {'ID', 'Modalitat', 'Prioritat', 'Colla_ID', 'anys_sense_captura'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Falten columnes obligatòries: {required_cols - set(df.columns)}")

    df['adjudicats'] = 0
    df_colla = df[df['Modalitat'] == 'A'].copy()
    df_indiv = df[df['Modalitat'] == 'B'].copy()
    n_colla_applicants = len(df_colla)
    n_indiv_applicants = len(df_indiv)

    total_applicants = n_colla_applicants + n_indiv_applicants
    ratio = math.ceil(total_applicants / total_captures)

    # --- Proportional distribution of captures
    n_indiv = round(total_captures * n_indiv_applicants / total_applicants)
    n_colla = total_captures - n_indiv

    # --- Distribution per colla utilitzant Webster
    colles_df = df_colla.groupby('Colla_ID').size().reset_index(name='caçadors')

    def webster_allocate(counts, k, max_iter=1000):
        counts = np.array(counts, dtype=float)
        low, high = 0.0, max(counts)
        for _ in range(max_iter):
            d = (low + high) / 2 if high > low else high
            if d == 0:
                d = 1e-6
            alloc = np.round(counts / d).astype(int)
            s = int(alloc.sum())
            if s == k or abs(high - low) < 1e-6:
                return alloc.tolist()
            if s > k:
                low = d
            else:
                high = d
        return np.round(counts / d).astype(int).tolist()

    colles_df['assignats'] = webster_allocate(colles_df['caçadors'], n_colla)

    # --- Assign inside colles
    for _, row in colles_df.iterrows():
        cid = row['Colla_ID']
        n_assign = int(row['assignats'])

        while n_assign > 0:
            # Troba el mínim d’adjudicacions dins la colla
            adjudicacions_actuals = df[
                (df['Modalitat'] == 'A') & (df['Colla_ID'] == cid)
            ]['adjudicats']
            min_adjud = adjudicacions_actuals.min()

            # Grup amb menys adjudicacions
            group = df[
                (df['Modalitat'] == 'A') &
                (df['Colla_ID'] == cid) &
                (df['adjudicats'] == min_adjud)
            ].copy()

            if group.empty:
                break

            group['rand'] = rng.random(size=len(group))
            sorted_group = group.sort_values(
                by=['Prioritat', 'anys_sense_captura', 'rand'],
                ascending=[True, False, True]
            )

            n_to_assign = min(n_assign, len(sorted_group))
            assign_indices = sorted_group.index[:n_to_assign]
            df.loc[assign_indices, 'adjudicats'] += 1
            n_assign -= n_to_assign


    # --- Assign in modality B (individual)
    if n_indiv > 0:
        remaining_indiv = n_indiv

        while remaining_indiv > 0:
            # Troba el mínim d’adjudicacions actuals entre els individuals
            min_adjud = df[df['Modalitat'] == 'B']['adjudicats'].min()

            group = df[
                (df['Modalitat'] == 'B') &
                (df['adjudicats'] == min_adjud)
            ].copy()

            if group.empty:
                break

            group['rand'] = rng.random(size=len(group))
            sorted_group = group.sort_values(
                by=['Prioritat', 'anys_sense_captura', 'rand'],
                ascending=[True, False, True]
            )

            n_to_assign = min(remaining_indiv, len(sorted_group))
            assign_indices = sorted_group.index[:n_to_assign]
            df.loc[assign_indices, 'adjudicats'] += 1
            remaining_indiv -= n_to_assign


    # --- Compute new priority and history
    df['nova_prioritat'] = df['adjudicats'].apply(lambda x: 4 if x == 1 else 2)
    df['nou_anys_sense_captura'] = df.apply(
        lambda row: 0 if row['adjudicats'] == 1 else row['anys_sense_captura'] + 1,
        axis=1
    )

    df.drop(columns=['rand'], errors='ignore').to_csv(output_csv, index=False)
    return df

st.set_page_config(page_title="App Sorteig Captures Isard", page_icon="🦌", layout="centered")

st.title("Sorteig de Captures d'Isard")

# 1. Pujar fitxer
uploaded_file = st.file_uploader("Carrega el fitxer CSV d'inscrits:", type=["csv"])

if uploaded_file is not None:
    df_inscrits = pd.read_csv(uploaded_file, sep=';')
    st.success("✅ Fitxer carregat correctament.")
    st.dataframe(df_inscrits.head())

    # 2. Número de captures
    total_captures = st.number_input("Nombre total de captures disponibles:", min_value=1, step=1)

    # 3. Llavor opcional
    seed = st.number_input("Llavor aleatòria (opcional):", value=None, step=1, format="%i")

    if st.button("🎯 Executar Sorteig"):
        # Guardar fitxer temporalment
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_input:
            df_inscrits.to_csv(tmp_input.name, sep=';', index=False)
            output_df = assignar_isards_sorteig_csv(tmp_input.name, int(total_captures), seed=int(seed) if seed else None)

        st.success("✅ Sorteig realitzat!")
        st.dataframe(output_df.head())

        # Baixar resultat
        csv = output_df.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="💾 Descarrega el fitxer de resultats",
            data=csv,
            file_name='resultats_sorteig.csv',
            mime='text/csv'
        )
