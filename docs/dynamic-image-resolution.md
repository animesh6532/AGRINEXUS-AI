# AgriNexus-AI Dynamic Image Resolution & Verification Architecture

**Document Status:** Complete Architecture & Operational Specification  
**Author:** Lead Agricultural Decision-Support Architect  
**System Version:** AgriNexus-AI v2.0  
**Date:** September 2026  

---

## 1. Executive Summary & Purpose

The **Dynamic Image Resolution & Verification System** provides automated, production-grade image discovery, relevance ranking, security validation, attribution preservation, and persistent caching for agricultural crop recommendations.

### Core Problem Solved
Traditional crop recommendation platforms suffer from **Content Integrity Bugs**, such as returning a cereal/wheat field photo when **Mango** (*Mangifera indica*) is recommended. Hardcoding local images or picking static category fallbacks creates misleading visual evidence for farmers.

AgriNexus-AI decouples Machine Learning classification from image retrieval:
- **ML & Agronomic Suitability Engine:** Answers *"Is this crop environmentally suitable?"*
- **Dynamic Image Resolver:** Answers *"What is the verified photographic identity of this crop?"*

---

## 2. Architecture & Pipeline

```
[Crop Recommendation Request]
              │
              ▼
    [SmartCropRecommender]
              │
              ▼
    [CropCatalogue Entity Lookup] (Normalizes "mango", "Mango", "MANGIFERA INDICA" -> "mango")
              │
              ▼
    [ImageResolver.resolve_entity_image("mango")]
              │
    ┌─────────┴─────────┐
    ▼                   ▼
 [SQLite Cache]     [Cache Miss]
 (Hit: Return)          │
                        ▼
            [Controlled Search Queries]
            ("Mangifera indica mango fruit tree agriculture")
                        │
                        ▼
            ┌───────────────────────┐
            │ Active Image Providers│
            ├───────────────────────┤
            │ • Wikimedia Commons   │ (Biological / reference)
            │ • GBIF Occurrence     │ (Botanical specimen)
            │ • Pexels API          │ (High-res photography)
            │ • iNaturalist API     │ (Research-grade species)
            └───────────┬───────────┘
                        │
                        ▼
            [Candidate Normalization]
                        │
                        ▼
            [Relevance Scoring & Negative Keyword Filtering]
            (Scientific Name +40, Canonical Name +25, Ag Context +10)
            (Negative terms: -60 / Reject wheat/rice for Mango)
                        │
                        ▼
            [Candidate Validation Gate]
            (URL Safety, No SSRF, Image Content-Type, Min Resolution)
                        │
                        ▼
            [Acceptance Threshold Filter]
            (Score >= 75 Accept; Score < 60 Reject)
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
 [Accepted Candidate]        [No Candidate >= 75]
         │                             │
         ▼                             ▼
 {available: true, url:...}   {available: false, reason:...}
         │                             │
         └──────────────┬──────────────┘
                        ▼
            [SQLite Persistent Cache] (TTL: 24h)
                        │
                        ▼
            [FastAPI Endpoint Response]
                        │
                        ▼
            [Frontend <CropImage /> Component]
```

---

## 3. Canonical Crop Entity Database (`backend/app/data/crop_catalogue.json`)

Every crop species maintains a canonical identity in `crop_catalogue.json`:

```json
{
  "mango": {
    "crop_id": "mango",
    "name": "Mango",
    "scientific_name": "Mangifera indica",
    "category": "Fruit",
    "aliases": ["aam", "mango tree", "mango fruit"],
    "search_terms": [
      "Mangifera indica mango fruit tree orchard agriculture",
      "Mangifera indica mango tree branch fruit",
      "Mango tree fruit agriculture"
    ],
    "negative_terms": ["wheat", "rice", "maize", "corn", "barley", "mustard", "potato"]
  }
}
```

### Strict Rule — Scientific Name Safety
The system **never invents scientific names**. If a crop profile lacks a verified scientific name, it is flagged as `is_resolved = false` and uses controlled common-name fallback queries.

---

## 4. Multi-Provider Image Search Architecture

All image search providers inherit from `ImageProvider` in `backend/app/services/image_search/base.py`:

| Provider | Purpose | Default Status | Auth |
| :--- | :--- | :--- | :--- |
| **Wikimedia Commons** | Open-access biological & agricultural reference photos | Active | None (Public MediaWiki API) |
| **GBIF** | Botanical species occurrence specimens | Active | None (Public REST API) |
| **Pexels** | High-resolution agricultural photography | Active when key set | `PEXELS_API_KEY` header |
| **iNaturalist** | Research-grade species observation photos | Active | None (Public REST API) |

