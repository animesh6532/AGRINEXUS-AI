# AgriNexus-AI Crop Suitability Methodology & Scientific Framework

**Document Status:** Approved Research & Methodology Specification  
**Author:** Lead Agricultural Decision-Support Architect & Senior Agronomist  
**System Version:** AgriNexus-AI v2.0  
**Date:** September 2026  

---

## 1. Introduction & Core Scientific Philosophy

The primary objective of the **AgriNexus-AI Smart Crop Advisor** is to provide transparent, explainable, and scientifically defensible crop recommendations tailored to specific field locations.

Unlike generic machine learning classifiers or black-box scoring systems that predict a crop label based on arbitrary weights, AgriNexus-AI adheres strictly to established **Agro-Ecological Zoning (AEZ)** principles developed by the **Food and Agriculture Organization (FAO)** and the **Indian Council of Agricultural Research (ICAR)**.

### The Core Decision Question
The engine answers the fundamental agricultural question:

> *"Given this specific field location, available soil information, recent and current weather, near-term forecast, regional season, crop calendar, water availability, and documented crop requirements — which crops are environmentally and seasonally suitable, what limits each crop, what evidence supports the assessment, and what should be verified before planting?"*

---

## 2. Review of Land Suitability Assessment Methodologies

To establish a defensible framework for AgriNexus-AI, seven major crop suitability assessment methodologies were evaluated:

| Methodology | Core Principle | Advantages | Limitations | Suitability for AgriNexus-AI |
| :--- | :--- | :--- | :--- | :--- |
| **1. FAO AEZ / GAEZ Matching** | Matching crop thermal, moisture, and soil requirements against land mapping units (LMUs). | Standardized internationally; highly defensible; transparent. | Requires detailed soil/climate spatial grids. | **Primary Framework** (Foundation for land suitability classification). |
| **2. Limiting-Factor Methodology** | Based on Liebig's Law of the Minimum: the most severely constrained factor limits overall suitability. | Prevents high scores when a lethal or severe constraint exists (e.g., extreme frost). | Can be overly rigid without soft boundary modeling. | **Core Constraint Engine** (Used for hard/soft limitation enforcement). |
| **3. Weighted Multi-Criteria Analysis (MCA/AHP)** | Weighted linear combination of factor scores. | Flexible; handles multiple continuous parameters. | Risk of "compensatory masking" (a high pH score hiding lethal temperature). | **Secondary Index Builder** (Applied only after limiting factors are evaluated). |
| **4. Multiplicative Suitability Indices** | Product of individual suitability factor ratings ($S = \prod s_i$). | Ensures zero rating if any single requirement is completely unmet. | High sensitivity to multiple minor suboptimal factors. | **Used in Soil/Climate Sub-indices**. |
| **5. Fuzzy Membership Functions** | Continuous membership curves ($\mu(x) \in [0, 1]$) representing smooth transitions from non-suitable to optimal. | Eliminates harsh artificial boundary cutoffs at exact values (e.g., 19.9°C vs 20.0°C). | Requires empirical calibration of inflection points. | **Core Parameter Evaluation Engine**. |
| **6. Machine Learning Classification** | Supervised learning (e.g., ExtraTrees, XGBoost) trained on historical crop-soil-climate datasets. | Captures complex non-linear feature interactions in multi-dimensional space. | Black-box nature; restricted to trained classes; requires complete input feature vector (N,P,K,T,H,pH,R). | **Independent Evidence Stream** (Frozen ML model evaluated separately). |
| **7. Hybrid ML + Agronomic Rules** | Multi-tier pipeline combining deterministic agronomic rule engines with ML classification evidence. | Combines strict scientific safety with learned statistical patterns; highly explainable. | Increased architectural complexity. | **AgriNexus-AI Adopted Architecture**. |

---

## 3. AgriNexus-AI Hybrid Architecture & Decision Hierarchy

Conceptual pipeline followed by AgriNexus-AI:

