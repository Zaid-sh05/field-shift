# Agronomy Knowledge Base for a Crop-Rotation Decision-Support Tool (Jordan / arid-semi-arid Mediterranean)

Research date: 2026-11-11. About 17 tool calls were used. Where a fact is unverified or the sources conflict, this is flagged inline.

## Q1. Soil data sources (SoilGrids, HWSD v2, OpenLandMap, Jordan national data) and lat/lon querying

### Takeaway
SoilGrids 2.0 (250 m, 6 depths, mean and quantiles) is the best global per-point soil source. Its REST point API is beta, rate-limited to 5 calls/min, and was paused at the time of checking, so the tool should cache results or use WCS, WebDAV COGs or Google Earth Engine. HWSD v2.0 (about 1 km, 7 depth layers, mapping-unit based) and OpenLandMap (250 m, Zenodo GeoTIFFs) work as fallbacks or cross-checks.

### Cited Findings
**SoilGrids 2.0 (ISRIC)**
- Properties and stored units, with the factor to divide by for conventional units:
  - bdod (bulk density), cg/cm³, ÷100 → kg/dm³
  - cec, mmol(c)/kg, ÷10 → cmol(c)/kg
  - cfvo (coarse fragments), cm³/dm³, ÷10 → vol%
  - clay, sand and silt, g/kg, ÷10 → %
  - nitrogen, cg/kg, ÷100 → g/kg
  - ocd, hg/m³, ÷10 → kg/m³
  - ocs, t/ha, ÷10 → kg/m²
  - soc, dg/kg, ÷10 → g/kg
  - phh2o, pH×10, ÷10 → pH
  - wv0010/wv0033/wv1500 (volumetric water at 10/33/1500 kPa), 10⁻³ cm³/cm³, ÷10 → % — [ISRIC SoilGrids FAQ](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html)
