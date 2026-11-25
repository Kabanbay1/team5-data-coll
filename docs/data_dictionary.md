# Data Dictionary — USGS Earthquake Dataset (2023–2026)

## 1. Source Overview

- **Provider:** United States Geological Survey (USGS) — Earthquake Hazards Program
- **API Service:** FDSN Event Web Service (`fdsnws-event`, API v2.8.4)
- **Base Endpoint:** `https://earthquake.usgs.gov/fdsnws/event/1/query`
- **HTTP Method:** `GET`
- **Response Format:** GeoJSON (`FeatureCollection`, `application/geo+json`)
- **Official API Documentation:** <https://earthquake.usgs.gov/fdsnws/event/1/>
- **Official GeoJSON Field Reference:** <https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php>

---

## 2. Multi-Year Paginated Collection Configuration (2023–2026)

`src/api_client.py` collects all available earthquake events ($\text{mag} \ge 4.5$) from `2023-01-01T00:00:00` to `2026-11-18T14:19:58` (UTC) by splitting the range by calendar year and paginating with `limit=2000` and `offset = 1 + (page - 1) * 2000` (`orderby=time-asc`).

| Period | `starttime` (UTC) | `endtime` (UTC) | Pages Fetched (`limit=2000`) | Collected Records |
|---|---|---|---:|---:|
| **2023** | `2023-01-01T00:00:00` | `2024-01-01T00:00:00` | 4 (`offset=1..6001`) | `7,643` |
| **2024** | `2024-01-01T00:00:00` | `2025-01-01T00:00:00` | 4 (`offset=1..6001`) | `6,397` |
| **2025** | `2025-01-01T00:00:00` | `2026-01-01T00:00:00` | 5 (`offset=1..8001`) | `8,559` |
| **2026** | `2026-01-01T00:00:00` | `2026-11-18T14:19:58` | 4 (`offset=1..6001`) | `7,075` |
| **Total** | `2023-01-01T00:00:00` | `2026-11-18T14:19:58` | **17 pages** | **29,674** |

---

## 3. Raw & Consumed Data Artifacts (Stages 1 & 2)

| Stage | File Path | Format | Description |
|---|---|---|---|
| **Stage 1 (API Collector)** | `data/raw/pages/usgs_<year>_page_<NN>.json` | GeoJSON | 17 unmodified raw GeoJSON page responses directly from the USGS API |
| **Stage 1 (API Collector)** | `data/raw/records.json` | JSON Array | 29,674 flattened JSON records (21 fields each) read by `src/producer.py` |
| **Stage 1 (API Collector)** | `data/raw_data.csv` | CSV | Tabular CSV snapshot of the 29,674 raw records prior to validation and cleaning |
| **Stage 2 (Kafka Consumer)** | `data/consumed/consumed_earthquakes.csv` | CSV | 29,674 records consumed from Kafka topic `usgs_earthquakes` by `src/consumer.py` |

---

## 4. Field-Level Data Dictionary (21 Extracted Fields)

| # | Field Name | Raw GeoJSON Path | Type | Category | Missing in Raw Dataset | Observed Range / Values (29,674 Records) | Description |
|---:|---|---|---|---|---:|---|---|
| 1 | `id` | `feature.id` | `str` | Identifier | `0` | `29,674` unique IDs | Unique USGS event identifier |
| 2 | `mag` | `properties.mag` | `float` | Numerical | `0` | `4.5` to `8.8` | Earthquake magnitude |
| 3 | `magType` | `properties.magType` | `str` | Categorical | `0` | `mb`, `md`, `ml`, `ml(texnet)`, `mw`, `mwb`, `mwc`, `mwp`, `mwr`, `mww` | Magnitude calculation algorithm |
| 4 | `net` | `properties.net` | `str` | Categorical | `0` | `ak`, `ci`, `hv`, `nc`, `nn`, `ok`, `pr`, `tx`, `us`, `uu`, `uw` | Contributing seismic network ID |
| 5 | `place` | `properties.place` | `str` | Categorical / Text | `0` | `18,420` distinct location strings | Human-readable geographic description of epicenter |
| 6 | `time` | `properties.time` | `int` | Date / Time | `0` | `2023-01-01` to `2026-11-18` (epoch ms UTC) | Origin timestamp in Unix epoch milliseconds (UTC) |
| 7 | `updated` | `properties.updated` | `int` | Date / Time | `0` | Unix epoch milliseconds (UTC) | Most recent catalog update timestamp |
| 8 | `type` | `properties.type` | `str` | Categorical | `0` | `earthquake` (`29,674`) | Seismic event classification |
| 9 | `status` | `properties.status` | `str` | Categorical | `0` | `reviewed` (`29,674`) | Seismologist review status |
| 10 | `tsunami` | `properties.tsunami` | `int` | Numerical / Binary | `0` | `0` or `1` | `1` if linked to a tsunami advisory/watch, else `0` |
| 11 | `sig` | `properties.sig` | `int` | Numerical | `0` | `312` to `2910` | Composite event significance score |
| 12 | `felt` | `properties.felt` | `float` | Numerical | `24,300` | $\ge 0$ (optional) | Number of citizen "Did You Feel It?" (DYFI) reports |
| 13 | `cdi` | `properties.cdi` | `float` | Numerical | `24,300` | `0.0` to `12.0` (optional) | Maximum reported Community Decimal Intensity |
| 14 | `mmi` | `properties.mmi` | `float` | Numerical | `26,496` | `0.0` to `12.0` (optional) | Maximum estimated ShakeMap Modified Mercalli Intensity |
| 15 | `alert` | `properties.alert` | `str` | Categorical | `26,940` | `green`, `yellow`, `orange`, `red` (optional) | PAGER fatality/economic loss alert level |
| 16 | `nst` | `properties.nst` | `float` | Numerical | `83` | $\ge 0$ (median `55.0`) | Number of seismic stations used to determine location |
| 17 | `gap` | `properties.gap` | `float` | Numerical | `85` | `0.0` to `360.0` (median `92.0`) | Largest azimuthal gap between azimuthally adjacent stations (degrees) |
| 18 | `dmin` | `properties.dmin` | `float` | Numerical | `88` | $\ge 0$ (median `2.4925`) | Horizontal distance from epicenter to nearest station (degrees) |
| 19 | `longitude` | `geometry.coordinates[0]` | `float` | Numerical | `0` | `-179.9997` to `179.9984` | Epicenter longitude in decimal degrees ($[-180, 180]$) |
| 20 | `latitude` | `geometry.coordinates[1]` | `float` | Numerical | `0` | `-65.8497` to `86.5939` | Epicenter latitude in decimal degrees ($[-90, 90]$) |
| 21 | `depth_km` | `geometry.coordinates[2]` | `float` | Numerical | `0` | `1.0` to `669.556` | Focal depth in kilometers |