```
                  [FIELD LOCATION & COORDINATES]
                                │
                                ▼
               ┌─────────────────────────────────┐
               │    FIELD INTELLIGENCE PANEL     │
               ├─────────────────────────────────┤
               │ • Geospatial & Lab Soil Context │
               │ • Real-time & Forecast Weather  │
               │ • Regional Season & Calendar    │
               └────────────────┬────────────────┘
                                │
                                ▼
               ┌─────────────────────────────────┐
               │    LIMITATION ANALYSIS ENGINE   │
               │   (Liebig's Law of the Minimum) │
               ├─────────────────────────────────┤
               │ • Thermal Range & Heat/Frost    │
               │ • Moisture / Rainfall / Water   │
               │ • Soil pH & Texture Alignment   │
               └────────────────┬────────────────┘
                                │
                                ▼
               ┌─────────────────────────────────┐
               │   SOWING FEASIBILITY ENGINE     │
               ├─────────────────────────────────┤
               │ • Regional Season Window Match  │
               │ • Crop Sowing Calendar Window   │
               │ • Moisture & Rainfall Readiness │
               └────────────────┬────────────────┘
                                │
                                ▼
         ┌──────────────────────┴──────────────────────┐
         ▼                                             ▼
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     FROZEN ML MODEL EVIDENCE    │           │    CATALOGUE SUITABILITY ENGINE │
│  (ExtraTrees Classifier Model)  │           │   (26 Source-Backed Profiles)   │
│  *Only evaluated when N,P,K,    │           │   *Evaluates Land Suitability   │
│   T,H,pH,R are fully available  │           │    & Sowing Window Feasibility  │
└────────────────┬────────────────┘           └────────────────┬────────────────┘
                 │                                             │
                 └──────────────────────┬──────────────────────┘
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │    SUITABILITY INDEX & RANKING ENGINE   │
                   ├─────────────────────────────────────────┤
                   │  • Agronomic Land Suitability Score     │
                   │  • Sowing Window Feasibility Status     │
                   │  • Separate ML Evidence Probability     │
                   │  • Decoupled Data Completeness Index   │
                   └────────────────────┬────────────────────┘
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │   EXPLAINABLE RECOMMENDATION CARDS      │
                   │  • Featured Recommendation (#1)         │
                   │  • Alternative Suitable Crops           │
                   │  • Full Factor Breakdown & Sources      │
                   └─────────────────────────────────────────┘
```

---

## 4. Mathematical Formulation of the AgriNexus Suitability Index

### 4.1 Fuzzy Membership Parameter Evaluation
For any continuous environmental parameter $x$ (e.g., temperature, pH, rainfall), suitability rating $s(x) \in [0, 100]$ is calculated using a trapezoidal fuzzy membership function:

$$
s(x) = \begin{cases} 
0, & x \le x_{\text{abs,min}} \text{ or } x \ge x_{\text{abs,max}} \\
100 \times \frac{x - x_{\text{abs,min}}}{x_{\text{opt,min}} - x_{\text{abs,min}}}, & x_{\text{abs,min}} < x < x_{\text{opt,min}} \\
100, & x_{\text{opt,min}} \le x \le x_{\text{opt,max}} \\
100 \times \frac{x_{\text{abs,max}} - x}{x_{\text{abs,max}} - x_{\text{opt,max}}}, & x_{\text{opt,max}} < x < x_{\text{abs,max}}
\end{cases}
$$

Where:
- $[x_{\text{opt,min}}, x_{\text{opt,max}}]$ is the documented **optimal range**.
- $[x_{\text{abs,min}}, x_{\text{abs,max}}]$ is the documented **acceptable/absolute threshold range**.

---

### 4.2 Limiting Factor Scoring & Hard Constraints
Let $S_{\text{temp}}, S_{\text{rain}}, S_{\text{ph}}, S_{\text{texture}}, S_{\text{water}}$ be the factor suitability scores.

If any factor score $s_i < 20.0$ (violating an absolute survival boundary), the crop is flagged as **HARD CONSTRAINED** (`is_hard_constrained = True`), capping the overall suitability score to:

$$
S_{\text{final}} = \min\left(10, \min_i(s_i)\right) \quad \implies \text{Land Suitability: "Not Suitable"}
$$

This ensures that a crop facing lethal temperatures or impossible soil conditions is **never** presented as "Suitable," regardless of other favorable parameters.

---

### 4.3 Composite Suitability Score & Dynamic Weight Re-allocation
When no hard constraints are violated, the raw suitability index is computed via dynamic multi-criteria weighting:

