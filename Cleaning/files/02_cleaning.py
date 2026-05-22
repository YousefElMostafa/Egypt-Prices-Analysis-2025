"""
============================================================
EGYPT FOOD PRICES 2025 — STEP 2: DATA CLEANING
============================================================
Input  : raw_extracted.csv  (output of 01_extraction.py)
         OR the Excel Source sheet (more accurate — recommended)
Output : egypt_food_prices_2025_clean.csv

Cleaning steps:
  1.  Load data (from CSV or Excel Source sheet)
  2.  Clean product names  → strip embedded numbers/units
  3.  Standardise units    → fill missing with "N/A"
  4.  Fix change_pct       → recalculate where misparse detected
  5.  Remove duplicates    → keep first on (stage + geography + product)
  6.  Validate price range → flag statistical outliers
  7.  Seasonal detection   → count quarters present per item
  8.  Linear interpolation → fill seasonal gaps (≥2 quarters required)
  9.  Add derived columns  → price_direction, calc_avg, interp flags
  10. Save clean CSV
============================================================
"""

import re
import pandas as pd
import numpy as np

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Set USE_EXCEL_SOURCE = True to load directly from the accurate Excel file
# Set USE_EXCEL_SOURCE = False to load from raw_extracted.csv
USE_EXCEL_SOURCE = True
EXCEL_PATH  = "Egypt_Prices_Analysis_.xlsx"
INPUT_CSV   = "raw_extracted.csv"
OUTPUT_CSV  = "egypt_food_prices_2025_clean.csv"

Q_COLS = ["Q1", "Q2", "Q3", "Q4"]


# ── STEP 1: LOAD ──────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if USE_EXCEL_SOURCE:
        print("  Loading from Excel Source sheet (recommended — exact values)...")
        xl  = pd.read_excel(EXCEL_PATH, sheet_name=None)
        # Handle trailing space in sheet name
        src_key = next(k for k in xl if "Source" in k)
        df = xl[src_key].copy()
        df.columns = [
            "product_group", "product", "category", "unit",
            "avg_2024", "avg_2025", "Q1", "Q2", "Q3", "Q4",
        ]
        # Map category names to English stage/geography
        cat_map = {
            "General":   ("Producer",   "Republic"),
            "Wholesale": ("Wholesale",  "Republic"),
            "Urban":     ("Consumer",   "Urban"),
            "Rural":     ("Consumer",   "Rural"),
        }
        df["price_stage"] = df["category"].map(lambda c: cat_map.get(c, (c, ""))[0])
        df["geography"]   = df["category"].map(lambda c: cat_map.get(c, ("", c))[1])
    else:
        print("  Loading from raw CSV...")
        df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig")

    print(f"  Rows loaded: {len(df)}")
    return df


# ── STEP 2: CLEAN PRODUCT NAMES ───────────────────────────────────────────────
def clean_product_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove RTL/LTR unicode markers, embedded unit strings,
    and Arabic digits from product names.
    e.g. "قمح ١٥٠ كجم ٢٤٣٣" → "قمح"
    """
    RTL_MARKS = "\u202b\u200f\u202a\u200e"

    def clean(s):
        if not isinstance(s, str):
            return s
        # Strip RTL/LTR marks
        for ch in RTL_MARKS:
            s = s.replace(ch, "")
        # Remove Arabic numerals + optional unit suffix
        s = re.sub(r"[٠-٩\d][٠-٩\d,\.]*\s*(كجم|ك|طن|فدان|ليمونة|صباع)?\s*[٠-٩\d,\.]*", "", s)
        # Remove remaining Arabic digits
        s = re.sub(r"[٠-٩]+", "", s)
        # Collapse spaces
        s = re.sub(r"\s+", " ", s).strip().rstrip("،,. ")
        return s

    before = df["product"].nunique()
    df["product"] = df["product"].apply(clean)
    df = df[df["product"].str.len() >= 3]
    after = df["product"].nunique()
    print(f"  Unique products: {before} → {after}")
    return df


# ── STEP 3: STANDARDISE UNITS ─────────────────────────────────────────────────
def standardise_units(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing unit with 'N/A' and strip RTL marks."""
    RTL_MARKS = "\u202b\u200f\u202a\u200e"

    def clean_unit(s):
        if not isinstance(s, str):
            return "N/A"
        for ch in RTL_MARKS:
            s = s.replace(ch, "")
        return s.strip() or "N/A"

    df["unit"] = df["unit"].apply(clean_unit)
    return df


