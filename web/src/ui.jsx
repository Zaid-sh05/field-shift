// Small presentational building blocks: charts, sliders, score ring, map, reveal-on-scroll.
import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export const BADGE = { high: "#1f8a5b", medium: "#d99a1c", low: "#c8553d" };

/** Fade and lift a section in the first time it scrolls into view. */
export function Reveal({ children, className = "", as: Tag = "div", ...rest }) {
  const ref = useRef(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const node = ref.current;
    if (!node || typeof IntersectionObserver === "undefined") return setSeen(true);
    const observer = new IntersectionObserver(([entry]) => entry.isIntersecting && (setSeen(true), observer.disconnect()), { threshold: 0.12 });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return <Tag ref={ref} className={`reveal ${seen ? "is-seen" : ""} ${className}`} {...rest}>{children}</Tag>;
}

/** Animate a number towards its target whenever the target changes. */
export function useCountUp(target, duration = 600) {
  const [value, setValue] = useState(target);
  const from = useRef(target);
  useEffect(() => {
    const start = from.current, t0 = performance.now();
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) { from.current = target; return setValue(target); }
    let frame = requestAnimationFrame(function step(now) {
      const p = Math.min(1, (now - t0) / duration), eased = 1 - (1 - p) ** 3;
      const current = start + (target - start) * eased;
      from.current = current;
      setValue(current);
      if (p < 1) frame = requestAnimationFrame(step);
    });
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);
  return value;
}

export function ScoreRing({ value, size = 120, label }) {
  const shown = useCountUp(value);
  const r = size / 2 - 9, c = 2 * Math.PI * r;
  const color = value >= 65 ? "#1f8a5b" : value >= 45 ? "#d99a1c" : "#c8553d";
  return (
    <div className="ring" style={{ width: size, height: size }} role="img" aria-label={`${label}: ${Math.round(value)} / 100`}>
      <svg viewBox={`0 0 ${size} ${size}`} dir="ltr">
        <circle cx={size / 2} cy={size / 2} r={r} className="ring-track" />
        <circle cx={size / 2} cy={size / 2} r={r} className="ring-value" stroke={color}
          strokeDasharray={c} strokeDashoffset={c * (1 - value / 100)} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      </svg>
      <div className="ring-text"><strong>{Math.round(shown)}</strong><span>/ 100</span></div>
    </div>
  );
}

/** A range slider that drags correctly inside a right-to-left page (the track itself stays left-to-right). */
export function Slider({ label, value, min, max, step, onChange, format = (v) => v, lowLabel, highLabel, accent }) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <label className="slider">
      <span className="slider-head"><span>{label}</span><output>{format(value)}</output></span>
      <input type="range" dir="ltr" min={min} max={max} step={step} value={value}
        style={{ "--pct": `${pct}%`, "--accent": accent || "#1f8a5b" }}
        onChange={(e) => onChange(Number(e.target.value))} />
      {(lowLabel || highLabel) && <span className="slider-ends" dir="ltr"><span>{lowLabel}</span><span>{highLabel}</span></span>}
    </label>
  );
}

