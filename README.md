
# 🏹 Hunting Plan – Multiyear Simulation and Capture Analysis

Simulation of isard captures across various controlled hunting scenarios, generating visual and analytical reports of allocations over multiple years.

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## 📂 Project Structure

```
/hunting-plan/
│
├── data/             # Input CSVs and results (initially empty)
├── figures/          # Automatically generated graphs
├── reports/          # Automatically generated Markdown reports
├── modules/          # Python modules
│   ├── analisi.py
│   ├── config_escenaris.py
│   ├── generador.py
│   ├── simulacio.py
│   ├── simulacio_estrategics.py
│   └── sorteig.py
│
├── main_pipeline.py  # Run the complete simulation + reports
├── main_generador.py # Generate custom initial data
├── main_analysis.py  # Generate graphs only
├── app_sorteig.py
│
├── requirements.txt  # Python dependencies
├── README.md         # This document
│
└── .gitignore        # Exclude unnecessary folders and files
```

## 🚀 How to Run the Project

### 1. Install Dependencies
Make sure you have Python 3.8 or higher installed.

```bash
pip install -r requirements.txt
```

### 2. Run Full Scenario Simulations
Execute the full pipeline:

```bash
python3 main_pipeline.py
```

### Outputs:
- CSV files saved in `data/`
- Graphs saved in `figures/SCENARIO_NAME/`
- Markdown reports saved individually in `reports/`
- Final combined Markdown report created at `reports/final_report.md`

## 🧐 Defined Scenarios

| Scenario | Description |
|:---------|:------------|
| `base` | Minimum 8 per colla, fixed captures, no entrants ni sortints |
| `colles_de_6` | Minimum 6 per colla, captures fixes |
| `captures_variables` | Variable number of captures between 60 and 300 per year |
| `nous_i_retirats` | Hunters joining and leaving (between 10 and 100 per year) |

## 📊 What This Project Generates

- Heatmap of consecutive captures (by ID, Mode A/B)
- Stacked bar charts showing capture percentages by year
- Detailed Markdown report for each scenario
- Final combined Markdown report for easier comparison

## 🔥 Libraries Used

- `pandas`
- `numpy`
- `matplotlib`
- `seaborn`
- `PyPDF2`
- `random`
- `pandoc` (optional, if you later want to convert Markdown to PDF)

## 🎯 Achieved Goals

- 🧹 Modular architecture (generator, simulator, analyzer, reports)
- 🔥 Full automation of the simulation pipeline
- 📊 Professional-quality data visualizations
- 🧠 Dynamic hunter management: entries and retirements
- 📦 Ready for scaling with new scenarios and configurations
- 📸 Sample Graphs: Heatmaps and Stacked Bar Charts

## 🛠️ Additional Modules

    /modules/simulacio_estrategics.py

This module simulates strategic behavior among hunters over multiple years.
It explores how coordination strategies (e.g., grouping past winners together) can influence the capture allocation results over time.
It simulates:
* A set of strategic hunters who reorganize themselves every year into new collas.
* The condition that only past winners can form new strategic groups.
* The evolution of their success compared to normal (non-strategic) hunters.

**Simulation Features:**
* Dynamic annual regrouping based on last year’s capture success.
* Measurement of the cumulative advantage of strategic behavior.
* Comparison against the baseline (non-strategic random grouping).

**Key Purpose:**
To evaluate whether collaborative strategies can systematically improve a hunter’s odds of securing captures in a fair allocation system.

# 🖥️ App Sorteig

This is a standalone **Streamlit** application for real-world allocation of captures based on hunter registrations.

## Main Features

1. **Species & Management Unit Selection**  
   - Choose an **Espècie** (`Isard`, `Cabirol`, `Mufló`).  
   - Choose a **Unitat de gestió** (e.g. `TCC`, `VC Enclar`, etc.).

2. **Upload Hunters CSV**  
   - The CSV must include at least these columns:  
     `ID`, `Prioritat`, `anys_sense_captura`, `Resultat_sorteigs_mateixa_sps`.

3. **Capture Configuration**  
   - **For Isard + TCC**: enter the **total number of captures**.  
   - **For all other combinations**: add one or more **Capture Types** (e.g. `Femella`, `Mascle`, `Adult`, or combinations like `Femella+Trofeu`) and specify the **number of captures** for each.

4. **Optional Random Seed**  
   - Provide a seed (`Llavor opcional`) to reproduce the same draw.

5. **Execute the Draw**  
   - Click **“Executar sorteig”** to run the allocation algorithm.

6. **Results & Download**  
   - The table displays:  
     - **Global** `adjudicats` column (total captures assigned per hunter)  
     - **Per-type** columns (`Adjudicats_Tipus1_<values>`, `Adjudicats_Tipus2_<values>`, …)  
     - Updated `nova_prioritat` and `nou_anys_sense_captura`  
   - Download a new CSV with these results.

---

## Algorithm Summary

- **Ordering**: first by `Prioritat`, then by total past captures (`adjudicats + Resultat_sorteigs_mateixa_sps`).
- **Sequential Assignment**: for each Capture Type in the order defined, assign exactly the specified number of slots.
- **Tie-breaking**: when multiple hunters share the same allocation count, ties are broken randomly (but reproducibly if a seed is set).
- **Priority Update**: hunters who harvest a female in the current draw retain top priority for the following season.  

Key Purpose:
Transforms the simulated logic into a usable web application for practical management of real capture processes.
Deployment:
The application is currently hosted via Streamlit Community Cloud 🔗 [Visit App.](https://multiyear-capture-analysis-hfn76hzqpwmup5xamhgaeq.streamlit.app)

And here is the final version fully adapting 2025 Regulatory Governamental Rules in ANDORRA 🔗 [Visit App.](https://sorteigfauna.streamlit.app) from the github repository [sorteig_fauna](https://github.com/jordiordonez/sorteig_fauna)


## 🧐 Final Reflection

This project allowed me to:

- Manage complex data-oriented projects.
- Learn how to modularize and scale realistic simulations.
- Automate generation of analytical reports.
- Practice building end-to-end data pipelines.
- Create a Streamlit app to allow users to allocate captures.

## 📌 Related Repositories

(coming soon...)

---

#### 🌟 If you enjoyed this project, please leave a ⭐ star on the repository!
#### 🔗 Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/jordi-ordoñez-814614341/)!
