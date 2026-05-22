"""
============================================================
EGYPT FOOD PRICES 2025 — STEP 1: DATA EXTRACTION
============================================================
Source : CAPMAS Annual Bulletin (PDF/ZIP)
Input  : أسعار_المواد_والمنتجات_الغذائية_والخدمات___2025_1166.pdf
Output : raw_extracted.csv

What this script does:
  1. Unzips the PDF (it's actually a ZIP of images + text pages)
  2. Reads each text page
  3. Parses all 4 table types:
       - Table 1  : Producer prices    (quarterly, republic-level)
       - Table 2  : Wholesale prices   (quarterly, republic-level)
       - Table 3  : Consumer prices    (monthly → converted to quarterly avg)
       - Table 4  : Rural prices       (monthly → converted to quarterly avg)
  4. Converts Arabic-Eastern numerals → Western
  5. Handles parenthesised negatives e.g. (٣٣,٩) → -33.9
  6. Saves combined raw CSV
============================================================
"""

import re
import os
import zipfile
import tempfile
import pandas as pd
import numpy as np

# ── CONFIG ────────────────────────────────────────────────────────────────────
PDF_PATH   = "أسعار_المواد_والمنتجات_الغذائية_والخدمات___2025_1166.pdf"
OUTPUT_CSV = "raw_extracted.csv"
EXTRACT_DIR = tempfile.mkdtemp()

# ── 1. ARABIC NUMERAL CONVERSION ─────────────────────────────────────────────
AR2EN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def ar2en(text: str) -> str:
    """Convert Arabic-Eastern digits to Western digits."""
    return text.translate(AR2EN)

def parse_num(val: str) -> float | None:
    """
    Parse an Arabic number string to float.
    Handles:
      - Arabic-Eastern digits  : ٢٤٣٣,٣٣  → 2433.33
      - Parenthesised negatives: (٣٣,٩)   → -33.9
      - Missing values         : ...       → None
    """
    val = str(val).strip()
    if not val or val in ["...", "---", "ـ", "", "nan", "None"]:
        return None
    val = ar2en(val)
    negative = val.startswith("(") and val.endswith(")")
    if negative:
        val = val[1:-1]
    val = val.replace(",", ".")
    try:
        n = float(val)
        return -n if negative else n
    except ValueError:
        return None


# ── 2. UNZIP & READ PAGES ────────────────────────────────────────────────────
def load_pages(pdf_path: str, extract_dir: str) -> dict[int, str]:
    """Unzip the PDF (which is a ZIP) and read all .txt pages."""
    with zipfile.ZipFile(pdf_path, "r") as z:
        z.extractall(extract_dir)

    pages = {}
    for fname in os.listdir(extract_dir):
        if fname.endswith(".txt"):
            page_num = int(fname.replace(".txt", ""))
            with open(os.path.join(extract_dir, fname), encoding="utf-8") as f:
                pages[page_num] = f.read()
    print(f"  Loaded {len(pages)} text pages")
    return pages


# ── 3. CATEGORY KEYWORDS ─────────────────────────────────────────────────────
CATEGORIES = [
    "المحاصيل الحقلية", "الحبوب الزيتية",
    "الخضر والفاكهه الطازجةوالمجففة", "الخضر والفاكهة", "الخضر والفاكهه",
    "اللحوم المحليه بالعظم", "اللحوم المحلية",
    "الديوك والطيور الحية والبيض", "الطيور الحية والمجمدة والبيض",
    "الاسماك الطازجة والمجمدة والمملحة", "الاسماك",
    "الالبان ومنتجاتها", "الالبان",
    "الزيوت", "البقالة والعطارة", "البقالة",
    "الحبوب والبقول", "السكر والمنتجات السكرية",
    "المنتجات المصنعة", "اللحوم المصنعة",
    "المشروبات", "التوابل والبهارات", "السمن والزيوت",
]