/** Minimal SVG line chart. `series`: [{ name, color, values: number[] }], all sharing `labels`. */
export function LineChart({ labels, series, yMin = 0, yMax = 1, bands = [], height = 230, yFormat = (v) => v, highlight }) {
  const W = 760, H = height, pad = { l: 40, r: 12, t: 12, b: 28 };
  const x = (i) => pad.l + (i / Math.max(1, labels.length - 1)) * (W - pad.l - pad.r);
  const y = (v) => pad.t + (1 - (v - yMin) / (yMax - yMin)) * (H - pad.t - pad.b);
  const [hover, setHover] = useState(null);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => yMin + f * (yMax - yMin));
  const every = Math.ceil(labels.length / 9);
  const onMove = (e) => {
    const box = e.currentTarget.getBoundingClientRect();
    const px = ((e.clientX - box.left) / box.width) * W;
    setHover(Math.max(0, Math.min(labels.length - 1, Math.round(((px - pad.l) / (W - pad.l - pad.r)) * (labels.length - 1)))));
  };
  return (
    <div className="chart">
      <svg viewBox={`0 0 ${W} ${H}`} dir="ltr" onPointerMove={onMove} onPointerLeave={() => setHover(null)} role="img">
        {bands.map((b) => <rect key={b.label} x={pad.l} width={W - pad.l - pad.r} y={y(b.to)} height={y(b.from) - y(b.to)} fill={b.color} opacity="0.13" />)}
        {ticks.map((v) => (
          <g key={v}><line x1={pad.l} x2={W - pad.r} y1={y(v)} y2={y(v)} className="grid" />
            <text x={pad.l - 6} y={y(v) + 4} textAnchor="end" className="axis">{yFormat(v)}</text></g>
        ))}
        {labels.map((l, i) => i % every === 0 && <text key={l} x={x(i)} y={H - 8} textAnchor="middle" className="axis">{l}</text>)}
        {highlight != null && <rect x={x(highlight) - 9} y={pad.t} width="18" height={H - pad.t - pad.b} fill="#c8553d" opacity="0.14" rx="4" />}
        {series.map((s) => (
          <polyline key={s.name} fill="none" stroke={s.color} strokeWidth="2.4" strokeLinejoin="round" className="line"
            points={s.values.map((v, i) => (v == null ? null : `${x(i)},${y(v)}`)).filter(Boolean).join(" ")} />
        ))}
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={pad.t} y2={H - pad.b} className="cursor" />}
        {hover != null && series.map((s) => s.values[hover] != null && <circle key={s.name} cx={x(hover)} cy={y(s.values[hover])} r="4.5" fill={s.color} stroke="#fff" strokeWidth="1.5" />)}
      </svg>
      <div className="chart-legend">
        {hover != null && <strong dir="ltr">{labels[hover]}</strong>}
        {series.map((s) => (
          <span key={s.name}><i style={{ background: s.color }} />{s.name}{hover != null && s.values[hover] != null && <b dir="ltr"> {yFormat(s.values[hover])}</b>}</span>
        ))}
      </div>
    </div>
  );
}

/** Satellite map of the fields. Clicking a field selects it. */
export function FieldMap({ fields, selected, onSelect, names }) {
  const holder = useRef(null), map = useRef(null), layers = useRef({});
  useEffect(() => {
    const m = (map.current = L.map(holder.current, { scrollWheelZoom: false, attributionControl: true }));
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { attribution: "Esri World Imagery", maxZoom: 18 }).addTo(m);
    const all = [];
    for (const [id, field] of Object.entries(fields)) {
      const latlngs = field.polygon.map(([lon, lat]) => [lat, lon]);
      all.push(...latlngs);
      layers.current[id] = L.polygon(latlngs, { color: "#ffd60a", weight: 2, fillOpacity: 0.12 }).addTo(m)
        .bindTooltip(names[id], { permanent: true, direction: "center", className: "field-tip" }).on("click", () => onSelect(id));
    }
    m.fitBounds(all, { padding: [24, 24] });
    return () => m.remove();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    for (const [id, layer] of Object.entries(layers.current)) {
      layer.setStyle(id === selected ? { color: "#ffffff", weight: 4, fillColor: "#1f8a5b", fillOpacity: 0.45 } : { color: "#ffd60a", weight: 2, fillColor: "#ffd60a", fillOpacity: 0.12 });
      layer.setTooltipContent(names[id]);
    }
  }, [selected, names]);
  return <div ref={holder} className="map" />;
}

/** Slow drifting shapes behind the page. Pure CSS animation; hidden for reduced-motion users. */
export function Backdrop() {
  return (
    <div className="backdrop" aria-hidden="true">
      <span className="blob b1" /><span className="blob b2" /><span className="blob b3" />
      <svg className="contours" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice">
        {[0, 1, 2, 3, 4, 5, 6].map((i) => (
          <path key={i} d={`M-50 ${120 + i * 95} C 250 ${40 + i * 95}, 450 ${220 + i * 95}, 700 ${130 + i * 95} S 1100 ${60 + i * 95}, 1260 ${160 + i * 95}`} />
        ))}
      </svg>
      {Array.from({ length: 14 }, (_, i) => (
        <span key={i} className="seed" style={{ "--x": `${(i * 53) % 100}%`, "--d": `${14 + (i % 5) * 4}s`, "--delay": `${-i * 2.3}s`, "--s": `${0.6 + (i % 4) * 0.25}` }} />
      ))}
    </div>
  );
}
