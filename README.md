# 🏹 Pla de Caça - Simulació i Anàlisi Multianual de Captures

Simulació de captures d'isards en diversos escenaris de caça controlada, generant informes visuals i analítics de les adjudicacions durant múltiples anys.

## 📂 Estructura del Projecte

```
/pla-de-caca/
│
├── data/             # CSVs d'entrada i resultats (buit inicialment)
├── figures/          # Gràfics generats automàticament
├── informes/         # Informes PDF generats automàticament
├── modules/          # Mòduls Python
│   ├── analisi.py
│   ├── config_escenaris.py
│   ├── generador.py
│   ├── simulacio.py
│   └── sorteig.py
│
├── main_pipeline.py  # Llançar tota la simulació + informes
├── main_generador.py # Generar dades inicials personalitzades
├── main_simulacio.py # Simulació simple
├── main_analisi.py   # Només generar gràfics
├── main_informes.py  # Combinar PDFs
│
├── requirements.txt  # Dependències Python
├── README.md         # Aquest document
│
└── .gitignore        # Excloure carpetes i fitxers no necessaris

````

## 🚀 Com executar el projecte

1. Instal·lació de dependències
Assegura't de tenir Python 3.8 o superior.

    `pip install -r requirements.txt`

2. Simular Escenaris Complets
Executa el pipeline complet:

    `python3 main_pipeline.py`


    Resultats:

    * CSVs a data/
    * Gràfics a figures/NOM_ESCENARI/
    * Informe PDF a informes/NOM_ESCENARI.pdf

## 🧠 Escenaris Definits


#### Escenari	Descripció
* base	Configuració bàsica (colles mínim 8 membres, captures fixes)
* colles_de_6	Simulació amb colles més petites (mínim 6 membres)
* captures_variables	Nombre variable de captures entre 60 i 300 per any
* nous_i_retirats	Incorporació i retirada de caçadors cada any

#### 📊 Què genera el projecte?

* Heatmap de captures consecutives (per ID, Modalitat A/B)
* Gràfic de barres apilades de percentatges de captures per any
* Informe PDF per cada escenari (explicacions + gràfics)
* Unió de tots els informes en un PDF únic


## 🔥 Llibreries utilitzades

    pandas
    numpy
    matplotlib
    seaborn
    PyPDF2
    random


## 🎯 Objectius assolits

* 🧩 Arquitectura modular (generador, simulador, analitzador, informes)
* 🔥 Automatització total del pipeline de simulació
* 📊 Visualització professional de dades
* 🧠 Gestió dinàmica de caçadors: nous ingressos i retirades
* 📦 Preprarat per a ser escalat amb nous escenaris o configuracions
* 📸 Exemples de Gràfics


    * Heatmap	
    * Barres Apilades


## 🧠 Reflexió Final

Aquest projecte ha suposat:

* Treballar la gestió de projectes de dades complexos.
* Aprendre a modularitzar i escalar simulacions realistes.
* Generar informes automàtics a partir d'anàlisis de dades.
* Practicar la creació de pipelines de dades end-to-end.


## 📎 Repositoris Relacionats

...


#### 🌟 Si t'ha agradat aquest projecte, deixa un ⭐ al repositori!
#### 🔗 També pots connectar amb mi a [LinkedIn](https://www.linkedin.com/in/jordi-ordoñez-814614341/)!

