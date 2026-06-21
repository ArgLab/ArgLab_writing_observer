"use client";

import { useMemo, useCallback, useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { Loader2, Info, TrendingDown, Lightbulb } from "lucide-react";

import { useLOConnectionDataManager } from "lo_event/lo_event/lo_assess/components/components.jsx";
import { MetricsPanel } from "@/app/components/MetricsPanel";
import { useCourseIdContext } from "@/app/providers/CourseIdProvider";
import { getConfiguredWsOrigin } from "@/app/utils/ws";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const DEBUG = false;

/* ══════════════════════════════════════════════════════════════
   6+1 TRAIT RUBRIC MAPPING
   ══════════════════════════════════════════════════════════════ */
const METRIC_DISPLAY = {
  academic_language:             { title: "Academic Language",               trait: "Word Choice" },
  informal_language:             { title: "Informal Language",               trait: "Word Choice" },
  latinate_words:                { title: "Latinate Words",                  trait: "Word Choice" },
  opinion_words:                 { title: "Opinion Words",                   trait: "Word Choice" },
  emotion_words:                 { title: "Emotion Words",                   trait: "Word Choice" },
  argument_words:                { title: "Argument Words",                  trait: "Ideas & Content" },
  explicit_argument:             { title: "Explicit Argument",               trait: "Ideas & Content" },
  statements_of_opinion:         { title: "Statements of Opinion",           trait: "Ideas & Content" },
  statements_of_fact:            { title: "Statements of Fact",              trait: "Ideas & Content" },
  information_sources:           { title: "Information Sources",             trait: "Ideas & Content" },
  attributions:                  { title: "Attributions",                    trait: "Ideas & Content" },
  citations:                     { title: "Citations",                       trait: "Ideas & Content" },
  quoted_words:                  { title: "Quoted Words",                    trait: "Ideas & Content" },
  concrete_details:              { title: "Concrete Details",                trait: "Ideas & Content" },
  main_idea_sentences:           { title: "Main Idea Sentences",             trait: "Ideas & Content" },
  supporting_idea_sentences:     { title: "Supporting Idea Sentences",       trait: "Ideas & Content" },
  supporting_detail_sentences:   { title: "Supporting Detail Sentences",     trait: "Ideas & Content" },
  explicit_claims:               { title: "Explicit Claims",                 trait: "Ideas & Content" },
  social_awareness:              { title: "Social Awareness",                trait: "Ideas & Content" },
  transition_words:              { title: "Transition Words",                trait: "Organization" },
  positive_transition_words:     { title: "Positive Transitions",            trait: "Organization" },
  conditional_transition_words:  { title: "Conditional Transitions",         trait: "Organization" },
  consequential_transition_words:{ title: "Consequential Transitions",       trait: "Organization" },
  contrastive_transition_words:  { title: "Contrastive Transitions",         trait: "Organization" },
  counterpoint_transition_words: { title: "Counterpoint Transitions",        trait: "Organization" },
  comparative_transition_words:  { title: "Comparative Transitions",         trait: "Organization" },
  cross_referential_transition_words: { title: "Cross-Referential Transitions", trait: "Organization" },
  illustrative_transition_words: { title: "Illustrative Transitions",        trait: "Organization" },
  negative_transition_words:     { title: "Negative Transitions",            trait: "Organization" },
  emphatic_transition_words:     { title: "Emphatic Transitions",            trait: "Organization" },
  evenidentiary_transition_words:{ title: "Evidentiary Transitions",         trait: "Organization" },
  general_transition_words:      { title: "General Transitions",             trait: "Organization" },
  ordinal_transition_words:      { title: "Ordinal Transitions",             trait: "Organization" },
  purposive_transition_words:    { title: "Purposive Transitions",           trait: "Organization" },
  periphrastic_transition_words: { title: "Periphrastic Transitions",        trait: "Organization" },
  hypothetical_transition_words: { title: "Hypothetical Transitions",        trait: "Organization" },
  summative_transition_words:    { title: "Summative Transitions",           trait: "Organization" },
  introductory_transition_words: { title: "Introductory Transitions",        trait: "Organization" },
  direct_speech_verbs:           { title: "Direct Speech Verbs",             trait: "Voice" },
  indirect_speech:               { title: "Indirect Speech",                 trait: "Voice" },
  positive_tone:                 { title: "Positive Tone",                   trait: "Voice" },
  negative_tone:                 { title: "Negative Tone",                   trait: "Voice" },
  character_trait_words:         { title: "Character Trait Words",           trait: "Voice" },
  adjectives:                    { title: "Adjectives",                      trait: "Sentence Fluency" },
  adverbs:                       { title: "Adverbs",                         trait: "Sentence Fluency" },
  nouns:                         { title: "Nouns",                           trait: "Sentence Fluency" },
  proper_nouns:                  { title: "Proper Nouns",                    trait: "Sentence Fluency" },
  verbs:                         { title: "Verbs",                           trait: "Sentence Fluency" },
  numbers:                       { title: "Numbers",                         trait: "Sentence Fluency" },
  prepositions:                  { title: "Prepositions",                    trait: "Sentence Fluency" },
  coordinating_conjunction:      { title: "Coordinating Conjunctions",       trait: "Sentence Fluency" },
  subordinating_conjunction:     { title: "Subordinating Conjunctions",      trait: "Sentence Fluency" },
  auxiliary_verb:                { title: "Auxiliary Verbs",                 trait: "Sentence Fluency" },
  pronoun:                       { title: "Pronouns",                        trait: "Sentence Fluency" },
  simple_sentences:              { title: "Simple Sentences",                trait: "Sentence Fluency" },
  simple_with_complex_predicates:{ title: "Simple + Complex Predicates",     trait: "Sentence Fluency" },
  simple_with_compound_predicates:{ title: "Simple + Compound Predicates",   trait: "Sentence Fluency" },
  simple_with_compound_complex_predicates: { title: "Simple + Compound-Complex Predicates", trait: "Sentence Fluency" },
  compound_sentences:            { title: "Compound Sentences",              trait: "Sentence Fluency" },
  complex_sentences:             { title: "Complex Sentences",               trait: "Sentence Fluency" },
  compound_complex_sentences:    { title: "Compound-Complex Sentences",      trait: "Sentence Fluency" },
  polysyllabic_words:            { title: "Polysyllabic Words",              trait: "Conventions" },
  low_frequency_words:           { title: "Low Frequency Words",             trait: "Conventions" },
  sentences:                     { title: "Sentences",                       trait: "Conventions" },
  paragraphs:                    { title: "Paragraphs",                      trait: "Conventions" },
  in_past_tense:                 { title: "In Past Tense",                   trait: "Conventions" },
};

function getMetricTitle(metricId) {
  return METRIC_DISPLAY[metricId]?.title
    || metricId.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function getMetricTrait(metricId) {
  return METRIC_DISPLAY[metricId]?.trait || "Conventions";
}

/* ══════════════════════════════════════════════════════════════
   TRAIT STYLE TOKENS
   ══════════════════════════════════════════════════════════════ */
const TRAIT_STYLE = {
  "Ideas & Content":  { badge: "bg-amber-50 text-amber-700 ring-amber-200" },
  "Organization":     { badge: "bg-blue-50 text-blue-700 ring-blue-200" },
  "Voice":            { badge: "bg-rose-50 text-rose-700 ring-rose-200" },
  "Word Choice":      { badge: "bg-violet-50 text-violet-700 ring-violet-200" },
  "Sentence Fluency": { badge: "bg-teal-50 text-teal-700 ring-teal-200" },
  "Conventions":      { badge: "bg-slate-50 text-slate-700 ring-slate-200" },
};

function TraitBadge({ trait }) {
  const cls = TRAIT_STYLE[trait]?.badge || "bg-gray-50 text-gray-600 ring-gray-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold ring-1 ring-inset ${cls}`}>
      {trait}
    </span>
  );
}

/* ══════════════════════════════════════════════════════════════
   ASSIGNMENT TYPE COLORS — full canonical list always in legend
   ══════════════════════════════════════════════════════════════ */
const GENRE_BAR_COLORS = {
  Narrative:     "#7c3aed",
  Argumentative: "#d97706",
  Analytical:    "#2563eb",
  Expository:    "#0d9488",
  Informational: "#0891b2",
  Document:      "#059669",
  Other:         "#6b7280",
};

const ALL_GENRES = ["Narrative", "Argumentative", "Analytical", "Expository", "Informational", "Document", "Other"];

function inferAssignmentType(text) {
  const t = (text || "").toLowerCase();
  if (/argue|claim|thesis|evidence|counterargument/.test(t)) return "Argumentative";
  if (/analyze|analysis|examine|compare|contrast/.test(t)) return "Analytical";
  if (/once upon|story|character|plot|setting/.test(t)) return "Narrative";
  if (/explain|describe|inform|definition/.test(t)) return "Expository";
  return "Document";
}

/* ══════════════════════════════════════════════════════════════
   TREND ANALYSIS
   ══════════════════════════════════════════════════════════════ */
function analyzeTrend(points, windowSize = 3) {
  if (!points || points.length < 2) return "stable";
  const recent = points.slice(-Math.min(windowSize, points.length));
  const delta = (recent[recent.length - 1]?.raw ?? 0) - (recent[0]?.raw ?? 0);
  if (delta < -1.5) return "declining";
  if (delta > 1.5) return "improving";
  return "stable";
}

function computeSlope(points, windowSize = 3) {
  if (!points || points.length < 2) return 0;
  const recent = points.slice(-Math.min(windowSize, points.length));
  const n = recent.length;
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  for (let i = 0; i < n; i++) {
    sumX += i; sumY += recent[i].raw;
    sumXY += i * recent[i].raw; sumX2 += i * i;
  }
  const denom = n * sumX2 - sumX * sumX;
  return denom === 0 ? 0 : (n * sumXY - sumX * sumY) / denom;
}

function getInstructionalSuggestion(metricId, trait, slope) {
  const title = getMetricTitle(metricId);
  const dropPct = Math.abs(slope * 3).toFixed(1);
  const map = {
    academic_language:   `${title} has declined over the last few essays (~${dropPct}pp). Consider a pre-writing vocabulary activity or a word bank to reinforce formal register.`,
    informal_language:   `Informal language use has increased recently. A brief editing checklist focusing on word choice before submission may help.`,
    latinate_words:      `Use of sophisticated vocabulary (Latinate words) is declining. Consider modeling academic synonyms during class discussion or mini-lessons.`,
    transition_words:    `Transition word use has dropped (~${dropPct}pp). A sentence-starter scaffold or revision task targeting connective language could help.`,
    citations:           `Citation use has declined recently. Review expectations for source integration and consider a brief conference on evidence-based writing.`,
    sentences:           `Sentence count or variety has been declining. Consider a sentence-combining exercise or revision pass focused on structural complexity.`,
    paragraphs:          `Paragraph structure appears to be declining. A quick conference reviewing organization expectations may be warranted before the next essay.`,
    explicit_argument:   `Explicit argument signals have weakened. Consider a targeted mini-lesson on thesis statements or claim framing.`,
    concrete_details:    `Use of concrete details has dropped. Encourage the student to add specific examples or evidence in the next revision cycle.`,
  };
  return map[metricId]
    || `${title} (${trait}) has shown a declining trend (~${dropPct}pp). Consider targeted feedback on this dimension before the next assignment.`;
}

/* ══════════════════════════════════════════════════════════════
   INSTRUCTIONAL SUGGESTION CALLOUT
   ══════════════════════════════════════════════════════════════ */
function InstructionalSuggestion({ metricId, trait, points }) {
  const [expanded, setExpanded] = useState(false);
  const trend = analyzeTrend(points);
  const slope = computeSlope(points);
  if (trend !== "declining") return null;
  const suggestion = getInstructionalSuggestion(metricId, trait, slope);

  return (
    <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-2.5 px-3 py-2 text-left hover:bg-amber-100 transition-colors"
      >
        <TrendingDown className="h-3.5 w-3.5 text-amber-600 shrink-0" />
        <Lightbulb className="h-3.5 w-3.5 text-amber-500 shrink-0" />
        <span className="text-[11px] font-semibold text-amber-800 flex-1">
          Declining trend — instructional suggestion available
        </span>
        <span className="shrink-0 inline-flex items-center px-2.5 py-0.5 rounded-md border border-amber-400 bg-white text-[10px] font-semibold text-amber-700 hover:bg-amber-50 transition-colors shadow-sm">
          {expanded ? "Hide" : "Show"}
        </span>
      </button>
      {expanded && (
        <div className="px-3 pb-3 pt-1 border-t border-amber-200">
          <p className="text-[12px] text-amber-900 leading-relaxed">{suggestion}</p>
          <p className="mt-1.5 text-[10px] text-amber-600 italic">
            Based on trend over last 3 essays. Verify against your knowledge of this student before acting.
          </p>
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   PINNED TOOLTIP
   ══════════════════════════════════════════════════════════════ */
function PinnedTooltip({ point, metricTitle, onClear }) {
  if (!point) return null;
  const genreColor = GENRE_BAR_COLORS[point.assignmentType] || GENRE_BAR_COLORS.Document;
  const pct = Number.isFinite(Number(point.raw)) ? Number(point.raw).toFixed(1) : "0.0";
  const date = point.date && !point.date.startsWith("Essay") ? point.date : null;

  return (
    <div className="mt-2 flex items-start justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2.5">
      <div className="flex flex-col gap-0.5 min-w-0">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full shrink-0" style={{ background: genreColor }} />
          <span className="text-xs font-bold text-gray-900 truncate">{point.title}</span>
        </div>
        {date && <span className="text-[11px] text-gray-500 ml-4">{date}</span>}
        <div className="ml-4 flex items-center gap-1.5 text-xs text-gray-700 mt-0.5">
          <span className="text-gray-500">{metricTitle}:</span>
          <span className="font-bold text-emerald-700">{pct}%</span>
          <span className="text-gray-400 text-[10px]">({point.assignmentType})</span>
        </div>
      </div>
      <button
        onClick={onClear}
        className="shrink-0 inline-flex items-center px-2.5 py-0.5 rounded-md border border-gray-300 bg-white text-[10px] font-semibold text-gray-600 hover:bg-gray-50 transition-colors shadow-sm mt-0.5"
      >
        Clear
      </button>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   STABLE STRINGIFY
   ══════════════════════════════════════════════════════════════ */
function stableStringify(obj) {
  const seen = new WeakSet();
  const sortObj = (v) => {
    if (v === null || typeof v !== "object") return v;
    if (seen.has(v)) return "[Circular]";
    seen.add(v);
    if (Array.isArray(v)) return v.map(sortObj);
    const keys = Object.keys(v).sort();
    const out = {};
    for (const k of keys) out[k] = sortObj(v[k]);
    return out;
  };
  try { return JSON.stringify(sortObj(obj)); } catch { return String(obj); }
}

/* ══════════════════════════════════════════════════════════════
   METRIC NORMALIZATION
   ══════════════════════════════════════════════════════════════ */
function normalizeSelectedMetrics(input) {
  if (!input) return [];
  const pickMetricId = (x) => {
    if (!x) return null;
    if (typeof x === "string") return x;
    if (typeof x === "object") {
      return x.metricKey || x.metric_key || x.metricId || x.metric_id || x.metric ||
        x.metric_name || x.metricName || x.id || x.key || x.name || x.value || x.label || null;
    }
    return null;
  };
  if (Array.isArray(input)) return input.map(pickMetricId).filter(Boolean).map((s) => String(s).trim()).filter(Boolean);
  if (typeof input === "object") return Object.entries(input).filter(([, v]) => !!v).map(([k]) => String(k).trim()).filter(Boolean);
  return [];
}

/* ══════════════════════════════════════════════════════════════
   COVERAGE HELPER
   ══════════════════════════════════════════════════════════════ */
function coveragePercentFromDoc(doc, metricId) {
  const text = (doc?.text || "").toString();
  const L = text.length; if (!L) return 0;
  const offsets = doc?.[metricId]?.offsets;
  if (!Array.isArray(offsets) || offsets.length === 0) return 0;
  const ranges = [];
  for (const pair of offsets) {
    if (!Array.isArray(pair) || pair.length < 2) continue;
    const start = Number(pair[0]), len = Number(pair[1]);
    if (!Number.isFinite(start) || !Number.isFinite(len) || len <= 0) continue;
    const s = Math.max(0, Math.min(L, start)), e = Math.max(0, Math.min(L, start + len));
    if (e > s) ranges.push([s, e]);
  }
  if (!ranges.length) return 0;
  ranges.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  let covered = 0; let [curS, curE] = ranges[0];
  for (let i = 1; i < ranges.length; i++) {
    const [s, e] = ranges[i];
    if (s <= curE) curE = Math.max(curE, e); else { covered += curE - curS; curS = s; curE = e; }
  }
  return ((covered + curE - curS) / L) * 100;
}

/* ══════════════════════════════════════════════════════════════
   LO RUNNER — isolated so its re-renders never reach charts
   ══════════════════════════════════════════════════════════════ */
function LORunner({ wsUrl, dataScope, scopeKey, onData, onErrors }) {
  const { data, errors } = useLOConnectionDataManager({ url: wsUrl, dataScope });
  useEffect(() => onData?.(data), [data, onData]);
  useEffect(() => onErrors?.(errors), [errors, onErrors]);
  useEffect(() => {
    if (!DEBUG) return;
    console.log("[LORunner] mounted scopeKey:", scopeKey);
    return () => console.log("[LORunner] unmounted scopeKey:", scopeKey);
  }, [scopeKey]);
  return null;
}

/* ══════════════════════════════════════════════════════════════
   ECHART OPTION BUILDER
   ══════════════════════════════════════════════════════════════ */
function buildEChartOption({ metricId, points }) {
  const rawLabels = points.map((p) => p.label);
  const uniqueDates = new Set(rawLabels.filter((l) => l && !l.startsWith("Essay")));
  const allSameDate = uniqueDates.size <= 1 && rawLabels.length > 1;
  const xLabels = points.map((p, i) => allSameDate ? `Essay ${i + 1}` : (p.label || `Essay ${i + 1}`));

  const values = points.map((p) => p.raw).filter(Number.isFinite);
  const dataMin = values.length ? Math.min(...values) : 0;
  const dataMax = values.length ? Math.max(...values) : 10;
  const range = dataMax - dataMin;
  const padding = Math.max(range * 0.25, 2);
  const yMin = Math.max(0, Math.floor((dataMin - padding) / 2) * 2);
  const yMax = Math.min(100, Math.ceil((dataMax + padding) / 2) * 2);
  const finalMin = yMin === yMax ? Math.max(0, yMin - 5) : yMin;
  const finalMax = yMin === yMax ? Math.min(100, yMax + 5) : yMax;

  const barData = points.map((p, i) => ({
    value: p.raw, docId: p.docId, label: xLabels[i], date: p.label,
    title: p.title, raw: p.raw, assignmentType: p.assignmentType || "Document",
    itemStyle: { color: GENRE_BAR_COLORS[p.assignmentType] || GENRE_BAR_COLORS.Document },
  }));

  const lineData = points.map((p, i) => ({
    value: p.raw, label: xLabels[i], date: p.label,
    title: p.title, raw: p.raw, assignmentType: p.assignmentType || "Document",
  }));

  const metricTitle = getMetricTitle(metricId);

  return {
    animation: false,
    grid: { top: 20, right: 20, bottom: 48, left: 56 },
    legend: {
      show: true, bottom: 0,
      data: [
        { name: "Essay value", icon: "roundRect" },
        { name: "Trend (rolling avg)", icon: "line" },
      ],
      textStyle: { fontSize: 10, color: "#6b7280" },
      itemWidth: 12, itemHeight: 6,
    },
    tooltip: {
      trigger: "axis", confine: true,
      axisPointer: { type: "line", lineStyle: { color: "rgba(107,114,128,0.4)", width: 1 } },
      formatter: (params) => {
        const primary = Array.isArray(params)
          ? params.find((p) => p.seriesName === "Essay value") || params[0] : params;
        const d = primary?.data || {};
        const pct = Number.isFinite(Number(d.raw)) ? Number(d.raw).toFixed(1) : "0.0";
        const title = d.title || "Untitled";
        const date = d.date && !d.date.startsWith("Essay") ? d.date : "";
        const genre = d.assignmentType || "Document";
        const genreColor = GENRE_BAR_COLORS[genre] || GENRE_BAR_COLORS.Document;
        return [
          `<div style="font-size:12px;min-width:170px;">`,
          `<div style="font-weight:700;margin-bottom:2px;">${title}</div>`,
          date ? `<div style="color:#6b7280;font-size:11px;margin-bottom:3px;">${date}</div>` : "",
          `<div style="display:flex;align-items:center;gap:5px;margin-bottom:4px;">`,
          `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${genreColor};flex-shrink:0;"></span>`,
          `<span style="color:#374151;font-size:11px;">${genre}</span></div>`,
          `<div><span style="color:#6b7280;">${metricTitle}:</span> <b>${pct}%</b></div>`,
          `<div style="color:#9ca3af;font-size:10px;margin-top:5px;border-top:1px solid #f3f4f6;padding-top:4px;">Click to pin · Click again to unpin</div>`,
          `</div>`,
        ].join("");
      },
    },
    xAxis: {
      type: "category", data: xLabels,
      axisLabel: { fontSize: 11, interval: 0, rotate: xLabels.length > 6 ? 30 : 0, overflow: "truncate", width: 80 },
      axisPointer: { show: true, type: "line", lineStyle: { color: "rgba(107,114,128,0.4)", width: 1 } },
    },
    yAxis: {
      type: "value", min: finalMin, max: finalMax,
      axisLabel: { formatter: "{value}%", fontSize: 11 },
      splitLine: { lineStyle: { color: "#f3f4f6" } },
    },
    series: [
      {
        name: "Essay value", type: "bar", data: barData, barMaxWidth: 32,
        emphasis: { focus: "none" }, select: { disabled: true },
        blur: { itemStyle: { opacity: 1 } }, z: 2,
      },
      {
        name: "Trend (rolling avg)", type: "line", data: lineData,
        smooth: true, symbol: "circle", symbolSize: 7,
        lineStyle: { color: "#84cc16", width: 2 }, itemStyle: { color: "#84cc16" },
        emphasis: { focus: "none" }, select: { disabled: true },
        blur: { lineStyle: { opacity: 1 }, itemStyle: { opacity: 1 } }, z: 3,
      },
    ],
  };
}

/* ══════════════════════════════════════════════════════════════
   FROZEN CHART COMPONENT
   Receives a fully-built, stable option object.
   Re-renders only when frozenOption reference changes.
   Pinned tooltip state lives in the parent and does NOT
   pass through here, so tooltip interactions never redraw charts.
   ══════════════════════════════════════════════════════════════ */
const FrozenChart = ({ frozenOption, onBarClick }) => {
  const onEvents = useMemo(() => ({
    click: (params) => {
      if (params?.seriesName !== "Essay value") return;
      onBarClick?.(params?.dataIndex);
    },
  }), [onBarClick]);

  return (
    <ReactECharts
      option={frozenOption}
      style={{ height: "100%", width: "100%" }}
      notMerge={false}
      lazyUpdate={false}
      onEvents={onEvents}
    />
  );
};

/* ══════════════════════════════════════════════════════════════
   COMPUTE SERIES FROM DOCS
   Pure function — no hooks, safe to call from useEffect.
   ══════════════════════════════════════════════════════════════ */
function computeSeriesFromDocs({ selectedMetrics, docIdsAsc, docsObj, essaysInRangeAsc }) {
  const out = {};
  for (const metricId of selectedMetrics) {
    const points = [];
    for (let i = 0; i < docIdsAsc.length; i++) {
      const docId = docIdsAsc[i];
      const doc = docsObj?.[docId];
      const essay = essaysInRangeAsc[i] || {};
      const dateLabel = (essay?.date && String(essay.date) !== "—") ? String(essay.date) : null;
      const label = dateLabel || `Essay ${i + 1}`;
      const title = (essay?.title && String(essay.title)) || `Document ${i + 1}`;
      const assignmentType = essay?.assignmentType || essay?.tags?.[0] || inferAssignmentType(doc?.text || "");
      const raw = coveragePercentFromDoc(doc, metricId);
      points.push({ idx: i, label, title, docId, raw, value: raw, assignmentType, metricLabel: metricId });
    }
    out[metricId] = points;
  }
  return out;
}

/* ══════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ══════════════════════════════════════════════════════════════ */
export default function StudentDetailGrowth({
  metrics,
  setMetrics,
  studentID,
  essaysInRangeAsc = [],
}) {
  const selectedMetrics = useMemo(() => normalizeSelectedMetrics(metrics), [metrics]);
  const { courseId } = useCourseIdContext();
  const origin = getConfiguredWsOrigin();
  const wsUrl = `${origin}/wsapi/communication_protocol`;

  const docIdsAsc = useMemo(() => {
    return (Array.isArray(essaysInRangeAsc) ? essaysInRangeAsc : [])
      .map((e) => (e?.id || "").toString().trim())
      .filter(Boolean);
  }, [essaysInRangeAsc]);

  const enabled = !!studentID && docIdsAsc.length > 0 && selectedMetrics.length > 0;

  const dataScope = useMemo(() => {
    if (!enabled) return { wo: { execution_dag: "writing_observer", target_exports: [], kwargs: {} } };
    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["single_student_docs_with_nlp_annotations", "student_with_docs"],
        kwargs: { course_id: courseId, student_id: studentID, document: docIdsAsc, nlp_options: selectedMetrics },
      },
    };
  }, [enabled, courseId, studentID, docIdsAsc, selectedMetrics]);

  const scopeKey = useMemo(() =>
    stableStringify({ enabled, studentID, courseId, docIdsAsc, selectedMetrics }),
  [enabled, studentID, courseId, docIdsAsc, selectedMetrics]);

  // ── Raw WS stream state ───────────────────────────────────────
  const [loData, setLoData] = useState(null);
  const [loErrors, setLoErrors] = useState(null);

  // ── Loading indicator state ───────────────────────────────────
  // Starts true when enabled so the loading spinner shows immediately.
  const [isFetching, setIsFetching] = useState(enabled);
  const prevScopeKeyRef = useRef(null); // null so first scope always triggers reset

  useEffect(() => {
    if (!enabled) {
      setIsFetching(false);
      return;
    }
    if (prevScopeKeyRef.current !== scopeKey) {
      prevScopeKeyRef.current = scopeKey;
      setIsFetching(true);
      setLoData(null);
      setLoErrors(null);
      setFrozenSeriesByMetric({});
      setFrozenChartOptions({});
    }
  }, [enabled, scopeKey]);

  useEffect(() => {
    if (!enabled) return;
    const hasErrors = loErrors && (
      (Array.isArray(loErrors) && loErrors.length > 0) ||
      (typeof loErrors === "object" && Object.keys(loErrors).length > 0)
    );
    if (hasErrors) { setIsFetching(false); }
  }, [enabled, loErrors]);

  // ── FROZEN SERIES & CHART OPTIONS ────────────────────────────
  // These are only ever updated once per scope: when loData first
  // arrives with actual doc content. After that, WS ticks may keep
  // updating loData but we ignore them for chart rendering.
  const [frozenSeriesByMetric, setFrozenSeriesByMetric] = useState({});
  const [frozenChartOptions, setFrozenChartOptions] = useState({});
  const frozenScopeRef = useRef(null); // tracks which scopeKey the frozen data belongs to

  useEffect(() => {
    if (!enabled || !loData) return;

    const docsObj = loData?.students?.[studentID]?.documents || {};

    // Only freeze once per scopeKey — ignore subsequent WS ticks
    if (frozenScopeRef.current === scopeKey) return;

    // Check that at least one metric has data in at least one doc
    // before freezing, so we don't freeze on a partial/empty response
    const hasAnyData = selectedMetrics.some((metricId) =>
      docIdsAsc.some((docId) => {
        const offsets = docsObj?.[docId]?.[metricId]?.offsets;
        return Array.isArray(offsets) && offsets.length > 0;
      })
    );

    if (!hasAnyData) return; // wait for a richer tick

    // Freeze
    frozenScopeRef.current = scopeKey;
    const series = computeSeriesFromDocs({ selectedMetrics, docIdsAsc, docsObj, essaysInRangeAsc });
    setFrozenSeriesByMetric(series);

    const options = {};
    for (const metricId of selectedMetrics) {
      const points = series[metricId];
      if (Array.isArray(points)) {
        options[metricId] = buildEChartOption({ metricId, points });
      }
    }
    setFrozenChartOptions(options);
    setIsFetching(false);
  }, [loData, enabled, scopeKey, selectedMetrics, docIdsAsc, essaysInRangeAsc, studentID]);

  // ── Pinned tooltips — never cause chart re-renders ────────────
  const [pinnedPointByMetric, setPinnedPointByMetric] = useState({});

  // ── Genres present in documents ──────────────────────────────
  const genresPresent = useMemo(() => {
    const types = new Set(essaysInRangeAsc.map((e) => e?.assignmentType || e?.tags?.[0] || "Document"));
    return new Set(ALL_GENRES.filter((g) => types.has(g)));
  }, [essaysInRangeAsc]);

  const showEmpty = selectedMetrics.length === 0;
  const showLoading = isFetching && Object.keys(frozenChartOptions).length === 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
      {enabled ? (
        <LORunner
          key={scopeKey}
          scopeKey={scopeKey}
          wsUrl={wsUrl}
          dataScope={dataScope}
          onData={(d) => setLoData(d)}
          onErrors={(e) => setLoErrors(e)}
        />
      ) : null}

      <MetricsPanel
        metrics={metrics}
        setMetrics={setMetrics}
        groupBy="trait"
        title="Metrics"
        stickyTopClassName="top-24"
      />

      <section className="col-span-12 md:col-span-8 xl:col-span-9">

        {/* ── Legend header ─────────────────────────────────── */}
        <div className="mb-4 flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3 flex-wrap">
            <div className="text-xs text-gray-500">
              Showing <span className="font-medium text-gray-700">{docIdsAsc.length}</span>{" "}
              {docIdsAsc.length === 1 ? "essay" : "essays"}
            </div>

            {/* Full genre legend — always show all, dim absent ones */}
            <div className="flex items-center gap-2 flex-wrap">
              {ALL_GENRES.map((genre) => {
                const active = genresPresent.has(genre);
                return (
                  <span
                    key={genre}
                    className={`inline-flex items-center gap-1.5 text-[11px] transition-opacity ${
                      active ? "text-gray-700 opacity-100" : "text-gray-400 opacity-40"
                    }`}
                    title={active ? `${genre} essays present` : `No ${genre} essays in current range`}
                  >
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-sm"
                      style={{ background: GENRE_BAR_COLORS[genre], opacity: active ? 1 : 0.35 }}
                    />
                    {genre}
                  </span>
                );
              })}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Rolling avg legend */}
            <div className="flex items-center gap-1.5 text-[11px] text-gray-500">
              <span className="inline-block h-0.5 w-6 rounded" style={{ background: "#84cc16" }} />
              <span>Rolling avg</span>
            </div>

            {isFetching && (
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-900">
                <Loader2 className="h-3.5 w-3.5 animate-spin" /> Updating...
              </div>
            )}
          </div>
        </div>

        {/* Genre mixing warning */}
        {genresPresent.size > 1 && (
          <div className="mb-4 flex items-start gap-2 rounded-xl bg-blue-50 border border-blue-200 px-4 py-2.5 text-xs text-blue-800">
            <Info className="h-3.5 w-3.5 text-blue-500 mt-0.5 shrink-0" />
            <span>
              This student has written multiple assignment types (shown by bar color).
              Changes between different genres may reflect task demands rather than skill growth.
              For clearest growth signals, compare bars of the same color.
            </span>
          </div>
        )}

        {/* ── Content ───────────────────────────────────────── */}
        {showEmpty ? (
          <div className="bg-white rounded-2xl border border-dashed border-gray-300 p-10 text-center text-gray-500 shadow-sm">
            Select one or more metrics from the left panel to view trends over time.
          </div>
        ) : showLoading ? (
          <div className="bg-white rounded-2xl border border-gray-200 p-6 text-gray-700 shadow-sm flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading documents...
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {selectedMetrics.map((metricId) => {
              const points = frozenSeriesByMetric[metricId];
              const frozenOption = frozenChartOptions[metricId];
              const metricTitle = getMetricTitle(metricId);
              const trait = getMetricTrait(metricId);
              const pinnedPoint = pinnedPointByMetric[metricId] || null;

              if (!frozenOption || !Array.isArray(points)) {
                return (
                  <div key={metricId} className="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-gray-900">{metricTitle}</h4>
                      <TraitBadge trait={trait} />
                      <Loader2 className="h-3.5 w-3.5 animate-spin ml-auto text-gray-400" />
                    </div>
                    <div className="h-64 rounded-xl border border-gray-200 bg-gray-50 flex items-center justify-center">
                      <div className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-700 shadow-sm">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" /> Computing metric...
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <div key={metricId} className="bg-white rounded-2xl border border-gray-200 p-4 shadow-sm">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex flex-col gap-1">
                      <h4 className="font-semibold text-gray-900 text-base">{metricTitle}</h4>
                      <TraitBadge trait={trait} />
                    </div>
                    <span className="text-xs text-gray-500 mt-0.5">
                      <span className="font-medium text-gray-700">{points.length}</span>
                      {" "}{points.length === 1 ? "essay" : "essays"}
                    </span>
                  </div>

                  {/* Frozen chart — WS ticks never reach here */}
                  <div className="relative h-64">
                    <FrozenChart
                      frozenOption={frozenOption}
                      onBarClick={(idx) => {
                        const point = points[idx];
                        if (!point) return;
                        setPinnedPointByMetric((prev) => {
                          const cur = prev[metricId];
                          if (cur && cur.idx === idx) {
                            const next = { ...prev }; delete next[metricId]; return next;
                          }
                          return { ...prev, [metricId]: { ...point, idx } };
                        });
                      }}
                    />
                  </div>

                  {pinnedPoint ? (
                    <PinnedTooltip
                      point={pinnedPoint}
                      metricTitle={metricTitle}
                      onClear={() => setPinnedPointByMetric((prev) => {
                        const n = { ...prev }; delete n[metricId]; return n;
                      })}
                    />
                  ) : (
                    <p className="mt-2 text-xs text-gray-400 leading-relaxed">
                      Hover a bar to see essay details. Click any bar to pin details below the chart.
                      {genresPresent.size > 1 && " Bar color shows assignment type."}
                    </p>
                  )}

                  <InstructionalSuggestion metricId={metricId} trait={trait} points={points} />
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
