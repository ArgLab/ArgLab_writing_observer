"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  X, Gauge, Loader2, AlertTriangle, Info, Clock, Pencil,
  ChevronLeft, ChevronRight, ChevronDown, ChevronUp,
  TrendingUp, TrendingDown, Minus, Clipboard, AlertCircle,
  FlaskConical, Lightbulb,
} from "lucide-react";

import { MetricsPanel, METRIC_BY_ID, METRIC_TEACHER_DESC } from "@/app/components/MetricsPanel";
import { useLOConnectionDataManager } from "lo_event/lo_event/lo_assess/components/components.jsx";
import { useCourseIdContext } from "@/app/providers/CourseIdProvider";
import { getConfiguredWsOrigin } from "@/app/utils/ws";

/* ─────────────────────────────────────────────
   6+1 Trait helpers
───────────────────────────────────────────── */
const TRAIT_FOR_CATEGORY = {
  language: "Word Choice", argumentation: "Ideas & Content",
  statements: "Ideas & Content", transitions: "Organization",
  pos: "Sentence Fluency", sentence_type: "Sentence Fluency",
  source_information: "Ideas & Content", dialogue: "Voice",
  tone: "Voice", details: "Ideas & Content", other: "Conventions",
};

function getMetricTrait(id) {
  const def = METRIC_BY_ID?.[id];
  if (def?.trait) return def.trait;
  if (def?.categoryKey) return TRAIT_FOR_CATEGORY[def.categoryKey] || "Conventions";
  return "Conventions";
}
function getMetricTitle(id) {
  const def = METRIC_BY_ID?.[id];
  if (def?.title) return def.title;
  return String(id).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const TRAIT_DOT = {
  "Ideas & Content":  "bg-amber-400",
  "Organization":     "bg-blue-400",
  "Voice":            "bg-rose-400",
  "Word Choice":      "bg-violet-400",
  "Sentence Fluency": "bg-teal-400",
  "Conventions":      "bg-slate-400",
};
const TRAIT_PILL = {
  "Ideas & Content":  "bg-amber-50 text-amber-700 ring-amber-200",
  "Organization":     "bg-blue-50 text-blue-700 ring-blue-200",
  "Voice":            "bg-rose-50 text-rose-700 ring-rose-200",
  "Word Choice":      "bg-violet-50 text-violet-700 ring-violet-200",
  "Sentence Fluency": "bg-teal-50 text-teal-700 ring-teal-200",
  "Conventions":      "bg-slate-50 text-slate-700 ring-slate-200",
};

function TraitDot({ trait, size = "h-2 w-2" }) {
  return <span className={`inline-block rounded-full shrink-0 ${size} ${TRAIT_DOT[trait] || "bg-gray-300"}`} />;
}
function TraitPill({ trait }) {
  const cls = TRAIT_PILL[trait] || "bg-gray-50 text-gray-600 ring-gray-200";
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-semibold ring-1 ring-inset ${cls}`}>
      <TraitDot trait={trait} size="h-1.5 w-1.5" />
      {trait}
    </span>
  );
}

/* ─────────────────────────────────────────────
   Assignment type
───────────────────────────────────────────── */
const TYPE_COLORS = {
  Narrative:     { bg:"bg-violet-50", text:"text-violet-700", ring:"ring-violet-200", dot:"bg-violet-400" },
  Argumentative: { bg:"bg-amber-50",  text:"text-amber-700",  ring:"ring-amber-200",  dot:"bg-amber-400" },
  Analytical:    { bg:"bg-blue-50",   text:"text-blue-700",   ring:"ring-blue-200",   dot:"bg-blue-400" },
  Expository:    { bg:"bg-teal-50",   text:"text-teal-700",   ring:"ring-teal-200",   dot:"bg-teal-400" },
  Document:      { bg:"bg-emerald-50",text:"text-emerald-700",ring:"ring-emerald-200",dot:"bg-emerald-400" },
  Other:         { bg:"bg-gray-50",   text:"text-gray-600",   ring:"ring-gray-200",   dot:"bg-gray-400" },
};
function inferAssignmentType(text) {
  const t = (text || "").toLowerCase();
  if (/argue|claim|thesis|evidence|counterargument/.test(t)) return "Argumentative";
  if (/analyze|analysis|examine|compare|contrast/.test(t)) return "Analytical";
  if (/once upon|story|character|plot|setting/.test(t)) return "Narrative";
  if (/explain|describe|inform|definition/.test(t)) return "Expository";
  return "Document";
}
function TypeBadge({ type }) {
  const c = TYPE_COLORS[type] || TYPE_COLORS.Document;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ring-1 ring-inset ${c.bg} ${c.text} ${c.ring}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />{type}
    </span>
  );
}

/* ─────────────────────────────────────────────
   Constants
───────────────────────────────────────────── */
const DEFAULT_METRICS = [
  "academic_language","informal_language","latinate_words",
  "transition_words","citations","sentences","paragraphs",
];

const AVG_WORD_LENGTH_CHARS = 5;
function charsToWords(chars) { return Math.round((chars || 0) / AVG_WORD_LENGTH_CHARS); }

/* ─────────────────────────────────────────────
   Extract real paste + time stats from doc node
───────────────────────────────────────────── */
function extractPasteStats(doc) {
  if (!doc || typeof doc !== "object") {
    return { largePasteCount: 0, totalPasteChars: 0, totalPasteWords: 0, copyCount: 0, allPasteCount: 0, timeOnTask: null };
  }
  const largePasteCount = doc.length_bins?.long_201_plus ?? 0;
  const totalPasteChars = doc.total_paste_chars ?? 0;
  return {
    largePasteCount,
    totalPasteChars,
    totalPasteWords: charsToWords(totalPasteChars),
    copyCount:     doc.copy_count         ?? 0,
    allPasteCount: doc.pastes_with_length ?? 0,
    timeOnTask:    typeof doc.time_on_task === "number" ? doc.time_on_task : null,
  };
}

/* ─────────────────────────────────────────────
   Process signal definitions
───────────────────────────────────────────── */
const PROCESS_DEFS = [
  { key: "pause_to_word_ratio", label: "Pause-to-Word Ratio",  desc: "How often the student pauses relative to words produced.",  unit: "",     category: "Fluency"    },
  { key: "revision_rate",       label: "Revision Rate",         desc: "Fraction of keystrokes that were deletions.",               unit: "%",    category: "Revision"   },
  { key: "burst_length",        label: "Avg. Burst Length",     desc: "Average words typed in uninterrupted runs.",                unit: " wds", category: "Fluency"    },
  { key: "time_on_task_mins",   label: "Time on Task",          desc: "Total active writing time for this essay.",                 unit: " min", category: "Engagement" },
  { key: "edit_count",          label: "Edit Count",            desc: "Total edit events. Reflects revision activity.",           unit: "",     category: "Revision"   },
];

function deriveProcessMetrics(doc) {
  if (!doc) return {};
  return {
    pause_to_word_ratio: doc?.pause_to_word_ratio ?? null,
    revision_rate:       doc?.revision_rate       ?? null,
    burst_length:        doc?.avg_burst_length    ?? null,
    time_on_task_mins:   doc?.time_on_task        ?? doc?.time_on_task_mins ?? null,
    edit_count:          doc?.edit_count          ?? null,
  };
}

/* ─────────────────────────────────────────────
   Pure helpers
───────────────────────────────────────────── */
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function mean(arr) {
  if (!arr.length) return 0;
  return arr.reduce((s, x) => s + x, 0) / arr.length;
}
function stableStringify(obj) {
  const seen = new WeakSet();
  const sort = (v) => {
    if (v === null || typeof v !== "object") return v;
    if (seen.has(v)) return "[Circular]";
    seen.add(v);
    if (Array.isArray(v)) return v.map(sort);
    const out = {};
    for (const k of Object.keys(v).sort()) out[k] = sort(v[k]);
    return out;
  };
  try { return JSON.stringify(sort(obj)); } catch { return String(obj); }
}
function normalizeMetrics(input) {
  if (!input) return [];
  const pick = (x) => {
    if (!x) return null;
    if (typeof x === "string") return x;
    if (typeof x === "object") return x.metricKey || x.id || x.key || x.name || x.value || null;
    return null;
  };
  if (Array.isArray(input)) return input.map(pick).filter(Boolean).map((s) => String(s).trim()).filter(Boolean);
  if (typeof input === "object") return Object.entries(input).filter(([, v]) => !!v).map(([k]) => String(k).trim()).filter(Boolean);
  return [];
}

/* ─────────────────────────────────────────────
   metricValue — the single source of truth for
   reading a metric number from a doc node.

   Priority order:
   1. doc[metricId].metric  — pre-computed number
      from the NLP pipeline (present in WS response
      as confirmed in the JSON: "metric": 19).
      This is the correct value to use for trajectory
      comparison since it's what the pipeline computed.
   2. Offset-based coverage % — fallback for older
      data shapes that don't have .metric yet.
───────────────────────────────────────────── */
function metricValue(doc, id) {
  // Prefer the pre-computed metric value — already the right number
  const direct = doc?.[id]?.metric;
  if (direct != null && Number.isFinite(Number(direct))) return Number(direct);

  // Fallback: compute coverage % from character offsets
  const text = (doc?.text || "").toString();
  const L = text.length;
  if (!L) return 0;
  const offsets = doc?.[id]?.offsets;
  if (!Array.isArray(offsets) || !offsets.length) return 0;
  const ranges = [];
  for (const p of offsets) {
    if (!Array.isArray(p) || p.length < 2) continue;
    const s0 = Number(p[0]), len = Number(p[1]);
    if (!Number.isFinite(s0) || !Number.isFinite(len) || len <= 0) continue;
    const s = clamp(s0, 0, L), e = clamp(s0 + len, 0, L);
    if (e > s) ranges.push([s, e]);
  }
  if (!ranges.length) return 0;
  ranges.sort((a, b) => a[0] - b[0]);
  let covered = 0, [cs, ce] = ranges[0];
  for (let i = 1; i < ranges.length; i++) {
    const [s, e] = ranges[i];
    if (s <= ce) ce = Math.max(ce, e);
    else { covered += ce - cs; cs = s; ce = e; }
  }
  return ((covered + ce - cs) / L) * 100;
}

/* ─────────────────────────────────────────────
   INSTRUCTIONAL SUGGESTION LOGIC
───────────────────────────────────────────── */
function getMetricSuggestion(metricKey, trait, delta, assignmentType) {
  const title = getMetricTitle(metricKey);
  const drop  = Math.abs(delta).toFixed(1);

  const specific = {
    academic_language:   `Academic language coverage dropped ${drop}pts on this essay. Before the next assignment, try a targeted vocabulary activity — give the student a word bank of formal alternatives for common informal terms they use.`,
    informal_language:   `Informal language increased by ${drop}pts. A focused editing pass before submission — specifically looking for casual phrasing — can help. Consider a brief 1:1 to discuss register and audience awareness.`,
    latinate_words:      `Use of Latinate (sophisticated) vocabulary fell ${drop}pts. Modeling three or four academic synonyms during whole-class discussion, or building a personal word wall for this student, could help rebuild this over the next few essays.`,
    transition_words:    `Transition word coverage dropped ${drop}pts. A sentence-starter scaffold for the next assignment — listing connective phrases the student can draw from — often produces quick improvement in this dimension.`,
    citations:           `Citation use declined ${drop}pts. Check whether the assignment prompt required source integration; if so, a brief conference reviewing how to embed and introduce evidence is warranted before the next task.`,
    sentences:           `Sentence count or variety fell ${drop}pts. A sentence-combining revision exercise focused on this essay — asking the student to merge two short sentences — can build structural complexity over time.`,
    paragraphs:          `Paragraph structure declined ${drop}pts. A quick conference reviewing paragraph expectations (topic sentence, evidence, wrap-up) before the next assignment may help this student rebuild organizational habits.`,
    explicit_argument:   `Explicit argument signals weakened ${drop}pts. Consider a targeted mini-lesson on thesis statement framing or claim-evidence structure before the next argumentative task.`,
    concrete_details:    `Use of concrete details dropped ${drop}pts. Ask the student to identify one claim in this essay and add a specific example or piece of evidence — this targeted revision habit builds detail use over time.`,
  };

  if (specific[metricKey]) return specific[metricKey];

  const traitFallback = {
    "Word Choice":      `${title} (Word Choice) fell ${drop}pts. A targeted vocabulary activity or editing checklist before the next assignment can help reinforce this dimension.`,
    "Ideas & Content":  `${title} (Ideas & Content) declined ${drop}pts. Consider a brief conference on the specific content expectation before the next essay.`,
    "Organization":     `${title} (Organization) dropped ${drop}pts. Review structural expectations explicitly with this student — a graphic organizer for the next assignment can help anchor organization.`,
    "Voice":            `${title} (Voice) fell ${drop}pts. Encourage the student to read a paragraph of their essay aloud — this often reveals where their voice feels flat or inconsistent.`,
    "Sentence Fluency": `${title} (Sentence Fluency) declined ${drop}pts. A sentence-level revision task on this essay can help; ask the student to vary the opening of three sentences.`,
    "Conventions":      `${title} (Conventions) dropped ${drop}pts. A targeted editing pass focused specifically on this convention before the next submission may help.`,
  };

  return traitFallback[trait] || `${title} declined ${drop}pts on this essay. Consider targeted feedback before the next assignment.`;
}

function MetricSuggestion({ metricKey, trait, delta, assignmentType }) {
  const [expanded, setExpanded] = useState(false);
  const suggestion = getMetricSuggestion(metricKey, trait, delta, assignmentType);
  return (
    <div className="mx-4 mb-2 rounded-xl border border-amber-200 bg-amber-50 overflow-hidden">
      <button onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-amber-100 transition-colors">
        <Lightbulb className="h-3 w-3 text-amber-500 shrink-0" />
        <span className="shrink-0 inline-flex items-center px-2.5 py-0.5 rounded-md border border-amber-400 bg-white text-[10px] font-semibold text-amber-700 hover:bg-amber-50 transition-colors shadow-sm ml-auto">
          {expanded ? "Hide suggestion" : "Show suggestion"}
        </span>
      </button>
      {expanded && (
        <div className="px-3 pb-2.5 pt-1 border-t border-amber-200">
          <p className="text-[11px] text-amber-900 leading-relaxed">{suggestion}</p>
          <p className="mt-1 text-[10px] text-amber-600 italic">
            Verify against your knowledge of this student and assignment context before acting.
          </p>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────
   MetricRow — shows direction label + raw values.
   Unit label adapts to the metric's summary_type:
     percent  → show as "X.0"  (already a %)
     total    → show as integer count
     counts   → show as integer count
───────────────────────────────────────────── */
function MetricRow({ metricKey, baseline, currentValue, assignmentType }) {
  const title = getMetricTitle(metricKey);
  const trait = getMetricTrait(metricKey);
  const desc  = METRIC_TEACHER_DESC?.[metricKey] || "";
  const delta = currentValue - baseline;
  const isUp   = delta >  0.15;
  const isDown = delta < -0.15;
  const absDelta = Math.abs(delta);
  const qualifier = absDelta < 1 ? "Slightly" : absDelta < 3 ? "Notably" : "Much";
  const directionLabel = isUp
    ? `↑ ${qualifier} higher than usual`
    : isDown
    ? `↓ ${qualifier} lower than usual`
    : "About the same as usual";
  const directionColor = isUp
    ? absDelta >= 3 ? "text-emerald-700" : absDelta >= 1 ? "text-emerald-600" : "text-emerald-500"
    : isDown
    ? absDelta >= 3 ? "text-rose-700" : absDelta >= 1 ? "text-rose-500" : "text-rose-400"
    : "text-gray-400";

  // Format the raw value sensibly:
  // percent metrics → show with 1 decimal + "%"
  // total/count metrics → show as integer
  const def = METRIC_BY_ID?.[metricKey];
  const isPercent = def?.function === "percent";
  const fmt = (v) => isPercent ? `${Number(v).toFixed(1)}%` : `${Math.round(Number(v))}`;

  return (
    <>
      <div className="flex items-start justify-between gap-4 px-4 py-3
        border-b border-gray-100 last:border-0 hover:bg-gray-50/60 transition-colors bg-white pl-5">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5">
            <TraitDot trait={trait} />
            <span className="text-sm font-medium text-gray-900">{title}</span>
          </div>
          {desc && <div className="text-[11px] text-gray-400 mt-0.5 leading-relaxed">{desc}</div>}
        </div>
        <div className="shrink-0 text-right">
          <div className={`text-xs font-semibold ${directionColor} whitespace-nowrap`}>{directionLabel}</div>
          <div className="text-[10px] text-gray-400 tabular-nums whitespace-nowrap mt-0.5">
            Usual: {fmt(baseline)} &nbsp;·&nbsp; This essay: {fmt(currentValue)}
          </div>
        </div>
      </div>
      {isDown && (
        <MetricSuggestion metricKey={metricKey} trait={trait} delta={delta} assignmentType={assignmentType} />
      )}
    </>
  );
}

function MetricSummaryPanel({ metricSummaries, assignmentType }) {
  const [collapsed, setCollapsed] = useState({});
  const TRAIT_ORDER = ["Ideas & Content","Organization","Voice","Word Choice","Sentence Fluency","Conventions"];
  const byTrait = {};
  for (const m of metricSummaries) {
    const t = getMetricTrait(m.key);
    if (!byTrait[t]) byTrait[t] = [];
    byTrait[t].push(m);
  }
  const traitGroups = TRAIT_ORDER.filter((t) => byTrait[t]?.length);
  if (!metricSummaries.length) return null;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
      {traitGroups.map((trait) => {
        const rows = byTrait[trait];
        const isCollapsed = collapsed[trait];
        const decliningCount = rows.filter((m) => (m.currentValue - m.baseline) < -0.15).length;
        return (
          <div key={trait}>
            <button onClick={() => setCollapsed((prev) => ({ ...prev, [trait]: !prev[trait] }))}
              className="w-full flex items-center justify-between px-4 py-2.5
                bg-gray-50 hover:bg-gray-100 border-b border-gray-200 transition-colors">
              <div className="flex items-center gap-2">
                <TraitDot trait={trait} size="h-2.5 w-2.5" />
                <span className="text-xs font-bold text-gray-800">{trait}</span>
                <span className="text-[10px] text-gray-400">{rows.length} {rows.length === 1 ? "metric" : "metrics"}</span>
                {decliningCount > 0 && (
                  <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-rose-50 text-rose-600 ring-1 ring-rose-200">
                    <TrendingDown className="h-2 w-2" />{decliningCount} lower than usual
                  </span>
                )}
              </div>
              {isCollapsed ? <ChevronDown className="h-3.5 w-3.5 text-gray-400" /> : <ChevronUp className="h-3.5 w-3.5 text-gray-400" />}
            </button>
            {!isCollapsed && rows.map((m) => (
              <MetricRow key={m.key} metricKey={m.key} baseline={m.baseline} currentValue={m.currentValue} assignmentType={assignmentType} />
            ))}
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────
   PasteCard
───────────────────────────────────────────── */
function PasteCard({ pasteStats }) {
  if (!pasteStats) return null;
  const { largePasteCount, totalPasteWords, copyCount, timeOnTask } = pasteStats;
  const isNotable = largePasteCount >= 3 || totalPasteWords >= 80;

  const stats = [
    { val: largePasteCount,    label: "large pastes",  desc: "Paste events 200+ chars",     hi: largePasteCount >= 3   },
    { val: `~${totalPasteWords}`, label: "words pasted", desc: "Estimated from paste chars", hi: totalPasteWords >= 80  },
    { val: copyCount,           label: "copy events",   desc: "Total copy actions",          hi: false                  },
  ];

  return (
    <div className={`rounded-2xl border p-4 shadow-sm ${isNotable ? "border-amber-200 bg-amber-50/60" : "border-gray-200 bg-white"}`}>
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <Clipboard className={`h-4 w-4 ${isNotable ? "text-amber-500" : "text-gray-400"}`} />
          <span className="text-sm font-semibold text-gray-900">Paste Activity</span>
        </div>
        <div className="flex items-center gap-2">
          {isNotable && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700 ring-1 ring-amber-200">
              <AlertCircle className="h-2.5 w-2.5" /> Notable
            </span>
          )}
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {stats.map(({ val, label, desc, hi }) => (
          <div key={label} className="rounded-xl bg-white border border-gray-100 px-2 py-2.5 text-center">
            <div className={`text-lg font-bold ${hi ? "text-amber-600" : "text-gray-900"}`}>{val}</div>
            <div className="text-[10px] font-medium text-gray-600 mt-0.5 leading-tight">{label}</div>
            <div className="text-[9px] text-gray-400 mt-0.5 leading-tight">{desc}</div>
          </div>
        ))}
      </div>
      {isNotable && (
        <p className="mt-3 text-xs text-amber-700 leading-relaxed">
          This essay contains notable paste activity. Pasted content may reflect research, drafting from notes, or copied material — consider discussing with the student how the pasted content connects to their own ideas.
        </p>
      )}
    </div>
  );
}

function DeltaBadge({ delta }) {
  if (delta == null || !Number.isFinite(delta)) return null;
  const isUp = delta > 0.15; const isDown = delta < -0.15;
  const Icon = isUp ? TrendingUp : isDown ? TrendingDown : Minus;
  const cls  = isUp ? "text-emerald-600" : isDown ? "text-rose-500" : "text-gray-400";
  return (
    <span className={`inline-flex items-center gap-0.5 text-[10px] font-semibold ${cls}`}>
      <Icon className="h-2.5 w-2.5" />
      {isUp ? `+${delta.toFixed(1)}` : isDown ? `${delta.toFixed(1)}` : "on baseline"}
    </span>
  );
}

function ProcessCard({ current, baseline }) {
  const hasAny = current && Object.values(current).some((v) => v != null);
  return (
    <div className="rounded-2xl border border-gray-200 bg-white shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 flex items-center gap-2">
        <span className="text-sm font-semibold text-gray-900">Process Signals</span>
        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-600 ring-1 ring-rose-200 uppercase tracking-wide">
          <FlaskConical className="h-2 w-2" /> Prototype
        </span>
        <span className="ml-auto text-[10px] text-gray-400 italic">RQ1 keystroke features</span>
      </div>
      {!hasAny ? (
        <div className="px-4 py-3 text-xs text-gray-400 italic">No process data available. Wire to keystroke pipeline.</div>
      ) : (
        <div className="divide-y divide-gray-100">
          {PROCESS_DEFS.map((def) => {
            const cur = current?.[def.key]; const base = baseline?.[def.key];
            const hasCur = cur != null && Number.isFinite(Number(cur));
            const hasBase = base != null && Number.isFinite(Number(base));
            const delta = hasCur && hasBase ? Number(cur) - Number(base) : null;
            return (
              <div key={def.key} className="grid grid-cols-[1fr_auto] gap-3 items-center px-4 py-2.5">
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-gray-800">{def.label}</div>
                  <div className="text-[10px] text-gray-400 mt-0.5 truncate">{def.desc}</div>
                </div>
                <div className="text-right shrink-0">
                  {hasCur ? <span className="text-sm font-bold text-gray-900">{Number(cur).toFixed(1)}{def.unit}</span>
                           : <span className="text-xs text-gray-300 italic">n/a</span>}
                  {delta != null && <div className="mt-0.5"><DeltaBadge delta={delta} /></div>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function BaselineInfo({ docIds, currentIdx, docsObj }) {
  const [open, setOpen] = useState(false);
  const priorIds = (docIds || []).slice(0, currentIdx);
  if (!priorIds.length) return null;
  const priorTypes = [...new Set(priorIds.map((id) => inferAssignmentType(docsObj?.[id]?.text || "")))];
  const mixed = priorTypes.length > 1;
  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden">
      <button onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-2.5 text-left hover:bg-gray-50 transition-colors">
        <Info className="h-3.5 w-3.5 text-gray-400 shrink-0" />
        <span className="text-xs text-gray-600 font-medium flex-1">
          Baseline from {priorIds.length} prior {priorIds.length === 1 ? "essay" : "essays"}{mixed && " (mixed genres)"}
        </span>
        {mixed && <AlertCircle className="h-3.5 w-3.5 text-amber-400 shrink-0" />}
        <span className="shrink-0 inline-flex items-center px-2 py-0.5 rounded-md border border-gray-300 bg-white text-[10px] font-semibold text-gray-600 hover:bg-gray-50 transition-colors shadow-sm">
          {open ? "Hide" : "Show"}
        </span>
      </button>
      {open && (
        <div className="border-t border-gray-100 px-4 py-3 space-y-1.5">
          {mixed && (
            <p className="text-[11px] text-amber-700 bg-amber-50 rounded-lg px-2.5 py-1.5 mb-2">
              Baseline spans {priorTypes.join(" and ")} essays. Comparisons are most reliable within the same genre.
            </p>
          )}
          {priorIds.map((id, i) => {
            const type  = inferAssignmentType(docsObj?.[id]?.text || "");
            const words = docsObj?.[id]?.text ? docsObj[id].text.trim().split(/\s+/).filter(Boolean).length : null;
            return (
              <div key={id} className="flex items-center gap-2 text-[11px] text-gray-500">
                <span className="text-gray-300">#{i + 1}</span>
                <TypeBadge type={type} />
                {words != null && <span>{words.toLocaleString()} words</span>}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function EffortPills({ doc }) {
  const t = doc?.time_on_task ?? doc?.time_on_task_mins;
  const e = doc?.edit_count;
  if (t == null && e == null) return null;
  return (
    <div className="flex items-center gap-1.5">
      {t != null && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200">
          <Clock className="h-3 w-3 text-emerald-500" />{Math.round(t)} min
        </span>
      )}
      {e != null && (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs text-gray-500 bg-white border border-gray-200">
          <Pencil className="h-3 w-3" />{e} edits
        </span>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────
   Exported Modal
   Accepts initialDocsObj — the already-loaded
   frozen doc data from StudentDetail/Compare.
   Seeding from this means text and paste stats
   show immediately on open without waiting for
   the modal's own WS connection.
───────────────────────────────────────────── */
export function SingleEssayModal({
  studentKey, docId, docIds, docTitle, docIndex,
  initialWords, subtitleDate, onClose, onNavigate,
  initialDocsObj,
}) {
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev || ""; };
  }, []);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose?.(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const title    = docTitle || (docIndex ? `Essay ${docIndex}` : "Essay");
  const subtitle = subtitleDate || "";

  const currentNavIdx = useMemo(() => {
    if (!Array.isArray(docIds)) return -1;
    return docIds.findIndex((id) => String(id) === String(docId));
  }, [docIds, docId]);

  const canGoPrev = currentNavIdx > 0;
  const canGoNext = currentNavIdx >= 0 && currentNavIdx < (docIds?.length ?? 0) - 1;
  const handleNav = (delta) => {
    if (!onNavigate || !docIds) return;
    const nx = currentNavIdx + delta;
    if (nx >= 0 && nx < docIds.length) onNavigate(docIds[nx], nx);
  };

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={() => onClose?.()} />
      <div className="absolute inset-x-0 top-4 bottom-4 mx-auto px-4 w-[96vw] max-w-[1560px]">
        <div className="h-full bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden flex flex-col"
          onClick={(e) => e.stopPropagation()}>
          {/* Header */}
          <div className="bg-gray-900 text-white px-6 py-4 flex items-center justify-between gap-4 shrink-0">
            <div className="flex items-center gap-3 min-w-0">
              {onNavigate && (
                <div className="flex items-center gap-1 shrink-0">
                  <button onClick={() => handleNav(-1)} disabled={!canGoPrev}
                    className="h-8 w-8 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-30 flex items-center justify-center transition-colors" aria-label="Previous essay">
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button onClick={() => handleNav(1)} disabled={!canGoNext}
                    className="h-8 w-8 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-30 flex items-center justify-center transition-colors" aria-label="Next essay">
                    <ChevronRight className="h-4 w-4" />
                  </button>
                  {currentNavIdx >= 0 && (
                    <span className="text-xs text-white/40 ml-1 tabular-nums">{currentNavIdx + 1} / {docIds?.length}</span>
                  )}
                </div>
              )}
              <div className="min-w-0">
                <h2 className="text-base font-semibold truncate leading-tight">{title}</h2>
                {subtitle && <p className="text-xs text-white/50 mt-0.5 truncate">{subtitle}</p>}
              </div>
            </div>
            <button onClick={() => onClose?.()}
              className="inline-flex items-center gap-1.5 h-8 px-3 rounded-lg bg-white/10 hover:bg-white/20 text-sm font-medium transition-colors shrink-0"
              aria-label="Close">
              <X className="h-4 w-4" /> Close
            </button>
          </div>

          <div className="flex-1 min-h-0">
            <SingleEssayInner
              studentKey={studentKey}
              docId={docId}
              docIds={docIds}
              initialDocsObj={initialDocsObj}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   Inner modal
───────────────────────────────────────────── */
function SingleEssayInner({ studentKey, docId, docIds, initialDocsObj }) {
  const [selectedMetrics, setSelectedMetricsRaw] = useState(DEFAULT_METRICS);
  const { courseId } = useCourseIdContext();

  const setSelectedMetrics = useCallback((next) => {
    setSelectedMetricsRaw((prev) => {
      const resolved = typeof next === "function" ? next(prev) : next;
      return normalizeMetrics(resolved);
    });
  }, []);

  const exportEnabled = !!studentKey && !!docId &&
    Array.isArray(docIds) && docIds.length > 0 && selectedMetrics.length > 0;

  const dataScope = useMemo(() => {
    if (!exportEnabled) return { wo: { execution_dag: "writing_observer", target_exports: [], kwargs: {} } };
    return {
      wo: {
        execution_dag: "writing_observer",
        target_exports: [
          "single_student_docs_with_nlp_annotations",
          "single_student_paste",
          "single_student_copy_cut",
          "single_student_time_on_task",
        ],
        kwargs: {
          course_id:   courseId,
          student_id:  studentKey,
          document:    docIds,
          doc_ids:     docIds,
          nlp_options: selectedMetrics,
        },
      },
    };
  }, [exportEnabled, courseId, docIds, selectedMetrics, studentKey]);

  const origin = getConfiguredWsOrigin();
  const { connection, data: loData, errors: loErrors } = useLOConnectionDataManager({
    url: `${origin}/wsapi/communication_protocol`, dataScope,
  });

  const prevScopeRef = useRef(null);
  useEffect(() => {
    if (!connection?.sendMessage || !exportEnabled) return;
    const str = stableStringify(dataScope);
    if (str === prevScopeRef.current) return;
    prevScopeRef.current = str;
    try { connection.sendMessage(JSON.stringify(dataScope)); } catch (e) { console.warn(e); }
  }, [connection, dataScope, exportEnabled]);

  // ── MERGED DOC ACCUMULATOR ───────────────────────────────────
  // docsVersion is a counter that increments whenever the accumulator
  // gains new data. This gives useMemo a stable dependency to react to,
  // since mutating a ref doesn't trigger re-renders on its own.
  const [docsVersion, setDocsVersion] = useState(0);
  const mergedDocsAccRef    = useRef({});
  const mergedStudentKeyRef = useRef(null);
  const seededRef           = useRef(false);

  if (mergedStudentKeyRef.current !== studentKey) {
    mergedStudentKeyRef.current = studentKey;
    mergedDocsAccRef.current    = {};
    seededRef.current           = false;
  }

  // Seed once from the parent's already-loaded data.
  // Uses useEffect so the state increment happens after render,
  // which triggers one re-render with the seeded data in place.
  useEffect(() => {
    if (seededRef.current) return;
    if (!initialDocsObj || Object.keys(initialDocsObj).length === 0) return;
    seededRef.current = true;
    for (const [dId, doc] of Object.entries(initialDocsObj)) {
      const existing = mergedDocsAccRef.current[dId] || {};
      const merged   = { ...existing };
      for (const [k, v] of Object.entries(doc)) {
        if (v !== null && v !== undefined) merged[k] = v;
      }
      mergedDocsAccRef.current[dId] = merged;
    }
    setDocsVersion((v) => v + 1);
  }, [initialDocsObj]);

  // Merge each incoming WS tick on top (NLP annotations etc.)
  // Also bump docsVersion so downstream memos recompute.
  useEffect(() => {
    const rawDocs = loData?.students?.[studentKey]?.documents || {};
    if (Object.keys(rawDocs).length === 0) return;
    let changed = false;
    for (const [dId, incoming] of Object.entries(rawDocs)) {
      const existing = mergedDocsAccRef.current[dId] || {};
      const merged   = { ...existing };
      for (const [k, v] of Object.entries(incoming)) {
        if (v !== null && v !== undefined) merged[k] = v;
      }
      mergedDocsAccRef.current[dId] = merged;
      changed = true;
    }
    if (changed) setDocsVersion((v) => v + 1);
  }, [loData, studentKey]);

  // Stable snapshot for this render — docsVersion ensures memos
  // below recompute whenever the accumulator is updated.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const docsObj = useMemo(() => ({ ...mergedDocsAccRef.current }), [docsVersion]);

  const hasError = useMemo(() => {
    if (!exportEnabled || !loErrors) return false;
    if (Array.isArray(loErrors)) return loErrors.length > 0;
    if (typeof loErrors === "object") return Object.keys(loErrors).length > 0;
    return true;
  }, [exportEnabled, loErrors]);

  // hasAllDocs: true as soon as every doc has text — satisfied immediately
  // if initialDocsObj was provided (the normal case when opened from the card grid).
  const hasAllDocs = useMemo(() => {
    if (!exportEnabled) return false;
    return docIds.every((id) => {
      const d = docsObj?.[id];
      return d && typeof d.text === "string" && d.text.length > 0;
    });
  }, [exportEnabled, docIds, docsObj]);

  const isLoading = useMemo(() => exportEnabled && !hasError && !hasAllDocs, [exportEnabled, hasError, hasAllDocs]);

  const currentIdx = useMemo(() => {
    const i = docIds.findIndex((id) => String(id) === String(docId));
    return Math.max(0, i);
  }, [docIds, docId]);

  const hasPrior = currentIdx > 0;

  // metricSummaries uses metricValue() which prefers doc[key].metric
  // (the pre-computed number from the NLP pipeline — confirmed present
  // in the WS response JSON: "metric": 19, 11, 20, etc.)
  const metricSummaries = useMemo(() => {
    if (!exportEnabled || !hasAllDocs) return [];
    return selectedMetrics.map((key) => {
      const series   = docIds.map((id) => metricValue(docsObj?.[id], key));
      const current  = Number(series[currentIdx] ?? 0);
      const prior    = series.slice(0, currentIdx).map((x) => Number(x) || 0);
      const baseline = prior.length ? mean(prior) : 0;
      return { key, baseline, currentValue: current };
    });
  }, [exportEnabled, hasAllDocs, selectedMetrics, docIds, docsObj, currentIdx]);

  const currentDoc     = useMemo(() => docsObj?.[docId] || null, [docsObj, docId]);
  const currentText    = useMemo(() => (currentDoc?.text || "").toString(), [currentDoc]);
  const assignmentType = useMemo(() => inferAssignmentType(currentText), [currentText]);
  const wordCount      = useMemo(() => {
    const t = (currentText || "").trim();
    return t ? t.split(/\s+/).filter(Boolean).length : 0;
  }, [currentText]);

  const pasteStats     = useMemo(() => extractPasteStats(currentDoc), [currentDoc]);
  const currentProcess = useMemo(() => deriveProcessMetrics(currentDoc), [currentDoc]);
  const baselineProcess = useMemo(() => {
    const priors = docIds.slice(0, currentIdx).map((id) => docsObj?.[id]).filter(Boolean);
    if (!priors.length) return null;
    const out = {};
    for (const def of PROCESS_DEFS) {
      const vals = priors.map((d) => deriveProcessMetrics(d)?.[def.key])
        .filter((v) => v != null && Number.isFinite(Number(v)));
      out[def.key] = vals.length ? mean(vals.map(Number)) : null;
    }
    return out;
  }, [docIds, currentIdx, docsObj]);

  return (
    <div className="h-full flex min-h-0 bg-gray-50">

      {/* ── Left sidebar: Metrics panel ── */}
      <aside className="w-72 shrink-0 border-r border-gray-200 bg-white flex flex-col min-h-0 overflow-auto">
        <div className="px-4 pt-4 pb-2 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Gauge className="h-4 w-4 text-emerald-600" />
            <span className="text-sm font-semibold text-gray-900">Writing Trajectory</span>
          </div>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
            Select signals to compare this essay against the student's prior baseline.
          </p>
        </div>
        <div className="flex-1 overflow-auto">
          <MetricsPanel
            metrics={selectedMetrics}
            setMetrics={setSelectedMetrics}
            groupBy="trait"
            title="Metrics"
            useSticky={false}
            stickyTopClassName="top-0"
            className="col-span-12"
            panelClassName="rounded-none border-0 shadow-none"
          />
        </div>
      </aside>

      {/* ── Middle: essay text ── */}
      <section className="flex-1 min-w-0 min-h-0 flex flex-col border-r border-gray-200 bg-white">
        <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 shrink-0">
          <div className="flex items-center gap-2 flex-wrap">
            <TypeBadge type={assignmentType} />
            <span className="text-xs font-medium text-gray-500 bg-white border border-gray-200 rounded-full px-2 py-0.5">
              {wordCount.toLocaleString()} words
            </span>
            <EffortPills doc={currentDoc} />
          </div>
        </div>
        <div className="flex-1 overflow-auto px-6 py-5">
          {currentText
            ? <p className="text-sm leading-7 text-gray-800 whitespace-pre-line">{currentText}</p>
            : <p className="text-sm text-gray-400 italic">No text available yet.</p>
          }
        </div>
      </section>

      {/* ── Right panel: trajectory results ── */}
      <aside className="w-[500px] shrink-0 flex flex-col min-h-0 overflow-auto bg-gray-50">
        <div className="p-5 space-y-4">

          {hasPrior && (
            <BaselineInfo docIds={docIds} currentIdx={currentIdx} docsObj={docsObj} />
          )}

          <PasteCard pasteStats={pasteStats} />

          <div>
            <div className="flex items-center gap-2 mb-2 px-1">
              <span className="text-xs font-semibold text-gray-700">Product Metrics</span>
              <span className="text-[10px] text-gray-400">{metricSummaries.length} selected</span>
            </div>

            {selectedMetrics.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center">
                <p className="text-sm font-medium text-gray-600">No metrics selected</p>
                <p className="text-xs text-gray-400 mt-1">Choose signals in the sidebar to view trajectory.</p>
              </div>
            ) : isLoading ? (
              <div className="rounded-2xl border border-gray-200 bg-white px-5 py-6 flex items-center gap-3">
                <Loader2 className="h-4 w-4 animate-spin text-emerald-500" />
                <span className="text-sm text-gray-600">Computing trajectory...</span>
              </div>
            ) : hasError ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0" />
                <span className="text-sm text-rose-700">Could not load metric data.</span>
              </div>
            ) : !hasPrior ? (
              <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center">
                <p className="text-sm font-medium text-gray-600">No prior essays</p>
                <p className="text-xs text-gray-400 mt-1">This is the student's first essay. No baseline yet.</p>
              </div>
            ) : metricSummaries.length > 0 ? (
              <MetricSummaryPanel metricSummaries={metricSummaries} assignmentType={assignmentType} />
            ) : null}
          </div>
        </div>
      </aside>

    </div>
  );
}
