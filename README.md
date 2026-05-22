# Egypt Food Prices Analysis 2025 🇪🇬
> **From CAPMAS PDF → Power Query → Python → Excel Pivot Tables → Power BI Dashboard**

---

## 📸 Project Preview

Screenshots and dashboard visuals are available in the `screenshots/` folder.

---

## 📌 Project Overview

This project analyzes food price changes in Egypt during **2025 vs 2024** using official data from CAPMAS (Central Agency for Public Mobilization and Statistics). Raw PDF data was extracted, cleaned in multiple stages, and transformed into interactive Excel and Power BI dashboards accessible to both technical and non-technical users.

---

## 🎯 Objectives

- Extract structured data from official CAPMAS PDF reports into Excel
- Clean and validate data using Power Query and Python (`pandas`)
- Analyze price trends across 4 pricing stages and 8 food categories
- Build interactive Pivot Tables with slicers for exploratory analysis
- Deliver a professional Power BI dashboard with KPI cards and dynamic filters
- Surface actionable insights on inflation, seasonal variation, and price stability

---

## 🛠️ Tools & Technologies

| Tool | Purpose |
|------|---------|
| **Excel** | PDF export, initial structuring |
| **Power Query** | Automated cleaning: headers, types, empty rows |
| **Python (pandas)** | Advanced cleaning, interpolation, computed columns |
| **Excel Pivot Tables** | Exploratory analysis with slicers |
| **Power BI** | Interactive dashboard — KPI cards, slicers, charts |
| **DAX** | Calculated measures and KPIs inside Power BI |
| **GitHub** | Version control and project documentation |

---

## 📚 Dataset Source

**CAPMAS** – Central Agency for Public Mobilization and Statistics (Egypt)
- Format: Official PDF reports
- Period: 2024 – 2025
- Coverage: National (Urban + Rural), 4 pricing stages

---

## 📂 Project Structure

```
egypt-food-prices-2025/
│
├── data/
│   ├── Egypt_Prices_Analysis_.xlsx          # Raw export from PDF (Stage 1)
│   └── Egypt_Food_Prices_2025_Clean.xlsx    # Final cleaned dataset (Stage 3)
│
├── excel_analysis/
│   └── Pivot_Tables_Analysis.xlsx           # 4 Pivot Tables with slicers
│
├── powerbi/
│   └── Egypt_Food_Dashboard_2025.pbix       # Interactive Power BI dashboard
│
├── presentation/
│   └── Egypt_Food_Prices_2025_Presentation.pptx
│
├── screenshots/
│   └── *.png                                # Dashboard and Pivot Table visuals
│
└── README.md
```

---

## 🔄 Data Pipeline

```
CAPMAS PDF
    ↓
Excel Export  →  Egypt_Prices_Analysis_.xlsx
    ↓
Power Query   →  Cleaned headers, types, structure
    ↓
Python        →  Egypt_Food_Prices_2025_Clean.xlsx
    ↓
Pivot Tables  →  4 analytical views
    ↓
Power BI      →  Interactive dashboard
    ↓
Insights
```

---

## 🗂️ Final Dataset Schema

`Egypt_Food_Prices_2025_Clean.xlsx` — **657 records × 13 columns**

| Column | Description |
|--------|-------------|
| `Product Group` | Food category (8 groups) |
| `Product / Item` | Individual product name (Arabic) |
| `Stage` | Pricing stage: منتج / جملة / حضر / ريف |
| `Unit` | Unit of measurement (e.g., كجم) |
| `2024_Avg_EGP` | Average price in 2024 (EGP) |
| `2025_Avg_EGP` | Average price in 2025 (EGP) |
| `Change_Pct` | Year-over-year price change (%) |
| `Q1` – `Q4` | Quarterly average prices |
| `Seasonal_Flag` | Year-Round / Seasonal (1Q–3Q) |
| `Quarters_Present` | Number of quarters with available data (1–4) |