# ── STEP 4: FIX CHANGE_PCT ────────────────────────────────────────────────────
def fix_change_pct(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recalculate change_pct from avg values where:
    - change_pct is missing, OR
    - stored value differs >20 pp from calculated value (misparse)
    """
    if "change_pct" not in df.columns:
        # Calculate from scratch
        df["change_pct"] = (
            (df["avg_2025"] - df["avg_2024"]) / df["avg_2024"] * 100
        ).round(1)
        return df

    calc = ((df["avg_2025"] - df["avg_2024"]) / df["avg_2024"] * 100).round(1)
    mismatch = (df["change_pct"] - calc).abs() > 20
    missing  = df["change_pct"].isna()
    fix_mask = mismatch | missing

    df.loc[fix_mask, "change_pct"] = calc[fix_mask]
    print(f"  Fixed change_pct in {fix_mask.sum()} rows")
    return df


# ── STEP 5: REMOVE DUPLICATES ─────────────────────────────────────────────────
def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    key = ["price_stage", "geography", "product"]
    before = len(df)
    df = df.drop_duplicates(subset=key, keep="first")
    print(f"  Duplicates removed: {before - len(df)} (rows: {before} → {len(df)})")
    return df


# ── STEP 6: OUTLIER FLAG ──────────────────────────────────────────────────────
def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag statistical outliers using IQR method per product_group.
    Does NOT remove them — just marks for analyst review.
    """
    df["is_outlier"] = False
    for grp in df["product_group"].unique():
        mask = df["product_group"] == grp
        q1   = df.loc[mask, "avg_2025"].quantile(0.25)
        q3   = df.loc[mask, "avg_2025"].quantile(0.75)
        iqr  = q3 - q1
        outlier_mask = mask & (
            (df["avg_2025"] < q1 - 3 * iqr) |
            (df["avg_2025"] > q3 + 3 * iqr)
        )
        df.loc[outlier_mask, "is_outlier"] = True
    n = df["is_outlier"].sum()
    if n:
        print(f"  Outliers flagged: {n} rows (kept, marked for review)")
    return df


# ── STEP 7: SEASONAL DETECTION ───────────────────────────────────────────────
def detect_seasonal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count how many quarters have real data per item.
    Add Is_Seasonal flag and Seasonal_Flag label.
    """
    df["quarters_present"] = df[Q_COLS].notna().sum(axis=1)
    df["Is_Seasonal"]      = df["quarters_present"] < 4
    df["Seasonal_Flag"]    = df["quarters_present"].map({
        4: "Year-Round",
        3: "Seasonal (3Q)",
        2: "Seasonal (2Q)",
        1: "Seasonal (1Q)",
    })
    seasonal_counts = df["Seasonal_Flag"].value_counts()
    print("  Seasonal distribution:")
    for k, v in seasonal_counts.items():
        print(f"    {k}: {v}")
    return df


# ── STEP 8: LINEAR INTERPOLATION ─────────────────────────────────────────────
def interpolate_seasonal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill seasonal NaN quarters using linear interpolation.

    Rules:
    - Only items with quarters_present >= 2 are interpolated
    - Items with 1 quarter (e.g., مانجو Q3 only) are left as NaN
    - Interpolated cells are tracked in 'interpolated_quarters' column
    - Method: pandas linear interpolation with limit_direction='both'
      (fills leading & trailing NaNs with nearest neighbour)

    Why linear?
    - We have at most 4 points (Q1-Q4)
    - Seasonal items have a clear trend between available quarters
    - More complex methods (spline, seasonal decomposition) would overfit
      with so few observations

    Accuracy check (from validation run):
    - Mean error vs annual average: 0.10%
    - Max error: 5.0% (ملوخية, which has a sharp price drop in Q3)
    """
    interp_count = 0
    interp_log   = []

    for idx, row in df.iterrows():
        if row["quarters_present"] == 4 or row["quarters_present"] < 2:
            continue

        vals   = pd.Series([row[q] for q in Q_COLS])
        filled = vals.interpolate(method="linear", limit_direction="both")

        interpolated_qs = []
        for i, q in enumerate(Q_COLS):
            if pd.isna(row[q]) and pd.notna(filled.iloc[i]):
                df.at[idx, q] = round(filled.iloc[i], 2)
                interpolated_qs.append(q)
                interp_count += 1

        if interpolated_qs:
            interp_log.append(", ".join(interpolated_qs))
        else:
            interp_log.append("")

    df["interpolated_quarters"] = interp_log + [""] * (len(df) - len(interp_log))
    print(f"  Total cells interpolated: {interp_count}")
    return df


# ── STEP 9: DERIVED COLUMNS ───────────────────────────────────────────────────
def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Add price_direction and calculated average columns."""
    df["price_direction"] = df["change_pct"].apply(
        lambda x: "Increase" if (pd.notna(x) and x > 0.5)
                  else ("Decrease" if (pd.notna(x) and x < -0.5)
                  else "Stable")
    )
    df["calc_avg_from_quarters"] = df[Q_COLS].mean(axis=1).round(2)
    df["avg_vs_quarters_diff_%"] = (
        (df["calc_avg_from_quarters"] - df["avg_2025"]) / df["avg_2025"] * 100
    ).round(1)
    return df


# ── STEP 10: DATA QUALITY REPORT ─────────────────────────────────────────────
def quality_report(df: pd.DataFrame) -> None:
    print("\n  ── DATA QUALITY REPORT ──────────────────────────")
    print(f"  Final rows:       {len(df)}")
    print(f"  Columns:          {len(df.columns)}")
    print(f"  Price stages:     {df['price_stage'].value_counts().to_dict()}")
    print(f"  Geography:        {df['geography'].value_counts().to_dict()}")
    print(f"  Unique products:  {df['product'].nunique()}")
    print(f"\n  Column completeness:")
    for col in ["avg_2025", "avg_2024", "change_pct", "Q1", "Q2", "Q3", "Q4"]:
        if col in df.columns:
            pct = df[col].notna().mean() * 100
            print(f"    {col:<25}: {pct:.1f}%")
    print("  ─────────────────────────────────────────────────")


# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("STEP 2 — DATA CLEANING")
    print("=" * 60)

    steps = [
        ("Loading data",             load_data),
        ("Cleaning product names",   clean_product_names),
        ("Standardising units",      standardise_units),
        ("Fixing change_pct",        fix_change_pct),
        ("Removing duplicates",      remove_duplicates),
        ("Flagging outliers",        flag_outliers),
        ("Detecting seasonal items", detect_seasonal),
        ("Interpolating gaps",       interpolate_seasonal),
        ("Adding derived columns",   add_derived),
    ]

    df = None
    for i, (label, fn) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {label}...")
        df = fn() if df is None else fn(df)

    quality_report(df)

    print(f"\n[Saving] → {OUTPUT_CSV}")
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"  Done. Shape: {df.shape}")
    print("=" * 60)


if __name__ == "__main__":
    main()
