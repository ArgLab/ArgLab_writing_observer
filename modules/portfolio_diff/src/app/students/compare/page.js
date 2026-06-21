"use client";

import { navigateTo } from "@/app/utils/navigation";
import {
  ArrowLeftRight, Check, ChevronDown, Clock, Eye, FileText, Focus, Info,
  ListCollapse, Minus, RefreshCw, Search, TrendingDown, TrendingUp,
  Users, X, AlertCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLOConnectionDataManager, LOConnectionLastUpdated } from "lo_event/lo_event/lo_assess/components/components.jsx";
import { MetricsPanel, METRIC_BY_ID, METRIC_TEACHER_DESC } from "@/app/components/MetricsPanel";
import { useCourseIdContext } from "@/app/providers/CourseIdProvider";
import { getConfiguredWsOrigin } from "@/app/utils/ws";

/* ── deterministic seed ── */
const seedFrom = (s) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = ((h ^ s.charCodeAt(i)) * 16777619) >>> 0;
  return h >>> 0;
};

/* ── highlight helpers ── */
const HIGHLIGHT_CLASSES = [
  "bg-emerald-200/70","bg-sky-200/70","bg-amber-200/70","bg-rose-200/70",
  "bg-indigo-200/70","bg-lime-200/70","bg-violet-200/60","bg-teal-200/70",
  "bg-fuchsia-200/60","bg-orange-200/70",
];
const highlightClassForMetric = (id) => HIGHLIGHT_CLASSES[seedFrom(id || "metric") % HIGHLIGHT_CLASSES.length];

function buildSpansFromDoc(doc, metricIds) {
  const text = (doc?.text || "").toString();
  const spans = [];
  for (const metricId of metricIds || []) {
    const offsets = doc?.[metricId]?.offsets;
    if (!Array.isArray(offsets)) continue;
    for (const pair of offsets) {
      if (!Array.isArray(pair) || pair.length < 2) continue;
      const start = Number(pair[0]), len = Number(pair[1]);
      if (!Number.isFinite(start) || !Number.isFinite(len) || len <= 0) continue;
      const s = Math.max(0, Math.min(text.length, start));
      const e = Math.max(0, Math.min(text.length, start + len));
      if (e > s) spans.push({ start: s, end: e, metricId });
    }
  }
  spans.sort((a, b) => a.start - b.start || b.end - b.start - (a.end - a.start));
  return { text, spans };
}

function segmentTextBySpans(text, spans) {
  const cuts = new Set([0, text.length]);
  for (const s of spans) { cuts.add(s.start); cuts.add(s.end); }
  const points = Array.from(cuts).sort((a, b) => a - b);
  const segs = [];
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i], b = points[i + 1];
    if (b <= a) continue;
    const active = spans.filter((sp) => sp.start <= a && sp.end >= b).map((sp) => sp.metricId);
    segs.push({ start: a, end: b, text: text.slice(a, b), active });
  }
  return segs;
}

/* ══════════════════════════════════════════════════════════════
   6+1 TRAIT RUBRIC MAPPING
   ══════════════════════════════════════════════════════════════ */
/* ══ coverage ══ */
function metricCoveragePercent(doc, metricId) {
  const text = (doc?.text || "").toString(); const L = text.length; if (!L) return 0;
  const offsets = doc?.[metricId]?.offsets;
  if (!Array.isArray(offsets) || !offsets.length) return 0;
  const ranges = [];
  for (const pair of offsets) {
    if (!Array.isArray(pair) || pair.length < 2) continue;
    const s0 = Number(pair[0]), len = Number(pair[1]);
    if (!Number.isFinite(s0) || !Number.isFinite(len) || len <= 0) continue;
    const s = Math.max(0, Math.min(L, s0)), e = Math.max(0, Math.min(L, s0 + len));
    if (e > s) ranges.push([s, e]);
  }
  if (!ranges.length) return 0;
  ranges.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  let covered = 0; let [cs, ce] = ranges[0];
  for (let i = 1; i < ranges.length; i++) {
    const [s, e] = ranges[i];
    if (s <= ce) ce = Math.max(ce, e); else { covered += ce - cs; cs = s; ce = e; }
  }
  return ((covered + ce - cs) / L) * 100;
}

function buildHighlightTooltip(doc, metricIds) {
  const uniq = Array.from(new Set(metricIds || []));
  if (!uniq.length) return "";
  return uniq.map((id) => {
    const label = METRIC_BY_ID[id]?.title || id;
    const desc = METRIC_TEACHER_DESC[id] || "";
    const cov = `${metricCoveragePercent(doc, id).toFixed(1)}% of this essay`;
    return desc ? `${label}: ${cov}\n${desc}` : `${label}: ${cov}`;
  }).join("\n\n");
}

