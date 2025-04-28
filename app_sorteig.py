import streamlit as st
import pandas as pd
import tempfile
from sorteig import assignar_isards_sorteig_csv  # o assegura't que la funció és a l'arxiu

st.set_page_config(page_title="App Sorteig Captures Isard", page_icon="🦌", layout="centered")

st.title("🦌 Sorteig de Captures d'Isard")

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
