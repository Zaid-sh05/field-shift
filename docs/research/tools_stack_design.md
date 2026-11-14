# Existing Crop-Rotation / Ag Decision-Support Tools, Hackathon Tech Stack, AI and UX Patterns (Field Shift prep, as of Nov 2026)

## Existing tools: features and gaps

### Takeaway
Existing tools fall into three groups. US cover-crop selectors are county-based and rank by goal. Model-heavy scenario tools (COMET-Farm, RotationARM) need lots of input data. Water and remote-sensing portals (OpenET, WaPOR, DE Africa) supply data but no rotation advice. None of the tools I found combines side-by-side rotation comparison, plain-language reasons with confidence levels, Arabic support and arid-region focus. That combination is the gap to aim at.

### Cited Findings
**Cover-crop selectors (Midwest / Northeast councils)**
- The MCCC Cover Crop Decision Tool works like this: pick a state or province, then a county, then goals such as erosion control or weed suppression. Adding a goal "automatically… rank[s] all of the cover crop options based on their fulfillment of that goal." — [Purdue Ag News 2020](https://ag.purdue.edu/news/2020/09/improved-tool-can-help-midwest-farmers-with-cover-crop-decisions.html)
- When you add a cash crop, a grey bar shows when it is in the field, set against the cover-crop seeding windows. Seeding dates are county-specific and come from climate data. The tool can also generate an information sheet. — [Purdue Ag News](https://ag.purdue.edu/news/2020/09/improved-tool-can-help-midwest-farmers-with-cover-crop-decisions.html); [KSU eUpdate](https://eupdate.agronomy.ksu.edu/article/updated-cover-crop-selection-tool-now-available-for-midwest-farmers-406-8)
- The tool is optimized for tablets and phones. — [Farms.com](https://farms.com/news/updated-cover-crop-decision-tool-160598.aspx)
- 2025 updates: Michigan added interseeding guidance. Minnesota added species including faba bean, sunn hemp and forage sorghum. — [MSU](https://www.canr.msu.edu/news/michigan-cover-crop-selector-tool-updates); [UMN Extension 2025](https://blog-crop-news.extension.umn.edu/2025/10/minnesota-cover-crop-selector-tool.html)

**USDA COMET-Farm**
- COMET-Farm is a free whole-farm greenhouse-gas and carbon accounting tool from USDA-NRCS and Colorado State University. It runs on the DayCent model and covers cropland, pasture, livestock, agroforestry and energy. — [Farmland Information Center](https://farmlandinfo.org/tools/comet-farm/)
- It has a drag-and-drop baseline rotation builder. Users can create multiple future scenarios, and the report shows the differences in carbon and greenhouse gas between them. Accurate carbon estimates need historic management data. — [COMET-Farm cropland tutorial PDF](https://planner-prod-dot-comet-201514.appspot.com/images/tutorial/pdf_tutorials/2a%20Cropland%20Demonstration%20Project%20Final.pdf)
- A 2023 USDA deck said a new interface due in summer 2024 would reduce the data and time required. I did not confirm that it is live. — [FIC COMET slides](https://farmlandinfo.org/wp-content/uploads/sites/2/2023/06/COMET-slides-may.pdf)

**Other rotation decision-support systems (research)**
- RotationARM (Australia) is built on APSIM and lets users "evaluate and compare multi-year cropping strategies". It is validated mainly for eastern Australia. Fruchtfolge (Germany) is an open-source, web-based farm optimization tool. PermVeg (Wageningen University) generates every possible rotation that meets explicit criteria. — [QLD DPI paper](https://era.dpi.qld.gov.au/id/eprint/15651/1/1-s2.0-S0168169926003200-main.pdf); [WUR PermVeg](https://models.pps.wur.nl/permveg-generic-tool-design-and-assess-crop-rotations-permanent-vegetable-production-systems); [IDEAS Fruchtfolge](https://ideas.repec.org/p/ags/ubfred/305287.html)
- A review of cropping-plan models found they "often [rely] on a single monetary criterion optimization… instead of a multi-criteria assessment". This supports a multi-criteria pitch. — [Dury et al. review, HAL](https://hal.archives-ouvertes.fr/hal-00930508)
- Combining crop simulation with multi-criteria decision analysis to assess rotation alternatives for smallholders has been published before. — [MODSIM 2018](https://www.modsimworld.org/papers/2018/MODSIM_2018_Nisperos.pdf)

**Water and remote sensing (data sources more than advisors)**
- OpenET launched in October 2021 for 17 western US states. It runs six satellite ET models at 30 m, field scale. It reached 23 states in 2023 and has since been reported to cover all 48 contiguous states (Collection v2.1). It is US-only, so it is not usable for Jordan. — [DRI](https://www.dri.edu/consortium-launches-new-online-water-data-platform-to-transform-water-management-in-the-western-united-states-as-droughts-intensify/); [Maven's Notebook Dec 2025](https://mavensnotebook.com/2025/12/17/openet-expands-satellite-based-water-use-data-across-48-states-providing-critical-information-to-farmers-and-water-managers-across-the-nation); [OpenET v2.0 readme](https://openet.dri.edu/readme/openet_collection_v2_0.md)
- FAO WaPOR v3 has a Jordan web portal integrated into the Jordan Valley Authority (JVA) water information system. It provides water-use statistics, hybrid efficiency indicators and seasonal crop water use at district and farm level, and flags high- and low-productivity areas using WaPOR v3 Level 3 data at 20 m. Its services are reached through WaPOR APIs that are "being published gradually". — [FAO WaPOR Jordan](https://www.fao.org/in-action/remote-sensing-for-water-productivity/country-activities/jordan/3/en)
- The Irrigation Performance Assessment and Diagnostics Tool (IPADT), built by IWMI, JVA and FAO for the Northern Jordan Valley, uses these inputs: WaPOR v3 actual ET and net primary production (NPP) at 20 m monthly for 2018–2025, reference ET at 5 km, CHIRPS rainfall, and JVA supply records. — [ESA conference abstract](https://stateo26.esa.int/iframe-agenda/files/ID_138.pdf)
- Digital Earth Africa's cropland extent map is a 10 m, 2019-only, Sentinel-2 + Random Forest product. Its `prob` band "can be used as a proxy for the uncertainty". It is CC-BY 4.0 and hosted on AWS S3. The Arabian peninsula has a sibling docs site, DE Arabia. — [DE Africa docs](https://docs.digitalearthafrica.org/en/latest/data_specs/Cropland_extent_specs.html); [DE Arabia notebook](https://dearabia-docs.readthedocs.io/sandbox/notebooks/Datasets/Cropland_extent.html)
- NASA Harvest has shown that satellites can evaluate crop-rotation practice (corn/soy) without ground data. It also has data-fusion work on crop cycles for Egyptian smallholders, which is a relevant MENA precedent. — [NASA Harvest rotation pub](https://www.nasaharvest.org/news/publication-highlights-reliability-of-satellite-data-for-evaluation-of-crop-rotation-practices); [NASA Harvest Egypt](https://www.nasaharvest.org/news/bringing-clarity-to-crop-cycles-how-data-fusion-is-advancing-smallholder-agriculture-in-egypt)
- NASA Earth Observatory reports that the yield benefit of rotation is generally larger in rainier conditions and varies with weather. This is useful context when explaining rotation benefits in arid Jordan. — [NASA Earth Observatory](https://science.nasa.gov/earth/earth-observatory/how-to-rotate-crops-154601/)

**Arabic-language farm apps**
- Ma' Al Muzare' (NARC + FAO, Jordan, launched June 2021) is an Arabic/English extension app covering weather and crop calendar, harvest, a marketplace and an expert-to-farmer forum. 708 people were trained to use it. I found no evidence of whether it is still maintained. — [UN Jordan press release](https://jordan.un.org/en/node/141750); [Jordan Times](https://jordantimes.com/node/345703)
- ICBA's Nabat app is AI-based crop-disorder detection in Arabic, English and French. The University of Sharjah's My FarmWell is an AI chatbot on irrigation and water regulations. — [ICBA](https://www.biosaline.org/news/2022-12-12-13203); [App Store My FarmWell](https://apps.apple.com/us/app/-/id6743693834)

### Inferences
- **Gap to target:** a field-level, satellite-informed comparison of 2–3 rotation strategies for arid or irrigated Jordan. Each option would get a plain-language Arabic "why" and an explicit confidence or "needs local review" flag. The Arabic apps I found cover extension content and disease detection, not rotation comparison. WaPOR and IPADT cover water productivity, not crop choice.
- **Ideas to borrow:** the MCCC goal-weighted ranking and grey crop-occupancy bar (which maps directly to a "bare-field period" timeline), COMET-Farm's baseline-vs-scenarios report, and DE Africa's use of classifier probability as a stand-in for uncertainty.
- **Credible Jordan data story:** WaPOR v3 20 m AETI/NPP plus CHIRPS rainfall, which repeats the IPADT inputs and can be pitched as aligned with JVA practice.

### Gaps
- I did not research Climate FieldView, CropX, USDA Web Soil Survey, CDL, GEOGLAM Crop Monitor or AquaCrop features in this pass (tool-call budget). Their descriptions in the report should come from other notes or be omitted. General knowledge, unsourced: FieldView is yield and planting-data analytics for large row-crop farms; CropX is soil-sensor irrigation advice; CDL is US-only annual crop-type maps; AquaCrop is FAO's water-driven crop yield model and is relevant for arid areas.
- I could not confirm an official Space Apps 2026 "Field Shift" challenge page through search. Use the team's own copy of the challenge text.
- I did not verify whether the WaPOR Jordan portal is publicly accessible without a JVA login.

## Hackathon tech stack options

### Takeaway
For a 48-hour student team, use **Streamlit + leafmap/geemap (folium backend) + Plotly**, deployed on Streamlit Community Cloud or Hugging Face Spaces. Precompute the satellite data for 1–3 demo fields so the live demo never calls Earth Engine. Only pick Next.js + MapLibre if a member already ships React quickly and the team wants polished Arabic RTL UI.

### Cited Findings
- Streamlit Community Cloud limits (docs dated Feb 2024): CPU 0.078–2 cores, memory 690 MB–2.7 GB, storage up to 50 GB, "may change at any time". Apps sleep after 12 hours without traffic. Over-limit apps throttle or fail; rebooting resets usage, and caching with `st.cache_data` helps. — [Streamlit docs: resource limits](https://docs.streamlit.io/knowledge-base/deploy/resource-limits); [Streamlit manage app](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app)
- Hugging Face Spaces CPU Basic is free: 2 vCPU, 16 GB RAM, 50 GB disk. It sleeps after about 48 hours idle and a visit wakes it. Free accounts cannot set a custom sleep time. Free users can run up to about 8 cpu-basic Spaces (forum, may be enforced dynamically). — [HF Spaces GPU/hardware docs](https://huggingface.co/docs/hub/main/spaces-gpus); [HF manage spaces](https://huggingface.co/docs/huggingface_hub/guides/manage-spaces)
- Earth Engine noncommercial quota tiers took effect on April 27, 2026. Community tier: 150 EECU-hours/month, the default. Contributor tier: 1,000 EECU-hours/month; it needs a billing account but noncommercial use is not charged. Partner tier: needs an application that takes weeks. Over quota, the project drops to a "restricted mode with lower processing power". Projects must register as noncommercial in the Cloud console and re-verify each year. — [GEE noncommercial tiers](https://developers.google.com/earth-engine/guides/noncommercial_tiers)
- leafmap is a spin-off of geemap. Streamlit apps render maps with `leafmap.foliumap` and `m.to_streamlit(height=500)`. The opengeos `streamlit-geospatial` multipage template already runs on HF Spaces. A leafmap HF Space draws polygons on the map and computes values from Cloud-Optimized GeoTIFFs with rasterio, which is close to the "draw field, get stats" pattern. — [opengeos/streamlit-geospatial](https://www.github.com/opengeos/streamlit-geospatial/blob/master/streamlit_app.py); [giswqs Streamlit Space](https://huggingface.co/spaces/giswqs/Streamlit/blob/main/apps/home.py); [boettiger-lab leafmap Space](https://huggingface.co/spaces/boettiger-lab/leafmap/blob/main/app.py); [leafmap JOSS](https://joss.theoj.org/papers/10.21105/joss.03414.pdf)
- NASA GIBS serves tiles through WMTS, TWMS and KML, and NASA's GitHub has working Leaflet and OpenLayers examples. Endpoints are organized by projection (EPSG 4326/3857/3413/3031) and type (best/nrt/std). Time is passed as `TIME=YYYY-MM-DD`, or in the path for REST. Without a date you get today's tiles, which are often empty. For 3857, clamp the extent slightly, for example to −179.999. — [Earthdata GIBS wiki](https://wiki.earthdata.nasa.gov/x/hQ3gB); [gibs-web-examples](https://github.com/pamilerinid/gibs-web-examples)
- MapLibre GL JS: older versions need `setRTLTextPlugin` (mapbox-gl-rtl-text, lazy-loaded) to draw Arabic labels correctly. A v6.9.0 release note says RTL now works natively and the plugin is deprecated. I found that only on an aggregator, so verify it. — [MapLibre RTL example](https://maplibre.org/maplibre-gl-js/docs/examples/add-support-for-right-to-left-scripts/); [newreleases v6.9.0](https://newreleases.io/project/github/maplibre/maplibre-gl-js/release/v6.9.0)

### Inferences
- **Recommended stack:**
  - Python 3.11
  - Streamlit
  - `leafmap.foliumap` or `streamlit-folium` with the Draw plugin for polygons
  - Plotly for the timeline, radar and bar charts
  - pandas/geopandas
  - `earthengine-api`/geemap **only in offline prep scripts** that export per-field CSV/GeoJSON into the repo
  - optional LLM call, with its result cached to JSON for the demo

  Skipped: FastAPI and a separate frontend. Add them only if a mobile or React UI becomes a judged requirement.
- **Hosting:** HF Spaces' 16 GB RAM beats Streamlit Cloud's ~2.7 GB if geopandas or rasters are loaded. Streamlit Cloud has the simplest GitHub deploy. Deploy to both as mutual backup.
- **Earth Engine quota:** 150 EECU-hours is plenty for prep on a few fields, but live queries during judging are a risk (latency, auth on the cloud host). Precompute everything.
- **Map tiles:** use GIBS true-color/NDVI tiles as background "NASA layer" eye candy with a fixed date. Field statistics should come from precomputed Sentinel-2/Landsat/WaPOR data, not tiles.

### Gaps
- I found no official 2025/2026 update to Streamlit Cloud limits. Confirm them at the event.
- I did not confirm the exact GIBS layer ID for an NDVI product. Check GetCapabilities in prep.
- I did not evaluate Vercel's free-tier limits in this pass.

## AI ("SI") approaches and uncertainty presentation

### Takeaway
Make the core a transparent rule-based multi-criteria score: farmer priority weights × per-criterion scores per rotation. Add light satellite analytics (NDVI anomaly z-score, seasonal-curve clustering), and use an LLM **only** to turn the computed numbers and cited rules into plain Arabic/English text. Show confidence per criterion and an explicit "needs local review" flag. The evidence that LLMs give wrong or generic farm advice is strong.

### Cited Findings
- The literature criticizes rotation models for single-criterion (money) optimization and argues for multi-criteria assessment. — [Dury et al., HAL](https://hal.archives-ouvertes.fr/hal-00930508); [MODSIM 2018 MCDA + crop sim](https://www.modsimworld.org/papers/2018/MODSIM_2018_Nisperos.pdf)
- A Reichman University study (Nature Food) found that ChatGPT 3.5/4 farming advice for African farmers contained inaccuracies "that could lead to… crop losses". CGIAR's summary says the answers were "too generic… or not practicable for smallholders". — [EurekAlert](https://www.eurekalert.org/news-releases/1046068); [CGIAR](https://www.cgiar.org/news-events/news/can-we-trust-ai-to-generate-agricultural-extension-advisories)
- An AIES paper proposes "contextual advisory reliability": a hallucination-free answer can still be risky advice, and a trivial hallucination may carry little risk. Judge advice by its consequences for the land. — [AAAI AIES](https://ojs.aaai.org/index.php/AIES/article/download/43268/50828/47374)
- Real-world harm has been reported: a Chinese farmer followed AI herbicide advice on 24.7 acres without cross-checking and lost the crop. — [TechRepublic](https://www.techrepublic.com/article/news-farmer-ai-pesticide-advice-crop-loss-china-apac/)
- A 2026 RAG advisory paper reports lower crop-fact hallucination for retrieval-grounded open models (about 6–7% vs 14.3% for GPT-4). I could not verify these figures beyond a secondary summary. — [J. Agric. Eng.](https://www.agroengineering.org/jae/article/view/1908)
- Precedent for showing uncertainty: DE Africa ships a classifier probability band as an explicit uncertainty proxy. — [DE Africa docs](https://docs.digitalearthafrica.org/en/latest/data_specs/Cropland_extent_specs.html)

### Inferences
- **Scoring:** `score(rotation) = Σ w_i · s_i`. The weights `w_i` come from the farmer's sliders and are normalized to sum to 1. Criteria could include water use (from WaPOR/ET or crop coefficient × ET0), soil cover / bare days, income, soil nitrogen (legume credit), risk and labor. Each `s_i` is in 0–1 and comes from a small crop-parameter table with a cited source per row. This is deterministic, testable and explainable ("water counted for 40% of the score and option B uses about 30% less").
- **Confidence per criterion:** high when the value comes from field-specific satellite data, medium when it comes from regional tables, low when it is assumed. Overall confidence is the weakest link, or a weighted mix. Raise a **"needs local review"** flag when confidence is low on a high-weight criterion, when the top two options are within ~5% of each other, or when the field's NDVI history is anomalous.
- **Sensitivity check as an uncertainty story:** perturb the weights ±10% and check whether the winner changes. If it does, show "close call". This is cheap and judge-friendly.
- **Satellite analytics:** an NDVI time series per field from Sentinel-2. Anomaly = z-score against the multi-year same-month mean. A simple k-means on the seasonal curves (k=3–4) labels each field's historical pattern (e.g. winter cereal, summer irrigated, fallow). This infers past rotations and bare periods with no ground data, in the spirit of the NASA Harvest rotation work.
- **LLM role:** the prompt includes the computed JSON (scores, confidence, flags, data sources). The LLM writes 3–4 short sentences per option in Arabic and English, may cite only the provided facts, and must keep the review flag. Cache the outputs for the demo so it works offline. Never let the LLM pick the winner.

### Gaps
- I found no published study on how low-literacy farmers in the Middle East and North Africa interpret confidence displays. The UX choices below are design inference.

## UX patterns for low-literacy farmers, bilingual AR/EN

### Takeaway
Use one screen per step:
1. Draw or pick a field.
2. Set priorities with three to five big sliders or icon cards.
3. See three rotation options as side-by-side cards. Each card shows a 12-month color timeline with bare-field periods hatched, a traffic-light confidence badge, and a two-sentence reason.

Arabic is the default with full RTL, and English is a toggle.

### Cited Findings
- The MCCC tool lets farmers choose goals, ranks options by those goals, and shows the cash crop's field occupancy as a bar on a seasonal chart. This is a proven pattern for the priorities → ranked list → calendar flow. — [Purdue Ag News](https://ag.purdue.edu/news/2020/09/improved-tool-can-help-midwest-farmers-with-cover-crop-decisions.html)
- COMET-Farm's baseline-vs-multiple-scenarios report with "easy to read tabular and interactive graphical" output is a precedent for side-by-side comparison. — [Farmland Information Center](https://farmlandinfo.org/tools/comet-farm/)
- Drawing a polygon on a leafmap map in a Streamlit/HF Space and computing statistics from it already exists as a template. — [boettiger-lab leafmap Space](https://huggingface.co/spaces/boettiger-lab/leafmap/blob/main/app.py)
- Arabic map labels need RTL shaping: the plugin on MapLibre before v6.9, reportedly native after. — [MapLibre RTL example](https://maplibre.org/maplibre-gl-js/docs/examples/add-support-for-right-to-left-scripts/)
- Jordan's Ma' Al Muzare' app is already Arabic/English with a crop calendar, so bilingual calendars match what farmers there have used before. — [UN Jordan](https://jordan.un.org/en/node/141750)

### Inferences
- **Priority sliders:** "Save water 💧", "More income 💰", "Healthier soil 🌱", "Less work 🧑‍🌾", "Less risk 🛡️". Show icons and words, 3–5 options at most, with presets ("Water is scarce this year").
- **Timeline:** a Plotly horizontal bar chart (`px.timeline`) with one row per option and months on the x-axis. Use crop colors, hatched or grey "bare soil" blocks, and a bare-days count next to each row. In Arabic, reverse the month axis (`autorange="reversed"`) so time runs right to left.
- **RTL in Streamlit:** inject CSS `direction: rtl; text-align: right` on the main container when Arabic is selected. Keep a `t(key)` dictionary in one `i18n.json` with AR and EN strings. Use an Arabic-friendly font such as Noto Naskh/Kufi Arabic or Cairo from Google Fonts. Keep numbers in Western digits unless the team decides otherwise.
- **Confidence badge:** green, amber or red, plus the words "confident / check with extension officer". Never show a bare percentage alone.
- **Accessibility:** large tap targets, text-to-speech of the explanation (optional; browser `speechSynthesis` supports Arabic voices on many devices), and icons next to every number.

### Gaps
- I did not verify that Streamlit has a native RTL option. The CSS-injection approach is an inference from common practice.
- I found no usability study specific to Jordanian farmers and digital decision-support tools.

## Recommended 48-hour MVP split and pre-event prep

### Takeaway
Scope the demo to 1–3 pre-selected real fields in Jordan (e.g. the Jordan Valley plus one rain-fed highland field). Use three fixed candidate rotations and precomputed data, and build the interactive scoring, timeline, explanation and confidence on top. Everything satellite-related should be done before or early, and offline.

### Cited Findings
- Earth Engine registration and noncommercial verification happen in the Cloud console. The Community tier is the default and over-quota projects are throttled, so register early. — [GEE noncommercial tiers](https://developers.google.com/earth-engine/guides/noncommercial_tiers)
- WaPOR v3 L3 (20 m) exists for Jordan, and IPADT used monthly AETI and NPP for 2018–2025 plus CHIRPS. These are realistic prep downloads. — [FAO WaPOR Jordan](https://www.fao.org/in-action/remote-sensing-for-water-productivity/country-activities/jordan/3/en); [ESA abstract](https://stateo26.esa.int/iframe-agenda/files/ID_138.pdf)
- Free hosts sleep when idle (Streamlit Cloud after 12 h, HF after about 48 h). Wake the app before judging. — [Streamlit docs](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app); [HF docs](https://huggingface.co/docs/huggingface_hub/guides/manage-spaces)

### Inferences
- **Prep before the event (if allowed by the rules; otherwise just practice it):**
  1. Register the GEE noncommercial project.
  2. Write a script that exports a Sentinel-2 NDVI monthly series and CHIRPS rainfall for chosen polygons to CSV.
  3. Download WaPOR AETI for the same polygons.
  4. Build a crop-parameter table (Kc, season months, water need, legume yes/no, rough income) for about 8 Jordanian crops: wheat, barley, lentil, chickpea, vetch, tomato, cucumber, potato, olive as fixed. Cite FAO-56 and Jordan Ministry of Agriculture or NARC sources.
  5. Start the Arabic string file.
  6. Hello-world deploy of Streamlit + leafmap on both hosts.
- **Day 1 (hours 0–24):**
  - Data person loads the precomputed CSVs and builds the NDVI chart, anomaly and k-means pattern label.
  - Logic person writes the scoring function, confidence and flags, plus one `assert` self-check (e.g. water weight = 1 makes the lowest-water option win).
  - UI person builds the map, field pick/draw, sliders and the three option cards with the timeline.
  - By hour 24, an end-to-end ugly version is deployed.
- **Day 2 (hours 24–40):**
  - LLM explanations, cached to JSON.
  - Arabic RTL polish.
  - Weight-sensitivity "close call" indicator.
  - "Needs local review" banner.
  - NASA GIBS background layer.
- **Hours 40–48:** freeze features, record a backup demo video, write the data-sources slide (NASA and other data used, with honest limitations), and rehearse a 3-minute story about one farmer and one field.
- **Cut first if behind:** live polygon drawing (keep pre-picked fields), the LLM (fall back to template sentences), and clustering.