/* ══ assignment type ══ */
const ASSIGNMENT_TYPE_COLORS = {
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

function AssignmentTypeBadge({ type }) {
  const c = ASSIGNMENT_TYPE_COLORS[type] || ASSIGNMENT_TYPE_COLORS.Document;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ring-1 ring-inset ${c.bg} ${c.text} ${c.ring}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${c.dot}`} />{type}
    </span>
  );
}

// Produce a readable title from a raw doc ID.
// Real metadata title is always preferred over this fallback.
function humanizeDocId(docId) {
  if (!docId) return "Document";
  return String(docId)
    .replace(/^fake-google-doc-id-?/i, "Doc ")
    .replace(/^doc-id-?/i, "Doc ")
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .trim() || docId;
}

/* ══ floating tooltip ══ */
function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }
function FloatingTooltip({ tooltip }) {
  if (!tooltip?.visible) return null;
  return (
    <div className="fixed z-[9999] pointer-events-none" style={{ left: tooltip.x, top: tooltip.y, maxWidth: 420 }}>
      <div className="bg-gray-900 text-white text-xs rounded-lg shadow-lg px-3 py-2 whitespace-pre-line leading-relaxed">{tooltip.content}</div>
    </div>
  );
}

// Stable essay component — only rebuilds spans when text content or active metrics actually change,
// not on every WebSocket data object re-reference, preventing visible flicker on server refresh.
function HighlightedEssay({ doc, activeMetricIds, containerRef, onShowTooltip, onMoveTooltip, onHideTooltip }) {
  const textContent = doc?.text || "";
  const { text, spans } = useMemo(
    () => buildSpansFromDoc(doc, activeMetricIds),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [textContent, activeMetricIds.join(",")]
  );
  const segments = useMemo(() => segmentTextBySpans(text, spans), [text, spans]);
  if (!text.trim()) return <div className="text-gray-600 text-sm leading-relaxed">(No text returned for this document.)</div>;
  return (
    <div ref={containerRef} className="text-gray-800 text-[15px] leading-7 whitespace-pre-line">
      {segments.map((seg, idx) => {
        if (!seg.active.length) return <span key={idx}>{seg.text}</span>;
        const cls = highlightClassForMetric(seg.active[0]);
        const tooltipText = buildHighlightTooltip(doc, seg.active);
        return (
          <mark key={idx} className={`${cls} rounded px-0.5 cursor-help`}
            data-primary-metric={seg.active[0]} data-metrics={seg.active.join(",")}
            onMouseEnter={(e) => onShowTooltip(tooltipText, e)}
            onMouseMove={(e) => onMoveTooltip(e)}
            onMouseLeave={() => onHideTooltip()}
          >{seg.text}</mark>
        );
      })}
    </div>
  );
}

/* ══ URL helpers ══ */
function readCompareParamsFromLocation() {
  if (typeof window === "undefined") return { urlReady: false, studentID: "", docIds: [] };
  const sp = new URLSearchParams(window.location.search);
  const studentID = (sp.get("student_id") || "").trim();
  const parts = (sp.get("ids") || "").trim().split(",").map((s) => s.trim()).filter(Boolean);
  const seen = new Set(); const docIds = [];
  for (const p of parts) { if (!seen.has(p)) { seen.add(p); docIds.push(p); } if (docIds.length === 2) break; }
  return { urlReady: true, studentID, docIds };
}

function buildEssayFromDoc({ docId, text, side, title }) {
  const content = (text || "").trim();
  const words = content ? content.split(/\s+/).filter(Boolean).length : 0;
  const humanTitle = title && !(/fake-google-doc|doc-id/i.test(title)) ? title : humanizeDocId(docId);
  return {
    id: docId || `${side}-unknown`, title: humanTitle || `Essay (${side})`,
    date: "", minutes: Math.max(10, Math.round(words / 30)), words,
    content: content || "(No text returned for this document.)",
    assignmentType: inferAssignmentType(content),
  };
}

/* ══ format helpers ══ */
function formatPct(n) { const x = Number.isFinite(Number(n)) ? Number(n) : 0; return `${x.toFixed(1)}%`; }
function formatDelta(n) {
  const x = Number.isFinite(Number(n)) ? Number(n) : 0;
  return `${x > 0 ? "+" : x < 0 ? "-" : "+-"}${Math.abs(x).toFixed(1)}%`;
}

function extractMetricExamples(doc, metricId, maxExamples = 2) {
  const text = (doc?.text || "").toString(); if (!text.trim()) return [];
  const offsets = doc?.[metricId]?.offsets; if (!Array.isArray(offsets) || !offsets.length) return [];
  const L = text.length; const spans = [];
  for (const pair of offsets) {
    if (!Array.isArray(pair) || pair.length < 2) continue;
    const s0 = Number(pair[0]), len = Number(pair[1]);
    if (!Number.isFinite(s0) || !Number.isFinite(len) || len <= 0) continue;
    spans.push([Math.max(0, Math.min(L, s0)), Math.max(0, Math.min(L, s0 + len))]);
  }
  spans.sort((a, b) => a[0] - b[0]);
  const seen = new Set(); const out = [];
  for (const [s, e] of spans) {
    if (out.length >= maxExamples) break;
    const pad = 70, a = Math.max(0, s - pad), b = Math.min(L, e + pad);
    let snippet = text.slice(a, b).replace(/\s+/g, " ").trim();
    if (a > 0) snippet = `...${snippet}`; if (b < L) snippet = `${snippet}...`;
    const key = snippet.toLowerCase(); if (seen.has(key)) continue; seen.add(key); out.push(snippet);
  }
  return out;
}

/* ══ UI components ══ */
function MetricDeltaIcon({ delta }) {
  const d = Number(delta) || 0;
  if (d > 0.0001) return <TrendingUp className="h-4 w-4 text-emerald-700" />;
  if (d < -0.0001) return <TrendingDown className="h-4 w-4 text-rose-700" />;
  return <Minus className="h-4 w-4 text-gray-500" />;
}

function MetricDeltaPill({ delta }) {
  const d = Number(delta) || 0;
  const cls = d > 0.0001 ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200"
    : d < -0.0001 ? "bg-rose-50 text-rose-700 ring-1 ring-rose-200" : "bg-gray-100 text-gray-700";
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${cls}`}>{formatDelta(d)}</span>;
}

