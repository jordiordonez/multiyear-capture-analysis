#!/usr/bin/env python3
# simulate_variable_hunters.py

import os
import pandas as pd
import numpy as np
from modules.simulacio import simular_6_anys_variable

def run_single_simulation(
    initial_csv: str,
    captures_per_year: list,
    seed: int,
    new_hunters_range: tuple,
    retired_hunters_range: tuple,
    output_csv: str
):
    """
    Run one 6-year sim with variable # of new/retiring hunters,
    and save the full history to output_csv.
    """
    df_hist = simular_6_anys_variable(
        initial_csv=initial_csv,
        captures_per_year_list=captures_per_year,
        seed=seed,
        new_hunters_range=new_hunters_range,
        retired_hunters_range=retired_hunters_range
    )
    df_hist.to_csv(output_csv, index=False, sep=';')
    print(f">>> Saved simulation history to {output_csv}")
    return df_hist


def monte_carlo_simulations(
    n_reps: int,
    initial_csv: str,
    captures_per_year: list,
    new_hunters_range: tuple,
    retired_hunters_range: tuple,
    out_folder: str = "mc_results"
):
    """
    Run n_reps independent sims, varying only the RNG seed,
    and collect per‐year total unique hunters.
    """
    os.makedirs(out_folder, exist_ok=True)
    summary_list = []

    for rep in range(1, n_reps + 1):
        seed = 1000 + rep
        out_csv = os.path.join(out_folder, f"history_rep_{rep}.csv")
        df_hist = run_single_simulation(
            initial_csv, captures_per_year, seed,
            new_hunters_range, retired_hunters_range,
            out_csv
        )

        # Summarise: how many unique hunters were present each year?
        agg = (
            df_hist
            .groupby("any")
            .ID
            .nunique()
            .reset_index()
            .rename(columns={"ID": "unique_hunters"})
        )
        agg["replicate"] = rep
        summary_list.append(agg)

    # Concatenate and save
    df_summary = pd.concat(summary_list, ignore_index=True)
    df_summary.to_csv(os.path.join(out_folder, "mc_summary.csv"), index=False)
    print(f">>> Monte Carlo summary saved to {os.path.join(out_folder, 'mc_summary.csv')}")
    return df_summary


if __name__ == "__main__":
    # === USER PARAMETERS ===
    initial_csv = "sorteig.csv"            # your original base file
    captures_per_year = [150, 180, 200, 170, 190, 210]
    # each year between 10 and 30 new hunters join,
    # and between 5 and 15 retire
    new_hunters_range = (10, 30)
    retired_hunters_range = (5, 15)

    # 1) Run a single "demo" sim
    run_single_simulation(
        initial_csv,
        captures_per_year,
        seed=42,
        new_hunters_range=new_hunters_range,
        retired_hunters_range=retired_hunters_range,
        output_csv="historial_variable_hunters.csv"
    )

    # 2) Optionally, run 50 Monte Carlo replicates
    mc_results = monte_carlo_simulations(
        n_reps=50,
        initial_csv=initial_csv,
        captures_per_year=captures_per_year,
        new_hunters_range=new_hunters_range,
        retired_hunters_range=retired_hunters_range,
        out_folder="mc_results"
    )
    
    # Quick inspect of MC summary
    print(mc_results.head())
