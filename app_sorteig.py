import streamlit as st
import pandas as pd
import numpy as np
import math
import unicodedata
import re

# Mapa de codis oficials
CODI_PARROQUIES = {
    1: "Canillo",
    2: "Encamp",
    3: "Ordino",
    4: "La Massana",
    5: "Andorra la Vella",
    6: "Sant Julià de Lòria",
    7: "Escaldes-Engordany"
}

# Expressió simplificada per identificació flexible
MATCH_PARROQUIES = {
    "CAN": "Canillo",
    "ENC": "Encamp",
    "ORD": "Ordino",
    "MAS": "La Massana",
    "LM": "La Massana",
    "ALV": "Andorra la Vella",  # o només "AND"
    "AND": "Andorra la Vella",
    "SJ": "Sant Julià de Lòria",
    "SJL": "Sant Julià de Lòria",
    "JULIA": "Sant Julià de Lòria",
    "SAN": "Sant Julià de Lòria",
    "ESC": "Escaldes-Engordany",
    "CALDES": "Escaldes-Engordany"
}

def normalitza_parroquia(valor):
    if not isinstance(valor, str):
        valor = str(valor)
    valor = valor.strip()
    if pd.isnull(valor):
        return None
    try:
        num = int(str(valor).strip())
        return CODI_PARROQUIES.get(num, None)
    except ValueError:
        pass
    txt = str(valor).lower()
    txt = unicodedata.normalize("NFD", txt)
    txt = txt.encode("ascii", "ignore").decode("utf-8")
    txt = re.sub(r"[^a-z]", "", txt)

    for clau, nom in MATCH_PARROQUIES.items():
        if clau.lower() in txt:
            return nom
    return None  # Valor no reconegut

# Percentatges de captures reservades per parròquia en vedats
VEDAT_PARRÒQUIES = {
    "VC Enclar": {
        "La Massana": 0.234,
        "Sant Julià de Lòria": 0.241,
        "Andorra la Vella": 0.522,
        "Escaldes-Engordany": 0.003
    },
    "VC Ransol Sorteny": {  # Ransol-Sorteny
        "Canillo": 0.5,
        "Ordino": 0.5,
    },
    "VC Xixerella": {"La Massana": 1.0},
    "VT Escaldes-Engordany": {"Escaldes-Engordany": 1.0},
}


# Funció per al sorteig amb colles (lògica existent)
def assignar_isards_sorteig_csv(
    df: pd.DataFrame, total_captures: int, seed: int = None
) -> pd.DataFrame:
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
    # Assign dins colles
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
    # Assign individus B
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
        lambda r: 0 if r["adjudicats"] > 0 else r["anys_sense_captura"] + 1, axis=1
    )
    return df


# Funció per al sorteig individual (sense colles)
def assignar_captura_csv(
    df: pd.DataFrame, tipus_captures: list, quantitats: dict, seed: int = None
) -> pd.DataFrame:
    required = {
        "ID",
        "Prioritat",
        "anys_sense_captura",
        "Resultat_sorteigs_mateixa_sps",
    }
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")
    df = df.copy()
    df["Adjudicats"] = 0
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()
    # Creem columnes individuals per cada Tipus\
    for i, tipus in enumerate(tipus_captures, start=1):
        safe = tipus.replace("+", "_")
        col_name = f"Adjudicats_Tipus{i}_{safe}"
        df[col_name] = 0
    # Assignació per tipus en ordre
    for i, tipus in enumerate(tipus_captures, start=1):
        target = quantitats.get(tipus, 0)
        assigned = 0
        safe = tipus.replace("+", "_")
        col_name = f"Adjudicats_Tipus{i}_{safe}"
        while assigned < target:
            df["Adjudicats_acumulats"] = (
                df["Adjudicats"] + df["Resultat_sorteigs_mateixa_sps"]
            )
            min_acc = df["Adjudicats_acumulats"].min()
            # Filtrar candidats amb captures assignades mínimes ja que són prioritaris
            candidates = df[df["Adjudicats_acumulats"] == min_acc].copy()
            candidates["rand"] = rng.random(size=len(candidates))
            # Mentre hi han candidts sense captures assignades en cap dels sortejos
            # se'ls assigna per prioritat i aleatoriament després.
            if min_acc == 0:
                ordered = candidates.sort_values(
                    by=["Prioritat", "rand"], ascending=[True, True]
                )
            # Si tots tenen com a mínim una captura assignada,
            # s'assigna aleatoriament, tots estan a la mateixa prioritat.
            else:
                ordered = candidates.sort_values(by=["rand"])
            idx = ordered.index[0]
            df.at[idx, "Adjudicats"] += 1
            df.at[idx, col_name] += 1
            assigned += 1
    df["Nou_Resultat_sorteigs_mateixa_sps"] = (
        df["Resultat_sorteigs_mateixa_sps"] + df["Adjudicats"]
    )
    # Calcular nova prioritat i anys sense captura
    df["nova_prioritat"] = df.apply(
        lambda row: 4 if row["Adjudicats_acumulats"] > 0 else row["Prioritat"],
        axis=1
    )
    df["nova_prioritat Any següent"] = df["Adjudicats_acumulats"].apply(lambda x: 4 if x > 0 else 2)
    df["nou_anys_sense_captura"] = df.apply(
        lambda r: 0 if r["Adjudicats_acumulats"] > 0 else r["anys_sense_captura"] + 1, axis=1
    )
    if "Adjudicats_acumulats" in df.columns:
        df.drop(columns=["Adjudicats_acumulats"], inplace=True)
    return df


