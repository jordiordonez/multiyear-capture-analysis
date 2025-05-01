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

    # --- Proporcional distribució de captures
    n_indiv = round(total_captures * n_indiv_applicants / total_applicants)
    n_colla = total_captures - n_indiv

    # --- Distribució per colla
    colles_df = df_colla.groupby('Colla_ID').size().reset_index(name='caçadors')
    colles_df['assignats'] = (colles_df['caçadors'] // ratio).astype(int)

    # --- Restants per proporció
    leftover = n_colla - colles_df['assignats'].sum()
    for _ in range(leftover):
        colles_df['rati'] = colles_df['assignats'] / colles_df['caçadors']
        min_rati = colles_df['rati'].min()
        candidates = colles_df[np.isclose(colles_df['rati'], min_rati, atol=1e-6)]
        selected = candidates.sample(n=1, random_state=rng)
        cid = selected['Colla_ID'].values[0]
        colles_df.loc[colles_df['Colla_ID'] == cid, 'assignats'] += 1

    # --- Assign dins colles
    for _, row in colles_df.iterrows():
        cid = row['Colla_ID']
        n_assign = int(row['assignats'])
        while n_assign > 0:
            group = df[(df['Modalitat']=='A') & (df['Colla_ID']==cid) & \
                       (df['adjudicats'] == df[(df['Modalitat']=='A') & (df['Colla_ID']==cid)]['adjudicats'].min())].copy()
            if group.empty:
                break
            group['rand'] = rng.random(size=len(group))
            sorted_grp = group.sort_values(by=['Prioritat', 'anys_sense_captura', 'rand'], 
                                           ascending=[True, False, True])
            take = min(n_assign, len(sorted_grp))
            idxs = sorted_grp.index[:take]
            df.loc[idxs, 'adjudicats'] += 1
            n_assign -= take

    # --- Assign individus B
    if n_indiv > 0:
        rem = n_indiv
        while rem > 0:
            indivs = df[df['Modalitat']=='B']
            min_adjud = indivs['adjudicats'].min() if not indivs.empty else 0
            group = df[(df['Modalitat']=='B') & (df['adjudicats']==min_adjud)].copy()
            if group.empty:
                break
            group['rand'] = rng.random(size=len(group))
            sorted_grp = group.sort_values(by=['Prioritat','anys_sense_captura','rand'],
                                           ascending=[True, False, True])
            take = min(rem, len(sorted_grp))
            idxs = sorted_grp.index[:take]
            df.loc[idxs, 'adjudicats'] += 1
            rem -= take

    # --- Nova prioritat i història
    df['nova_prioritat'] = df['adjudicats'].apply(lambda x: 4 if x == 1 else 2)
    df['nou_anys_sense_captura'] = df.apply(
        lambda r: 0 if r['adjudicats']==1 else r['anys_sense_captura']+1, axis=1)

    df.drop(columns=['rand'], errors='ignore').to_csv(output_csv, index=False)
    return df

# Funció per al sorteig individual (sense colles)
def assignar_captura_csv(df, config, tipus_captures, quantitats):
    required = {'ID','Modalitat','Prioritat','Colla_ID','anys_sense_captura','Resultat_sorteigs_mateixa_sps'}
    if not required.issubset(df.columns):
        raise ValueError(f"Falten columnes: {required - set(df.columns)}")
    rng = np.random.RandomState(None)
    df = df.copy()
    if 'Adjudicats' not in df:
        df['Adjudicats'] = 0

    for tipus in tipus_captures:
        n = quantitats.get(tipus, 0)
        while n > 0:
            df['Adjudicats_acumulats'] = df['Adjudicats'] + df['Resultat_sorteigs_mateixa_sps']
            min_acc = df['Adjudicats_acumulats'].min()
            candidates = df[df['Adjudicats_acumulats']==min_acc].copy()
            candidates['rand'] = rng.random(size=len(candidates))
            if min_acc == 0:
                sorted_cands = candidates.sort_values(by=['Prioritat','rand'], ascending=[True, True])
            else:
                sorted_cands = candidates.sort_values(by=['rand'])
            idx = sorted_cands.index[0]
            df.at[idx,'Adjudicats'] += 1
            n -= 1

    df['Nou_Resultat_sorteigs_mateixa_sps'] = df['Resultat_sorteigs_mateixa_sps'] + df['Adjudicats']
    return df

# Streamlit UI
st.title("App Sorteig Pla de Caça")

# 1. Selecció inicial
especie = st.selectbox("Espècie:", ['Isard','Cabirol','Mufló'])
unidad = st.selectbox("Unitat de gestió:", [
    'VC Enclar','VC Xixerella','VCR Ansó-Sorteny','VCR Ansó','VC Sorteny','VT Escaldes-Engordany','TCC'
])

# 2. Tipus de captura
options = ['Femella','Mascle','Adult','Juvenil','Trofeu','Selectiu','Indeterminat']
seleccio = st.multiselect("Tipus de captura:", options)
if 'Indeterminat' in seleccio:
    seleccio = ['Indeterminat']
quantitats = {tipus: st.number_input(f"Nº captures {tipus}:",1,1) for tipus in seleccio}

# 3. Pujar CSV
file = st.file_uploader("CSV sol·licitants", type='csv')
if file:
    df = pd.read_csv(file, sep=';')
    config = {'especie':especie,'unidad':unidad,'tipus':seleccio,'quantitats':quantitats}

    if especie=='Isard' and unidad=='TCC':
        # nombre de captures total = suma quantitats
        total = sum(quantitats.values())
        result = assignar_isards_sorteig_csv(file, total)
    else:
        result = assignar_captura_csv(df, config, seleccio, quantitats)
        st.info("L'any següent, prioritat 1 als qui hagin abatut femella.")

    st.dataframe(result)
    st.download_button('Descarregar CSV', result.to_csv(index=False),
                       file_name=f"sorteig_{especie}_{unidad}.csv")
else:
    st.info("Puja un CSV per iniciar el sorteig.")


# Títol de la pàgina
st.title("App Sorteig Pla de Caça")

# 1. Selecció inicial
especie = st.selectbox("Selecciona l'espècie:", ['Isard', 'Cabirol', 'Mufló'])
unidad = st.selectbox("Selecciona la Unitad de gestió:", [
    'VC Enclar', 'VC Xixerella', 'VCR Ansó-Sorteny', 'VCR Ansó', 'VC Sorteny', 'VT Escaldes-Engordany', 'TCC'
])

# 2. Selecció de tipus de captura
opciones = ['Femella', 'Mascle', 'Adult', 'Juvenil', 'Trofeu', 'Selectiu', 'Indeterminat']
seleccio = st.multiselect("Tipus de captura (tria múltiples):", opciones)
# Si Indeterminat, anul·la la resta\
if 'Indeterminat' in seleccio:
    seleccio = ['Indeterminat']
# Número d’ordre preservat per l'ordre seleccionat
quantitats = {}
for tipus in seleccio:
    quantitats[tipus] = st.number_input(f"Nombre de captures per '{tipus}':", min_value=1, step=1)

# 3. Pujar CSV
df_cacadors = st.file_uploader("Puja el CSV de sol·licitants", type=['csv'])
if df_cacadors: 
    df = pd.read_csv(df_cacadors, sep=';')

config = {'especie': especie, 'unidad': unidad, 'tipus': seleccio, 'quantitats': quantitats}

# 4. Cridar la lògica adequada\        
if especie == 'Isard' and unidad == 'TCC':
    result = assignar_isards_sorteig_csv(df, config)
else:
    result = assignar_captura_csv(df, config, seleccio, quantitats)
    # Missatge informatiu
    st.info('Per a l\'any següent, caldrà assignar prioritat 1 als caçadors que hagin abatut una femella.')

# Mostrar resultats\        
st.dataframe(result)
# Botó per descarregar
st.download_button('Descarregar resultat CSV', result.to_csv(index=False), file_name=f"sorteig_{especie}_{unidad}.csv")
