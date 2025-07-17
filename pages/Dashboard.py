import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 Resultats sorteig", layout="wide")

# 1️⃣  Grab the objects produced in the main app
if "resultat" not in st.session_state or "resums" not in st.session_state:
    st.error("⚠️ Primer executa un sorteig des de la pestanya «🎲 Sorteig».")
    st.stop()

df      = st.session_state["resultat"]
summary = (pd.concat(st.session_state["resums"])
           if st.session_state["resums"] else pd.DataFrame())

st.title("📊 Resultats del sorteig")

# ── 3.1 KPI cards ────────────────────────────────────
total   = len(df)
estrang = (df["Estranger"].str.lower() == "si").sum()
sense_cap = (df["anys_sense_captura"] > 0).sum()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Sol·licituds totals", f"{total:,}")
kpi2.metric("Estrangers", f"{estrang:,}", delta=f"{estrang/total: .1%}")
kpi3.metric(">0 anys sense captura", f"{sense_cap:,}",
            delta=f"{sense_cap/total: .1%}")

st.divider()

# ── 3.2 Interactive filters ─────────────────────────
with st.sidebar:
    st.header("Filtres")
    mod_sel   = st.multiselect("Modalitat", sorted(df["Modalitat"].dropna().unique()))
    parro_sel = st.multiselect("Parròquia", sorted(df.get("Parroquia", pd.Series()).dropna().unique()))
    pri_sel   = st.slider("Prioritat", 0, int(df["Prioritat"].max()), (0, int(df["Prioritat"].max())))
    
###############################################################################
# Correct way to build the filter mask
###############################################################################
# start with the “always-true” mask
mask = pd.Series(True, index=df.index)

# 1️⃣ Modalitat ---------------------------------------------------------------
if mod_sel:                          # only if user picked something
    mask &= df["Modalitat"].isin(mod_sel)

# 2️⃣ Parròquia --------------------------------------------------------------
if parro_sel:
    mask &= df["Parroquia"].isin(parro_sel)

# 3️⃣ Prioritat --------------------------------------------------------------
mask &= df["Prioritat"].between(*pri_sel)

# finally slice the frame
data = df[mask]


# ── 3.3 Plot section ────────────────────────────────
tabs = st.tabs(["Barres", "Distribucions", "Mapa (parròquia)"])

with tabs[0]:
    fig = px.histogram(data, x="Prioritat", nbins=6,
                       title="Sol·licituds per prioritat (filtres aplicats)")
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    box = px.box(data, x="Estranger", y="anys_sense_captura",
                 points="all", title="Anys sense captura · Estrangers vs locals")
    st.plotly_chart(box, use_container_width=True)

with tabs[2]:
    if "Parroquia" in data.columns:
        map_data = (data.groupby("Parroquia").size()
                         .reset_index(name="Sol·licituds"))
        bar = px.bar(map_data, x="Parroquia", y="Sol·licituds",
                     title="Sol·licituds per parròquia")
        st.plotly_chart(bar, use_container_width=True)
    else:
        st.info("No hi ha columna «Parroquia» al CSV.")

st.caption("⚙️  Totes les gràfiques responen als filtres del panell lateral.")
