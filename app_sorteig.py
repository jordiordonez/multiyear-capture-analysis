import streamlit as st
import pandas as pd
import numpy as np
import math

# Funció per al sorteig amb colles (lògica existent)
def assignar_isards_sorteig_csv(
    file_csv: str,
    total_captures: int,
    output_csv: str = "resultats.csv",
    seed: int = None
) -> pd.DataFrame:
    rng = np.random.RandomState(seed) if seed is not None else np.random
    df = pd.read_csv(file_csv, sep=';')

    required = {'ID', 'Modalitat', 'Prioritat', 'Colla_ID', 'anys_sense_captura'}
    if not required.issubset(df.columns):
        raise ValueError(f"Falten columnes obligatòries: {required - set(df.columns)}")

    df['adjudicats'] = 0
    df_colla = df[df['Modalitat'] == 'A'].copy()
    df_indiv = df[df['Modalitat'] == 'B'].copy()

    total_applicants = len(df_colla) + len(df_indiv)
    ratio = math.ceil(total_applicants / total_captures)

    # Proporcional distribució
    n_indiv = round(total_captures * len(df_indiv) / total_applicants)
    n_colla = total_captures - n_indiv

    # Distribució per colla
    colles_df = df_colla.groupby('Colla_ID').size().reset_index(name='caçadors')
    colles_df['assignats'] = (colles_df['caçadors'] // ratio).astype(int)
    leftover = n_colla - colles_df['assignats'].sum()
    for _ in range(leftover):
        colles_df['rati'] = colles_df['assignats'] / colles_df['caçadors']
        min_rati = colles_df['rati'].min()
        candidates = colles_df[np.isclose(colles_df['rati'], min_rati, atol=1e-6)]
        selected = candidates.sample(n=1, random_state=rng)
        cid = selected['Colla_ID'].iloc[0]
        colles_df.loc[colles_df['Colla_ID'] == cid, 'assignats'] += 1

    # Assign dins colles
    for _, row in colles_df.iterrows():
        cid = row['Colla_ID']
        to_assign = int(row['assignats'])
        while to_assign > 0:
            sub = df[(df['Modalitat']=='A') & (df['Colla_ID']==cid)]
            min_adj = sub['adjudicats'].min()
            group = sub[sub['adjudicats']==min_adj].copy()
            if group.empty:
                break
            group['rand'] = rng.random(size=len(group))
            sorted_grp = group.sort_values(by=['Prioritat','anys_sense_captura','rand'], ascending=[True,False,True])
            take = min(to_assign, len(sorted_grp))
            idxs = sorted_grp.index[:take]
            df.loc[idxs,'adjudicats'] += 1
            to_assign -= take

    # Assign individual B
    if n_indiv > 0:
        rem = n_indiv
        while rem > 0:
            sub = df[df['Modalitat']=='B']
            min_adj = sub['adjudicats'].min()
            group = sub[sub['adjudicats']==min_adj].copy()
            if group.empty:
                break
            group['rand'] = rng.random(size=len(group))
            sorted_grp = group.sort_values(by=['Prioritat','anys_sense_captura','rand'], ascending=[True,False,True])
            take = min(rem, len(sorted_grp))
            idxs = sorted_grp.index[:take]
            df.loc[idxs,'adjudicats'] += 1
            rem -= take

    # Nova prioritat i anys
    df['nova_prioritat'] = df['adjudicats'].apply(lambda x: 4 if x==1 else 2)
    df['nou_anys_sense_captura'] = df.apply(lambda r: 0 if r['adjudicats']==1 else r['anys_sense_captura']+1, axis=1)
    df.drop(columns=['rand'], errors='ignore', inplace=True)
    df.to_csv(output_csv, index=False)
    return df

# Funció per al sorteig individual (sense colles)
def assignar_captura_csv(
    df: pd.DataFrame,
    tipus_captures: list,
    quantitats: dict
) -> pd.DataFrame:
    # Validació columnes
    req = {'ID','Modalitat','Prioritat','Colla_ID','anys_sense_captura','Resultat_sorteigs_mateixa_sps'}
    if not req.issubset(df.columns):
        missing = req - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")

    df = df.copy()
    # Inicialitzar adjudicats
    if 'Adjudicats' not in df.columns:
        df['Adjudicats'] = 0

    rng = np.random.RandomState(None)
    # Iterar en ordre de tipus\    
    for tipus in tipus_captures:
        target = quantitats.get(tipus, 0)
        assigned = 0
        while assigned < target:
            df['Adjudicats_acumulats'] = df['Adjudicats'] + df['Resultat_sorteigs_mateixa_sps']
            min_acc = df['Adjudicats_acumulats'].min()
            candidates = df[df['Adjudicats_acumulats']==min_acc].copy()
            candidates['rand'] = rng.random(size=len(candidates))
            if min_acc == 0:
                sorted_cands = candidates.sort_values(by=['Prioritat','rand'],ascending=[True,True])
            else:
                sorted_cands = candidates.sort_values(by=['rand'])
            chosen = sorted_cands.index[0]
            df.at[chosen,'Adjudicats'] += 1
            assigned += 1

    # Calcular nou resultat\    df['Nou_Resultat_sorteigs_mateixa_sps'] = df['Resultat_sorteigs_mateixa_sps'] + df['Adjudicats']
    return df

# Streamlit UI
st.title("App Sorteig Pla de Caça")

# 1. Selecció inicial
especie = st.selectbox("Espècie:", ['Isard','Cabirol','Mufló'])
unidad = st.selectbox("Unitat de gestió:",[
    'VC Enclar','VC Xixerella','VCR Ansó-Sorteny','VCR Ansó',
    'VC Sorteny','VT Escaldes-Engordany','TCC'
])

# 2. Tipus de captura
options = ['Femella','Mascle','Adult','Juvenil','Trofeu','Selectiu','Indeterminat']
seleccio = st.multiselect("Tipus de captura:", options)
if 'Indeterminat' in seleccio:
    seleccio = ['Indeterminat']
quantitats = {}
for t in seleccio:
    quantitats[t] = st.number_input(f"Nº captures {t}:", min_value=1, step=1)

# 3. Pujar CSV i execució
file = st.file_uploader("CSV sol·licitants", type='csv')
if file:
    # Llegir i validar
    df = pd.read_csv(file, sep=';')
    # Cridar logica
    if especie=='Isard' and unidad=='TCC':
        total = sum(quantitats.values())
        result = assignar_isards_sorteig_csv(file, total)
    else:
        result = assignar_captura_csv(df, seleccio, quantitats)
        st.info("L'any següent, prioritat 1 als qui hagin abatut femella.")
    # Mostra i descarrega
    st.dataframe(result)
    st.download_button('Descarregar CSV', result.to_csv(index=False), file_name=f"sorteig_{especie}_{unidad}.csv")
else:
    st.info("Puja un CSV per iniciar el sorteig.")

# Mostrar resultats\        
if result: st.dataframe(result)
# Botó per descarregar
st.download_button('Descarregar resultat CSV', result.to_csv(index=False), file_name=f"sorteig_{especie}_{unidad}.csv")
