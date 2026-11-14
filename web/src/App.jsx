import { useEffect, useMemo, useState } from "react";
import data from "./data.json";
import { evaluate, nextSeason, predictVigor } from "./engine.js";
import { BADGE, Backdrop, FieldMap, LineChart, Reveal, ScoreRing, Slider, useCountUp } from "./ui.jsx";

// Strings that only this site needs. Everything else comes from the shared i18n.json (exported in data.json).
const LOCAL = {
  ar: {
    brand_tag: "تحدي ناسا Space Apps 2026 · مرو، إربد",
    hero_title: "أي دورة زراعية تناسب حقلك؟",
    hero_text: "قارن ثلاث دورات زراعية ببيانات أقمار ناسا التي فحصناها مقابل القياس الأرضي. نعرض لك الأرقام ومقدار الثقة بها، والقرار يبقى لك.",
    hero_cta: "ابدأ باختيار حقلك",
    fact_fallow: "موسم بور رصدته الأقمار منذ 2015", fact_error: "انخفاض خطأ الحرارة بعد تصحيح الارتفاع", fact_drought: "نقص مطر موسم 2024–25 عن المعتاد",
    step_field: "الحقل", step_priorities: "أولوياتك", step_compare: "المقارنة", step_advisor: "المستشار", step_trust: "الثقة",
    field_title: "١. اختر حقلك", field_hint: "اضغط على حقل في الخريطة أو اختره من الأزرار.",
    elevation: "الارتفاع", slope: "الميل", metres: "م",
    priorities_title: "٢. ما الذي يهمّك أكثر؟", less: "أقل أهمية", more: "أكثر أهمية",
    preset_balanced: "متوازن", preset_water: "الماء أولًا", preset_soil: "التربة أولًا", preset_harvest: "الحصاد أولًا",
    compare_title: "٣. قارن الدورات", drought_side: "جفاف", wet_side: "مطر أكثر",
    calendar_title: "متى تكون التربة مزروعة ومتى تكون مكشوفة",
    advisor_section: "٤. مستشار الموسم القادم", trust_section: "٥. إلى أي حد نثق ببيانات ناسا؟",
    pick_field_first: "اختر حقلًا أولًا لتظهر المقارنة.", not_set: "لم أحدّد",
    footer: "Field Shift أداة لدعم القرار وليست بديلًا عن خبرتك أو عن المرشد الزراعي.", code: "الشيفرة والبيانات على GitHub",
    rank: "الترتيب", sources_toggle: "مصادر الأرقام وحدودها",
  },
  en: {
    brand_tag: "NASA Space Apps 2026 · Maru, Irbid",
    hero_title: "Which crop rotation fits your field?",
    hero_text: "Compare three rotations using NASA satellite data that we checked against ground measurements. You see the numbers and how far to trust them. The decision stays yours.",
    hero_cta: "Start by picking your field",
    fact_fallow: "fallow seasons seen by satellites since 2015", fact_error: "less temperature error after the elevation correction", fact_drought: "less rain in 2024–25 than normal",
    step_field: "Field", step_priorities: "Priorities", step_compare: "Compare", step_advisor: "Advisor", step_trust: "Trust",
    field_title: "1. Pick your field", field_hint: "Click a field on the map or use the buttons.",
    elevation: "Elevation", slope: "Slope", metres: "m",
    priorities_title: "2. What matters most to you?", less: "Matters less", more: "Matters more",
    preset_balanced: "Balanced", preset_water: "Water first", preset_soil: "Soil first", preset_harvest: "Harvest first",
    compare_title: "3. Compare the rotations", drought_side: "Drought", wet_side: "More rain",
    calendar_title: "When the soil is cropped and when it is bare",
    advisor_section: "4. Next-season advisor", trust_section: "5. How far do we trust NASA data here?",
    pick_field_first: "Pick a field first to see the comparison.", not_set: "Not set",
    footer: "Field Shift supports your decision. It does not replace your experience or your extension officer.", code: "Code and data on GitHub",
    rank: "Rank", sources_toggle: "Where the numbers come from, and their limits",
  },
};
const PRESETS = {
  preset_balanced: { water: 3, risk: 3, soil: 3, bare: 3, income: 3 },
  preset_water: { water: 5, risk: 5, soil: 2, bare: 1, income: 2 },
  preset_soil: { water: 2, risk: 2, soil: 5, bare: 4, income: 2 },
  preset_harvest: { water: 2, risk: 2, soil: 2, bare: 1, income: 5 },
};
const ROTATION_COLORS = { WW: "#c8553d", WL: "#1f8a5b", WF: "#3b7cc4" };
const CROP_CLASS = { WHEAT: "wheat", LENTIL: "lentil" };
// Isolate as left-to-right so "2024–25" does not flip to "25–2024" inside Arabic text.
const season = (year) => `⁦${year - 1}–${String(year).slice(2)}⁩`;