# Sorteig amb possibles prioritats parroquials per a vedats
def assignar_captura_parroquial_csv(
    df: pd.DataFrame,
    tipus_captures: list,
    quantitats: dict,
    unitat: str,
    seed: int = None,
) -> pd.DataFrame:
    required = {
        "ID",
        "Prioritat",
        "anys_sense_captura",
        "Resultat_sorteigs_mateixa_sps",
    }
    if not required.issubset(df.columns):
        missing = required - set(df.columns)
        raise ValueError(f"Falten columnes: {missing}")
    if "Parroquia" in df.columns:
        df["Parroquia_Normalitzada"] = df["Parroquia"].apply(normalitza_parroquia)
        errors = df[df["Parroquia_Normalitzada"].isnull()]
        if not errors.empty:
            st.error(
                "⚠️ Hi ha valors de 'Parroquia' no reconeguts. Si us plau, reviseu aquestes files:"
            )
            st.dataframe(errors[["ID", "Parroquia"]])
            st.markdown(
                "💡 Utilitzeu els codis oficials de parròquia (1=Canillo, 2=Encamp, ..., 7=Escaldes)."
            )
            st.stop()
    df["Parroquia"] = df["Parroquia_Normalitzada"]
    df.drop(columns=["Parroquia_Normalitzada"], inplace=True)

    if unitat.startswith("V") and "Parroquia" not in df.columns:
        raise ValueError("El CSV ha d'incloure la columna 'Parroquia' per aquest vedat")

    df = df.copy()
    df["Adjudicats"] = 0

    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()

    # Configuració de quotes parroquials
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
            df["Adjudicats_acumulats"] = (
                df["Adjudicats"] + df["Resultat_sorteigs_mateixa_sps"]
            )
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

    df["Nou_Resultat_sorteigs_mateixa_sps"] = (
        df["Resultat_sorteigs_mateixa_sps"] + df["Adjudicats"]
    )
   # Calcular nova prioritat i anys sense captura
    df["nova_prioritat"] = df.apply(
        lambda row: 4 if row["Adjudicats_acumulats"] > 0 else row["Prioritat"],
        axis=1
    )
    df["nova_prioritat Any següent"] = df["Adjudicats_acumulats"].apply(lambda x: 4 if x > 0 else 2)
    df["nou_anys_sense_captura"] = df.apply(
        lambda r: 0 if r["Adjudicats_acumulats"] > 0 else r["anys_sense_captura"] + 1, axis=1
    )
    if "Adjudicats_acumulats" in df.columns:
        df.drop(columns=["Adjudicats_acumulats"], inplace=True)
    return df


# Streamlit UI
st.title("App Sorteig Pla de Caça")
# Instruccions d'ús en català
with st.expander("Instruccions d'ús"):
    st.markdown(
        """
        1. Seleccioneu l'espècie i la unitat de gestió.
        2. Pugeu el fitxer CSV de sol·licitants.
        3. Si no és Isard + TCC, afegiu un o més Tipus de captura en l'ordre que es sortejaran:
           - Clic a "Afegeix Tipus"
           - seleccioneu un o diversos valors
           - indiqueu el nombre de captures.
        4. Opcional: introduïu una llavor per reproduir el mateix sorteig.
        5. Feu clic a "Executar sorteig" per veure els resultats i descarregar el CSV.
        """
    )

