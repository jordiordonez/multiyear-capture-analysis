import math            # ← NEW: for ceil, floor, isnan
import pandas as pd
import numpy as np
import streamlit as st
from collections import OrderedDict


# ── CONSTANTS ────────────────────────────────────────────────────────────────

ESPECIE_SORTEIGS = OrderedDict({
    "Isard":   ["IS TCC", "IS VCRS", "IS VCX", "IS VCE"],
    "Cabirol": ["CAB"],
    "Mufló":   ["MUF UGEO", "MUF UGC", "MUF VTE-E", "MUF VCE", "MUF R"],
})

# Order of vedats must be preserved for UI display
VEDAT_PARRÒQUIES = OrderedDict([
    ("IS VCE", {
        "La Massana": 0.234,
        "Sant Julià de Lòria": 0.241,
        "Andorra la Vella": 0.522,
        "Escaldes-Engordany": 0.003,
    }),
    ("IS VCRS", {"Canillo": 0.5, "Ordino": 0.5}),
    ("IS VCX", {"La Massana": 1.0}),
])

TIPUS_OPTIONS = [
    "Femella", "Mascle", "Adult", "Juvenil",
    "Trofeu", "Selectiu", "Indeterminat",
]


# ── UTILITIES ────────────────────────────────────────────────────────────────

def normalitza_parroquia(valor):
    CODI_PARROQUIES = {
        1: "Canillo", 2: "Encamp", 3: "Ordino",
        4: "La Massana", 5: "Andorra la Vella",
        6: "Sant Julià de Lòria", 7: "Escaldes-Engordany",
    }
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return None
    txt = str(valor).strip()
    if txt.isdigit():
        return CODI_PARROQUIES.get(int(txt))
    txt = (txt.lower()
           .replace("-", " ")
           .replace("_", " ")
           .replace("sj", "Sant Julià de Lòria"))
    for name in CODI_PARROQUIES.values():
        if name.lower() in txt:
            return name
    return None


def normalitza_estranger(valor) -> str:
    if isinstance(valor, str) and valor.strip().lower() in {"si", "sí", "s", "yes", "true", "1"}:
        return "si"
    return "no"


# ── CSV VALIDATION HELPERS ───────────────────────────────────────────────────