> 🟡 Yellow cells in the source file = values filled by linear interpolation for seasonal gaps.

---

## 📊 Analysis: 4 Pivot Tables

### Pivot 1 — Inflation by Food Group × Pricing Stage
- **Question:** What is the average price change per food group across pricing stages?
- **Fields:** Rows = Product Group, Columns = Stage, Values = Avg(Change_Pct)

### Pivot 2 — Top & Bottom Products
- **Question:** Which products had the highest and lowest price changes?
- **Fields:** Product / Item, 2024_Avg_EGP, 2025_Avg_EGP, Change_Pct
- Sorted descending for Top 10 / ascending for Bottom 10

### Pivot 3 — Quarterly Price Trends
- **Question:** How do food prices shift across Q1–Q4?
- **Fields:** Rows = Product Group, Values = Avg(Q1), Avg(Q2), Avg(Q3), Avg(Q4)
- **Slicer:** Stage

### Pivot 4 — Price Stability Classification
- **Question:** How many products are stable, moderate, or highly volatile?
- **Classification:**
  - Stable: `|Change_Pct| < 5%` → 35 products
  - Moderate: `5% ≤ Change_Pct ≤ 20%` → 18 products
  - High: `Change_Pct > 20%` → 26 products

---

## 📈 Key Insights

### Inflation by Category (Producer Stage — منتج)

| Food Group | Avg Change % |
|------------|-------------|
| 🥦 Vegetables & Fruits | **+22.9%** |
| 🐔 Poultry & Eggs | +9.8% |
| 🐟 Fish | +6.4% |
| 🛒 Groceries & Beverages | +2.3% |
| 🥩 Meat | +1.5% |
| 🧀 Dairy Products | -0.1% |
| 🌾 Grains & Legumes | **-4.6%** |

### Top 5 Price Increases (منتج stage)

| Product | Change % |
|---------|---------|
| برتقال بلدي (Local Orange) | **+117.7%** |
| برتقال صيفي (Summer Orange) | +96.2% |
| بلح زغلول (Zaghloul Dates) | +84.0% |
| مشمش (Apricots) | +70.2% |
| مانجو زبدية (Mango) | +65.1% |

### Top 5 Price Decreases (منتج stage)

| Product | Change % |
|---------|---------|
| حلبة (Fenugreek) | **-49.9%** |
| بطاطس (Potatoes) | -44.8% |
| ثوم بلدي (Local Garlic) | -33.9% |
| بسلة (Green Peas) | -33.1% |
| فاصوليا جافة (Dried Beans) | -28.4% |

### Pricing Stage Comparison

| Stage | Avg Change % |
|-------|-------------|
| جملة (Wholesale) | **+21.8%** |
| ريف (Rural) | +14.4% |
| حضر (Urban) | +13.3% |
| منتج (Producer) | +12.6% |

### Other Key Findings
- **Q4** records the highest average prices across all groups
- **Vegetables & Fruits** show the strongest seasonal volatility between quarters
- **Dairy** is the most price-stable category overall (-0.1% avg change)
- **27%** of products exceeded 20% price increase — warranting ongoing monitoring
- **Wheat (قمح)** rose +9.5% despite overall grain category decline — a food security signal

---

## 🏁 Conclusion

This project transformed raw official PDF data into a clean, structured dataset and two interactive analytical tools. The results provide accessible, data-driven insights on Egypt's food inflation in 2025 — useful for students, analysts, policymakers, and consumers.

> *"From Raw Data to Clear Insights."*

---

## 👥 Team Members

| Name | Role |
|------|------|
| **Youssef Mostafa AbdelFattah** | Team Leader — Data Cleaning & GitHub |
| **Salma Hassan Fawzy** | Excel Analysis & Pivot Tables |
| **Bola Adel Sedky** | Power BI Dashboard |
| **Mohamed Alaa** | Presentation |
| **Nader George Emil** | Presentation |

---

## 📄 License

This project uses publicly available data from CAPMAS for educational and analytical purposes.