function StoryCard({ label, metricTitle, category, left, right, delta, tone, isDisabled }) {
  const toneCls = tone === "up" ? "border-emerald-200 bg-emerald-50/40"
    : tone === "down" ? "border-rose-200 bg-rose-50/40" : "border-gray-200 bg-gray-50";
  if (isDisabled) return (
    <div className="rounded-2xl border p-4 border-gray-200 bg-gray-50">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-3 text-sm text-gray-400 italic">No significant change detected</div>
    </div>
  );
  return (
    <div className={`rounded-2xl border p-4 ${toneCls}`}>
      <div className="text-xs text-gray-600">{label}</div>
      <div className="mt-1 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-semibold truncate text-gray-900">{metricTitle || "—"}</div>
          <div className="mt-0.5 text-xs text-gray-500 truncate">{category || ""}</div>
        </div>
        <MetricDeltaPill delta={delta} />
      </div>
      <div className="mt-3 flex items-center justify-between text-sm text-gray-700">
        <span className="font-medium text-gray-900">{formatPct(left)}</span>
        <span className="text-gray-400">to</span>
        <span className="font-medium text-gray-900">{formatPct(right)}</span>
      </div>
    </div>
  );
}

function MetricRow({ row, isFocused, onFocusToggle, onShow }) {
  const { def, left, right, delta } = row;
  const teacherDesc = METRIC_TEACHER_DESC[def.id] || def.desc || "";
  return (
    <div className={`rounded-xl border p-3 transition ${isFocused ? "border-emerald-300 bg-emerald-50/40" : "border-gray-100 hover:bg-gray-50/40"}`}>
      <div className="flex items-center gap-3">
        <span className={`inline-block h-3 w-3 rounded flex-shrink-0 ${highlightClassForMetric(def.id)}`} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 min-w-0">
            <div className="text-sm font-semibold text-gray-900 truncate">{def.title}</div>
            <span className="text-xs text-gray-500 truncate hidden sm:inline">&middot; {def.category}</span>
          </div>
          <div className="mt-0.5 text-xs text-gray-500 line-clamp-1">{teacherDesc}</div>
        </div>
        <div className="ml-auto flex items-center gap-3 flex-shrink-0">
          <div className="hidden sm:flex items-center gap-2 text-sm text-gray-700">
            <span className="font-medium text-gray-900">{formatPct(left)}</span>
            <span className="text-gray-400">to</span>
            <span className="font-medium text-gray-900">{formatPct(right)}</span>
          </div>
          <div className="flex items-center gap-2"><MetricDeltaIcon delta={delta} /><MetricDeltaPill delta={delta} /></div>
          <button onClick={onFocusToggle}
            className={`inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm border transition ${isFocused ? "bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700" : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"}`}>
            <Focus className="h-4 w-4" />{isFocused ? "Focused" : "Focus"}
          </button>
          <button onClick={onShow}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-xl text-sm border border-gray-200 bg-white hover:bg-gray-50 text-gray-700">
            <Eye className="h-4 w-4" /> Show
          </button>
        </div>
      </div>
    </div>
  );
}