function useTranslator(lang) {
  return useMemo(() => {
    const table = { ...data.i18n[lang], ...LOCAL[lang] };
    return (key, vars) => (table[key] ?? key).replace(/\{(\w+)\}/g, (_, name) => (vars && name in vars ? vars[name] : `{${name}}`));
  }, [lang]);
}

const Badge = ({ t, level }) => (
  <span className="badge" style={{ "--c": BADGE[level] }}><i />{t("confidence")}: {t(`confidence_${level}`)}</span>
);

function criterionDetail(t, criterion, v) {
  const score = Math.round(v.score), mark = (ok) => (ok ? "✓" : "✗");
  if (criterion === "water") return t("detail_water", { score, pairs: v.crops.map((c) => t("water_pair", { crop: t(`crop_${c.crop}`), demand: c.demand, rain: c.rain })).join(" · ") });
  if (criterion === "risk") return t("detail_risk", { score, dry: v.dry, n: v.seasons });
  if (criterion === "soil") return t("detail_soil", { n: v.legume + v.noRepeat, legume: mark(v.legume), no_repeat: mark(v.noRepeat) });
  if (criterion === "bare") return t("detail_bare", { months: v.greenMonths });
  return t("detail_income", { harvests: v.harvests, of: v.of });
}

function Hero({ t, onStart }) {
  const first = Object.values(data.fields)[0];
  const temp = data.validation.temperature_mean_c;
  const fallow = Object.values(data.fields).reduce((s, f) => s + f.evidence.fallow, 0);
  const errorDrop = Math.round(100 * (1 - temp.power_lapse_corrected["6.5"].mae / temp.power_raw.mae));
  const facts = [[fallow, "", "fact_fallow"], [errorDrop, "%", "fact_error"], [Math.abs(first.evidence.rain_change_pct), "%", "fact_drought"]];
  return (
    <header className="hero">
      <p className="tag">{t("brand_tag")}</p>
      <h1>{t("hero_title")}</h1>
      <p className="lead">{t("hero_text")}</p>
      <button className="cta" onClick={onStart}>{t("hero_cta")} <span aria-hidden="true">↓</span></button>
      <div className="facts">
        {facts.map(([value, unit, key]) => <Fact key={key} value={value} unit={unit} label={t(key)} />)}
      </div>
    </header>
  );
}

function Fact({ value, unit, label }) {
  const shown = useCountUp(value, 1200);
  return <div className="fact"><strong dir="ltr">{Math.round(shown)}{unit}</strong><span>{label}</span></div>;
}