SKIP_TOKENS = [
    "السنة الحالیة", "السنة السابقة", "المتوسط السنوى", "جدول رقم",
    "الاسعار بالجنيه", "نسبة تغیر", "الوحدة", "السـلعــة",
    "تابع", "ینایر", "فبرایر", "مارس", "ابریل", "مایو", "یونیو",
    "یولیو", "اغسطس", "سبتمبر", "اكتوبر", "نوفمبر", "دیسمبر",
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

def is_skip(line: str) -> bool:
    return any(tok in line for tok in SKIP_TOKENS)

def extract_numbers(line: str) -> list[float]:
    """Extract all numeric values from a line."""
    pattern = r"\(?[٠-٩\d][٠-٩\d,\.]*\)?"
    raw = re.findall(pattern, line)
    return [n for r in raw if (n := parse_num(r)) is not None]

def extract_item_name(line: str) -> str | None:
    """Extract Arabic item name from the start of a line."""
    line = line.strip()
    m = re.match(r"^([\u0600-\u06ff\s\(\)\/\-،]+)", line)
    if m:
        name = m.group(1).strip()
        if (len(name) >= 3
                and "السنة" not in name
                and "المتوسط" not in name
                and "جدول" not in name
                and "الوحدة" not in name):
            return name
    return None


# ── 4. PARSE QUARTERLY TABLES (Tables 1 & 2) ─────────────────────────────────
def parse_quarterly(pages: dict, page_range: range,
                    price_stage: str) -> list[dict]:
    """
    Parse quarterly-format tables.
    Column order in PDF: Item | Unit | Q1 | Q2 | Q3 | Q4 | Avg_2025 | Avg_2024 | Pct
    """
    records = []
    current_cat = "غير محدد"

    for pg in page_range:
        if pg not in pages:
            continue
        for line in pages[pg].split("\n"):
            line = line.replace("\r", "").strip()
            if not line:
                continue

            # Update category
            for cat in CATEGORIES:
                if cat in line and len(line) <= len(cat) + 5:
                    current_cat = cat
                    break

            if is_skip(line):
                continue

            nums = extract_numbers(line)
            if len(nums) < 3:
                continue

            item = extract_item_name(line)
            if not item:
                continue

            unit = next(
                (u for u in ["كجم", "طن", "فدان", "زوج", "الالف", "بالواحدة", "ليمونة"]
                 if u in line),
                None,
            )

            rec = {
                "price_stage":  price_stage,
                "geography":    "Republic",
                "category":     current_cat,
                "product":      item,
                "unit":         unit,
            }

            if len(nums) >= 7:
                rec["Q1"]        = nums[0]
                rec["Q2"]        = nums[1]
                rec["Q3"]        = nums[2]
                rec["Q4"]        = nums[3]
                rec["avg_2025"]  = nums[4]
                rec["avg_2024"]  = nums[5]
                rec["change_pct"]= nums[6]
            elif len(nums) >= 3:
                rec["avg_2025"]  = nums[0]
                rec["avg_2024"]  = nums[1]
                rec["change_pct"]= nums[2]

            records.append(rec)

    return records


# ── 5. PARSE MONTHLY TABLES → QUARTERLY AVG (Tables 3 & 4) ───────────────────
MONTH_COLS = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]

def parse_monthly(pages: dict, page_range: range,
                  geography: str) -> list[dict]:
    """
    Parse monthly tables and convert to quarterly averages.
    Q1 = avg(Jan,Feb,Mar) | Q2 = avg(Apr,May,Jun)
    Q3 = avg(Jul,Aug,Sep) | Q4 = avg(Oct,Nov,Dec)
    """
    records = []
    current_cat = "غير محدد"

    for pg in page_range:
        if pg not in pages:
            continue
        for line in pages[pg].split("\n"):
            line = line.replace("\r", "").strip()
            if not line:
                continue

            for cat in CATEGORIES:
                if cat in line and len(line) <= len(cat) + 5:
                    current_cat = cat
                    break

            if is_skip(line):
                continue

            nums = extract_numbers(line)
            if len(nums) < 5:
                continue

            item = extract_item_name(line)
            if not item:
                continue

            unit = next(
                (u for u in ["كجم", "طن", "فدان", "زوج", "الالف", "بالواحدة"]
                 if u in line),
                None,
            )

            rec = {
                "price_stage":  "Consumer",
                "geography":    geography,
                "category":     current_cat,
                "product":      item,
                "unit":         unit,
            }

            # 12 monthly values + avg_2025 + avg_2024 + pct = 15
            if len(nums) >= 12:
                monthly = nums[:12]
                # Convert months → quarters (average of 3 months)
                rec["Q1"]        = round(np.nanmean(monthly[0:3]), 2)
                rec["Q2"]        = round(np.nanmean(monthly[3:6]), 2)
                rec["Q3"]        = round(np.nanmean(monthly[6:9]), 2)
                rec["Q4"]        = round(np.nanmean(monthly[9:12]), 2)
                rec["avg_2025"]  = nums[12] if len(nums) > 12 else None
                rec["avg_2024"]  = nums[13] if len(nums) > 13 else None
                rec["change_pct"]= nums[14] if len(nums) > 14 else None
            elif len(nums) >= 3:
                rec["avg_2025"]  = nums[0]
                rec["avg_2024"]  = nums[1]
                rec["change_pct"]= nums[2]

            records.append(rec)

    return records


# ── 6. MAIN ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("STEP 1 — DATA EXTRACTION")
    print("=" * 60)

    print("\n[1/4] Loading pages from PDF/ZIP...")
    pages = load_pages(PDF_PATH, EXTRACT_DIR)

    print("\n[2/4] Parsing tables...")
    t1 = parse_quarterly(pages, range(11, 19), "Producer")
    print(f"  Table 1 (Producer):       {len(t1):>4} raw records")

    t2 = parse_quarterly(pages, range(20, 29), "Wholesale")
    print(f"  Table 2 (Wholesale):      {len(t2):>4} raw records")

    t3 = parse_monthly(pages, range(31, 45), "Urban")
    print(f"  Table 3 (Consumer/Urban): {len(t3):>4} raw records")

    t4 = parse_monthly(pages, range(49, 63), "Rural")
    print(f"  Table 4 (Consumer/Rural): {len(t4):>4} raw records")

    print("\n[3/4] Combining all tables...")
    df = pd.concat(
        [pd.DataFrame(t) for t in [t1, t2, t3, t4]],
        ignore_index=True,
        sort=False,
    )
    print(f"  Total raw rows: {len(df)}")

    print(f"\n[4/4] Saving → {OUTPUT_CSV}")
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"  Done. Shape: {df.shape}")
    print("=" * 60)


if __name__ == "__main__":
    main()
