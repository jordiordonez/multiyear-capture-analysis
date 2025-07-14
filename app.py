import math
import pandas as pd
import numpy as np
import streamlit as st

# --- Configuracions de vedats per percentatge de parròquia ---
VEDAT_PARRÒQUIES = {
    "VC Enclar": {
        "La Massana": 0.234,
        "Sant Julià de Lòria": 0.241,
        "Andorra la Vella": 0.522,
        "Escaldes-Engordany": 0.003,
    },
    "VC Ransol Sorteny": {"Canillo": 0.5, "Ordino": 0.5},
    "VC Xixerella": {"La Massana": 1.0},
    "VT Escaldes-Engordany": {"Escaldes-Engordany": 1.0},
}

TIPUS_OPTIONS = [
    "Femella",
    "Mascle",
    "Adult",
    "Juvenil",
    "Trofeu",
    "Selectiu",
    "Indeterminat",
]

# --- Funcions utilitàries ---

def normalitza_parroquia(valor):
    CODI_PARROQUIES = {
        1: "Canillo",
        2: "Encamp",
        3: "Ordino",
        4: "La Massana",
        5: "Andorra la Vella",
        6: "Sant Julià de Lòria",
        7: "Escaldes-Engordany",
    }
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    txt = str(valor).strip()
    if txt.isdigit():
        return CODI_PARROQUIES.get(int(txt))
    txt = (
        txt.lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("sj", "Sant Julià de Lòria")
    )
    for name in CODI_PARROQUIES.values():
        if name.lower() in txt:
            return name
    return None


# --- Algorismes de sorteig ---

