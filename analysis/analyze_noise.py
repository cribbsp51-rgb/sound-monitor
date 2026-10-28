#!/usr/bin/env python3
"""
Noise Pollution Post-Processing — Facebook Infographic Generator.

Usage:
    python analyze_noise.py DATA_DIR [options]

Reads daily sound logs and compiles a single, long PNG infographic report 
containing text metrics, tables, and charts that can be posted straight to Facebook.
"""

from __future__ import annotations
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")  # Headless rendering engine
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
except ImportError as exc:
    print(f"Missing dependency: {exc}\nInstall with: pip install pandas numpy matplotlib", file=sys.stderr)
    sys.exit(1)

DAY_THRESHOLD_DB: float = 65.0
NIGHT_THRESHOLD_DB: float = 55.0

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze noise logs and generate a Facebook PNG report.")
    parser.add_argument("log_dir", metavar="LOG_DIR", type=Path, help="Directory containing your daily CSV logs")
    parser.add_argument("--limit-day", type=float, default=DAY_THRESHOLD_DB, help="Day threshold limit")
    parser.add_argument("--limit-night", type=float, default=NIGHT_THRESHOLD_DB, help="Night threshold limit")
    parser.add_argument("--out", dest="out_dir", type=Path, default=None, help="Output directory")
    return parser.parse_args()

def energetic_mean(db_series: pd.Series) -> float:
    if db_series.empty:
        return 0.0
    return float(10 * np.log10(np.mean(10 ** (db_series.dropna() / 10.0))))

def calculate_percentile(db_series: pd.Series, percentile: int) -> float:
    if db_series.empty:
        return 0.0
    return float(np.percentile(db_series.dropna(), 100 - percentile))

def compile_data(log_dir: Path) -> pd.DataFrame:
    files = sorted(list(log_dir.glob("*.csv")))
    daily_files = [f for f in files if re.search(r"\d{4}-\d{2}-\d{2}", f.name)]
    if not daily_files:
        print(f"No daily sound logs found in {log_dir}", file=sys.stderr)
        sys.exit(1)

    frames = []
    for f in daily_files:
        try:
            df = pd.read_csv(f)
            df.columns = [col.lower() for col in df.columns]
            frames.append(df)
        except Exception:
            pass

    if not frames:
        print("Error: No data chunks could be extracted from files.", file=sys.stderr)
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    ts_col = next((c for c in combined.columns if 'ts' in c or 'time' in c), None)
    db_col = next((c for c in combined.columns if 'spl' in c or 'db' in c), None)

    if not ts_col or not db_col:
        print("Error: CSV files must contain timestamp ('ts') and decibel ('spl') columns.", file=sys.stderr)
        sys.exit(1)

    combined['timestamp'] = pd.to_datetime(combined[ts_col])
    combined['db'] = combined[db_col].astype(float)
    combined['hour'] = combined['timestamp'].dt.hour
    combined['is_night'] = (combined['hour'] < 6) | (combined['hour'] >= 22)
    return combined.sort_values('timestamp').reset_index(drop=True)