function FieldStep({ t, lang, fieldId, setFieldId }) {
  const names = useMemo(() => Object.fromEntries(Object.entries(data.fields).map(([id, f]) => [id, f[`name_${lang}`]])), [lang]);
  const field = data.fields[fieldId];
  return (
    <Reveal as="section" id="field" className="panel">
      <h2>{t("field_title")}</h2>
      <p className="hint">{t("field_hint")}</p>
      <div className="field-grid">
        <FieldMap fields={data.fields} selected={fieldId} onSelect={setFieldId} names={names} />
        <div className="field-list">
          {Object.entries(data.fields).map(([id, f]) => (
            <button key={id} className={`field-pick ${id === fieldId ? "is-on" : ""}`} onClick={() => setFieldId(id)} aria-pressed={id === fieldId}>
              <strong>{names[id]}</strong>
              <span>{t("elevation")} {f.elevation_m} {t("metres")} · {t("slope")} <span dir="ltr">{f.slope_deg}°</span></span>
            </button>
          ))}
          <p className="note">{t("geometry_source")} {t("static_source")}</p>
        </div>
      </div>
      {field && <Evidence t={t} field={field} />}
    </Reveal>
  );
}

function Evidence({ t, field }) {
  const e = field.evidence;
  const labels = e.ndvi.map(([m]) => m), values = e.ndvi.map(([, v]) => v);
  return (
    <div className="evidence" key={field.name_en}>
      <h3>{t("evidence_title")}</h3>
      <div className="tiles">
        <div className="tile"><strong dir="ltr">{e.winter_crop} / {e.seasons}</strong><span>{t("ev_winter_crop")}</span></div>
        <div className="tile"><strong>{e.fallow}</strong><span>{t("ev_fallow")}</span></div>
        <div className="tile"><strong dir="ltr">{e.rain_mean} mm</strong><span>{t("ev_rain")}</span></div>
      </div>
      <LineChart labels={labels} series={[{ name: "NDVI", color: "#1f8a5b", values }]} yMin={0} yMax={1} yFormat={(v) => v.toFixed(2)}
        bands={[{ label: "bare", from: 0, to: 0.25, color: "#8a5a2b" }, { label: "crop", from: 0.4, to: 1, color: "#1f8a5b" }]} />
      <p className="note">{t("ev_ndvi_note")} {t("ev_history_note", { first: e.first, last: e.last })} <Badge t={t} level="high" /></p>
      <p className="callout">{t(e.rain_driest ? "ev_drought" : "ev_last_season", { season: season(e.rain_season), rain: e.rain_last, change: Math.abs(e.rain_change_pct), n: e.rain_seasons, prev: e.peak_prev, last: e.peak_last })}</p>
      <p className="note">{t("ev_rain_note")} <Badge t={t} level="medium" /></p>
      {field.soil.clay_pct != null && <p className="note"><b>{t("ev_soil", { clay: field.soil.clay_pct, sand: field.soil.sand_pct, ph: field.soil.ph })}</b> {t("ev_soil_note")} <Badge t={t} level="medium" /></p>}
    </div>
  );
}

function PrioritiesStep({ t, weights, setWeights }) {
  return (
    <Reveal as="section" id="priorities" className="panel">
      <h2>{t("priorities_title")}</h2>
      <p className="hint">{t("preference_notice")}</p>
      <div className="chips">
        {Object.entries(PRESETS).map(([key, preset]) => (
          <button key={key} className={`chip ${data.criteria.every((c) => weights[c] === preset[c]) ? "is-on" : ""}`} onClick={() => setWeights(preset)}>{t(key)}</button>
        ))}
      </div>
      <div className="sliders">
        {data.criteria.map((c) => (
          <Slider key={c} label={t(`priority_${c}`)} value={weights[c]} min={1} max={5} step={1} lowLabel={t("less")} highLabel={t("more")}
            format={(v) => `${v} / 5`} onChange={(v) => setWeights({ ...weights, [c]: v })} />
        ))}
      </div>
    </Reveal>
  );
}