---

## 5. Relevance Scoring & Entity-Aware Negative Matching

Candidate scoring matrix ($S \in [0, 100]$):
- **Scientific Name Match:** $+40$ points
- **Canonical Crop Name Match:** $+25$ points
- **Alias Match:** $+15$ points
- **Agricultural Context Keywords** (`crop`, `plant`, `tree`, `fruit`, `field`, `farm`, `harvest`, `orchard`): $+10$ points
- **Description / Tag Depth:** $+5$ points
- **Resolution & Aspect Ratio Quality:** $+5$ points

### Negative Keyword Filtering
If candidate metadata contains negative keywords associated with other crops (e.g. searching for **Mango** encounters a candidate tagged `wheat` or `maize field`), the candidate is penalized by $-60$ points or rejected, guaranteeing that **Mango never returns a cereal image**.

### Acceptance Thresholds
- **90–100:** Excellent Match
- **75–89:** Acceptable Match (Default cutoff `IMAGE_MIN_RELEVANCE_SCORE = 75`)
- **Below 60:** Automatic Rejection

If no candidate meets the cutoff, the API returns `image.available = false`. The UI renders a clean **"Image Unavailable"** card instead of a wrong or random agricultural photo.

---

## 6. Persistent Caching Architecture

Resolved image metadata is cached in an embedded SQLite database (`backend/app/data/image_cache.db`):
- **Cache Key:** `crop:{crop_id}` (e.g. `crop:mango`)
- **Configurable TTL:** `IMAGE_CACHE_TTL = 86400` (24 Hours)
- **Purge & Refresh:** `POST /api/v1/images/crop/{crop_id}/refresh`

---

## 7. Environment Variables Configuration

The following environment variables control image resolution behavior in `backend/app/core/config.py`:

```env
IMAGE_SEARCH_ENABLED=True
PEXELS_API_KEY=your_pexels_api_key_here
IMAGE_CACHE_TTL=86400
IMAGE_MIN_WIDTH=640
IMAGE_MIN_HEIGHT=360
IMAGE_MIN_RELEVANCE_SCORE=75
IMAGE_REQUEST_TIMEOUT=8.0
IMAGE_MAX_CANDIDATES=20
```

---

## 8. API Endpoints Specification

### 1. `GET /api/v1/images/crop/{crop_id}`
Returns cached or newly resolved image metadata:
```json
{
  "success": true,
  "entity": {
    "id": "mango",
    "name": "Mango",
    "scientific_name": "Mangifera indica",
    "category": "Fruit",
    "is_resolved": true
  },
  "image": {
    "available": true,
    "url": "https://images.pexels.com/photos/...",
    "thumbnail_url": "https://images.pexels.com/photos/...",
    "provider": "Pexels",
    "source_url": "https://www.pexels.com/photo/...",
    "author": "Photo by Photographer on Pexels",
    "license": "Pexels License",
    "license_url": "https://www.pexels.com/license/",
    "alt": "Mango tree with fruit",
    "relevance_score": 94.0,
    "reason": "Successfully resolved high-relevance crop photo"
  }
}
```

### 2. `POST /api/v1/images/crop/{crop_id}/refresh`
Forces cache invalidation and re-queries active image providers.

### 3. `GET /api/v1/images/health`
Returns provider configuration and cache readiness.

---

## 9. Fault-Tolerant Non-Blocking Guarantee

Image resolution is **100% fault-tolerant**. If external provider APIs time out, return HTTP errors, or fail network requests, the crop recommendation API (`POST /api/v1/crop/recommend-smart`) catches the exception gracefully and returns `image.available = false`.

**The crop recommendation pipeline NEVER fails due to image resolution errors.**

---

## 10. How to Add a New Crop

Adding support for a new crop species requires **zero frontend code changes** and **zero image file additions**:

1. Open `backend/app/data/crop_catalogue.json`.
2. Add the canonical entity block:
   ```json
   "avocado": {
     "crop_id": "avocado",
     "name": "Avocado",
     "scientific_name": "Persea americana",
     "category": "Fruit",
     "aliases": ["butter fruit"],
     "search_terms": [
       "Persea americana avocado fruit tree orchard agriculture"
     ],
     "negative_terms": ["wheat", "rice", "corn", "potato"]
   }
   ```
3. Done! The Image Resolver automatically fetches, scores, validates, and caches verified photos for Avocado.

---
*Architecture Specification Approved for AgriNexus-AI Platform Integration.*
