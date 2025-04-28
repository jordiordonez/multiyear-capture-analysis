
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
│   └── sorteig.py
│
├── main_pipeline.py  # Run the complete simulation + reports
├── main_generador.py # Generate custom initial data
├── main_analysis.py  # Generate graphs only
├── main_reports.py   # Merge Markdown reports
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

## 🧐 Final Reflection

This project allowed me to:

- Manage complex data-oriented projects.
- Learn how to modularize and scale realistic simulations.
- Automate generation of analytical reports.
- Practice building end-to-end data pipelines.

## 📌 Related Repositories

(coming soon...)

---

#### 🌟 If you enjoyed this project, please leave a ⭐ star on the repository!
#### 🔗 Feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/jordi-ordoñez-814614341/)!