# ==============================================================================
# IMAGE GRAPHIC ENGINE (Fixed Text Collision)
# ==============================================================================
def generate_png_report(df: pd.DataFrame, out_dir: Path, day_lim: float, night_lim: float) -> Path:
    max_date = df['timestamp'].max().strftime('%Y-%m-%d')
    min_date = df['timestamp'].min().strftime('%Y-%m-%d')
    
    laeq_all = energetic_mean(df['db'])
    l90_floor = calculate_percentile(df['db'], 90)
    l10_spike = calculate_percentile(df['db'], 10)
    l1_peak = calculate_percentile(df['db'], 1)

    day_df = df[~df['is_night']]
    night_df = df[df['is_night']]
    laeq_day = energetic_mean(day_df['db'])
    laeq_night = energetic_mean(night_df['db'])

    fig = plt.figure(figsize=(10, 14), facecolor='#f7f9fa')
    
    # 1. Header Banner
    fig.text(0.5, 0.95, "COMMUNITY NOISE POLLUTION REPORT", fontsize=18, color='#1e3c72', weight='bold', ha='center')
    fig.text(0.5, 0.93, f"Civic Advocacy Monitoring Array: {min_date} to {max_date}", fontsize=11, color='#555', style='italic', ha='center')
    
    # 2. Key Metric Cards
    metrics = [
        ("$L_{Aeq}$ Avg\nEnergy", f"{laeq_all:.1f} dB", '#1e3c72'),
        ("$L_{90}$ Base\nAmbient", f"{l90_floor:.1f} dB", '#2ca02c'),
        ("$L_{10}$ Traffic\nSpikes", f"{l10_spike:.1f} dB", '#d62728'),
        ("$L_{1}$ Max\nCeiling", f"{l1_peak:.1f} dB", '#d62728')
    ]
    
    for i, (label, val, col) in enumerate(metrics):
        x_pos = 0.12 + (i * 0.21)
        fig.text(x_pos + 0.08, 0.87, val, fontsize=20, weight='bold', color=col, ha='center')
        fig.text(x_pos + 0.08, 0.84, label, fontsize=9, color='#444', ha='center')
        fig.patches.append(plt.Rectangle((x_pos, 0.83), 0.17, 0.07, transform=fig.transFigure, fill=False, color='#ccc', lw=0.8))

    # 3. Time-of-Day Blocks
    tod_metrics = [
        ("Daytime $L_{day}$\n(06:00 - 22:00)", f"{laeq_day:.1f} dBA", '#2ca02c' if laeq_day<=day_lim else '#d62728'),
        ("Nighttime $L_{night}$\n(22:00 - 06:00)", f"{laeq_night:.1f} dBA", '#2ca02c' if laeq_night<=night_lim else '#d62728')
    ]
    for i, (label, val, col) in enumerate(tod_metrics):
        x_pos = 0.15 + (i * 0.40)
        fig.text(x_pos + 0.15, 0.77, val, fontsize=22, weight='bold', color=col, ha='center')
        fig.text(x_pos + 0.15, 0.74, label, fontsize=10, color='#333', ha='center', weight='bold')
        fig.patches.append(plt.Rectangle((x_pos, 0.73), 0.30, 0.07, transform=fig.transFigure, fill=True, facecolor='#fff', edgecolor='#bbb', lw=0.8))

    # 4. Hourly Bar Chart Subplot
    ax = fig.add_axes([0.1, 0.38, 0.8, 0.28])
    hourly_means = df.groupby('hour')['db'].apply(energetic_mean).reindex(range(24), fill_value=0.0)
    bar_colors = ['#1f77b4' if not (h < 6 or h >= 22) else '#d62728' for h in range(24)]
    
    bars = ax.bar(hourly_means.index, hourly_means.values, color=bar_colors, alpha=0.85, edgecolor='black', linewidth=0.5)
    ax.axhline(day_lim, color='#2ca02c', linestyle='--', alpha=0.8, label=f'Day Ordinance Cap ({int(day_lim)} dB)')
    ax.axhline(night_lim, color='#d62728', linestyle=':', alpha=0.8, label=f'Night Sleep Cap ({int(night_lim)} dB)')
    
    ax.set_title("Logarithmic Hourly Sound Distribution Grid", fontsize=11, weight='bold', color='#1e3c72')
    ax.set_ylabel("Sound Pressure Level (dBA)", fontsize=9)
    ax.set_xlabel("24-Hour Timeline Mode Index", fontsize=9)
    ax.set_xlim(-0.5, 23.5)
    ax.set_xticks(range(24))
    ax.grid(axis='y', linestyle=':', alpha=0.5)
    ax.legend(loc='lower left', fontsize=8, framealpha=0.9)
    
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2., h + 1, f'{int(h)}', ha='center', va='bottom', fontsize=7)

    # 5. Table Layout Footer (✅ FIX: Row Elements Separated to Stop Overwriting)
    fig.text(0.1, 0.32, "EXECUTIVE ANALYSIS REFERENCE TABLE", fontsize=11, weight='bold', color='#1e3c72')
    
    table_data = [
        ["Acoustic Context Window", "Measured Value", "Ordinance Limit", "Status Assessment"],
        ["Daytime Average (Lday)", f"{laeq_day:.1f} dBA", f"< {int(day_lim)} dBA", "EXCEEDED" if laeq_day > day_lim else "COMPLIANT"],
        ["Nighttime Average (Lnight)", f"{laeq_night:.1f} dBA", f"< {int(night_lim)} dBA", "EXCEEDED" if laeq_night > night_lim else "COMPLIANT"],
        ["Ambient Baseline (L90)", f"{l90_floor:.1f} dBA", "45-50 dBA Typ.", "Constant Noise Floor"],
        ["Peak Impact Level (L1)", f"{l1_peak:.1f} dBA", "Transient Spikes", "Isolates Loud Pass-bys"]
    ]
    
    y_start = 0.27
    for row_idx, row in enumerate(table_data):
        y_pos = y_start - (row_idx * 0.035)
        bg_col = '#edf2f7' if row_idx == 0 else '#fff'
        weight = 'bold' if row_idx == 0 else 'normal'
        
        # Row backgrounds
        fig.patches.append(plt.Rectangle((0.1, y_pos - 0.01), 0.8, 0.032, transform=fig.transFigure, fill=True, facecolor=bg_col, edgecolor='#edf2f7', lw=0.5))
        
        # ✅ FIX: Map index positions (row[0], row[1], row[2], row[3]) explicitly to decouple cells
        fig.text(0.12, y_pos, row[0], fontsize=9, weight=weight)
        fig.text(0.42, y_pos, row[1], fontsize=9, weight=weight)
        fig.text(0.58, y_pos, row[2], fontsize=9, weight=weight)
        
        status_col = '#d62728' if "EXCEEDED" in row[3] else ('#2ca02c' if "COMPLIANT" in row[3] else '#333')
        fig.text(0.76, y_pos, row[3], fontsize=9, weight='bold', color=status_col)

    fig.text(0.5, 0.04, f"Generated automatically from 1.0Hz acoustic monitoring array logs. Total records analyzed: {len(df)}.", fontsize=8, color='#888', ha='center')

    out_dir.mkdir(parents=True, exist_ok=True)
    report_img_path = out_dir / f"facebook_noise_report_{max_date}.png"
    plt.savefig(report_img_path, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    return report_img_path

def main() -> None:
    args = _parse_args()
    print("Loading split daily CSV log array...")
    df = compile_data(args.log_dir)
    out_dir = args.out_dir if args.out_dir else args.log_dir / "reports"
    print("Processing decibel parameters and generating high-res PNG Infographic...")
    infographic_file = generate_png_report(df, out_dir, args.limit_day, args.limit_night)
    print(f"\n🎉 Done! Facebook-Ready PNG saved to:\n👉 {infographic_file.resolve()}")

if __name__ == "__main__":
    main()
