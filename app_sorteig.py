import streamlit as st
import pandas as pd
import numpy as np
import math

# Funció per al sorteig amb colles (lògica existent)
def assignar_isards_sorteig_csv(
    df: pd.DataFrame,
    total_captures: int,
    seed: int = None
) -> pd.DataFrame:
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    required = {'ID','Modalitat','Prioritat','Colla_ID','anys_sense_captura'}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")

    df = df.copy()
    df['adjudicats'] = 0
    df_colla = df[df['Modalitat']=='A']
    df_indiv = df[df['Modalitat']=='B']
    total_applicants = len(df_colla) + len(df_indiv)
    ratio = math.ceil(total_applicants / total_captures)

    # Distribució proporcional
    n_indiv = round(total_captures * len(df_indiv) / total_applicants)
    n_colla = total_captures - n_indiv

    # Distribució i assign dins colles
    colles = df_colla.groupby('Colla_ID').size().reset_index(name='caçadors')
    colles['assignats'] = (colles['caçadors'] // ratio).astype(int)
    leftover = n_colla - colles['assignats'].sum()
    for _ in range(leftover):
        colles['rati'] = colles['assignats'] / colles['caçadors']
        min_rati = colles['rati'].min()
        cand = colles[np.isclose(colles['rati'], min_rati, atol=1e-6)]
        sel = cand.sample(1, random_state=rng)
        cid = sel['Colla_ID'].iloc[0]
        colles.loc[colles['Colla_ID']==cid,'assignats'] += 1

    for _,row in colles.iterrows():
        cid, to_assign = row['Colla_ID'], int(row['assignats'])
        while to_assign>0:
            sub = df[(df['Modalitat']=='A') & (df['Colla_ID']==cid)]
            min_adj = sub['adjudicats'].min()
            group = sub[sub['adjudicats']==min_adj].copy()
            group['rand'] = rng.random(len(group))
            sorted_g = group.sort_values(
                by=['Prioritat','anys_sense_captura','rand'],
                ascending=[True,False,True]
            )
            take = min(to_assign, len(sorted_g))
            idxs = sorted_g.index[:take]
            df.loc[idxs,'adjudicats'] += 1
            to_assign -= take

    # Assign individus B
    rem = n_indiv
    while rem>0:
        sub = df[df['Modalitat']=='B']
        min_adj = sub['adjudicats'].min()
        group = sub[sub['adjudicats']==min_adj].copy()
        group['rand'] = rng.random(len(group))
        sorted_g = group.sort_values(
            by=['Prioritat','anys_sense_captura','rand'],
            ascending=[True,False,True]
        )
        take = min(rem, len(sorted_g))
        idxs = sorted_g.index[:take]
        df.loc[idxs,'adjudicats'] += 1
        rem -= take

    df['nova_prioritat'] = df['adjudicats'].apply(lambda x: 4 if x==1 else 2)
    df['nou_anys_sense_captura'] = df.apply(
        lambda r: 0 if r['adjudicats']==1 else r['anys_sense_captura']+1,
        axis=1
    )
    return df

# Funció per al sorteig individual (sense colles)
def assignar_captura_csv(
    df: pd.DataFrame,
    tipus_captures: list,
    quantitats: dict,
    seed: int = None
) -> pd.DataFrame:
    req = {'ID','Modalitat','Prioritat','Colla_ID','anys_sense_captura','Resultat_sorteigs_mateixa_sps'}
    if not req.issubset(df.columns):
        missing = req - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")
    df = df.copy()
    if 'Adjudicats' not in df.columns:
        df['Adjudicats'] = 0
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()

    # Assignació per tipus
    for tipus in tipus_captures:
        target = quantitats.get(tipus, 0)
        assigned = 0
        while assigned < target:
            df['Adjudicats_acumulats'] = df['Adjudicats'] + df['Resultat_sorteigs_mateixa_sps']
            min_acc = df['Adjudicats_acumulats'].min()
            cand = df[df['Adjudicats_acumulats']==min_acc].copy()
            cand['rand'] = rng.random(len(cand))
            if min_acc == 0:
                ordered = cand.sort_values(by=['Prioritat','rand'], ascending=[True,True])
            else:
                ordered = cand.sort_values(by=['rand'])
            idx = ordered.index[0]
            df.at[idx,'Adjudicats'] += 1
            assigned += 1

    df['Nou_Resultat_sorteigs_mateixa_sps'] = (
        df['Resultat_sorteigs_mateixa_sps'] + df['Adjudicats']
    )
    return df

# Streamlit UI
st.title("App Sorteig Pla de Caça")

# 1. Selecció inicial
especie = st.selectbox("Espècie:", ['Isard','Cabirol','Mufló'])
unidad = st.selectbox("Unitat de gestió:", ['VC Enclar','VC Xixerella','VCR Ansó-Sorteny','VCR Ansó','VC Sorteny','VT Escaldes-Engordany','TCC'])

# 2. Opció de semilla
seed = st.number_input("Semilla opcional (deixa buit per aleatori):", min_value=0, step=1, format="%d")
seed = None if seed == 0 else seed

# 3. Configuració captures
if especie == 'Isard' and unidad == 'TCC':
    total_cap = st.number_input("Nombre total de captures:", min_value=1, step=1)
    tipus_captures = None
    quantitats = None
else:
    simple_opts = ['Femella','Mascle','Adult','Juvenil','Trofeu','Selectiu','Indeterminat']
    simples = st.multiselect("Tipus simples:", simple_opts)
    compostos_input = st.text_area("Tipus compostos (un per línia, ex: Trofeu+Mascle)", height=100)
    compostos = [s.strip() for s in compostos_input.splitlines() if s.strip()]
    if 'Indeterminat' in simples:
        tipus_captures = ['Indeterminat']
    else:
        tipus_captures = simples + compostos
    quantitats = {t: st.number_input(f"Nº captures {t}:", min_value=1, step=1) for t in tipus_captures}

# 4. Pujar CSV i previsualització
df = None
file = st.file_uploader("CSV sol·licitants", type='csv')
if file:
    df = pd.read_csv(file, sep=';')
    st.subheader("Previsualització de sol·licitants")
    st.dataframe(df)

# 5. Botó Execució
executar = st.button("Executar sorteig")
if executar and df is not None:
    if especie == 'Isard' and unidad == 'TCC':
        result = assignar_isards_sorteig_csv(df, total_cap, seed)
    else:
        result = assignar_captura_csv(df, tipus_captures, quantitats, seed)
        st.info("L'any següent, prioritat 1 als qui hagin abatut femella.")
    st.subheader("Resultats del sorteig")
    st.dataframe(result)
    st.download_button('Descarregar CSV', result.to_csv(index=False), file_name=f"sorteig_{especie}_{unidad}.csv")
elif not executar and df is None:
    st.info("Puja un CSV per iniciar el sorteig.")
elif executar and df is None:
    st.warning("Cal pujar un CSV abans d'executar el sorteig.")
elif executar:
    if especie != 'Isard' or unidad != 'TCC':
        st.warning("Completa la configuració de tipus i quantitats abans d'executar.")