function Scenario({ t, fieldId, rain, setRain, warming, setWarming }) {
  const vigor = predictVigor(data, fieldId, rain);
  const shown = useCountUp(vigor.ndvi * 100);
  return (
    <div className="scenario">
      <h3>{t("scenario_title")}</h3>
      <div className="scenario-grid">
        <Slider label={t("scenario_rain")} value={rain} min={-50} max={20} step={10} accent="#3b7cc4" lowLabel={`☀ ${t("drought_side")}`} highLabel={`${t("wet_side")} ☂`}
          format={(v) => `${v > 0 ? "+" : ""}${v}%`} onChange={setRain} />
        <Slider label={t("scenario_warming")} value={warming} min={0} max={3} step={0.5} accent="#c8553d" lowLabel="0" highLabel="+3 °C"
          format={(v) => `+${v.toFixed(1)} °C`} onChange={setWarming} />
        <div className={`vigor vigor-${vigor.state}`}>
          <span>{t("vigor_ndvi")}</span>
          <strong dir="ltr">{(shown / 100).toFixed(2)} ± {vigor.error.toFixed(2)}</strong>
          <div className="vigor-bar" dir="ltr"><i style={{ width: `${vigor.ndvi * 100}%` }} /><b style={{ left: "25%" }} /><b style={{ left: "40%" }} /></div>
          <span>{t(`vigor_${vigor.state}`)} · {t("vigor_rain")}: <span dir="ltr">{vigor.rain} mm</span></span>
        </div>
      </div>
      <p className={rain || warming ? "callout" : "note"}>{rain || warming ? t("scenario_note", { rain, warming }) : t("scenario_hint")}</p>
      <details><summary>{t("vigor_ndvi")}</summary><p className="note">{t("vigor_model", data.vigor)} {vigor.extrapolated && t("vigor_extrapolated", data.vigor)}</p></details>
    </div>
  );
}

function Cards({ t, lang, result, current }) {
  const totals = Object.fromEntries(result.rotations.map((r) => [r.id, r.total]));
  return (
    <div className="cards">
      {result.rotations.map((r, index) => {
        const ordered = [...data.criteria].sort((a, b) => r.criteria[a].score - r.criteria[b].score);
        const gap = current && current !== r.id ? Math.round(r.total - totals[current]) : null;
        return (
          <article key={r.id} className={`card ${index === 0 ? "is-top" : ""}`} style={{ "--accent": ROTATION_COLORS[r.id] }}>
            <header>
              <div><span className="rank">{t("rank")} {index + 1}</span><h3>{r.rotation[`name_${lang}`]}</h3></div>
              <ScoreRing value={r.total} label={t("score")} size={104} />
            </header>
            <p className="status">
              {current === r.id ? t("your_current") : gap != null ? t(gap >= 0 ? "vs_current_up" : "vs_current_down", { points: Math.abs(gap) })
                : t(r.rotation.is_current === false ? "not_current_rotation" : r.rotation.is_current ? "current_rotation" : "current_rotation_unknown")}
            </p>
            <p className="summary">{t("strongest", { a: t(`priority_${ordered[ordered.length - 1]}`), b: t(`priority_${ordered[0]}`) })}</p>
            <ul className="criteria">
              {data.criteria.map((c) => (
                <li key={c}>
                  <div className="bar-head"><span>{t(`priority_${c}`)}</span><b>{Math.round(r.criteria[c].score)}</b></div>
                  <div className="bar" dir="ltr"><i style={{ width: `${r.criteria[c].score}%`, background: BADGE[data.confidence[c]] }} /></div>
                  <p>{criterionDetail(t, c, r.criteria[c])} <Badge t={t} level={data.confidence[c]} /></p>
                </li>
              ))}
            </ul>
            <details><summary>{t("sources_toggle")}</summary>{data.criteria.map((c) => <p key={c} className="note"><b>{t(`priority_${c}`)}:</b> {t(`source_${c}`)}</p>)}</details>
          </article>
        );
      })}
    </div>
  );
}