function ComparisonTypeMismatchBanner({ typeA, typeB }) {
  if (!typeA || !typeB || typeA === typeB || typeA === "Document" || typeB === "Document") return null;
  return (
    <div className="flex items-start gap-2 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 mb-4 text-sm text-amber-800">
      <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
      <div>
        <span className="font-semibold">Different assignment types selected.</span>{" "}
        Comparing a <strong>{typeA}</strong> essay with a <strong>{typeB}</strong> essay.
        Language-level signals (word choice, transitions) are still useful across types.
        Structural signals (sentence types, paragraphs) are most meaningful within the same type.
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ══════════════════════════════════════════════════════════════ */
export default function EssayComparison() {
  const initial = useMemo(() => readCompareParamsFromLocation(), []);
  const [urlReady, setUrlReady] = useState(initial.urlReady);
  const [studentID, setStudentID] = useState(initial.studentID);
  const [docIds, setDocIds] = useState(initial.docIds);
  const { courseId } = useCourseIdContext();

  useEffect(() => {
    const next = readCompareParamsFromLocation(); if (!next.urlReady) return;
    if (next.studentID !== studentID) setStudentID(next.studentID);
    if (!(next.docIds.length === docIds.length && next.docIds[0] === docIds[0] && next.docIds[1] === docIds[1])) setDocIds(next.docIds);
    if (!urlReady) setUrlReady(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const leftDocId = docIds[0] || "", rightDocId = docIds[1] || "";
  const hasCourseId = courseId !== undefined && courseId !== null && String(courseId).trim().length > 0;
  const enabled = urlReady && hasCourseId && !!studentID && docIds.length === 2;
  const missingParams = urlReady && (!studentID || docIds.length !== 2);

  const [selectedMetrics, setSelectedMetrics] = useState([
    "academic_language","informal_language","latinate_words","transition_words","citations","sentences","paragraphs",
  ]);

  const origin = getConfiguredWsOrigin();
  const dataScope = useMemo(() => {
    if (!urlReady || !studentID || !hasCourseId) return { wo: { execution_dag: "writing_observer", target_exports: [], kwargs: {} } };
    const te = ["student_with_docs","single_student_profile"];
    if (docIds.length === 2 && docIds[0] && docIds[1]) te.push("single_student_docs_with_nlp_annotations");
    return { wo: { execution_dag: "writing_observer", target_exports: te, kwargs: {
      course_id: courseId, student_id: studentID,
      ...(docIds.length === 2 && docIds[0] && docIds[1] ? { document: docIds, nlp_options: selectedMetrics } : {}),
    }}};
  }, [urlReady, studentID, hasCourseId, courseId, docIds, selectedMetrics]);

  const { data: loData, errors: loErrors, connection: loConnection } = useLOConnectionDataManager({
    url: `${origin}/wsapi/communication_protocol`, dataScope,
  });

  const availableDocIds = useMemo(() => {
    const ids = Object.keys(loData?.students?.[studentID]?.documents || {}); ids.sort(); return ids;
  }, [loData, studentID]);

  useEffect(() => {
    if (loConnection?.sendMessage && dataScope?.wo?.target_exports?.length > 0) {
      try { loConnection.sendMessage(JSON.stringify(dataScope)); } catch (e) { console.warn(e); }
    }
  }, [dataScope, loConnection]);

  const docTitle = useCallback((docId) => {
    if (!docId) return "—";
    const raw = loData?.students?.[studentID]?.documents?.[docId]?.title || "";
    if (raw && !(/fake-google-doc|doc-id/i.test(raw))) return raw;
    return humanizeDocId(docId);
  }, [loData, studentID]);

  const studentDisplayName = loData?.students?.[studentID]?.profile?.name?.full_name || studentID || "—";
  const docsObj = loData?.students?.[studentID]?.documents || {};
  const leftDoc = leftDocId ? docsObj?.[leftDocId] : null;
  const rightDoc = rightDocId ? docsObj?.[rightDocId] : null;

  const leftHasText = !!(leftDoc && "text" in leftDoc);
  const rightHasText = !!(rightDoc && "text" in rightDoc);
  const leftTextNonEmpty = leftHasText && typeof leftDoc.text === "string" && leftDoc.text.trim().length > 0;
  const rightTextNonEmpty = rightHasText && typeof rightDoc.text === "string" && rightDoc.text.trim().length > 0;
  const isDocsLoading = enabled && !(leftTextNonEmpty && rightTextNonEmpty);
  const leftDocLoading = enabled && !leftTextNonEmpty;
  const rightDocLoading = enabled && !rightTextNonEmpty;

  const hasPendingMetricData = useMemo(() => {
    if (!enabled || !leftTextNonEmpty || !rightTextNonEmpty) return false;
    return selectedMetrics.some((id) => !leftDoc?.[id] || !rightDoc?.[id]);
  }, [enabled, leftTextNonEmpty, rightTextNonEmpty, selectedMetrics, leftDoc, rightDoc]);

  const showLoadingIndicator = isDocsLoading || hasPendingMetricData;

  const [leftEssay, setLeftEssay] = useState(() => buildEssayFromDoc({ docId: leftDocId, text: "", side: "left" }));
  const [rightEssay, setRightEssay] = useState(() => buildEssayFromDoc({ docId: rightDocId, text: "", side: "right" }));

  useEffect(() => {
    setLeftEssay(buildEssayFromDoc({ docId: leftDocId, text: "", side: "left", title: docTitle(leftDocId) }));
    setRightEssay(buildEssayFromDoc({ docId: rightDocId, text: "", side: "right", title: docTitle(rightDocId) }));
  }, [leftDocId, rightDocId, docTitle]);

  useEffect(() => {
    if (!enabled) return;
    if (leftHasText) setLeftEssay(buildEssayFromDoc({ docId: leftDocId, text: leftDoc?.text || "", side: "left", title: docTitle(leftDocId) }));
    if (rightHasText) setRightEssay(buildEssayFromDoc({ docId: rightDocId, text: rightDoc?.text || "", side: "right", title: docTitle(rightDocId) }));
  }, [enabled, leftHasText, rightHasText, leftDocId, rightDocId, leftDoc, rightDoc, docTitle]);

  /* tooltip */
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, content: "" });
  const positionFromMouse = useCallback((e) => ({
    x: clamp(e.clientX + 12, 8, (typeof window !== "undefined" ? window.innerWidth : 1200) - 420),
    y: clamp(e.clientY + 12, 8, (typeof window !== "undefined" ? window.innerHeight : 800) - 220),
  }), []);
  const onShowTooltip = useCallback((content, e) => {
    if (!content) return; const { x, y } = positionFromMouse(e); setTooltip({ visible: true, x, y, content });
  }, [positionFromMouse]);
  const onMoveTooltip = useCallback((e) => {
    setTooltip((t) => { if (!t.visible) return t; const { x, y } = positionFromMouse(e); return { ...t, x, y }; });
  }, [positionFromMouse]);
  const onHideTooltip = useCallback(() => setTooltip((t) => ({ ...t, visible: false })), []);

  /* URL update */
  const updateUrlIds = useCallback((next) => {
    if (typeof window === "undefined") return;
    const sp = new URLSearchParams(window.location.search);
    sp.set("student_id", studentID || ""); sp.set("ids", next.join(","));
    window.history.replaceState({}, "", `${window.location.pathname}?${sp.toString()}`);
  }, [studentID]);

  const setDocIdForSide = useCallback((side, newId) => {
    const id = (newId || "").trim(); if (!id) return;
    setDocIds((prev) => {
      const n = [...prev]; const L = n[0] || "", R = n[1] || "";
      if (side === "left") { n[0] = id === R ? R : id; n[1] = id === R ? L : R; }
      else { n[0] = id === L ? R : L; n[1] = id === L ? L : id; }
      if (!n[0]) n[0] = L; if (!n[1]) n[1] = R;
      updateUrlIds(n); return n;
    });
  }, [updateUrlIds]);

  const swapDocSides = useCallback(() => {
    setDocIds((prev) => { if (!Array.isArray(prev) || prev.length < 2) return prev; const n = [prev[1]||"", prev[0]||""]; updateUrlIds(n); return n; });
  }, [updateUrlIds]);

  /* modals */
  const [replaceModal, setReplaceModal] = useState({ open: false, side: "left" });
  const [replaceQuery, setReplaceQuery] = useState("");
  const [replaceActiveIdx, setReplaceActiveIdx] = useState(0);
  const [metricsModalOpen, setMetricsModalOpen] = useState(false);

  const openReplace = (side) => { setReplaceQuery(""); setReplaceActiveIdx(0); setReplaceModal({ open: true, side }); };
  const closeReplace = () => { setReplaceModal({ open: false, side: "left" }); setReplaceQuery(""); setReplaceActiveIdx(0); };

  useEffect(() => {
    if (typeof document === "undefined") return;
    document.body.style.overflow = replaceModal.open || metricsModalOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [replaceModal.open, metricsModalOpen]);

  const currentIdForSide = replaceModal.side === "left" ? leftDocId : rightDocId;
  const otherIdForSide   = replaceModal.side === "left" ? rightDocId : leftDocId;

  const replaceMatches = useMemo(() => {
    const q = replaceQuery.trim().toLowerCase();
    return (availableDocIds || []).filter((id) => !q || docTitle(id).toLowerCase().includes(q) || id.toLowerCase().includes(q));
  }, [replaceQuery, availableDocIds, docTitle]);

  const replacePick = (id) => { setDocIdForSide(replaceModal.side, id); closeReplace(); };

  const onReplaceKeyDown = (e) => {
    if (!replaceModal.open) return;
    if (e.key === "Escape") { e.preventDefault(); closeReplace(); return; }
    if (e.key === "ArrowDown") { e.preventDefault(); setReplaceActiveIdx((i) => Math.min(replaceMatches.length - 1, i + 1)); return; }
    if (e.key === "ArrowUp") { e.preventDefault(); setReplaceActiveIdx((i) => Math.max(0, i - 1)); return; }
    if (e.key === "Enter") { e.preventDefault(); const id = replaceMatches[replaceActiveIdx]; if (id) replacePick(id); }
  };

  useEffect(() => { if (replaceModal.open) setReplaceActiveIdx(0); }, [replaceModal.open, replaceQuery]);

  /* metrics comparison */
  const [focusedMetricId, setFocusedMetricId] = useState(null);
  const [showAllMetrics, setShowAllMetrics] = useState(false);

  useEffect(() => { if (focusedMetricId && !selectedMetrics.includes(focusedMetricId)) setFocusedMetricId(null); }, [focusedMetricId, selectedMetrics]);

  const activeMetricIds = focusedMetricId ? [focusedMetricId] : selectedMetrics;

  const coverageRows = useMemo(() => {
    if (!selectedMetrics.length) return [];
    return selectedMetrics.map((id) => METRIC_BY_ID[id]).filter(Boolean).map((def) => {
      const a = metricCoveragePercent(leftDoc, def.id), b = metricCoveragePercent(rightDoc, def.id);
      const delta = (Number(b) || 0) - (Number(a) || 0);
      return { def, left: Number(a)||0, right: Number(b)||0, delta, absDelta: Math.abs(delta) };
    }).sort((x, y) => y.absDelta - x.absDelta || String(x.def.title).localeCompare(String(y.def.title)));
  }, [selectedMetrics, leftDoc, rightDoc]);

  const metricsSummary = useMemo(() => {
    if (!coverageRows.length) return { mostIncreased: null, mostDecreased: null, mostStable: null };
    const byDesc = [...coverageRows].sort((a, b) => b.delta - a.delta);
    const byStable = [...coverageRows].sort((a, b) => a.absDelta - b.absDelta);
    const negs = coverageRows.filter((r) => r.delta < -0.0001).sort((a, b) => a.delta - b.delta);
    return { mostIncreased: byDesc[0]||null, mostDecreased: negs[0]||null, mostStable: byStable[0]||null };
  }, [coverageRows]);

  const topChanges = useMemo(() => coverageRows.slice(0, 8), [coverageRows]);
  const allRemaining = useMemo(() => coverageRows.length > 8 ? coverageRows.slice(8) : [], [coverageRows]);

  const leftEssayRef = useRef(null), rightEssayRef = useRef(null);

  const scrollToFirstHighlight = useCallback((metricId) => {
    if (!metricId) return;
    const sel = `mark[data-metrics*="${metricId}"], mark[data-primary-metric="${metricId}"]`;
    const target = leftEssayRef.current?.querySelector(sel) || rightEssayRef.current?.querySelector(sel);
    if (target) target.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
  }, []);

  const focusMetric = useCallback((metricId, shouldScroll = false) => {
    if (!metricId) return;
    setFocusedMetricId((cur) => (cur === metricId ? null : metricId));
    if (shouldScroll) setTimeout(() => scrollToFirstHighlight(metricId), 30);
  }, [scrollToFirstHighlight]);

  const focusedMeta = focusedMetricId ? METRIC_BY_ID[focusedMetricId] : null;

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <FloatingTooltip tooltip={tooltip} />

      {/* Mobile metrics modal */}
      {metricsModalOpen && (
        <div className="fixed inset-0 z-[9997] lg:hidden">
          <div className="absolute inset-0 bg-black/30" onClick={() => setMetricsModalOpen(false)} />
          <div className="absolute inset-0 flex items-end justify-center p-3">
            <div className="w-full max-w-xl rounded-2xl bg-white shadow-2xl border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <div className="text-sm font-semibold text-gray-900">Metrics</div>
                <button onClick={() => setMetricsModalOpen(false)} className="p-2 rounded-lg hover:bg-gray-50"><X className="h-5 w-5 text-gray-500" /></button>
              </div>
              <div className="p-3 max-h-[80vh] overflow-y-auto">
                <MetricsPanel metrics={selectedMetrics} setMetrics={setSelectedMetrics} groupBy="trait" title="Metrics" useSticky={false} stickyTopClassName="top-0" className="col-span-12" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Replace modal */}
      {replaceModal.open && (
        <div className="fixed inset-0 z-[9998]" onKeyDown={onReplaceKeyDown} tabIndex={-1}>
          <div className="absolute inset-0 bg-black/30" onClick={closeReplace} />
          <div className="absolute inset-0 flex items-start justify-center p-4 pt-16">
            <div className="w-full max-w-2xl rounded-2xl bg-white shadow-2xl border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <div>
                  <div className="text-sm font-semibold text-gray-900">Replace {replaceModal.side === "left" ? "left" : "right"} essay</div>
                  <div className="mt-1 text-xs text-gray-500">
                    {studentDisplayName} &middot; {availableDocIds.length} essays available
                  </div>
                </div>
                <button onClick={closeReplace} className="p-2 rounded-lg hover:bg-gray-50"><X className="h-5 w-5 text-gray-500" /></button>
              </div>
              <div className="p-4 border-b border-gray-100">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input value={replaceQuery} onChange={(e) => setReplaceQuery(e.target.value)} autoFocus
                    placeholder="Search essays..." className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-500" />
                </div>
                <div className="mt-2 text-xs text-gray-500">Use arrow keys then Enter to select.</div>
              </div>
              <div className="max-h-[55vh] overflow-auto">
                {replaceMatches.length === 0 ? (
                  <div className="p-4 text-sm text-gray-600">No matching essays.</div>
                ) : replaceMatches.map((id, idx) => {
                  const isCurrent = id === currentIdForSide, isOther = id === otherIdForSide;
                  const rawText = (loData?.students?.[studentID]?.documents?.[id]?.text || "").replace(/\s+/g, " ").trim();
                  const preview = rawText.slice(0, 120);
                  return (
                    <button key={id} onClick={() => replacePick(id)} onMouseEnter={() => setReplaceActiveIdx(idx)}
                      className={`w-full text-left px-4 py-3 flex items-start gap-3 border-b border-gray-50 last:border-0 ${idx === replaceActiveIdx ? "bg-emerald-50" : "hover:bg-gray-50"}`}>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-gray-900 truncate">{docTitle(id)}</span>
                          <div className="flex items-center gap-1.5 ml-auto">
                            {isCurrent && <span className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700"><Check className="h-3 w-3" /> Current</span>}
                            {isOther && !isCurrent && <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 ring-1 ring-amber-200">Other side</span>}
                          </div>
                        </div>
                        {preview && (
                          <p className="mt-1 text-xs text-gray-400 line-clamp-2 leading-relaxed">
                            {preview}{rawText.length > 120 ? "..." : ""}
                          </p>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>
              <div className="p-4 border-t border-gray-100 flex items-center justify-end gap-2">
                <button onClick={closeReplace} className="px-4 py-2 rounded-xl border border-gray-200 hover:bg-gray-50 text-sm">Cancel</button>
                <button onClick={closeReplace} className="px-4 py-2 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 text-sm">Done</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Page */}
      <div className="px-6 pt-6">
        <nav className="text-sm text-gray-500 mb-4" aria-label="Breadcrumb">
          <ol className="inline-flex items-center gap-1 md:gap-2">
            <li className="cursor-pointer" onClick={() => navigateTo("students", {})}>
              <span className="inline-flex gap-2 items-center text-gray-500 hover:text-emerald-600"><Users className="h-4 w-4" /><span>Students</span></span>
            </li>
            <li className="text-gray-400">&#8250;</li>
            <li className="text-gray-700 font-medium cursor-pointer hover:text-emerald-600" onClick={() => navigateTo("students", { student_id: studentID })}>
              <span className="inline-flex items-center gap-2">
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-gray-100 text-gray-700 text-xs font-semibold">
                  {studentDisplayName.split(/\s+/).map((w) => w[0]).join("").toUpperCase().slice(0, 2)}
                </span>
                {studentDisplayName}
              </span>
            </li>
            <li className="text-gray-400">&#8250;</li>
            <li className="text-gray-900 font-semibold">Essay Comparison</li>
          </ol>
        </nav>
        {missingParams && (
          <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Missing URL params. Expected: <span className="font-mono">?student_id=...&ids=docA,docB</span>
          </div>
        )}
        {urlReady && (
          <div className="mb-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full
            bg-white border border-gray-200 shadow-sm text-xs text-gray-500">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse shrink-0" />
            <LOConnectionLastUpdated message={loData} connectionStatus={loConnection?.connectionStatus} showText />
          </div>
        )}
      </div>

      <div className="px-6 pb-6">
        {showLoadingIndicator && (
          <div className="mb-4 bg-white rounded-xl border border-emerald-200 shadow-sm px-4 py-3">
            <div className="flex items-center gap-2 text-sm text-emerald-800">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span className="font-medium">{isDocsLoading ? "Loading essays..." : "Refreshing metrics..."}</span>
            </div>
            <div className="mt-1 text-xs text-emerald-700/90">Keeping the current comparison visible while new data arrives.</div>
          </div>
        )}

        {/* Apples-to-apples mismatch banner */}
        <ComparisonTypeMismatchBanner typeA={leftEssay.assignmentType} typeB={rightEssay.assignmentType} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="hidden lg:block lg:col-span-3">
            <MetricsPanel metrics={selectedMetrics} setMetrics={setSelectedMetrics} groupBy="trait" title="Metrics" stickyTopClassName="top-24" />
          </div>

          <section className="lg:col-span-9">
            <div className="mb-4 flex items-center gap-2 flex-wrap">
              <button onClick={swapDocSides}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700">
                <ArrowLeftRight className="h-4 w-4" /> Swap documents
              </button>
              <button onClick={() => setMetricsModalOpen(true)}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700 lg:hidden">
                <ListCollapse className="h-4 w-4" /> Metrics
              </button>
            </div>

            {/* Essay panels */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                { essay: leftEssay, doc: leftDoc, side: "left", loading: leftDocLoading, displayIndex: 1, ref: leftEssayRef },
                { essay: rightEssay, doc: rightDoc, side: "right", loading: rightDocLoading, displayIndex: 2, ref: rightEssayRef },
              ].map(({ essay, doc, side, loading, displayIndex, ref }) => (
                <div key={side} className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
                  <div className="p-6 pb-4 border-b border-gray-100">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        {/* Humanized title — never raw doc ID */}
                        <h2 className="text-lg font-semibold text-gray-900 truncate">{essay.title}</h2>

                      </div>
                      <button onClick={() => openReplace(side)}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700 shrink-0">
                        <RefreshCw className="h-4 w-4" /> Replace
                      </button>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-gray-600">
                      <AssignmentTypeBadge type={essay.assignmentType} />
                      <span className="inline-flex items-center gap-1"><Clock className="h-4 w-4" /> {essay.minutes} min</span>
                      <span className="inline-flex items-center gap-1"><FileText className="h-4 w-4" /> {essay.words.toLocaleString()} words</span>
                    </div>
                    {focusedMetricId && (
                      <div className="mt-3 flex items-center gap-2 text-xs">
                        <span className="inline-flex items-center gap-2 px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">
                          <Focus className="h-3.5 w-3.5" /> Showing: <span className="font-medium">{focusedMeta?.title || focusedMetricId}</span>
                        </span>
                        <button onClick={() => setFocusedMetricId(null)} className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:bg-gray-50 text-gray-700">Clear</button>
                      </div>
                    )}
                  </div>
                  <div className="p-6 py-2 bg-white h-[16rem] overflow-y-auto">
                    {loading ? (
                      <div className="h-full flex items-center justify-center">
                        <div className="text-center">
                          <RefreshCw className="h-5 w-5 animate-spin text-emerald-600 mx-auto" />
                          <div className="mt-2 text-sm text-gray-700 font-medium">Loading essay...</div>
                        </div>
                      </div>
                    ) : (
                      <>
                        {/* Plain-English baseline explanation */}
                        <div className="text-xs text-gray-400 mb-3 leading-relaxed">
                          Highlights show where each selected signal appears in this essay.
                          Hover any highlight to see what it represents and how much of the essay it covers.
                        </div>
                        <HighlightedEssay doc={doc} activeMetricIds={activeMetricIds}
                          containerRef={ref}
                          onShowTooltip={onShowTooltip} onMoveTooltip={onMoveTooltip} onHideTooltip={onHideTooltip} />
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* What changed */}
            {selectedMetrics.length > 0 && (
              <div className="mt-6 bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="text-xl font-semibold text-gray-900">What changed between these essays</h3>
                    <div className="mt-1 text-xs text-gray-500">
                      Each percentage shows how much of the essay contains that signal.
                      A higher percentage means the signal appears more throughout the writing.
                    </div>
                  </div>
                  {focusedMetricId && (
                    <button onClick={() => setFocusedMetricId(null)}
                      className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700">
                      <X className="h-4 w-4" /> Clear focus
                    </button>
                  )}
                </div>

                {/* Summary cards */}
                <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
                  <StoryCard label="Biggest improvement (left to right)"
                    metricTitle={metricsSummary.mostIncreased?.def?.title}
                    category={metricsSummary.mostIncreased?.def?.category}
                    left={metricsSummary.mostIncreased?.left ?? 0} right={metricsSummary.mostIncreased?.right ?? 0}
                    delta={metricsSummary.mostIncreased?.delta ?? 0} tone="up"
                    isDisabled={!metricsSummary.mostIncreased} />
                  <StoryCard label="Most consistent (smallest change)"
                    metricTitle={metricsSummary.mostStable?.def?.title}
                    category={metricsSummary.mostStable?.def?.category}
                    left={metricsSummary.mostStable?.left ?? 0} right={metricsSummary.mostStable?.right ?? 0}
                    delta={metricsSummary.mostStable?.delta ?? 0} tone="flat"
                    isDisabled={!metricsSummary.mostStable} />
                  <StoryCard label="Biggest decline (left to right)"
                    metricTitle={metricsSummary.mostDecreased?.def?.title}
                    category={metricsSummary.mostDecreased?.def?.category}
                    left={metricsSummary.mostDecreased?.left ?? 0} right={metricsSummary.mostDecreased?.right ?? 0}
                    delta={metricsSummary.mostDecreased?.delta ?? 0} tone="down"
                    isDisabled={!metricsSummary.mostDecreased} />
                </div>

                {/* Top changes list */}
                <div className="mt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-gray-900">Top changes</div>
                      <div className="mt-0.5 text-xs text-gray-500">Click "Focus" to highlight that signal in both essays above.</div>
                    </div>
                    <div className="text-xs text-gray-500">
                      Showing <span className="font-medium text-gray-700">{Math.min(8, coverageRows.length)}</span> of{" "}
                      <span className="font-medium text-gray-700">{coverageRows.length}</span>
                    </div>
                  </div>
                  <div className="mt-3 space-y-3">
                    {topChanges.length === 0
                      ? <div className="text-sm text-gray-600">No metrics selected.</div>
                      : topChanges.map((r) => (
                        <MetricRow key={r.def.id} row={r}
                          isFocused={focusedMetricId === r.def.id}
                          onFocusToggle={() => focusMetric(r.def.id, false)}
                          onShow={() => { setFocusedMetricId(r.def.id); setTimeout(() => scrollToFirstHighlight(r.def.id), 30); }} />
                      ))
                    }
                  </div>
                  {coverageRows.length > 8 && (
                    <div className="mt-4">
                      <button onClick={() => setShowAllMetrics((v) => !v)}
                        className="inline-flex items-center gap-2 px-3 py-2 rounded-xl border border-gray-200 bg-white hover:bg-gray-50 text-sm text-gray-700">
                        <ChevronDown className={`h-4 w-4 transition-transform ${showAllMetrics ? "rotate-180" : ""}`} />
                        {showAllMetrics ? "Hide remaining metrics" : `Show all ${coverageRows.length} metrics`}
                      </button>
                      {showAllMetrics && (
                        <div className="mt-3 space-y-3">
                          {allRemaining.map((r) => (
                            <MetricRow key={r.def.id} row={r}
                              isFocused={focusedMetricId === r.def.id}
                              onFocusToggle={() => focusMetric(r.def.id, false)}
                              onShow={() => { setFocusedMetricId(r.def.id); setTimeout(() => scrollToFirstHighlight(r.def.id), 30); }} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
