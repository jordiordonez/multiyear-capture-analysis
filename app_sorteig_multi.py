import math
import pandas as pd
import numpy as np
import streamlit as st
from collections import OrderedDict

# --- Constants ---

ESPECIE_SORTEIGS = OrderedDict({
    "Isard": ["IS TCC", "IS VCRS", "IS VCX", "IS VCE"],
    "Cabirol": ["CAB"],
    "Mufló": ["MUF UGEO", "MUF UGC", "MUF VTE-E", "MUF VCE", "MUF R"],
})

VEDAT_PARRÒQUIES = {
    "IS VCE": {
        "La Massana": 0.234,
        "Sant Julià de Lòria": 0.241,
        "Andorra la Vella": 0.522,
        "Escaldes-Engordany": 0.003,
    },
    "IS VCRS": {"Canillo": 0.5, "Ordino": 0.5},
    "IS VCX": {"La Massana": 1.0},
}

TIPUS_OPTIONS = [
    "Femella",
    "Mascle",
    "Adult",
    "Juvenil",
    "Trofeu",
    "Selectiu",
    "Indeterminat",
    "Indeferent",
]


def normalitza_parroquia(valor: str | int | float | None) -> str | None:
    """Normalitza diferents formats de parròquia al nom oficial."""
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


def normalitza_estranger(valor) -> str:
    """Retorna 'si' o 'no' en minúscules."""
    if isinstance(valor, str) and valor.strip().lower() in {"si", "sí", "s", "yes", "true", "1"}:
        return "si"
    return "no"