function Calendar({ t, lang, result }) {
  const months = Array.from({ length: 12 }, (_, i) => t(`month_${((9 + i) % 12) + 1}`));
  return (
    <div className="calendar">
      <h3>{t("calendar_title")}</h3>
      {result.rotations.map((r) => (
        <div key={r.id} className="cal-rotation">
          <strong>{r.rotation[`name_${lang}`]}</strong>
          {r.rotation.sequence.map((crop, i) => (
            <div key={i} className="cal-row">
              <span className="cal-label">{t("season_n", { n: i + 1 })}: {t(`crop_${crop}`)}</span>
              <div className="cal-strip">
                {data.crops[crop].calendar.map((slot, m) => <span key={m} className={`cal-cell ${slot ? CROP_CLASS[slot] : "bare"}`} title={`${months[m]}: ${slot ? t(`crop_${slot}`) : t("bare_soil")}`}>{months[m].slice(0, 3)}</span>)}
              </div>
            </div>
          ))}
        </div>
      ))}
      <div className="cal-legend"><span className="cal-cell wheat">{t("crop_WHEAT")}</span><span className="cal-cell lentil">{t("crop_LENTIL")}</span><span className="cal-cell bare">{t("bare_soil")}</span></div>
      <p className="note">{t("timeline_legend")}</p>
    </div>
  );
}

function Backtest({ t, lang, field }) {
  const years = Object.keys(field.replay).map(Number).sort((a, b) => a - b);
  const names = Object.fromEntries(field.rotations.map((r) => [r.id, r[`name_${lang}`]]));
  const worst = years.reduce((w, y) => (Math.min(...Object.values(field.replay[y])) < Math.min(...Object.values(field.replay[w])) ? y : w));
  return (
    <div className="backtest">
      <h3>{t("replay_title")}</h3>
      <LineChart labels={years.map(season)} highlight={years.indexOf(worst)} yMin={0} yMax={100} yFormat={(v) => `${Math.round(v)}%`}
        series={field.rotations.map((r) => ({ name: names[r.id], color: ROTATION_COLORS[r.id], values: years.map((y) => field.replay[y][r.id]) }))} />
      <p className="note">{t("replay_note", { n: years.length, season: season(worst), values: field.rotations.map((r) => `${names[r.id]} ${field.replay[worst][r.id]}%`).join(" · ") })}</p>
      <div className="table-wrap"><table>
        <thead><tr><th>{t("bt_rotation")}</th><th>{t("bt_mean")}</th><th>{t("bt_worst")}</th><th>{t("bt_under_half")}</th></tr></thead>
        <tbody>{field.rotations.map((r) => { const b = field.backtest[r.id]; return (
          <tr key={r.id}><td><i className="dot" style={{ background: ROTATION_COLORS[r.id] }} />{names[r.id]}</td><td dir="ltr">{b.mean}%</td><td><span dir="ltr">{b.worst}%</span> ({season(b.worst_year)})</td><td dir="ltr">{b.under_half} / {b.seasons}</td></tr>); })}</tbody>
      </table></div>
    </div>
  );
}