- Depth intervals: 0–5, 5–15, 15–30, 30–60, 60–100 and 100–200 cm. Statistics: Q0.05, Q0.50, mean and Q0.95, plus an uncertainty layer ((Q0.95−Q0.05)/Q0.50 ×10). Resolution is 250 m, with 1 km and 5 km aggregates published as COGs via WebDAV. File naming follows `property_depth_quantile`, e.g. `cfvo_5-15cm_Q05.vrt` — [ISRIC SoilGrids FAQ](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_01.html)
- REST API v2.0 is in beta. The fair-use limit is "5 API calls per 1 minute period". ISRIC "decided to temporarily pause the service" and gave no restore date. For repeated or production use it recommends WCS (maps.isric.org), WebDAV full VRT maps (files.isric.org/soilgrids/latest/data/, about 5 GB each), Google Earth Engine community datasets, WMS (for visualisation) or soilgrids.org downloads — [ISRIC SoilGrids access FAQ](https://docs.isric.org/globaldata/soilgrids/SoilGrids_faqs_02.html)
- Point-query base: `https://rest.isric.org/soilgrids/v2.0/properties/query` with `lon` and `lat` parameters — [ISRIC REST entry](https://rest.isric.org/); [ISRIC SoilGrids docs](https://docs.isric.org/globaldata/soilgrids/). Additional parameters (`property`, `depth`, `value`=mean/Q0.05/Q0.5/Q0.95/uncertainty) are documented in the [Swagger docs](https://rest.isric.org/soilgrids/v2.0/docs) (the docs page timed out during this research, so these are unverified here). R wrapper: [soilDB::fetchSoilGrids](https://search.r-project.org/CRAN/refmans/soilDB/html/fetchSoilGrids.html).

**HWSD v2.0 (FAO and IIASA, 2023)**
- Built in 2008, updated in 2013 (v1.2) and 2023 (v2.0). A revised v2.01 followed in September 2023. v2.0 has "an enhanced number of soil attributes available for seven soil depth layers, instead of two in HWSD v1.2". It covers nearly 30,000 soil mapping units at about 1 km. Citation: FAO & IIASA 2023, DOI 10.4060/cc3823en — [IIASA PURE](https://pure.iiasa.ac.at/18595); [FAO GSP HWSD](https://www.fao.org/global-soil-partnership/data/harmonized-world-soil-database/en); [HWSD v2 technical report PDF](https://pure.iiasa.ac.at/18595/1/cc3823en.pdf)
- v1.2 was a 30 arc-second raster with more than 15,000 mapping units — [FAO Soils Portal](https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v12/en/)
- A Google Earth Engine copy exists. The licence is CC BY-NC-SA 3.0 (non-commercial), which matters if the tool is ever commercialised — [GEE community catalog](https://gee-community-catalog.org/projects/hwsd/)

**OpenLandMap (Hengl et al., v0.2, 250 m, Zenodo)**
- pH in H₂O at 6 depths (0, 10, 30, 60, 100, 200 cm), stored as pH×10, about 21.9 GB — [Zenodo 2525664](https://zenodo.org/records/2525664)
- Soil organic carbon content is stored in units of 5 g/kg (×5 g/kg). The record says to divide by 2 to get percent; take the conversion from the record itself — [Zenodo 2525553](https://zenodo.org/record/2525553). OC stock in kg/m² (×10 → t/ha) — [Zenodo 2536040](https://zenodo.org/records/2536040). USDA texture classes at 6 depths — [Zenodo 2525817](https://zenodo.org/records/2525817)

### Inferences
- Recommended engine inputs: topsoil (0–30 cm, depth-weighted from 0–5/5–15/15–30) clay/sand/silt → USDA texture class; phh2o; soc; cfvo; and AWC ≈ (wv0033 − wv1500) × root depth for water-holding capacity. Use Q0.05–Q0.95 to show confidence.
- Given the 5 calls/min limit and the pause, pre-extract a Jordan bounding box (about 34.9–39.3°E, 29.2–33.4°N) from WCS or COGs once and serve it locally.

### Gaps
- I found no Jordan national soil dataset in this research, either from NARC or from the Ministry of Agriculture's national soil map and land-use project (JSMLUP, 1990s). It needs a targeted search.
- The full SoilGrids Swagger parameter list and the current API status (it may have resumed after the pause) were not verified.

## Q2. Crop characteristic data (ECOCROP, FAO-56 Kc and season lengths, AquaCrop, Jordan crop water requirements)

### Takeaway
FAO-56 Table 12 (Kc) and Table 11 (stage lengths, including Mediterranean entries) give a ready-made water-use model: ETc = Kc × ET0, with ET0 from NASA POWER. ECOCROP supplies the min/max ranges for temperature, rainfall and pH used in suitability screening. It is discontinued but hosted on GAEZ.

### Cited Findings
**FAO-56 Table 12, single Kc (ini / mid / end, max height m)** — [FAO-56 ch.6](https://www.fao.org/4/x0490e/x0490e0b.htm)

| Crop | Kc ini | Kc mid | Kc end | h (m) |
|---|---|---|---|---|
| Winter wheat (non-frozen soil) | 0.7 | 1.15 | 0.25–0.4 | 1 |
| Spring wheat | 0.3 (cereal group) | 1.15 | 0.25–0.4 | 1 |
| Barley | (0.3 group) | 1.15 | 0.25 | 1 |
| Sorghum grain | (0.3 group) | 1.00–1.10 | 0.55 | 1–2 |
| Millet | (0.3 group) | 1.00 | 0.30 | 1.5 |
| Maize grain | (0.3 group) | 1.20 | 0.60–0.35 | 2 |
| Lentil | (group, ~0.4) | 1.10 | 0.30 | 0.5 |
| Chickpea | 0.4 | 1.00 | 0.35 | 0.4 |
| Faba bean dry | 0.5 | 1.15 | 0.30 | 0.8 |
| Faba bean fresh | 0.5 | 1.15 | 1.10 | 0.8 |
| Peas dry | (group) | 1.15 | 0.30 | 0.5 |
| Alfalfa hay (avg cuttings) | 0.40 | 0.95 | 0.90 | 0.7 |
| Tomato | 0.6 (solanaceae) | 1.15 | 0.70–0.90 | 0.6 |
| Potato | (0.5 group) | 1.15 | 0.75 | 0.6 |
| Cucumber fresh | 0.6 | 1.00 | 0.75 | 0.3 |
| Watermelon | 0.4 | 1.00 | 0.75 | 0.4 |
| Onion dry | (0.7 group) | 1.05 | 0.75 | 0.4 |
| Sugar beet | 0.35 | 1.20 | 0.70 | 0.5 |
| Olives (40–60% cover) | 0.65 | 0.70 | 0.70 | 3–5 |
| Date palms | 0.90 | 0.95 | 0.95 | 8 |
| Citrus, no cover, 50% canopy | 0.65 | 0.60 | 0.65 | 3 |
| Grapes table/raisin | 0.30 | 0.85 | 0.45 | 2 |

Notes on the table:
- Per-crop Kc ini for several cereals and vegetables sits in an image in the FAO HTML. The "group" values are the group headers, so verify them against the FAO-56 PDF.
- The lentil group value (~0.4) is my reading and was not confirmed.
- The page extraction gave two chickpea rows. "Chick pea" read Kc mid 1.00, end 0.35, h 0.4, with no Kc ini. A separate "Grabanzo" row read Kc ini 0.4, mid 1.15, end 0.35, h 0.8. The table uses the first row and borrows Kc ini 0.4 from the second, so the chickpea row mixes two sources. Check it against the FAO-56 PDF.

**FAO-56 Table 11, Mediterranean / Near East stage lengths (init / dev / mid / late = total days, planting month)** — [FAO-56 ch.6](https://www.fao.org/4/x0490e/x0490e0b.htm)
- Winter wheat: 30/140/40/30 = 240, November, Mediterranean
- Small grains: 20/30/60/40 = 150, April
- Faba bean: 20/30/35/15 = 100, Mar/Apr
- Peas: same as faba bean (100)
- Sorghum: 20/35/40/30 = 130, May/June
- Tomato: 30/40/45/30 = 145, Apr/May
- Watermelon (Near East desert): 10/20/20/30 = 80
- Onion dry: 15/25/70/40 = 150, April
- Sugar beet: 45/75/80/30 = 230, November
- Olives: 30/90/60/90 = 270, March
- Citrus: 60/90/120/95 = 365, January
- Table 11 has no Mediterranean entry for lentil, chickpea, potato, alfalfa or date palm. FAO says these values should be replaced with local observations.
- Basal Kcb (Table 17) values are lower than Kc because Kc includes soil evaporation. Tomato is Kc mid 1.20 / Kcb mid 1.15 in the FAO worked example — [FAO-56 ch.7](https://www.fao.org/4/x0490e/x0490e0c.htm)

**ECOCROP**
- Holds min/max (absolute and optimal) values for temperature, annual precipitation, soil pH, light, Köppen zone, photoperiod, latitude, altitude and soil traits. It was discontinued around 2015 and is now accessible via the GAEZ platform — [FAO ECOCROP portal](https://www.fao.org/geospatial/data-and-tools/data-portals/ecocrop/en)
- Example barley values from a secondary source (column headers were truncated, so verify): optimal rain 500–1000 mm, absolute 200–2000 mm; optimal temperature 15–20 °C, absolute 2–40 °C; pH optimal 6.5–7.5, absolute 6–8 — [Sustainability 2020 land-evaluation paper (mirror)](https://p.gyb.elementfx.com/2071-1050/12/8/3110)
- A 2024 Scientific Data paper appears to be a curated crop-parameter dataset, but I could not open it behind the paywall redirect — [Nature Sci Data s41597-024-03118-1](https://www.nature.com/articles/s41597-024-03118-1)
- R package `FAO56` ships Table 12 as datasets (e.g. `Kc_Cereals`) — [CRAN FAO56](https://search.r-project.org/CRAN/refmans/FAO56/html/Kc_Cereals.html)

### Inferences
- Engine approach: seasonal ETc = Σ(Kc_stage × ET0_daily × days), compared with effective rainfall. A crop whose deficit exceeds the available irrigation is scored down. Drought-tolerant choices for rainfed zones are barley (Kc end 0.25, short season) and lentil (Kc mid 1.10, low height).
- ECOCROP absolute minimum rainfall can act as a hard filter and the optimal ranges as a soft score.

### Gaps
- I did not retrieve AquaCrop crop parameter files (CGC, CDC, WP*, HI0, Zr max). The AquaCrop default crop files for wheat, barley and tomato, and FAO I&D Paper 66, are the sources to check.
- ECOCROP values for chickpea, lentil, faba bean, vetch, sorghum, millet, olive and date palm were not retrieved. Pull them from the GAEZ ECOCROP search.
- I found no Jordan-specific measured crop water requirements (e.g. Jordan Valley tomato mm/season).

## Q3. Rotation principles and ICARDA cereal–legume evidence

### Takeaway
ICARDA's long-term Tel Hadya (N. Syria) trials show that legume–cereal rotations beat continuous cereal and fallow on soil N, quality and water-use efficiency. Barley yields were highest after vetch (hay or grazed) and lowest after lentil. Measured residual N credits in dry areas are modest (about 10 kg N/ha). Larger credits (100–200 kg/ha fertiliser savings after faba bean) come from wetter, non-ICARDA studies.

### Cited Findings
- Long-term durum-wheat rotation trial at Tel Hadya: rotations with vetch, lentil, chickpea, medic and watermelon were compared against continuous wheat and fallow at 0–90 kg N/ha. Soil N was highest under medic and lowest under wheat and fallow. Legume rotations "improve soil quality, in addition to raising yields and water-use efficiency" — [AGRIS: Changes in organic matter and N with cereal–legume rotation](https://agris.fao.org/search/en/records/64775d785eb437ddff772132)
- In an 11-year rainfed barley–legume rotation (Mediterranean), 60 kg N/ha raised barley grain yield by 39% and straw by 65%. Barley grain yield was highest after vetch for hay or grazing, and lowest after lentil and in continuous barley — [CGIAR MEL repo, long-term barley–legume rotations](https://repo.mel.cgiar.org/items/1c026447-172c-4c17-9081-29aabc18d3ce/full)
- The residual legume N effect on following barley was about 10 kg N/ha, described as substantial for N. Syrian dry areas — [Crops Soc. 2006 abstract](https://crops.confex.com/crops/2006am/techprogram/P22818.HTM)
- Improved legume management raised crop N uptake from 31.8 to 68.7 kg N/ha, and the fixed share from 55% to 69% (N. Syria) — [J. Agric. Sci., Cambridge](https://www.cambridge.org/core/journals/journal-of-agricultural-science/article/abs/effect-of-improved-management-of-legumes-in-a-legumecereal-rotation-on-field-estimates-of-crop-nitrogen-uptake-and-symbiotic-nitrogen-fixation-in-northern-syria/8BE1773C52BF99120E497197A405C9C0)
- Legume–cereal rotations returned about US$537/ha (48%) more than wheat monocropping (Morocco-type dry areas). Cited studies report 100–200 kg/ha N fertiliser savings for cereals after faba bean — [Agron. Sustain. Dev. 2019](https://link.springer.com/article/10.1007/s13593-019-0602-2)
- On-farm forage-legume/barley vs fallow/barley vs continuous barley trials in NW Syria — [Experimental Agriculture (Cambridge)](https://www-cambridge-org.ezproxyberklee.flo.org/core/services/aop-cambridge-core/content/view/C4409364EFB8AAA4748A089D5101D404/S0014479700002064a.pdf/on-farm-trials-with-forage-legume-barley-compared-with-fallow-barley-rotations-and-continuous-barley-in-north-west-syria.pdf)
- In Jordan, chickpea and/or lentil rotate with cereals (mostly wheat) where annual rain usually exceeds 300 mm. Lentil is sown mostly in December; chickpea is delayed to spring (often March), partly to avoid Ascochyta blight — [Univ. Debrecen thesis on Jordan legumes](https://dea.lib.unideb.hu/server/api/core/bitstreams/756c6925-3acb-47f8-9048-981f9ddfe8dc/content)
- A 10-year trial at Mushaqar (semi-arid central Jordan) tested wheat–lentil, wheat–vetch and wheat–lentil–melon rotations under tillage and N treatments — [same thesis](https://dea.lib.unideb.hu/server/api/core/bitstreams/756c6925-3acb-47f8-9048-981f9ddfe8dc/content); [AGRIS record](https://agris.fao.org/search/en/records/6471cbde2a40512c710e5a5b)

### Inferences
- Suggested scoring rules:
  - +N credit for legume preceding cereal. Use a conservative 10–30 kg N/ha in zones under 350 mm and higher values for faba bean or irrigated crops.
  - Prefer vetch or medic (forage) before barley in 250–350 mm zones.
  - Penalise cereal after cereal, and same-family repeats (Solanaceae: tomato, potato, eggplant; Cucurbitaceae: cucumber, melon, watermelon; Fabaceae lentil–chickpea back-to-back because of shared Ascochyta/root diseases).
  - Credit winter cover or forage over bare fallow for erosion and SOC.
- Fallow conserves some moisture in the driest zones. The Tel Hadya results show fallow gives the lowest soil N, so rotation should be the default advice wherever rain is about 300 mm or more.

### Gaps
- I found no single headline ICARDA "% yield boost of rotation vs continuous cereal" figure for Jordan. Quantified erosion-reduction and SOC-gain numbers for Jordan cover crops were also not found.
- Deep-rooting and alfalfa-specific evidence for Jordan was not retrieved. Alfalfa is high-water (Kc mid 0.95–1.20, perennial), so it suits only irrigated settings.

## Q4. Jordan agricultural context (regions, crops, rainfall zones, water, groundwater, calendars, risks)

### Takeaway
More than 90% of Jordan gets under 200 mm of rain a year. Rainfed farming is limited to the north-west highlands (300–650 mm; wheat, legumes, olives) and the 200–350 mm marginal belt (barley). The Jordan Valley (irrigated winter vegetables, dates, citrus) and the Azraq and Mafraq groundwater farms rely on water that is heavily over-abstracted. Azraq is pumped at about 2.6 times its safe yield.

### Cited Findings
**Rainfall and land**
- Rainfall ranges from about 50 mm (east and south desert) to 650 mm (northern highlands) — [FAO Jordan country profile](https://www.fao.org/4/W4356E/w4356e0f.htm)
- About 8,090,000 ha (90% of the Kingdom) has very sparse vegetation and less than 200 mm of rain — [WUR Global Yield Gap Atlas, Jordan](https://yieldgap.containers.wur.nl/jordan). One older paper states about 8%, which conflicts; it likely refers to a different land class — [MPRA 66782](https://mpra.ub.uni-muenchen.de/66782/1/MPRA_paper_66782.pdf)
- Barley is the main rainfed crop in the 200–350 mm plains; wheat and fruit trees grow at 300–350 mm and above — [FAO Jordan](https://www.fao.org/4/W4356E/w4356e0f.htm)
- 1997 snapshot: about 290,000 ha cultivated (130,000 ha olives and fruit trees, 50,000 vegetables, 110,000 field crops), with about 80% of cultivated area rainfed — [WUR GYGA Jordan](https://yieldgap.containers.wur.nl/jordan). More than 70% of agriculture is rainfed according to the Ministry of Agriculture — [Jordan Times](https://jordantimes.com/news/local/climate-change-hit-impoverished-jordanians-hardest-streamlining-funding-process-vital)

**Mafraq and Azraq**
- Mafraq rainfall is under 200 mm. Its share of national barley, wheat and clover output fell from one third in 2015 to 10% in 2020 (DoS data via ARIJ). ARIJ reports both a 62% shrink in arable land and an area that fell "by almost half", which is internally inconsistent — [ARIJ data story](https://arij.net/projects/100-watt-podcast/en/data-stories/story-20/index.html)
- Azraq cultivated area grew from 2,200 acres (early 1980s) to about 25,000 acres (2010) — [New Lines Magazine](https://newlinesmag.com/reportage/water-scarcity-in-jordan-is-causing-an-agricultural-crisis/)
- Azraq safe yield is about 24 MCM/yr. 2018 abstraction was 61.2 MCM, at least 260% of safe yield (MWI 2020 data). A model projects a further 15–25 m water-level decline by 2045 under current pumping — [Sustainability Science 2022](https://link.springer.com/doi/10.1007/s11625-022-01135-w). A MODFLOW study puts Upper Aquifer safe yield at about 25 MCM/yr — [Cardiff ORCA, Resources 2015](https://orca.cardiff.ac.uk/92822/1/resources-04-00819.pdf). USAID 2015 reported withdrawal of more than twice capacity through 580 wells — [New Lines](https://newlinesmag.com/reportage/water-scarcity-in-jordan-is-causing-an-agricultural-crisis/)
- Nationally (1990s): 6 of 12 groundwater basins were over-extracted, and depletion was about 172–190 MCM/yr — [FAO Jordan](https://www.fao.org/4/W4356E/w4356e0f.htm)

**Water stats**
- Renewable freshwater is about 61 m³/capita/yr, projected to fall to 35 m³ by 2040 — [MWI National Water Conservation Roadmap 2024](https://mwi.gov.jo/ebv4.0/root_storage/ar/eb_list_page/national_water_conservation_roadmap_english_2024-0.pdf); [National Water Strategy 2023–2040 summary](https://agwkp.unescwa.org/sites/default/files/2023-10/National_Water_Strategy_2023-2040_Summary-English_-ver2-%20Jordan.pdf)
- Agriculture's share of water use is about 52% (2017; 45% domestic, 3% industry) — [GWP Jordan brief](https://www.gwp.org/globalassets/global/about-gwp/publications/country-briefs/gwp_country_brief_jordan.pdf). Other sources give 49% or about 55%, depending on year and definition.

**Calendar and risks**
- Planting months: lentil in December (some farmers late December–January); chickpea in March — [Debrecen thesis](https://dea.lib.unideb.hu/server/api/core/bitstreams/756c6925-3acb-47f8-9048-981f9ddfe8dc/content). Winter wheat in November (FAO Mediterranean default) — [FAO-56](https://www.fao.org/4/x0490e/x0490e0b.htm)
- January 2022 frost in the Jordan Valley damaged about 30–90% of open-field crops (potato, courgette, tomato, eggplant); greenhouses fared better — [Jordan Times](https://jordantimes.com/news/local/frost-damaged-crops-now-add-farmers%E2%80%99-woes-%E2%80%94-stakeholder); [Jordan News](https://jordannews.jo/Section-109/News/Committee-to-conclude-frost-damage-assessment-on-crops-Hneifat-13074)
- A late-summer 2022 heatwave ran 12–15 °C above normal (union figure). Some Jordan Valley and Mafraq farmers lost more than 50% of yield, and olive fruit size and number were cut. Southern Jordan Valley farmers shifted tomato planting from August to late September — [Jordan Times: Heatwave takes toll](https://jordantimes.com/news/local/heatwave-takes-toll-crop-yield)

### Inferences
- Zone rules for the engine:
  - Under 200 mm with no irrigation: rangeland or barley only (high risk).
  - 200–300 mm: barley, barley–vetch/medic.
  - 300–350 mm and above: wheat–lentil/chickpea, olives.
  - Jordan Valley (irrigated, frost-sensitive in January, heat-sensitive in August–September): winter vegetables with family rotation, dates.
  - Azraq and Mafraq groundwater farms: penalise high-ETc summer crops and alfalfa because the aquifer is over-abstracted.
- Frost and heat flags can be derived from NASA POWER daily Tmin/Tmax against crop thresholds.

### Gaps
- I did not retrieve current DoS/MoA crop-area and production figures (2022–2025), NARC planting-calendar publications, or Badia barley practice. The DoS Agricultural Statistics yearbook and the NARC website (narc.gov.jo) need a direct look.
- Date-palm area and production in the Jordan Valley were not found.

## Q5. Climate trends in Jordan relevant to farming

### Takeaway
Official Jordanian assessments project steady warming, less and more variable rainfall, and a shifting wet season. Later NDC-related figures give +2.1 to +4.5 °C and −15 to −35% precipitation by 2070–2100, plus a 5–20% rise in irrigation demand by the 2070s.

### Cited Findings
- The Third National Communication (2014) projects a steady temperature increase, more dry spells and lower precipitation. It names four agricultural risks: temperature rise, rainfall decrease, drought and a shift in the wet season. It also says the timing and intra-seasonal pattern of rain are critical for smallholders — [UNDP TNC summary](https://www.undp.org/node/204201); [TNC PDF](https://unfccc.int/resource/docs/natc/jornc3.pdf)
- Rising evaporative demand could raise irrigation requirements by 5–20% or more by the 2070s — [Jordan Times](https://jordantimes.com/news/local/climate-change-hit-impoverished-jordanians-hardest-streamlining-funding-process-vital)
- Later projections give +2.1 to +4.5 °C and a 15–35% decline in accumulated precipitation (medium confidence) by 2070–2100. The sources mix the TNC with NDC and fourth-communication material, so verify before citing — [Middle East Environment (Jordan Times reprint)](https://mideastenvironment.apps01.yorku.ca/?p=19075)
- Water tables dropped by about 25 m on average across Jordan over 28 years (national, secondary source) — [Springer Sustain. Sci. 2022](https://link.springer.com/doi/10.1007/s11625-022-01135-w)

### Inferences
- The tool should favour short-cycle, drought-tolerant options (barley, lentil, early-maturing wheat) and supplemental irrigation. It should also shift sowing-date advice when the season starts late, which can be detected from NASA POWER or IMERG rainfall onset.

### Gaps
- Observed historical trends were not retrieved (e.g. °C per decade since 1960 and mm/decade by station from the Jordan Meteorological Department). Published station-trend papers would be needed.