with st.expander("Cas `Isard` amb `TCC`"):
    st.markdown(
        """
        El fitxer CSV ha de contenir les següents columnes:
        | Columna | Descripció |
        |----------------------------------|--------------------------------------------|
        | `ID` | Identificador únic del caçador |
        | `Modalitat` | Modalitat d'inscripció (`A` = colla, `B` = individual) |
        | `Colla_ID` | Identificador de la colla |
        | `Prioritat` | Prioritat actual del caçador (nombre enter: 1 = màxima) |
        | `anys_sense_captura` | Anys consecutius sense captura (nombre enter) |
        """
    )

with st.expander("Altres espècies / unitats de gestió"):
    st.markdown(
        """
        A més de les columnes anteriors, cal una columna per cada **tipus de captura disponible** amb el nombre de captures que es vol assignar. Si la unitat triada és un vedat (comença per `V`), el CSV ha d'incloure també la columna `Parroquia`.

        La configuració dels tipus de captura es fa a l'apartat següent de l'aplicació. Exemple:

        | Columna | Exemple de valor |
        |----------------------------------|------------------|
        | `ID` | Identificador únic del caçador |
        | `Prioritat` | Prioritat actual del caçador (nombre enter: 1 = màxima) |
        | `anys_sense_captura` | Anys consecutius sense captura (nombre enter) |
        | `Resultat_sorteigs_mateixa_sps` | Resultat acumulat de captures de la mateixa espècie en any en curs |
        | `Parroquia` | Si es tracta d'un Vedat |
        """
    )

with st.expander("Nota sobre les quotes parroquials en vedats"):
    st.markdown(
        """
        Quan es defineixen diversos tipus de captura per a un mateix vedat (per exemple, “Femella” i “Mascle+Trofeu”), la reserva del 50% de captures per a les parròquies s'aplica sobre la suma total de captures definides per al sorteig. Aquest percentatge es reparteix entre les parròquies afectades segons el percentatge establert per vedat.

        ⚠️ Aquest 50% no és obligatòriament assolit. L'assignació de captures dins aquesta quota segueix les prioritats individuals dels caçadors. La condició per donar preferència a un caçador de la parròquia és:
        - Que tingui la mateixa prioritat individual que altres sol·licitants.
        - Que la seva parròquia no hagi assolit encara el percentatge corresponent dins del 50%.

        Un cop es compleixen aquestes dues condicions, el sistema prioritza els caçadors locals fins a exhaurir la quota. Un cop superada, totes les captures es reparteixen exclusivament per prioritat individual.
        """
    )

with st.expander("Parròquies"):
    st.markdown(
        """
        | Codi | Parròquia              |
        |------|------------------------|
        | 1    | Canillo                |
        | 2    | Encamp                 |
        | 3    | Ordino                 |
        | 4    | La Massana             |
        | 5    | Andorra la Vella       |
        | 6    | Sant Julià de Lòria    |
        | 7    | Escaldes-Engordany     |

        Si el nom està escrit de manera alternativa (majúscules, minúscules, abreviatures com `SJ`, `ESCALDES`, etc.), també serà reconegut automàticament, però **es recomana el format numèric** per garantir la màxima fiabilitat.
        """
    )

with st.expander("Columnes del fitxer de resultats"):
    st.markdown(
        """
        El CSV resultants inclou:
        - `Adjudicats`: nombre total de captures assignades al caçador.
        - Columnes `Adjudicats_TipusX_<nom>` per a cada tipus de captura.
        - `Nou_Resultat_sorteigs_mateixa_sps`: suma acumulada de captures d'aquesta espècie.
        - `nova_prioritat`: prioritat a utilitzar si es repeteix sorteig de la mateixa espècie durant l'any actual.
        - `nova_prioritat Any següent`: prioritat que es tindrà en compte per a la temporada següent.

        Si cal fer un altre sorteig de la mateixa espècie en el mateix any, torneu a carregar el CSV generat i substituïu `Prioritat` per `nova_prioritat` i `Resultat_sorteigs_mateixa_sps` per `Nou_Resultat_sorteigs_mateixa_sps`. A l'inici de cada temporada s'hauran d'actualitzar manualment els caçadors de prioritat 1 segons si havien abatut una femella l'any anterior.
        """
    )

st.markdown("💡 Pots descarregar exemples de fitxers aquí:")