function Advisor({ t, fieldId, weights, rain, warming }) {
  // ?history=WHEAT,WHEAT,WHEAT pre-fills the three seasons, for demo links.
  const [history, setHistory] = useState(() => {
    const asked = (new URLSearchParams(window.location.search).get("history") || "").split(",").filter((c) => c in data.crops).slice(-3);
    return [...Array(3 - asked.length).fill(null), ...asked];
  });
  const field = data.fields[fieldId];
  const known = history.filter(Boolean);
  const ready = history[2] != null;
  const result = ready ? nextSeason(data, fieldId, known, weights, rain, warming) : null;
  const labels = ["adv_two_before", "adv_before", "adv_last"];
  return (
    <Reveal as="section" id="advisor" className="panel">
      <h2>{t("advisor_section")}</h2>
      <p className="hint">{t("advisor_how")}</p>
      <div className="history">
        {labels.map((label, i) => (
          <div key={label} className="history-slot">
            <span>{t(label)}</span>
            <div className="segmented">
              {[null, ...Object.keys(data.crops)].map((crop) => (
                <button key={crop ?? "none"} className={history[i] === crop ? "is-on" : ""} aria-pressed={history[i] === crop}
                  onClick={() => setHistory(history.map((h, j) => (j === i ? crop : h)))}>{crop ? t(`crop_${crop}`) : t("not_set")}</button>
              ))}
            </div>
          </div>
        ))}
      </div>
      {!ready && <p className="callout soft">{t("advisor_prompt")}</p>}
      {ready && (
        <div className="advice" key={known.join()}>
          <p className="note">
            {t(field.last_season.driest ? "adv_last_driest" : "adv_last_rain", { season: season(field.last_season.year), rain: field.last_season.rain_mm })}{" "}
            {t(`adv_moisture_${field.soil_moisture.state}`, { month: field.soil_moisture.month })} <Badge t={t} level="medium" />
          </p>
          {(rain !== 0 || warming !== 0) && <p className="callout">{t("adv_scenario", { rain, warming })}</p>}
          <ol className="options">
            {result.options.map((o, i) => (
              <li key={o.crop} className={`option ${i === 0 ? "is-top" : ""} ${o.legumeRepeat ? "is-blocked" : ""}`}>
                <div className="option-head"><span className="option-rank">{i + 1}</span><h3>{t(`crop_${o.crop}`)}</h3><strong dir="ltr">{Math.round(o.total)} / 100</strong></div>
                <ul className="rules">{Object.entries(o.rules).map(([rule, ok]) => <li key={rule} className={ok ? "ok" : "no"}>{ok ? "✓" : "✗"} {t(`rule_${rule}`)}</li>)}</ul>
                {o.legumeRepeat && <p className="callout">{t("adv_legume_repeat")}</p>}
                <p className="note">{o.outlook ? t("adv_outlook", { ...o.outlook, seasons: field.seasons }) : t("adv_outlook_fallow")}</p>
              </li>
            ))}
          </ol>
          {result.closeCall && <p className="callout">{t("close_call")}</p>}
          <p className="note">{t("advisor_limits")}</p>
        </div>
      )}
    </Reveal>
  );
}

function Trust({ t }) {
  const v = data.validation, temp = v.temperature_mean_c, rain = v.rain_mm;
  const errors = Object.values(temp.power_lapse_corrected).map((x) => x.mae);
  const max = rain.station_total;
  const bars = [[t("trust_rain_station"), rain.station_total, "#0f3d2e"], ["NASA POWER", rain.power.total, "#c8553d"], ["GPM IMERG", rain.imerg.total, "#d99a1c"]];
  return (
    <Reveal as="section" id="trust" className="panel">
      <h2>{t("trust_section")}</h2>
      <p className="hint">{t("trust_intro", { months: v.station.months })}</p>
      <div className="trust-grid">
        <div className="trust-card">
          <div className="compare-nums"><div><strong dir="ltr">{temp.power_raw.mae} °C</strong><span>{t("trust_temp_raw")}</span></div><span className="arrow" aria-hidden="true">←</span>
            <div className="good"><strong dir="ltr">{temp.power_lapse_corrected["6.5"].mae} °C</strong><span>{t("trust_temp_fixed")}</span></div></div>
          <p className="note">{t("trust_temp_note", { gap: Math.round(v.station.elevation_m - v.station.power_cell_elevation_m), low: Math.min(...errors), high: Math.max(...errors) })}</p>
        </div>
        <div className="trust-card">
          {bars.map(([name, value, color]) => (
            <div key={name} className="hbar"><span>{name}</span><div dir="ltr"><i style={{ width: `${(100 * value) / max}%`, background: color }} /></div><b dir="ltr">{Math.round(value)} mm</b></div>
          ))}
          <p className="note">{t("trust_rain_note", { pct: Math.round(100 - (100 * rain.power.total) / rain.station_total) })} {t("trust_heat_note")}</p>
        </div>
      </div>
    </Reveal>
  );
}