def assignar_isards_sorteig_csv(df: pd.DataFrame, total_captures: int, seed: int | None = None) -> pd.DataFrame:
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    required = {"ID", "Modalitat", "Prioritat", "Colla_ID", "anys_sense_captura"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")
    df = df.copy()
    df["adjudicats"] = 0
    df_colla = df[df["Modalitat"] == "A"]
    df_indiv = df[df["Modalitat"] == "B"]
    total_applicants = len(df_colla) + len(df_indiv)
    ratio = math.ceil(total_applicants / total_captures)
    n_indiv = round(total_captures * len(df_indiv) / total_applicants)
    n_colla = total_captures - n_indiv
    colles = df_colla.groupby("Colla_ID").size().reset_index(name="caçadors")
    colles["assignats"] = (colles["caçadors"] // ratio).astype(int)
    leftover = n_colla - colles["assignats"].sum()
    for _ in range(leftover):
        colles["rati"] = colles["assignats"] / colles["caçadors"]
        min_rati = colles["rati"].min()
        cand = colles[np.isclose(colles["rati"], min_rati, atol=1e-6)]
        sel = cand.sample(1, random_state=rng)
        cid = sel["Colla_ID"].iloc[0]
        colles.loc[colles["Colla_ID"] == cid, "assignats"] += 1
    for _, row in colles.iterrows():
        cid, to_assign = row["Colla_ID"], int(row["assignats"])
        while to_assign > 0:
            sub = df[(df["Modalitat"] == "A") & (df["Colla_ID"] == cid)]
            min_adj = sub["adjudicats"].min()
            group = sub[sub["adjudicats"] == min_adj].copy()
            group["rand"] = rng.random(len(group))
            sorted_g = group.sort_values(
                by=["Prioritat", "anys_sense_captura", "rand"],
                ascending=[True, False, True],
            )
            take = min(to_assign, len(sorted_g))
            idxs = sorted_g.index[:take]
            df.loc[idxs, "adjudicats"] += 1
            to_assign -= take
    rem = n_indiv
    while rem > 0:
        sub = df[df["Modalitat"] == "B"]
        min_adj = sub["adjudicats"].min()
        group = sub[sub["adjudicats"] == min_adj].copy()
        group["rand"] = rng.random(len(group))
        sorted_g = group.sort_values(
            by=["Prioritat", "anys_sense_captura", "rand"],
            ascending=[True, False, True],
        )
        take = min(rem, len(sorted_g))
        idxs = sorted_g.index[:take]
        df.loc[idxs, "adjudicats"] += 1
        rem -= take
    df["nova_prioritat"] = df["adjudicats"].apply(lambda x: 4 if x > 0 else 2)
    df["nou_anys_sense_captura"] = df.apply(
        lambda r: 0 if r["adjudicats"] > 0 else r["anys_sense_captura"] + 1,
        axis=1,
    )
    return df


def assignar_captura_csv(
    df: pd.DataFrame,
    tipus_captures: list,
    quantitats: dict,
    unitat: str,
    seed: int | None = None,
) -> pd.DataFrame:
    required = {"ID", "Prioritat", "anys_sense_captura"}
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")
    if "Resultat_sorteigs_mateixa_sps" not in df.columns:
        df["Resultat_sorteigs_mateixa_sps"] = 0
    if "Parroquia" in df.columns:
        df["Parroquia"] = df["Parroquia"].apply(normalitza_parroquia)
    if unitat.startswith("V") and "Parroquia" not in df.columns:
        raise ValueError("El CSV ha d'incloure la columna 'Parroquia' per aquest vedat")
    df = df.copy()
    df["Adjudicats"] = 0
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()

    total_caps = sum(quantitats.get(t, 0) for t in tipus_captures)
    parr_quota = {}
    if unitat.startswith("V"):
        info = VEDAT_PARRÒQUIES.get(unitat, {})
        for parr, pct in info.items():
            parr_quota[parr] = int(round(total_caps * 0.5 * pct, 0))
    assignats_parr = {k: 0 for k in parr_quota}

    for i, tipus in enumerate(tipus_captures, start=1):
        target = quantitats.get(tipus, 0)
        assigned = 0
        safe = tipus.replace("+", "_")
        col_name = f"Adjudicats_Tipus{i}_{safe}"
        df[col_name] = 0
        while assigned < target:
            df["Adjudicats_acumulats"] = df["Adjudicats"] + df["Resultat_sorteigs_mateixa_sps"]
            min_acc = df["Adjudicats_acumulats"].min()
            candidates = df[df["Adjudicats_acumulats"] == min_acc].copy()
            candidates["rand"] = rng.random(size=len(candidates))
            if min_acc == 0:
                min_prio = candidates["Prioritat"].min()
                group = candidates[candidates["Prioritat"] == min_prio].copy()
            else:
                group = candidates
            if unitat.startswith("V") and parr_quota:
                group["quota"] = group["Parroquia"].apply(
                    lambda p: parr_quota.get(p, 0) - assignats_parr.get(p, 0)
                )
                group["quota_flag"] = group["quota"] > 0
                order_cols = ["quota_flag", "rand"]
                order_asc = [False, True]
            else:
                order_cols = ["rand"]
                order_asc = [True]
            selected = group.sort_values(by=order_cols, ascending=order_asc).iloc[0]
            idx = selected.name
            df.at[idx, "Adjudicats"] += 1
            df.at[idx, col_name] += 1
            assigned += 1
            if unitat.startswith("V") and selected.get("Parroquia") in assignats_parr:
                assignats_parr[selected["Parroquia"]] += 1

    df["Nou_Resultat_sorteigs_mateixa_sps"] = df["Resultat_sorteigs_mateixa_sps"] + df["Adjudicats"]
    df["nova_prioritat"] = df.apply(
        lambda row: 4 if row["Nou_Resultat_sorteigs_mateixa_sps"] > 0 else row["Prioritat"],
        axis=1,
    )
    df["nova_prioritat Any següent"] = df["Nou_Resultat_sorteigs_mateixa_sps"].apply(lambda x: 4 if x > 0 else 2)
    df["nou_anys_sense_captura"] = df.apply(
        lambda r: 0 if r["Nou_Resultat_sorteigs_mateixa_sps"] > 0 else r["anys_sense_captura"] + 1,
        axis=1,
    )
    df.drop(columns=["Adjudicats_acumulats"], inplace=True)
    return df

# --- Interfície Streamlit ---

st.title("App Sorteig Pla de Caça")

especie = st.selectbox("Espècie:", ["Isard", "Cabirol", "Mufló"])
unitat = st.selectbox(
    "Unitat de gestió:",
    [
        "VC Enclar",
        "VC Xixerella",
        "VC Ransol Sorteny",
        "VT Escaldes-Engordany",
        "TCC",
        "TCC-UGC",
        "TCC-UGE",
        "TCC-UGO",
        "TCC-UGEO",
    ],
)

if unitat.startswith("V"):
    info = VEDAT_PARRÒQUIES.get(unitat, {})
    if info:
        st.subheader(
            "📍 Repartiment parroquial (50% prioritzat en cas de mateixa prioritat individual)"
        )
        data = []
        for p, pct in info.items():
            percent_50 = round(pct * 50, 2)
            data.append({"Parròquia": p, "% del total de captures prioritzat per la Parròquia": percent_50})
        st.dataframe(pd.DataFrame(data))

# Carrega del CSV
file = st.file_uploader("CSV sol·licitants", type="csv")
df = None
if file:
    df = pd.read_csv(file, sep=";")
    st.subheader("Previsualització de sol·licitants")
    st.dataframe(df)

# Configuració de captures
tipus_captures = []
quantitats = {}
if especie == "Isard" and unitat == "TCC":
    total_cap = st.number_input("Quantitat Captures:", min_value=1, step=1)
else:
    if "configs" not in st.session_state:
        st.session_state["configs"] = [{"selections": [], "qty": 1}]
    if st.button("Afegeix Tipus"):
        st.session_state["configs"].append({"selections": [], "qty": 1})
    for idx, conf in enumerate(st.session_state["configs"]):
        st.subheader(f"Tipus {idx+1}")
        sel = st.multiselect(
            f"Seleccioni un o diversos valors per Tipus {idx+1}:",
            TIPUS_OPTIONS,
            key=f"sel_{idx}",
        )
        if "Indeterminat" in sel:
            sel = ["Indeterminat"]
        qty = st.number_input(
            f"Nº captures per Tipus {idx+1}:", min_value=1, step=1, key=f"qty_{idx}"
        )
        st.session_state["configs"][idx]["selections"] = sel
        st.session_state["configs"][idx]["qty"] = qty
        val = sel[0] if len(sel) == 1 else "+".join(sel)
        tipus_captures.append(val)
        quantitats[val] = qty

seed = st.number_input("Llavor opcional (Nombre enter):", min_value=0, step=1, format="%d")
seed = None if seed == 0 else seed

# Executar sorteig
if st.button("Executar sorteig"):
    if df is None:
        st.warning("Cal pujar un CSV abans d'executar el sorteig.")
    else:
        tipus_captures = []
        quantitats = {}
        if especie == "Isard" and unitat == "TCC":
            if total_cap is None:
                st.warning("Cal especificar el nombre de captures.")
                st.stop()
            try:
                result = assignar_isards_sorteig_csv(df, int(total_cap), seed)
            except ValueError as e:
                st.error(str(e))
                st.stop()
        else:
            for conf in st.session_state.get("configs", []):
                sel = conf["selections"]
                val = sel[0] if len(sel) == 1 else "+".join(sel)
                tipus_captures.append(val)
                quantitats[val] = conf["qty"]
            try:
                result = assignar_captura_csv(df, tipus_captures, quantitats, unitat, seed)
            except ValueError as e:
                st.error(str(e))
                st.stop()
            st.info("L'any següent, prioritat 1 als qui hagin abatut femella.")
        st.subheader("Resultats del sorteig")
        st.dataframe(result)
        if unitat.startswith("V") and "Parroquia" in result.columns:
            st.subheader("📊 Resum per parròquia")
            adj_per_parr = result.groupby("Parroquia")["Adjudicats"].sum().reset_index()
            adj_per_parr["% del total"] = (
                adj_per_parr["Adjudicats"] / adj_per_parr["Adjudicats"].sum() * 100
            ).round(1)
            st.dataframe(adj_per_parr)
        st.download_button(
            "Descarregar CSV",
            result.to_csv(index=False),
            file_name=f"sorteig_{especie}_{unitat}.csv",
        )
else:
    if df is None:
        st.info("Puja un CSV per iniciar el sorteig.")
    else:
        if not (especie == "Isard" and unitat == "TCC"):
            if st.session_state.get("configs") is None:
                st.info("Configura els Tipus i quantitats abans d'executar.")