def validar_csv_isard(df: pd.DataFrame) -> None:
    required = {"ID", "Modalitat", "Colla_ID", "Prioritat", "anys_sense_captura", "Parroquia", "Estranger"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Falten columnes: {', '.join(sorted(missing))}")


def validar_csv_altres(df: pd.DataFrame) -> None:
    required = {"ID", "Prioritat", "anys_sense_captura", "Resultat_sorteigs_mateixa_sps", "Estranger"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Falten columnes: {', '.join(sorted(missing))}")


def validar_csv2(df: pd.DataFrame) -> None:
    required = {"ID", "Codi_Sorteig"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Falten columnes: {', '.join(sorted(missing))}")


# --- Sorteig helpers ---

def tria_candidat(
    df: pd.DataFrame,
    assigned: set,
    estranger_count: int,
    assignats: int,
    vedat: str | None,
    assignats_parr: dict,
    rng: np.random.RandomState,
) -> int | None:
    pool = df[~df["ID"].isin(assigned)].copy()
    if pool.empty:
        return None
    limit = math.floor(0.10 * max(len(df), assignats))
    if estranger_count >= limit:
        pool = pool[pool["Estranger"] == "no"]
    if pool.empty:
        return None
    pool["rand"] = rng.random(len(pool))
    if vedat and vedat in VEDAT_PARRÒQUIES:
        quotas = VEDAT_PARRÒQUIES[vedat]
        pool["quota_flag"] = pool["Parroquia"].apply(lambda p: quotas.get(p, 0) - assignats_parr.get(p, 0) > 0)
        order_cols = ["quota_flag", "Prioritat", "anys_sense_captura", "rand"]
        asc = [False, True, False, True]
    else:
        order_cols = ["Prioritat", "anys_sense_captura", "rand"]
        asc = [True, False, True]
    return pool.sort_values(by=order_cols, ascending=asc).index[0]


def sorteig_individual(
    df: pd.DataFrame,
    tipus_quant: list[tuple[str, int]],
    ordre_aleatori: bool,
    vedat: str | None,
    rng: np.random.RandomState,
) -> pd.DataFrame:
    df = df.copy()
    df["Estranger"] = df["Estranger"].apply(normalitza_estranger)
    if "Parroquia" in df.columns:
        df["Parroquia"] = df["Parroquia"].apply(normalitza_parroquia)
    df["assigned"] = False
    df["ordre"] = np.nan
    df["tipus"] = np.nan

    assignats_parr = {k: 0 for k in VEDAT_PARRÒQUIES.get(vedat, {})}

    captures_pool = []
    for t, q in tipus_quant:
        captures_pool.extend([t] * q)
    if not ordre_aleatori:
        captures_pool = []
        for t, q in tipus_quant:
            captures_pool.extend([t] * q)
    ordre = 1
    estrangers = 0
    assignats = 0
    if ordre_aleatori:
        while captures_pool and not df[df["assigned"] == False].empty:
            idx = tria_candidat(df, set(df[df["assigned"]]["ID"]), estrangers, assignats, vedat, assignats_parr, rng)
            if idx is None:
                break
            tipus = rng.choice(captures_pool)
            captures_pool.remove(tipus)
            df.at[idx, "assigned"] = True
            df.at[idx, "ordre"] = ordre
            df.at[idx, "tipus"] = tipus
            assignats += 1
            if df.at[idx, "Estranger"] == "si":
                estrangers += 1
            if vedat and df.at[idx, "Parroquia"] in assignats_parr:
                assignats_parr[df.at[idx, "Parroquia"]] += 1
            ordre += 1
    else:
        for tipus, q in tipus_quant:
            for _ in range(q):
                idx = tria_candidat(df, set(df[df["assigned"]]["ID"]), estrangers, assignats, vedat, assignats_parr, rng)
                if idx is None:
                    break
                df.at[idx, "assigned"] = True
                df.at[idx, "ordre"] = ordre
                df.at[idx, "tipus"] = tipus
                assignats += 1
                if df.at[idx, "Estranger"] == "si":
                    estrangers += 1
                if vedat and df.at[idx, "Parroquia"] in assignats_parr:
                    assignats_parr[df.at[idx, "Parroquia"]] += 1
                ordre += 1
    res = df[["ID", "ordre", "tipus", "Estranger"]].copy()
    return res


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
            sorted_g = group.sort_values(by=["Prioritat", "anys_sense_captura", "rand"], ascending=[True, False, True])
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
        sorted_g = group.sort_values(by=["Prioritat", "anys_sense_captura", "rand"], ascending=[True, False, True])
        take = min(rem, len(sorted_g))
        idxs = sorted_g.index[:take]
        df.loc[idxs, "adjudicats"] += 1
        rem -= take
    return df


# --- Main processing ---

def processar_sorteigs(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    config: pd.DataFrame,
    especie: str,
    seed: int | None,
) -> tuple[pd.DataFrame, list[pd.DataFrame]]:
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    ids_totals = df2["ID"].unique()
    base = df1[df1["ID"].isin(ids_totals)].drop_duplicates("ID")
    resultat = base[["ID", "Prioritat", "anys_sense_captura", "Estranger"]].copy()
    resum_sorteigs = []

    for sorteig in ESPECIE_SORTEIGS[especie]:
        conf_rows = config[config["Codi_Sorteig"] == sorteig]
        col_base = sorteig.replace(" ", "_")
        resultat[col_base] = np.nan
        resultat[f"Tipus_{col_base}"] = np.nan
        subset = df2[df2["Codi_Sorteig"] == sorteig]
        if subset.empty or conf_rows.empty:
            continue
        if subset["ID"].duplicated().any():
            raise ValueError(f"ID duplicats al sorteig {sorteig}")
        part = subset.merge(df1, on="ID")
        if especie == "Isard" and sorteig == "IS TCC":
            total_cap = int(conf_rows["Quantitat"].sum())
            sub_seed = rng.randint(0, 2**32 - 1)
            asignats = assignar_isards_sorteig_csv(part, total_cap, seed=sub_seed)
            asignats = asignats[["ID", "adjudicats", "Estranger"]].rename(columns={"adjudicats": "ordre"})
            asignats["tipus"] = "+".join(conf_rows.iloc[0]["Tipus"]) if isinstance(conf_rows.iloc[0]["Tipus"], list) else conf_rows.iloc[0]["Tipus"]
        else:
            tipus_quant = []
            for _, r in conf_rows.iterrows():
                tipus = r["Tipus"] if isinstance(r["Tipus"], list) else []
                if "Indeferent" in tipus:
                    tipus = ["Indeferent"]
                tipus_quant.append(("+".join(tipus), int(r["Quantitat"])) )
            vedat = sorteig if especie == "Isard" and sorteig != "IS TCC" else None
            ordre_aleatori = bool(conf_rows.iloc[0].get("Aleatori", False))
            sub_seed = rng.randint(0, 2**32 - 1)
            asignats = sorteig_individual(part, tipus_quant, ordre_aleatori, vedat, np.random.RandomState(sub_seed))
        resultat = resultat.merge(asignats[["ID", "ordre", "tipus"]], on="ID", how="left")
        resultat[col_base] = asignats["ordre"]
        resultat[col_base] = resultat[col_base].fillna(0)
        resultat[f"Tipus_{col_base}"] = asignats["tipus"]
        total_cap = asignats["ordre"].notna().sum()
        estr = asignats[asignats["Estranger"] == "si"]["ordre"].count()
        tipus_counts = asignats["tipus"].value_counts().to_dict()
        resum = pd.DataFrame({"Sorteig": [sorteig], "Captures": [total_cap], "% Estrangers": [round(100*estr/max(1,total_cap),1)]})
        for t, v in tipus_counts.items():
            resum[t] = v
        resum_sorteigs.append(resum)
    capture_cols = [s.replace(" ", "_") for s in ESPECIE_SORTEIGS[especie]]
    resultat["te_capture"] = resultat[capture_cols].apply(lambda r: r.fillna(0).gt(0).any(), axis=1)
    resultat["Nou_Anys_sense_captura"] = resultat.apply(lambda r: r["anys_sense_captura"] + 1 if not r["te_capture"] else 0, axis=1)
    resultat["Nova_prioritat"] = resultat.apply(
        lambda r: 4 if any(str(r[f"Tipus_{c}"]).find("Mascle") >=0 for c in capture_cols) else (4 if r["te_capture"] else 2),
        axis=1
    )
    resultat.drop(columns=["te_capture"], inplace=True)
    return resultat, resum_sorteigs


# --- Streamlit UI ---

st.title("Sorteig captures")

especie = st.selectbox("Espècie", list(ESPECIE_SORTEIGS.keys()))

with st.expander("Configuració de captures per sorteig"):
    initial_rows = [{"Codi_Sorteig": c, "Tipus": [], "Quantitat": 0, "Aleatori": True} for c in ESPECIE_SORTEIGS[especie]]
    config_df = st.data_editor(
        pd.DataFrame(initial_rows),
        column_config={
            "Tipus": st.column_config.ListColumn("Tipus", width="medium", options=TIPUS_OPTIONS),
            "Quantitat": st.column_config.NumberColumn("Quantitat", min_value=0, step=1),
            "Aleatori": st.column_config.CheckboxColumn("Ordre aleatori"),
        },
        num_rows="dynamic",
        key=f"config_{especie}",
    )

csv1 = st.file_uploader("CSV principal", type="csv", key="csv1")
csv2 = st.file_uploader("CSV de sorteigs", type="csv", key="csv2")

seed_input = st.number_input("Llavor opcional", value=0, step=1)
seed = int(seed_input) if seed_input else None

if st.button("Executar sorteig"):
    if not csv1 or not csv2:
        st.error("Cal carregar els dos CSV")
        st.stop()
    df1 = pd.read_csv(csv1, sep=";")
    df2 = pd.read_csv(csv2, sep=";")
    try:
        validar_csv2(df2)
        if especie == "Isard":
            validar_csv_isard(df1)
        else:
            validar_csv_altres(df1)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    resultat, resums = processar_sorteigs(df1, df2, config_df, especie, seed)
    st.subheader("Resultats")
    st.dataframe(resultat)
    csv = resultat.to_csv(index=False).encode("utf-8")
    st.download_button("Descarregar CSV", csv, file_name="resultats.csv")
    tabs = st.tabs(["Per sorteig", "Resum global"])
    with tabs[0]:
        for resum in resums:
            st.dataframe(resum)
    with tabs[1]:
        if resums:
            global_df = pd.concat(resums).groupby("Sorteig").sum(numeric_only=True)
            st.dataframe(global_df)
            st.bar_chart(global_df["Captures"])
