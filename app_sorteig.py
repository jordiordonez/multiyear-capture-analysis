import streamlit as st
import pandas as pd
import numpy as np
import math

# Funció per al sorteig amb colles (lògica existent)
def assignar_isards_sorteig_csv(df: pd.DataFrame, total_captures: int, seed: int = None) -> pd.DataFrame:
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    required = {'ID', 'Modalitat', 'Prioritat', 'Colla_ID', 'anys_sense_captura'}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")
    df = df.copy()
    df['adjudicats'] = 0
    df_colla = df[df['Modalitat'] == 'A']
    df_indiv = df[df['Modalitat'] == 'B']
    total_applicants = len(df_colla) + len(df_indiv)
    ratio = math.ceil(total_applicants / total_captures)
    n_indiv = round(total_captures * len(df_indiv) / total_applicants)
    n_colla = total_captures - n_indiv
    # Assign dins colles
    colles = df_colla.groupby('Colla_ID').size().reset_index(name='caçadors')
    colles['assignats'] = (colles['caçadors'] // ratio).astype(int)
    leftover = n_colla - colles['assignats'].sum()
    for _ in range(leftover):
        colles['rati'] = colles['assignats'] / colles['caçadors']
        min_rati = colles['rati'].min()
        cand = colles[np.isclose(colles['rati'], min_rati, atol=1e-6)]
        sel = cand.sample(1, random_state=rng)
        cid = sel['Colla_ID'].iloc[0]
        colles.loc[colles['Colla_ID'] == cid, 'assignats'] += 1
    for _, row in colles.iterrows():
        cid, to_assign = row['Colla_ID'], int(row['assignats'])
        while to_assign > 0:
            sub = df[(df['Modalitat'] == 'A') & (df['Colla_ID'] == cid)]
            min_adj = sub['adjudicats'].min()
            group = sub[sub['adjudicats'] == min_adj].copy()
            group['rand'] = rng.random(len(group))
            sorted_g = group.sort_values(
                by=['Prioritat', 'anys_sense_captura', 'rand'],
                ascending=[True, False, True]
            )
            take = min(to_assign, len(sorted_g))
            idxs = sorted_g.index[:take]
            df.loc[idxs, 'adjudicats'] += 1
            to_assign -= take
    # Assign individus B
    rem = n_indiv
    while rem > 0:
        sub = df[df['Modalitat'] == 'B']
        min_adj = sub['adjudicats'].min()
        group = sub[sub['adjudicats'] == min_adj].copy()
        group['rand'] = rng.random(len(group))
        sorted_g = group.sort_values(
            by=['Prioritat', 'anys_sense_captura', 'rand'],
            ascending=[True, False, True]
        )
        take = min(rem, len(sorted_g))
        idxs = sorted_g.index[:take]
        df.loc[idxs, 'adjudicats'] += 1
        rem -= take
    df['nova_prioritat'] = df['adjudicats'].apply(lambda x: 4 if x > 1 else 2)
    df['nou_anys_sense_captura'] = df.apply(
        lambda r: 0 if r['adjudicats'] == 1 else r['anys_sense_captura'] + 1,
        axis=1
    )
    return df

# Funció per al sorteig individual (sense colles)
def assignar_captura_csv(df: pd.DataFrame, tipus_captures: list, quantitats: dict, seed: int = None) -> pd.DataFrame:
    required = {'ID', 'Prioritat', 'anys_sense_captura', 'Resultat_sorteigs_mateixa_sps'}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")
    df = df.copy()
    if 'Adjudicats' not in df.columns:
        df['Adjudicats'] = 0
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    # Creem columnes individuals per cada Tipus\    
    for i, tipus in enumerate(tipus_captures, start=1):
        safe = tipus.replace('+','_')
        col_name = f'Adjudicats_Tipus{i}_{safe}'
        df[col_name] = 0
    # Assignació per tipus en ordre
    for i, tipus in enumerate(tipus_captures, start=1):
        target = quantitats.get(tipus, 0)
        assigned = 0
        safe = tipus.replace('+','_')
        col_name = f'Adjudicats_Tipus{i}_{safe}'
        while assigned < target:
            df['Adjudicats_acumulats'] = df['Adjudicats'] + df['Resultat_sorteigs_mateixa_sps']
            min_acc = df['Adjudicats_acumulats'].min()
            candidates = df[df['Adjudicats_acumulats'] == min_acc].copy()
            candidates['rand'] = rng.random(size=len(candidates))
            if min_acc == 0:
                ordered = candidates.sort_values(by=['Prioritat','rand'],ascending=[True,True])
            else:
                ordered = candidates.sort_values(by=['rand'])
            idx = ordered.index[0]
            df.at[idx, 'Adjudicats'] += 1
            df.at[idx, col_name] += 1
            assigned += 1
    df['Nou_Resultat_sorteigs_mateixa_sps'] = df['Resultat_sorteigs_mateixa_sps'] + df['Adjudicats']
    # Calcular nova prioritat i anys sense captura
    df['nova_prioritat'] = df['Adjudicats'].apply(lambda x: 4 if x > 1 else 2)
    df['nou_anys_sense_captura'] = df.apply(
        lambda r: 0 if r['Adjudicats'] == 1 else r['anys_sense_captura'] + 1,
        axis=1
    )
    if 'Adjudicats_acumulats' in df.columns:
        df.drop(columns=['Adjudicats_acumulats'], inplace=True)
    return df

# Streamlit UI
st.title("App Sorteig Pla de Caça")
# Instruccions d'ús en català
st.markdown("""
    ## Instruccions d'ús:

    1. Seleccioneu l'espècie i la unitat de gestió.
    2. Pugeu el fitxer CSV de sol·licitants.
    3. Si no és Isard + TCC, afegiu un o més Tipus de captura en l'ordre que es sortejaran :
        - Clic a "Afegeix Tipus", 
        - seleccioneu un o diversos valors 
        - indiqueu el nombre de captures.
    4. Opcional: introduïu una llavor per a reproduir el mateix sorteig.
    5. Feu clic a "Executar sorteig" per veure els resultats i descarregar el CSV.
    """)

# 1. Selecció inicial
especie = st.selectbox("Espècie:", ['Isard', 'Cabirol', 'Mufló'])
unidad = st.selectbox(
    "Unitat de gestió:",
    ['VC Enclar', 'VC Xixerella', 'VCR Ansó-Sorteny', 'VCR Ansó', 'VC Sorteny', 'VT Escaldes-Engordany', 'TCC']
)

# 3. Carrega CSV i vista prèvia
df = None
file = st.file_uploader("CSV sol·licitants", type='csv')
if file:
    df = pd.read_csv(file, sep=';')
    st.subheader("Previsualització de sol·licitants")
    st.dataframe(df)

# 4. Configuració de Tipus de captura dinàmica
options = ['Femella', 'Mascle', 'Adult', 'Juvenil', 'Trofeu', 'Selectiu', 'Indeterminat']
# Si Isard+TTC, demanar total captures
tipus_captures = []
quantitats = {}
if especie == 'Isard' and unidad == 'TCC':
    total_cap = st.number_input("Quantitat Captures:", min_value=1, step=1)
else:
    if 'configs' not in st.session_state:
        st.session_state['configs'] = [{'selections': [], 'qty': 1}]
    if st.button("Afegeix Tipus"):
        st.session_state['configs'].append({'selections': [], 'qty': 1})
    for idx, conf in enumerate(st.session_state['configs']):
        st.subheader(f"Tipus {idx+1}")
        sel = st.multiselect(
            f"Seleccioni un o diversos valors per Tipus {idx+1}:",
            options,
            key=f"sel_{idx}"
        )
        if 'Indeterminat' in sel:
            sel = ['Indeterminat']
        qty = st.number_input(
            f"Nº captures per Tipus {idx+1}:",
            min_value=1,
            step=1,
            key=f"qty_{idx}"
        )
        st.session_state['configs'][idx]['selections'] = sel
        st.session_state['configs'][idx]['qty'] = qty
        # Preparar llistes\        
        val = sel[0] if len(sel)==1 else '+'.join(sel)
        tipus_captures.append(val)
        quantitats[val] = qty

# 2. Semilla opcional
seed = st.number_input("Llavor opcional (Nombre enter):", min_value=0, step=1, format="%d")
seed = None if seed == 0 else seed

# 5. Executar sorteig
if st.button("Executar sorteig"):
    if df is None:
        st.warning("Cal pujar un CSV abans d'executar el sorteig.")
    else:
        tipus_captures = []
        quantitats = {}
        if especie == 'Isard' and unidad == 'TCC':
            if total_cap is None:
                st.warning("Cal especificar el nombre de captures.")
                st.stop()
            try:
                result = assignar_isards_sorteig_csv(df, total_cap, seed)
            except ValueError as e:
                st.error(str(e))
                st.stop()
        else:
            for conf in st.session_state.get('configs', []):
                sel = conf['selections']
                val = sel[0] if len(sel) == 1 else '+'.join(sel)
                tipus_captures.append(val)
                quantitats[val] = conf['qty']
            try:
                result = assignar_captura_csv(df, tipus_captures, quantitats, seed)
            except ValueError as e:
                st.error(str(e))
                st.stop()
            st.info("L'any següent, prioritat 1 als qui hagin abatut femella.")
        st.subheader("Resultats del sorteig")
        st.dataframe(result)
        st.download_button(
            'Descarregar CSV',
            result.to_csv(index=False),
            file_name=f"sorteig_{especie}_{unidad}.csv"
        )
else:
    if df is None:
        st.info("Puja un CSV per iniciar el sorteig.")
    else:
        if not (especie == 'Isard' and unidad == 'TCC'):
            if st.session_state.get('configs') is None:
                st.info("Configura els Tipus i quantitats abans d'executar.")
