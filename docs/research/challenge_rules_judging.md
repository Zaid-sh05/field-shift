# Field Shift: Adapting Farms with NASA Data — Official Challenge, Rules & Judging (Space Apps 2026)

> Research date: 2026-11-11. Event weekend: 14–15 Nov 2026.
> **Important access caveat:** every page on spaceappschallenge.org failed to load from this research environment ("unable to get local issuer certificate", a local TLS/proxy issue, not a site outage). Proxy and cache workarounds were blocked. So the official challenge page and its **Resources tab could not be read directly**. Everything below about the challenge text comes from search-engine extracts, the official YouTube video transcript, and team repos that quote the brief. **Action for team:** open the challenge page in a browser and copy the Resources tab into this folder.

## 1. What the official challenge page contains (incl. Resources tab)

### Takeaway
The challenge asks for a **decision-support tool that combines NASA Earth observations with local soil information, crop characteristics and farmer priorities**, so farmers can explore **crop-rotation strategies** that improve soil health and adapt to changing climate. The tool should support farmers' own judgment, not replace it. It is rated Intermediate/Advanced, with subjects Earth Science, Software, and Arts & Multimedia. The verbatim Resources list could NOT be retrieved.

### Cited Findings
- Official page URL: https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/ — [Search index](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/)
- Search summary of the page: "Create decision-support tools pairing NASA Earth observations with local farming data". Difficulty: Intermediate / Advanced. Subjects: Earth Science, Software, Arts & Multimedia. It is 1 of **14** 2026 challenges. — [Space Apps page via search](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/); [Romania Journal: 14 challenges](https://www.romaniajournal.ro/society-people/science/nasa-space-apps-challenge-2026-launches-14-global-challenges/)
- Brief as quoted by a team repo: "Create a decision-support tool that uses NASA Earth observations along with local soil information..." (the repo shortens it), plus crop characteristics and farmer priorities, to build rotation scenarios. — [FarmStack repo](https://github.com/anirban-islam/farmstack)
- Search extract across repos echoing the brief: help farmers "explore rotation strategies that strengthen soil health and adapt to changing conditions". Supporting farmer judgment and local expertise, rather than replacing them, is part of the core requirement. — [samuelakosaonyejekwe/fieldshift (search extract; repo now 404)](https://github.com/samuelakosaonyejekwe/fieldshift); [RavenEibu/field-shift](https://github.com/RavenEibu/field-shift)
- One team repo calls it "NASA Space Apps 2026, **Challenge 7**". This is unconfirmed numbering. — [RotaShift repo](https://github.com/XtremeseOISHEE/RotaShift)
- **Datasets teams cite (NOT the confirmed official Resources list):**
  - NASA POWER (API, monthly and climatology)
  - SMAP L4 soil moisture (SPL4SMGP: root zone 0–100 cm, surface 0–5 cm, 9 km)
  - GPM IMERG precipitation
  - MODIS/VIIRS NDVI (e.g., MOD13Q1, 250 m, 16-day)
  - ECOSTRESS
  - OpenET/Landsat
  - HLS
  - GRACE-FO
  - NASA Earthdata CMR
  - NASA GIBS tiles
  - Non-NASA: FAO Ecocrop, FAO-56 crop parameters, AmeriFlux US-Ne1
  - Sources: [FarmStack](https://github.com/anirban-islam/farmstack); [BlinkFarms](https://github.com/umar-essayed/BlinkFarms-NASA-SpaceApps); [search extract of Field Shift repos](https://github.com/shahkhalid030056-prog/space2earth-field-shift); [sagar25446-prog/FieldShift-NASA](https://github.com/sagar25446-prog/FieldShift-NASA)
- One repo notes that SMAP root-zone soil moisture is model-assimilated and is not the same as plant-available water. Interpreting crop stress needs soil field capacity and wilting point. — [search extract, Field Shift repos](https://github.com/umar-essayed/BlinkFarms-NASA-SpaceApps)

### Inferences
- The challenge's three subjects include Arts & Multimedia, so games, visualizations and storytelling entries are in scope, not only software.
- All four people in the video work at NASA Johnson Space Center (see Q2), and two of them work with **ISS astronaut photography of Earth**. That makes it likely the Resources tab lists astronaut-photography sources such as the Gateway to Astronaut Photography of Earth, and that judges would value this data. This is unverified; check the tab.

### Gaps
- The verbatim Summary, Background, Objectives and Potential Considerations, and the **full Resources tab** (NASA, partner-agency such as CSA/ESA/JAXA/CNES, and other links with URLs) could not be read because of the TLS error. Copy them manually.
- Any updates or FAQ posted on the challenge page: unknown, for the same reason.

## 2. The challenge YouTube video (https://youtu.be/cF0U2WXsM7o)

### Takeaway
The video is a 3 min 37 s trailer titled "2026 Challenge | Field Shift: Adapting Farms with NASA Data". It frames the task as turning NASA Earth-observation signals (rainfall, soil moisture, heat, vegetation, water) into a tool that compares rotations, shows trade-offs and risk, and makes **uncertainty visible**. The challenge author and three subject-matter experts from NASA Johnson Space Center introduce themselves.

### Cited Findings
All of the following come from the transcript and metadata, extracted with the MarkItDown YouTube converter: [YouTube](https://www.youtube.com/watch?v=cF0U2WXsM7o).
- Title: "2026 Challenge | Field Shift: Adapting Farms with NASA Data". Runtime 3:37. The description links back to the challenge page; the extractor returned that text in Arabic, partly garbled.
- Narration (key lines): "Heat shifts, rainfall changes, water becomes less certain, soil loses nutrients, and farmers must decide what comes next... NASA's public Earth observation data gives us new ways to listen. Rainfall, soil moisture, heat, vegetation, water. Different observations, different scales, pieces of the same story. Your mission: turn these observations into a tool that helps explore what could come next. **Compare rotations, reveal trade-offs, understand risk, make uncertainty visible.** Build an [AI] model, an interactive map, a visualization, a decision support tool. Or build something none of us has imagined yet."
- People in the video:
  - **Sadie Burnett Boudro** (name as auto-transcribed): challenge author; engineer and developer at NASA JSC working on Artemis mission management and integration.
  - **Mani Deep Gogineni**: JSC data solutions architect working on custom web apps and tooling.
  - **William Stefanov**: JSC senior Earth system scientist working with ISS Earth imagery for disaster response and remote sensing; subject-matter expert for this challenge.
  - **Alex Stoken**: JSC data scientist in the Earth Science and Remote Sensing Unit; machine-learning expert who applies ML to astronaut photography of Earth.

### Inferences
- The phrase "make uncertainty visible" is a strong signal of what judges want: show confidence ranges and data limitations, not a single "answer".
- A good pitch will mention multi-scale data fusion ("different scales"): coarse POWER/SMAP grids combined with field-level local inputs.
- An ML component built on imagery, ideally astronaut photography, would match the SMEs' expertise.

### Gaps
- Names come from auto-transcription, so spellings may be off (e.g., "Boudro").
- The full English description text was not retrieved.

## 3. Space Apps 2026 rules: judging, awards, submission, AI, data, teams, timeline, Jordan

### Takeaway
Judging uses five criteria: Influence/Impact, Creativity, Validity, Relevance, and Presentation, weighted equally. Each submission needs a project page with a 30-second video **or** a 7-slide deck (English, or English subtitles), a project link such as a repo or demo, and **disclosure of any AI use**. Teams have at most 6 members. Global Finalists are announced in Dec 2026 and Global Winners in Jan 2027. A 2026 Amman event listing could not be confirmed.

### Cited Findings
**Judging criteria**
- The criteria are Influence/Impact, Creativity, Validity, Relevance and Presentation. Each is defined below.
  - **Influence**: how far the project could reach, and whether the problem it addresses is major or minor.
  - **Creativity**: originality and ingenuity.
  - **Validity**: whether the solution is scientifically valid, whether it does what it sets out to do, and whether it could work in the real world.
  - **Relevance**: whether it answers the chosen challenge, and how complete, technically feasible and user-friendly it is.
  - **Presentation**: how well the team tells the story of the problem, the solution and why it matters.
  - The guide tells teams to give Presentation the same attention as the other four. — [Judging & Awards Guide](https://www.spaceappschallenge.org/resources/judging-awards-guide)
- A third-party page says the 2025 edition used "Impact, Creativity, Validity, Relevance, and Presentation". The 2026 guide was not read directly. — [third-party mirror](https://66b8783ce930a118fc45939c--voluble-conkies-fba672.netlify.app/judgingCriteria)
- Projects entered in "Create Your Own Challenge" are not eligible for Global Judging. — [Judging & Awards Guide (search extract)](https://www.spaceappschallenge.org/resources/judging-awards-guide)

**Awards** (2024–2025 editions; no 2026 list was found)
- There are 10 Global Awards. The 2025 categories were Best Use of Science, Best Use of Data, Best Use of Technology, Galactic Impact, Best Mission Concept, Most Inspirational, Best Use of Storytelling, Global Connection, Art & Technology, and Local Impact. — [NASA: 2025 Global Winners](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-announces-2025-international-space-apps-challenge-global-winners/)
- An executive committee reviews the Global Finalists to pick the 10 Global Winners. — [Space Apps 2025 awards (search extract)](https://www.spaceappschallenge.org/2025/awards/global-winners/)

**Submission requirements** (Project Submission Guide; the 2026 version is listed as released 13 Nov 2026)
- The demo is either a 7-slide presentation or a video of **no more than 30 seconds**. Videos are hosted externally because they cannot be uploaded to the site. Videos need English subtitles and slides must be in English. — [Project Submission Guide (search extract)](https://www.spaceappschallenge.org/resources/project-submission-guide/)
- Project submission opens 14 Nov 2026 at 09:00 local time. — [Project Submission Guide (search extract)](https://www.spaceappschallenge.org/resources/project-submission-guide/)
- Videos must not include recognizable names, voices or likenesses of anyone under 18. Adults who appear must consent to NASA using their name and likeness. — [Project Submission Guide (search extract)](https://www.spaceappschallenge.org/resources/project-submission-guide/)

**AI rules**
- AI tools are permitted, but their use must be disclosed. AI-generated images and video need a **visible watermark** saying they are AI-generated. AI-generated audio, code and data need an acknowledgement. Judges "will consider originality, intent, and execution in the context of AI-assisted work." — [Project Submission Guide (search extract)](https://www.spaceappschallenge.org/resources/project-submission-guide/)

**Data**
- Participants are encouraged to use NASA data and data from partner space agencies. — [AWS Builder article](https://builder.aws.com/content/3IMmoniLChLMLTT1gfCWtHYdxL6/nasa-space-apps-challenge-2026-what-it-is-and-how-to-join)
- The Validity and Relevance criteria above imply that NASA data must be central to the project. I found no exact 2026 wording that makes NASA data mandatory (see Gaps).

**Teams and eligibility**
- Teams are limited to **6 people**; 4–5 is ideal. All ages may take part, and under-18s follow the Terms & Conditions and need parental consent. — [Participant FAQs](https://www.spaceappschallenge.org/resources/participant-faqs/); [Kodland (third-party)](https://www.kodland.org/blog/nasa-space-apps-challenge-2026)
- To be eligible for global judging, a Universal Event team needs at least 2 participants and a Local Event team needs at least 1. Each team picks one challenge. — [Participant FAQs](https://www.spaceappschallenge.org/resources/participant-faqs/); [AWS Builder](https://builder.aws.com/content/3IMmoniLChLMLTT1gfCWtHYdxL6/nasa-space-apps-challenge-2026-what-it-is-and-how-to-join)
- The full rules are in the Terms & Conditions. — [2026 Participant Terms and Conditions](https://www.spaceappschallenge.org/legal/)

**Timeline**
- Registration opened 26 Aug 2026 and the hackathon runs **14–15 Nov 2026**. Judging happens first at the local or Universal Event, then globally. — [AWS Builder](https://builder.aws.com/content/3IMmoniLChLMLTT1gfCWtHYdxL6/nasa-space-apps-challenge-2026-what-it-is-and-how-to-join)
- **Dec 2026**: Global Nominees, Finalists and Honorable Mentions are announced. **Jan 2027**: Global Winners are announced. — [Participant FAQs](https://www.spaceappschallenge.org/resources/participant-faqs/)
- Participants can attend a Local Event (in person or virtual) or the online Universal Event. — [AWS Builder](https://builder.aws.com/content/3IMmoniLChLMLTT1gfCWtHYdxL6/nasa-space-apps-challenge-2026-what-it-is-and-how-to-join)
- Also available: a Virtual Bootcamp resource page. — [Virtual Bootcamp](https://www.spaceappschallenge.org/resources/virtual-bootcamp/)

**Jordan** (older editions only)
- **2025**: Zain Innovation Campus (ZINC) ran its 5th Amman edition in Oct 2025, with 249 participants from Amman, Irbid and Aqaba. — [Petra (search extract)](https://pt1.petra.gov.jo/en/news/zinc-organizes-local-edition-of-nasas-space-apps-challenge)
- **2025**: Jordan University of Science and Technology (JUST) hosted a site, and Petra reported the event ending there. — [Petra](https://pstg1.petra.gov.jo/en/news/nasa-space-apps-challenge-concludes-at-just)
- **2024**: there was an IEEE-listed Irbid event. — [IEEE vTools](https://events.vtools.ieee.org/m/433531)
- An Amman Arab University "Astro Code 2026" IEEE event exists, but its link to Space Apps is unverified. — [IEEE vTools](https://events.vtools.ieee.org/m/554517)

**2025 scale** (for context)
- Over 114,000 participants, 551 local events in 167 countries and territories, and more than 11,500 submissions. — [NASA](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-announces-2025-international-space-apps-challenge-global-winners/)

### Inferences
- With equal weights and a 30-second demo, a polished story is worth as much as the code. Plan the 30-second video and the 7 slides from the start.
- Teams usually win local awards first, then become Global Nominees. Find out who the local judges are at your Jordan event.

### Gaps
- The 2026 Judging & Awards Guide and Submission Guide were not read directly (TLS error), and the 2026 award list is unconfirmed.
- No exact 2026 rule text was found on whether NASA data is mandatory.
- No 2026 Jordan or Amman local event listing was confirmed. Check the Locations page or contact ZINC.
- One search-tool summary mentioned an "AI renamed to Super Intelligence" executive order. It is unverified and deliberately excluded.

## 4. Past winners on agriculture challenges and why they won

### Takeaway
**2025** (older edition): the only agriculture Global Winner was **Zumorroda-X** from Egypt, which won **Art & Technology** in the "NASA Farm Navigators" challenge with farmer-perspective mini-games. The Local Impact winner, QUEÑARIS from Peru, worked on water and reforestation. The pattern: storytelling and gamification, plus concrete local impact, beat generic dashboards.

### Cited Findings
- **2025, Art & Technology: Zumorroda-X** (Egypt), challenge "NASA Farm Navigators: Using NASA Data Exploration in Agriculture". Mini-games where players "step into the shoes of a farmer" around the world and learn how farmers adapt to heat waves, flooding and similar hazards. — [NASA 2025 winners](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-announces-2025-international-space-apps-challenge-global-winners/); [2025 challenge page](https://www.spaceappschallenge.org/2025/challenges/nasa-farm-navigators-using-nasa-data-exploration-in-agriculture/)
- **2025, Local Impact: QUEÑARIS** (Peru), BloomWatch challenge. Tackles water scarcity in Arequipa by combining native microorganisms, NASA satellite data, drones and AI to find reforestation sites and monitor ecosystems. — [NASA 2025 winners](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-announces-2025-international-space-apps-challenge-global-winners/)
- **2025, Best Use of Technology: Twisters** (Mexico). SkySense, which uses NASA Earth observation data plus AI for hyperlocal weather risk and timing advice. Not agriculture, but the same "decision support from EO" pattern. — [NASA 2025 winners](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-announces-2025-international-space-apps-challenge-global-winners/)
- **2025**: "Henry's Farm Adventure", a pixel-style game about farmers' challenges using NASA data, is reported as a 2025 winner. Its challenge and award were not confirmed. — [search extract, Space Apps 2025 winners](https://www.spaceappschallenge.org/2025/meet-the-2025-global-winners/)
- **Earlier edition, year unconfirmed**: an ESA blog describes a Rome team (CROPP) as a global winner with a project on the future of agriculture and food production. — [ESA blog](https://blogs.esa.int/rocketscience/?p=2192)
- **2024**: Global Winners were announced 16 Jan 2025. No agriculture winner was confirmed in what I found. — [NASA 2024 winners](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-international-space-apps-challenge-announces-2024-global-winners/)

### Inferences
- Patterns that win:
  - a specific local user and place (Arequipa; farmers by region)
  - a clear human story
  - NASA data visibly driving the experience
  - an angle that fits an award category (Art & Technology, Local Impact)
- For a Jordan team, a Jordan-specific story could target Local Impact: water scarcity, rotations in rainfed vs. Jordan Valley farming, and Arabic/English bilingual UI. This also fits the challenge's "farmer priorities" and "local soil" language.
- Many teams worldwide are already building similar crop-rotation dashboards. Ten or more public "Field Shift 2026" repos exist, most of them POWER-based rotation planners. Differentiate with uncertainty visualization, local ground data and storytelling.

### Gaps
- The 2024 and 2023 agriculture winners were not verified, because the official winners pages on spaceappschallenge.org did not load.

## 5. Updates posted to the challenge page before the hackathon

### Takeaway
Unknown. The challenge page could not be loaded.

### Cited Findings
- None. The page was blocked by the local TLS error.

### Inferences
- The Project Submission Guide for 2026 is reportedly released on 13 Nov, the day before the event. Re-check the guides and the challenge page that day. — [Project Submission Guide (search extract)](https://www.spaceappschallenge.org/resources/project-submission-guide/)

### Gaps
- All challenge-page updates and FAQs. Check manually.
