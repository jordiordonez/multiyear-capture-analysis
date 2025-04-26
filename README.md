# 📈 Projecte Pla de Caça

## 📂 Estructura del projecte

```plaintext
/project/
│
├── data/                   # Fitxers CSV d'entrada i resultats
│    ├── sorteig.csv         # Fitxer d'entrada inicial generat
│    ├── historial_6_anys.csv# Historial de 6 anys generat per simulacions
│    ├── resultats_any_X.csv # Resultats de cada any
│
├── figures/                 # Figures i gràfics generats
│    ├── escenari_normal/
│    ├── escenari_colles_6/
│    ├── escenari_captures_variables_colles_8/
│    ├── escenari_captures_variables_colles_6/
│
├── reports/                 # Informes PDF generats
│    ├── INFORME_ESCENARI_X.pdf
│    ├── INFORME_FINAL.pdf
│
├── modules/                 # Codi Python modularitzat
│    ├── generador.py         # Generador de dades inicials
│    ├── sorteig.py           # Assignació d'isards
│    ├── simulacio.py         # Simulació multianual
│    └── analisi.py           # Anàlisi gràfica
│
├── main_generador.py         # Crear dades inicials manualment
├── main_simulacio.py         # Simular una única execució
├── main_analisi.py           # Anàlisi i gràfics d'una simulació
├── main_pipeline.py          # Pipeline COMPLET per múltiples escenaris
│
├── requirements.txt          # Dependències del projecte
└── README.md                 # Aquest document


```
## 🚀 Com començar

### Instal·lació d'entorn
Assegura't que tens Python 3.8+ instal·lat.

Instal·la totes les dependències amb:

`pip install -r requirements.txt`

## 📊 Execució Manual

Generar dades inicials:

`python3 main_generador.py`

Simular 6 anys:

`python3 main_simulacio.py`

Generar figures i gràfics:

`python3 main_analisi.py`

## 🛠️ PIPELINE Automàtic de tots els Escenaris

Executa tot el projecte automàticament:

`python3 main_pipeline.py`

Això farà:

🔥 Generar dades diferents per cada escenari.
🏹 Simular 6 anys (captures fixes o variables).
📊 Crear figures (heatmaps i stacked bar charts).
📄 Crear informes PDF per cada escenari.
📑 Combinar tot en un INFORME_FINAL.pdf dins /reports/.

## 📦 Llibreries utilitzades

pandas
numpy
matplotlib
seaborn
fpdf

## 🧠 Notes finals

El codi és 100% modular i extensible.
Suporta escenaris amb variació de captures i variació de mides de colles.
Gestiona correctament les carpetes i fitxers.
Organitza figures i informes per escenari.
Crea un report final únic combinant tots els resultats.