$$
S_{\text{raw}} = w_{\text{land}} \cdot S_{\text{land}} + w_{\text{sowing}} \cdot S_{\text{sowing}} + w_{\text{region}} \cdot S_{\text{region}} + w_{\text{ml}} \cdot S_{\text{ml}}
$$

Default Weight Distribution:
- $w_{\text{land}} = 0.45$ (Agro-ecological land & soil suitability)
- $w_{\text{sowing}} = 0.25$ (Current sowing window feasibility)
- $w_{\text{region}} = 0.10$ (Regional state adaptation priority)
- $w_{\text{ml}} = 0.20$ (Frozen ML model probability, scaled to 0–100)

#### Dynamic Re-allocation Rule:
If required nutrient inputs (P or K) are missing, or if the crop is a **catalogue-only crop** not included in the frozen ML model training set, $w_{\text{ml}}$ is set to $0$, and remaining weights are normalized:

$$
w'_i = \frac{w_i}{\sum_{j \neq \text{ml}} w_j}
$$

This guarantees that catalogue crops are evaluated fairly on agronomic grounds without synthetic penalty or artificial inflation.

---

### 4.4 Decoupling Suitability Index from Data Completeness
AgriNexus-AI strictly separates **Agronomic Suitability** from **Data Completeness**:

$$\text{Data Completeness} = 0.20 \cdot I_{\text{loc}} + 0.20 \cdot I_{\text{weather}} + 0.20 \cdot I_{\text{season}} + 0.20 \cdot I_{\text{soil\_ph}} + 0.20 \cdot I_{\text{npk}}$$

Where $I \in [0, 1]$ indicates telemetry presence.

- **Suitability Index:** Reflects environmental and seasonal alignment based on *available* evidence.
- **Data Completeness:** Reflects missing telemetry or unmeasured lab soil parameters.

*Example:* A crop may receive a **High Suitability (88/100)** score based on climate and pH, but display **Data Completeness: 60%** with an explicit notice: *"Phosphorus and Potassium unmeasured — verify with a field soil test prior to planting."*

---

## 5. Distinction Between Seven Key Assessment Dimensions

The system explicitly distinguishes and reports seven distinct evaluation dimensions:

1. **Environmental / Land Suitability:** Long-term agro-climatic alignment (temperature, rainfall, soil pH, texture, soil depth).
2. **Current Weather Suitability:** Near-term atmospheric conditions (7-day forecast rainfall, relative humidity, temperature extremes).
3. **Seasonal Suitability:** Alignment with the active regional agricultural season (Kharif, Rabi, Zaid, Annual).
4. **Sowing Window Feasibility:** Alignment between the current date and the crop's recommended sowing/transplanting calendar window (`IDEAL_WINDOW`, `GOOD_WINDOW`, `LATE`, `OUTSIDE_WINDOW`).
5. **Water / Management Suitability:** Crop water demand class vs field water availability (`RAINFED`, `LIMITED_IRRIGATION`, `IRRIGATED`).
6. **ML Evidence:** Independent classification probability from the frozen ExtraTrees ML model (`ML SUPPORT: Available (XX%)` or `Catalogue-only assessment`).
7. **Data Completeness:** Percentage of required environmental and nutrient telemetry available for evaluation.

---

## 6. Crop Requirement Profile Provenance

All crop requirement profiles in AgriNexus-AI are sourced from authoritative agricultural research institutions:

- **FAO ECOCROP:** Crop ecological requirements database (Food and Agriculture Organization).
- **ICAR Institutes:** Specialized Indian Council of Agricultural Research institutes:
  - ICAR-IIMR (Maize), ICAR-CRIJAF (Jute), ICAR-CICR (Cotton), ICAR-IIWBR (Wheat), ICAR-IIPR (Pulses), ICAR-CAZRI (Arid Crops), ICAR-NRCP (Pomegranate), ICAR-NRCB (Banana), ICAR-CISH (Mango), ICAR-NRCG (Grapes), ICAR-IIHR (Horticulture), ICAR-CPRI (Potato), ICAR-DRMR (Mustard), ICAR-SBI (Sugarcane), ICAR-DGR (Groundnut), ICAR-CPCRI (Coconut).
- **State Agricultural Universities (SAUs) & IMD:** Regional crop calendars and sowing guidelines.

---
*Methodology Specification Approved for AgriNexus-AI Engine Integration.*