export default function App() {
  // ?field=maru_1&lang=en opens the site on a field, for demo links.
  const query = new URLSearchParams(window.location.search);
  const [lang, setLang] = useState(query.get("lang") === "en" ? "en" : "ar");
  const [fieldId, setFieldId] = useState(query.get("field") in data.fields ? query.get("field") : null);
  const [weights, setWeights] = useState(PRESETS.preset_balanced);
  const [rain, setRain] = useState(0);
  const [warming, setWarming] = useState(0);
  const [current, setCurrent] = useState(null);
  const t = useTranslator(lang);
  useEffect(() => { document.documentElement.lang = lang; document.documentElement.dir = lang === "ar" ? "rtl" : "ltr"; }, [lang]);
  const field = fieldId ? data.fields[fieldId] : null;
  const result = useMemo(() => (fieldId ? evaluate(data, fieldId, weights, rain, warming) : null), [fieldId, weights, rain, warming]);
  const go = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  const pick = (id) => { setFieldId(id); setCurrent(null); };
  const steps = [["field", "step_field"], ["priorities", "step_priorities"], ["compare", "step_compare"], ["advisor", "step_advisor"], ["trust", "step_trust"]];
  const possible = field ? field.rotations.filter((r) => r.is_current !== false) : [];
  return (
    <>
      <Backdrop />
      <nav className="topbar">
        <a className="brand" href="#top" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: "smooth" }); }}><span className="logo" aria-hidden="true">🌾</span> Field Shift</a>
        <div className="steps">{steps.map(([id, key]) => <button key={id} onClick={() => go(id)}>{t(key)}</button>)}</div>
        <button className="lang" onClick={() => setLang(lang === "ar" ? "en" : "ar")} aria-label="Language">{lang === "ar" ? "English" : "العربية"}</button>
      </nav>
      <main id="top">
        <Hero t={t} onStart={() => go("field")} />
        <FieldStep t={t} lang={lang} fieldId={fieldId} setFieldId={pick} />
        <PrioritiesStep t={t} weights={weights} setWeights={setWeights} />
        <Reveal as="section" id="compare" className="panel">
          <h2>{t("compare_title")}</h2>
          {!result && <p className="callout soft">{t("pick_field_first")}</p>}
          {result && (
            <>
              <Scenario t={t} fieldId={fieldId} rain={rain} setRain={setRain} warming={warming} setWarming={setWarming} />
              <div className="current">
                <span>{t("current_question")}</span>
                <div className="segmented">
                  {[null, ...possible.map((r) => r.id)].map((id) => (
                    <button key={id ?? "none"} className={current === id ? "is-on" : ""} aria-pressed={current === id} onClick={() => setCurrent(id)}>
                      {id ? possible.find((r) => r.id === id)[`name_${lang}`] : t("not_set")}</button>
                  ))}
                </div>
              </div>
              <Cards t={t} lang={lang} result={result} current={current} />
              <p className="verdict">{t("top_by_priorities", { name: result.rotations[0].rotation[`name_${lang}`] })}</p>
              {result.closeCall && <p className="callout">{t("close_call")}</p>}
              {result.lowConfidenceTop && <p className="callout">{t("low_conf_top")}</p>}
              <Calendar t={t} lang={lang} result={result} />
              <Backtest t={t} lang={lang} field={field} />
            </>
          )}
        </Reveal>
        {fieldId && <Advisor key={fieldId} t={t} fieldId={fieldId} weights={weights} rain={rain} warming={warming} />}
        <Trust t={t} />
      </main>
      <footer className="footer">
        <p>{t("footer")}</p>
        <a href="https://github.com/Zaid-sh05/field-shift" target="_blank" rel="noreferrer">{t("code")}</a>
      </footer>
    </>
  );
}