with open("exemple1.csv", "rb") as f1:
    st.download_button(
        label="📥 Exemple Isard TCC (exemple1.csv)",
        data=f1,
        file_name="exemple1.csv",
        mime="text/csv",
    )

with open("exemple2.csv", "rb") as f2:
    st.download_button(
        label="📥 Exemple altres espècies/unitats (exemple2.csv)",
        data=f2,
        file_name="exemple2.csv",
        mime="text/csv",
    )


# 1. Selecció inicial
especie = st.selectbox("Espècie:", ["Isard", "Cabirol", "Mufló"])
unidad = st.selectbox(
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

if unidad.startswith("V"):
    info = VEDAT_PARRÒQUIES.get(unidad, {})
    if info:
        st.subheader("📍 Repartiment parroquial (50% prioritzat en cas de mateixa prioritat individual)")
        # Mostra percentatges sobre el 50%
        data = []
        for p, pct in info.items():
            percent_50 = round(pct * 50, 2)
            data.append({"Parròquia": p, "% del total de captures prioritzat per la Parròquia": percent_50})
        df_info = pd.DataFrame(data)
        st.dataframe(df_info)
        st.markdown("_Aquest és el repartiment previst de captures reservades per parròquia si s’esgotés el 50%._")


# 3. Carrega CSV i vista prèvia
df = None
file = st.file_uploader("CSV sol·licitants", type="csv")
if file:
    df = pd.read_csv(file, sep=";")
    st.subheader("Previsualització de sol·licitants")
    st.dataframe(df)

# 4. Configuració de Tipus de captura dinàmica
options = [
    "Femella",
    "Mascle",
    "Adult",
    "Juvenil",
    "Trofeu",
    "Selectiu",
    "Indeterminat",
]
# Si Isard+TTC, demanar total captures
tipus_captures = []
quantitats = {}
if especie == "Isard" and unidad == "TCC":
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
            options,
            key=f"sel_{idx}",
        )
        if "Indeterminat" in sel:
            sel = ["Indeterminat"]
        qty = st.number_input(
            f"Nº captures per Tipus {idx+1}:", min_value=1, step=1, key=f"qty_{idx}"
        )
        st.session_state["configs"][idx]["selections"] = sel
        st.session_state["configs"][idx]["qty"] = qty
        # Preparar llistes\
        val = sel[0] if len(sel) == 1 else "+".join(sel)
        tipus_captures.append(val)
        quantitats[val] = qty

# 2. Semilla opcional
seed = st.number_input(
    "Llavor opcional (Nombre enter):", min_value=0, step=1, format="%d"
)
seed = None if seed == 0 else seed

# 5. Executar sorteig
if st.button("Executar sorteig"):
    if df is None:
        st.warning("Cal pujar un CSV abans d'executar el sorteig.")
    else:
        tipus_captures = []
        quantitats = {}
        if especie == "Isard" and unidad == "TCC":
            if total_cap is None:
                st.warning("Cal especificar el nombre de captures.")
                st.stop()
            try:
                result = assignar_isards_sorteig_csv(df, total_cap, seed)
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
                result = assignar_captura_parroquial_csv(
                    df, tipus_captures, quantitats, unidad, seed
                )
            except ValueError as e:
                st.error(str(e))
                st.stop()
            st.info("L'any següent, prioritat 1 als qui hagin abatut femella.")
        st.subheader("Resultats del sorteig")
        st.dataframe(result)
        # Mostrar resum per parròquia si és un vedat
        if unidad.startswith("V") and "Parroquia" in result.columns:
            st.subheader("📊 Resum per parròquia")
            adj_per_parr = result.groupby("Parroquia")["Adjudicats"].sum().reset_index()
            adj_per_parr["% del total"] = (
                adj_per_parr["Adjudicats"] / adj_per_parr["Adjudicats"].sum() * 100
            ).round(1)
            st.dataframe(adj_per_parr)

            st.markdown(
                "_Aquest resum mostra quantes captures s'han assignat a cada parròquia entre totes les modalitats._"
            )

        st.download_button(
            "Descarregar CSV",
            result.to_csv(index=False),
            file_name=f"sorteig_{especie}_{unidad}.csv",
        )
else:
    if df is None:
        st.info("Puja un CSV per iniciar el sorteig.")
    else:
        if not (especie == "Isard" and unidad == "TCC"):
            if st.session_state.get("configs") is None:
                st.info("Configura els Tipus i quantitats abans d'executar.")