def validar_csv_isard(df):
    required = {"ID", "Modalitat", "Colla_ID", "Prioritat",
                "anys_sense_captura", "Parroquia", "Estranger"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Falten columnes: {', '.join(sorted(missing))}")


def validar_csv_altres(df):
    required = {"ID", "Prioritat", "anys_sense_captura", "Estranger"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Falten columnes: {', '.join(sorted(missing))}")


def validar_csv2(df):
    required = {"ID", "Codi_Sorteig"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Falten columnes: {', '.join(sorted(missing))}")


# ── HELPER: CHOOSE NEXT CANDIDATE ────────────────────────────────────────────

def tria_candidat(df, assigned, estr_cnt, assignats,
                  vedat, assignats_parr, rng):
    pool = df[~df["ID"].isin(assigned)].copy()
    if pool.empty:
        return None

    limit = math.floor(0.10 * max(len(df), assignats))
    if estr_cnt >= limit:
        pool = pool[pool["Estranger"] == "no"]
    if pool.empty:
        return None

    pool["rand"] = rng.random(len(pool))

    if vedat and vedat in VEDAT_PARRÒQUIES:
        quotas = VEDAT_PARRÒQUIES[vedat]
        pool["quota_flag"] = pool["Parroquia"].apply(
            lambda p: quotas.get(p, 0) - assignats_parr.get(p, 0) > 0
        )
        order_cols, asc = ["quota_flag", "Prioritat",
                           "anys_sense_captura", "rand"], [False, True, False, True]
    else:
        order_cols, asc = ["Prioritat", "anys_sense_captura", "rand"], [True, False, True]

    return pool.sort_values(order_cols, ascending=asc).index[0]


# ── HELPER: INDIVIDUAL DRAW (no colles) ──────────────────────────────────────

def sorteig_individual(df, tipus_quant, ordre_aleatori, vedat, rng):
    df = df.copy()
    df["Estranger"] = df["Estranger"].apply(normalitza_estranger)
    if "Parroquia" in df.columns:
        df["Parroquia"] = df["Parroquia"].apply(normalitza_parroquia)

    df["assigned"], df["ordre"], df["tipus"] = False, np.nan, np.nan
    assignats_parr = {k: 0 for k in VEDAT_PARRÒQUIES.get(vedat, {})}

    captures_pool = [t for t, q in tipus_quant for _ in range(q)]
    if not ordre_aleatori:
        captures_pool = captures_pool.copy()   # keep deterministic order

    ordre, estrangers, assignats = 1, 0, 0

    if ordre_aleatori:
        while captures_pool and not df.loc[~df["assigned"]].empty:
            idx = tria_candidat(df, set(df[df["assigned"]]["ID"]),
                                estrangers, assignats, vedat,
                                assignats_parr, rng)
            if idx is None:
                break
            tipus = rng.choice(captures_pool)
            captures_pool.remove(tipus)

            df.loc[idx, ["assigned", "ordre", "tipus"]] = [True, ordre, tipus]

            assignats += 1
            if df.at[idx, "Estranger"] == "si":
                estrangers += 1
            if vedat and df.at[idx, "Parroquia"] in assignats_parr:
                assignats_parr[df.at[idx, "Parroquia"]] += 1
            ordre += 1
    else:
        for tipus, q in tipus_quant:
            for _ in range(q):
                idx = tria_candidat(df, set(df[df["assigned"]]["ID"]),
                                    estrangers, assignats, vedat,
                                    assignats_parr, rng)
                if idx is None:
                    break
                df.loc[idx, ["assigned", "ordre", "tipus"]] = [True, ordre, tipus]

                assignats += 1
                if df.at[idx, "Estranger"] == "si":
                    estrangers += 1
                if vedat and df.at[idx, "Parroquia"] in assignats_parr:
                    assignats_parr[df.at[idx, "Parroquia"]] += 1
                ordre += 1

    return df[["ID", "ordre", "tipus", "Estranger"]].copy()


# ── HELPER: PARSE 'Tipus' FIELD ──────────────────────────────────────────────

def _parse_tipus(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [t.strip() for t in str(value).split(",") if t.strip()]


# ── MAIN: PROCESSAR SORTEIGS ────────────────────────────────────────────────

def processar_sorteigs(df1, df2, config, especie, seed):
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()

    ids_totals = df2["ID"].unique()
    base = df1[df1["ID"].isin(ids_totals)].drop_duplicates("ID")
    resultat = base[["ID", "Prioritat", "anys_sense_captura", "Estranger"]].copy()
    resum_sorteigs = []

    for sorteig in ESPECIE_SORTEIGS[especie]:
        conf_rows = config[config["Codi_Sorteig"] == sorteig].copy()
        conf_rows["Tipus"] = conf_rows["Tipus"].apply(_parse_tipus)

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
            if total_cap <= 0:
                raise ValueError("Total de captures per IS TCC ha de ser > 0")
            asignats = assignar_isards_sorteig_csv(
                part, total_cap, seed=rng.randint(0, 2**32 - 1)
            )
            asignats["tipus"] = "+".join(conf_rows.iloc[0]["Tipus"])
        else:
            tipus_quant = []
            for _, r in conf_rows.iterrows():
                tipus = ["Indeterminat"] if "Indeterminat" in r["Tipus"] else r["Tipus"]
                tipus_quant.append(("+".join(tipus), int(r["Quantitat"])))
            vedat = sorteig if (especie == "Isard" and sorteig != "IS TCC") else None
            asignats = sorteig_individual(
                part, tipus_quant,
                bool(conf_rows.iloc[0].get("Aleatori", False)),
                vedat,
                np.random.RandomState(rng.randint(0, 2**32 - 1))
            )

        # ── SAFE MERGE: unique column names per sorteig
        # 1️⃣  keep Estranger for the résumé, but don’t let it into the merge
        asignats = asignats.rename(columns={
            "ordre": f"ordre_{col_base}",
            "tipus": f"tipus_{col_base}"
        })

        # 2️⃣  calculate 'estr' **before** we drop Estranger
        estr = asignats[asignats["Estranger"] == "si"][f"ordre_{col_base}"].count()

        # 3️⃣  we only need ID, ordre_*, tipus_* for the merge
        merge_cols = ["ID", f"ordre_{col_base}", f"tipus_{col_base}"]
        resultat = resultat.merge(asignats[merge_cols], on="ID", how="left")

        resultat[col_base] = resultat[f"ordre_{col_base}"].fillna(0)
        resultat[f"Tipus_{col_base}"] = resultat[f"tipus_{col_base}"]
        resultat.drop(columns=[f"ordre_{col_base}", f"tipus_{col_base}"],
                      inplace=True)

        total_cap = rezultat_cap = asignats[f"ordre_{col_base}"].notna().sum()
        estr = asignats[asignats["Estranger"] == "si"]\
                        [f"ordre_{col_base}"].count()
        tipus_counts = asignats[f"tipus_{col_base}"].value_counts().to_dict()

        resum = pd.DataFrame({
            "Sorteig": [sorteig],
            "Captures": [total_cap],
            "% Estrangers": [round(100 * estr / max(1, total_cap), 1)],
        })
        for t, v in tipus_counts.items():
            resum[t] = v
        resum_sorteigs.append(resum)

    capture_cols = [s.replace(" ", "_") for s in ESPECIE_SORTEIGS[especie]]
    resultat["te_capture"] = resultat[capture_cols].apply(
        lambda r: r.fillna(0).gt(0).any(), axis=1
    )
    resultat["Nou_Anys_sense_captura"] = resultat.apply(
        lambda r: r["anys_sense_captura"] + 1 if not r["te_capture"] else 0,
        axis=1
    )
    resultat["Nova_prioritat"] = resultat.apply(
        lambda r: 4 if any(
            str(r[f"Tipus_{c}"]).find("Mascle") >= 0 for c in capture_cols
        ) else (4 if r["te_capture"] else 2),
        axis=1
    )
    resultat.drop(columns=["te_capture"], inplace=True)
    return resultat, resum_sorteigs


# ── DRAW WITH COLLES (IS TCC) ────────────────────────────────────────────────

def assignar_isards_sorteig_csv(df, total_captures, seed=None):
    if total_captures <= 0:
        raise ValueError("total_captures ha de ser > 0 (reviseu 'Quantitat').")

    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    required = {"ID", "Modalitat", "Prioritat", "Colla_ID", "anys_sense_captura"}
    if not required.issubset(df.columns):
        raise ValueError(f"Falten columnes: {required - set(df.columns)}")

    df = df.copy()
    df["adjudicats"] = 0
    df["ordre"] = np.nan
    ordre_counter = 1
    df_colla, df_indiv = df[df["Modalitat"] == "A"], df[df["Modalitat"] == "B"]

    total_applicants = len(df_colla) + len(df_indiv)
    ratio = math.ceil(total_applicants / total_captures)
    n_indiv = round(total_captures * len(df_indiv) / total_applicants)
    n_colla = total_captures - n_indiv

    # assign colles
    colles = df_colla.groupby("Colla_ID").size().reset_index(name="caçadors")
    colles["assignats"] = (colles["caçadors"] // ratio).astype(int)
    leftover = n_colla - colles["assignats"].sum()
    for _ in range(leftover):
        colles["rati"] = colles["assignats"] / colles["caçadors"]
        cid = colles.loc[np.isclose(colles["rati"],
                                    colles["rati"].min())]\
                     .sample(1, random_state=rng)["Colla_ID"].iat[0]
        colles.loc[colles["Colla_ID"] == cid, "assignats"] += 1

    for _, row in colles.iterrows():
        cid, to_assign = row["Colla_ID"], int(row["assignats"])
        while to_assign:
            sub = df[(df["Modalitat"] == "A") & (df["Colla_ID"] == cid)]
            group = sub[sub["adjudicats"] == sub["adjudicats"].min()].copy()
            group["rand"] = rng.random(len(group))
            idxs = group.sort_values([
                "Prioritat",
                "anys_sense_captura",
                "rand",
            ], ascending=[True, False, True]).index[:min(to_assign, len(group))]
            for idx in idxs:
                if df.at[idx, "adjudicats"] == 0:
                    df.at[idx, "ordre"] = ordre_counter
                    ordre_counter += 1
                df.at[idx, "adjudicats"] = 1
            to_assign -= len(idxs)

    # assign individuals
    rem = n_indiv
    while rem:
        sub = df[df["Modalitat"] == "B"]
        group = sub[sub["adjudicats"] == sub["adjudicats"].min()].copy()
        group["rand"] = rng.random(len(group))
        idxs = group.sort_values([
            "Prioritat",
            "anys_sense_captura",
            "rand",
        ], ascending=[True, False, True]).index[:min(rem, len(group))]
        for idx in idxs:
            if df.at[idx, "adjudicats"] == 0:
                df.at[idx, "ordre"] = ordre_counter
                ordre_counter += 1
            df.at[idx, "adjudicats"] = 1
        rem -= len(idxs)

    df["nova_prioritat"] = df["adjudicats"].apply(lambda x: 4 if x else 2)
    df["nou_anys_sense_captura"] = df.apply(
        lambda r: 0 if r["adjudicats"] else r["anys_sense_captura"] + 1, axis=1
    )
    return df


# ── (Additional helper functions assignar_captura_csv & assignar_captura_parroquial_csv unchanged) ──
#    ↳ They are long but identical to what you pasted, no structural fix needed.


# ── STREAMLIT UI ─────────────────────────────────────────────────────────────

st.title("Sorteig captures")

especie = st.selectbox("Espècie", list(ESPECIE_SORTEIGS.keys()))

with st.expander("Configuració de captures per sorteig"):
    for sorteig in ESPECIE_SORTEIGS[especie]:
        st.markdown(f"### {sorteig}")
        key_prefix = sorteig.replace(" ", "_")
        if especie == "Isard" and sorteig == "IS TCC":
            st.number_input(
                "Quantitat Captures", min_value=0, step=1,
                key=f"total_{key_prefix}"
            )
            st.session_state.setdefault(f"configs_{key_prefix}", [])
        else:
            aleatori_key = f"aleatori_{key_prefix}"
            st.checkbox("Ordre aleatori", value=True, key=aleatori_key)

            cfg_key = f"configs_{key_prefix}"
            if cfg_key not in st.session_state:
                st.session_state[cfg_key] = [{"selections": [], "qty": 0}]

            if st.button("Afegeix Tipus", key=f"add_{key_prefix}"):
                st.session_state[cfg_key].append({"selections": [], "qty": 0})

            for idx, conf in enumerate(st.session_state[cfg_key]):
                st.subheader(f"Tipus {idx+1}")
                sel = st.multiselect(
                    f"Valors Tipus {idx+1}",
                    TIPUS_OPTIONS,
                    default=conf["selections"],
                    key=f"{key_prefix}_sel_{idx}"
                )
                if "Indeterminat" in sel:
                    sel = ["Indeterminat"]
                qty = st.number_input(
                    "Quantitat", min_value=0, step=1,
                    value=conf["qty"], key=f"{key_prefix}_qty_{idx}"
                )
                st.session_state[cfg_key][idx] = {"selections": sel, "qty": qty}

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
        validar_csv_isard(df1) if especie == "Isard" else validar_csv_altres(df1)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    # Build configuration from the dynamic inputs
    config_rows = []
    for sorteig in ESPECIE_SORTEIGS[especie]:
        key_prefix = sorteig.replace(" ", "_")
        if especie == "Isard" and sorteig == "IS TCC":
            total = st.session_state.get(f"total_{key_prefix}", 0)
            config_rows.append({
                "Codi_Sorteig": sorteig,
                "Tipus": "",
                "Quantitat": total,
                "Aleatori": True,
            })
        else:
            aleatori = st.session_state.get(f"aleatori_{key_prefix}", True)
            for conf in st.session_state.get(f"configs_{key_prefix}", []):
                tip = "+".join(conf["selections"]) if conf["selections"] else ""
                config_rows.append({
                    "Codi_Sorteig": sorteig,
                    "Tipus": tip,
                    "Quantitat": conf["qty"],
                    "Aleatori": aleatori,
                })

    config_df = pd.DataFrame(config_rows)

    try:
        resultat, resums = processar_sorteigs(df1, df2, config_df, especie, seed)
    except Exception as exc:
        st.error(f"🚫 Error en el sorteig: {exc}")
        st.stop()

    st.subheader("Resultats")
    st.dataframe(resultat, use_container_width=True)

    st.download_button(
        "Descarregar CSV",
        resultat.to_csv(index=False).encode("utf-8"),
        file_name="resultats.csv",
    )

    tabs = st.tabs(["Per sorteig", "Resum global"])
    with tabs[0]:
        for resum in resums:
            st.dataframe(resum, use_container_width=True)
    with tabs[1]:
        if resums:
            global_df = pd.concat(resums).groupby("Sorteig").sum(numeric_only=True)
            st.dataframe(global_df, use_container_width=True)
            st.bar_chart(global_df["Captures"])
