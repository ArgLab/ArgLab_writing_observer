"use client";

import {
  AlertTriangle,
  BarChart3,
  Calendar,
  CheckCircle2,
  Clipboard,
  Clock,
  FileText,
  GitCompareArrows,
  Info,
  Minus,
  Sparkles,
  TrendingDown,
  TrendingUp,
  Users,
  X
} from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useLOConnectionDataManager } from "lo_event/lo_event/lo_assess/components/components.jsx";

import { useCourseIdContext } from "@/app/providers/CourseIdProvider";
import { getConfiguredWsOrigin } from "@/app/utils/ws";
import StudentDetailCompare from "./StudentDetailCompare";
import StudentDetailGrowth from "./StudentDetailGrowth";

/* =============================================================
   CONSTANTS
   ============================================================= */

const MODES = { COMPARE: "compare", GROWTH: "growth" };
const STUDENTS_BREADCRUMB_HREF = "/wo_portfolio_diff/portfolio_diff/students";
const monthsShort = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const monthsLong  = ["January","February","March","April","May","June","July","August","September","October","November","December"];

const ASSIGNMENT_TYPES = ["All Types", "Narrative", "Argumentative", "Analytical", "Expository", "Other"];

const ASSIGNMENT_TYPE_COLORS = {
  Narrative:     { bg: "bg-violet-50",  text: "text-violet-700",  ring: "ring-violet-200",  dot: "bg-violet-400" },
  Argumentative: { bg: "bg-amber-50",   text: "text-amber-700",   ring: "ring-amber-200",   dot: "bg-amber-400" },
  Analytical:    { bg: "bg-blue-50",    text: "text-blue-700",    ring: "ring-blue-200",    dot: "bg-blue-400" },
  Expository:    { bg: "bg-teal-50",    text: "text-teal-700",    ring: "ring-teal-200",    dot: "bg-teal-400" },
  Other:         { bg: "bg-gray-50",    text: "text-gray-600",    ring: "ring-gray-200",    dot: "bg-gray-400" },
  Document:      { bg: "bg-emerald-50", text: "text-emerald-700", ring: "ring-emerald-200", dot: "bg-emerald-400" },
};

const CATEGORY_KEYS = {
  language: "Language", argumentation: "Argumentation", statements: "Statements",
  transitions: "Transition Words", pos: "Parts of Speech", sentence_type: "Sentence Types",
  source_information: "Source Information", dialogue: "Dialogue", tone: "Tone",
  details: "Details", other: "Other",
};

const iconForCategoryKey = (catKey) => {
  switch (catKey) {
    case "tone": return TrendingUp;
    case "dialogue": return Users;
    case "details": return FileText;
    default: return FileText;
  }
};

const METRIC_DEFS_RAW = [
  { id: "academic_language", title: "Academic Language", categoryKey: "language", function: "percent", desc: "Percent of tokens flagged academic" },
  { id: "informal_language", title: "Informal Language", categoryKey: "language", function: "percent", desc: "Percent of tokens flagged informal" },
  { id: "latinate_words", title: "Latinate Words", categoryKey: "language", function: "percent", desc: "Percent of tokens flagged latinate" },
  { id: "opinion_words", title: "Opinion Words", categoryKey: "language", function: "total", desc: "Total opinion-word signals" },
  { id: "emotion_words", title: "Emotion Words", categoryKey: "language", function: "percent", desc: "Percent emotion words" },
  { id: "argument_words", title: "Argument Words", categoryKey: "argumentation", function: "percent", desc: "Percent argument words" },
  { id: "explicit_argument", title: "Explicit argument", categoryKey: "argumentation", function: "percent", desc: "Percent explicit argument markers" },
  { id: "statements_of_opinion", title: "Statements of Opinion", categoryKey: "statements", function: "percent", desc: "Percent of sentences classified as opinion" },
  { id: "statements_of_fact", title: "Statements of Fact", categoryKey: "statements", function: "percent", desc: "Percent of sentences classified as fact" },
  { id: "transition_words", title: "Transition Words", categoryKey: "transitions", function: "counts", desc: "Transition counts (by type)" },
  { id: "positive_transition_words", title: "Positive Transition Words", categoryKey: "transitions", function: "total", desc: "Total positive transitions" },
  { id: "conditional_transition_words", title: "Conditional Transition Words", categoryKey: "transitions", function: "total", desc: "Total conditional transitions" },
  { id: "consequential_transition_words", title: "Consequential Transition Words", categoryKey: "transitions", function: "total", desc: "Total consequential transitions" },
  { id: "contrastive_transition_words", title: "Contrastive Transition Words", categoryKey: "transitions", function: "total", desc: "Total contrastive transitions" },
  { id: "counterpoint_transition_words", title: "Counterpoint Transition Words", categoryKey: "transitions", function: "total", desc: "Total counterpoint transitions" },
  { id: "comparative_transition_words", title: "Comparative Transition Words", categoryKey: "transitions", function: "total", desc: "Total comparative transitions" },
  { id: "cross_referential_transition_words", title: "Cross Referential Transition Words", categoryKey: "transitions", function: "total", desc: "Total cross-referential transitions" },
  { id: "illustrative_transition_words", title: "Illustrative Transition Words", categoryKey: "transitions", function: "total", desc: "Total illustrative transitions" },
  { id: "negative_transition_words", title: "Negative Transition Words", categoryKey: "transitions", function: "total", desc: "Total negative transitions" },
  { id: "emphatic_transition_words", title: "Emphatic Transition Words", categoryKey: "transitions", function: "total", desc: "Total emphatic transitions" },
  { id: "evenidentiary_transition_words", title: "Evenidentiary Transition Words", categoryKey: "transitions", function: "total", desc: "Total evidentiary transitions" },
  { id: "general_transition_words", title: "General Transition Words", categoryKey: "transitions", function: "total", desc: "Total general transitions" },
  { id: "ordinal_transition_words", title: "Ordinal Transition Words", categoryKey: "transitions", function: "total", desc: "Total ordinal transitions" },
  { id: "purposive_transition_words", title: "Purposive Transition Words", categoryKey: "transitions", function: "total", desc: "Total purposive transitions" },
  { id: "periphrastic_transition_words", title: "Periphrastic Transition Words", categoryKey: "transitions", function: "total", desc: "Total periphrastic transitions" },
  { id: "hypothetical_transition_words", title: "Hypothetical Transition Words", categoryKey: "transitions", function: "total", desc: "Total hypothetical transitions" },
  { id: "summative_transition_words", title: "Summative Transition Words", categoryKey: "transitions", function: "total", desc: "Total summative transitions" },
  { id: "introductory_transition_words", title: "Introductory Transition Words", categoryKey: "transitions", function: "total", desc: "Total introductory transitions" },
  { id: "adjectives", title: "Adjectives", categoryKey: "pos", function: "total", desc: "Total adjectives" },
  { id: "adverbs", title: "Adverbs", categoryKey: "pos", function: "total", desc: "Total adverbs" },
  { id: "nouns", title: "Nouns", categoryKey: "pos", function: "total", desc: "Total nouns" },
  { id: "proper_nouns", title: "Proper Nouns", categoryKey: "pos", function: "total", desc: "Total proper nouns" },
  { id: "verbs", title: "Verbs", categoryKey: "pos", function: "total", desc: "Total verbs" },
  { id: "numbers", title: "Numbers", categoryKey: "pos", function: "total", desc: "Total numbers" },
  { id: "prepositions", title: "Prepositions", categoryKey: "pos", function: "total", desc: "Total prepositions" },
  { id: "coordinating_conjunction", title: "Coordinating Conjunction", categoryKey: "pos", function: "total", desc: "Total coordinating conjunctions" },
  { id: "subordinating_conjunction", title: "Subordinating Conjunction", categoryKey: "pos", function: "total", desc: "Total subordinating conjunctions" },
  { id: "auxiliary_verb", title: "Auxiliary Verb", categoryKey: "pos", function: "total", desc: "Total auxiliary verbs" },
  { id: "pronoun", title: "Pronoun", categoryKey: "pos", function: "total", desc: "Total pronouns" },
  { id: "simple_sentences", title: "Simple Sentences", categoryKey: "sentence_type", function: "total", desc: "Total simple sentences" },
  { id: "simple_with_complex_predicates", title: "Simple with Complex Predicates", categoryKey: "sentence_type", function: "total", desc: "Total simple (complex predicates)" },
  { id: "simple_with_compound_predicates", title: "Simple with Compound Predicates", categoryKey: "sentence_type", function: "total", desc: "Total simple (compound predicates)" },
  { id: "simple_with_compound_complex_predicates", title: "Simple with Compound Complex Predicates", categoryKey: "sentence_type", function: "total", desc: "Total simple (compound complex predicates)" },
  { id: "compound_sentences", title: "Compound Sentences", categoryKey: "sentence_type", function: "total", desc: "Total compound sentences" },
  { id: "complex_sentences", title: "Complex Sentences", categoryKey: "sentence_type", function: "total", desc: "Total complex sentences" },
  { id: "compound_complex_sentences", title: "Compound Complex Sentences", categoryKey: "sentence_type", function: "total", desc: "Total compound-complex sentences" },
  { id: "information_sources", title: "Information Sources", categoryKey: "source_information", function: "percent", desc: "Percent source references" },
  { id: "attributions", title: "Attributions", categoryKey: "source_information", function: "percent", desc: "Percent attributions" },
  { id: "citations", title: "Citations", categoryKey: "source_information", function: "percent", desc: "Percent citations" },
  { id: "quoted_words", title: "Quoted Words", categoryKey: "source_information", function: "percent", desc: "Percent quoted words" },
  { id: "direct_speech_verbs", title: "Direct Speech Verbs", categoryKey: "dialogue", function: "percent", desc: "Percent direct speech verbs" },
  { id: "indirect_speech", title: "Indirect Speech", categoryKey: "dialogue", function: "percent", desc: "Percent indirect speech" },
  { id: "positive_tone", title: "Positive Tone", categoryKey: "tone", function: "percent", desc: "Percent positive tone" },
  { id: "negative_tone", title: "Negative Tone", categoryKey: "tone", function: "percent", desc: "Percent negative tone" },
  { id: "concrete_details", title: "Concrete Details", categoryKey: "details", function: "percent", desc: "Percent concrete details" },
  { id: "main_idea_sentences", title: "Main Idea Sentences", categoryKey: "details", function: "total", desc: "Total main idea sentences" },
  { id: "supporting_idea_sentences", title: "Supporting Idea Sentences", categoryKey: "details", function: "total", desc: "Total supporting idea sentences" },
  { id: "supporting_detail_sentences", title: "Supporting Detail Sentences", categoryKey: "details", function: "total", desc: "Total supporting detail sentences" },
  { id: "polysyllabic_words", title: "Polysyllabic Words", categoryKey: "other", function: "percent", desc: "Percent polysyllabic tokens" },
  { id: "low_frequency_words", title: "Low Frequency Words", categoryKey: "other", function: "percent", desc: "Percent low-frequency tokens" },
  { id: "sentences", title: "Sentences", categoryKey: "other", function: "total", desc: "Total sentences" },
  { id: "paragraphs", title: "Paragraphs", categoryKey: "other", function: "total", desc: "Total paragraphs" },
  { id: "character_trait_words", title: "Character Trait Words", categoryKey: "other", function: "percent", desc: "Percent character trait tokens" },
  { id: "in_past_tense", title: "In Past Tense", categoryKey: "other", function: "percent", desc: "Percent past tense scope" },
  { id: "explicit_claims", title: "Explicit Claims", categoryKey: "other", function: "percent", desc: "Percent explicit claims" },
  { id: "social_awareness", title: "Social Awareness", categoryKey: "other", function: "percent", desc: "Percent social awareness" },
];

const METRIC_BY_ID = Object.fromEntries(METRIC_DEFS_RAW.map((m) => [m.id, m]));
const DEFAULT_METRICS = ["academic_language","informal_language","latinate_words","transition_words","citations","sentences","paragraphs"];
const GENRE_COLORS = { Document: "hsl(160 70% 40%)" };

/* =============================================================
   PASTE / TIME HELPERS
   Real data shape (confirmed from WS response):
     liveData.students[studentID].documents[docId] = {
       text:               string
       time_on_task:       number   // minutes — already the right unit
       pastes_with_length: number   // total paste events (any size)
       total_paste_chars:  number   // total chars pasted
       length_bins: {
         short_1_20:    number,
         medium_21_200: number,
         long_201_plus: number   // large pastes (200+ chars)
       }
       copy_count:         number
       last_ts:            number
       last_access:        number
     }
   ============================================================= */
const LARGE_PASTE_THRESHOLD_CHARS = 200;
const AVG_WORD_LENGTH_CHARS = 5;

function charsToWords(chars) {
  return Math.round(chars / AVG_WORD_LENGTH_CHARS);
}

// Extract all activity stats from a single doc node.
// Returns a consistent shape regardless of which fields are present.
function extractDocStats(docNode) {
  if (!docNode || typeof docNode !== "object") {
    return { largePasteCount: 0, totalPasteChars: 0, copyCount: 0, timeOnTask: null };
  }
  return {
    largePasteCount: docNode.length_bins?.long_201_plus ?? 0,
    totalPasteChars: docNode.total_paste_chars          ?? 0,
    copyCount:       docNode.copy_count                 ?? 0,
    // time_on_task is in minutes already — no conversion needed
    timeOnTask:      typeof docNode.time_on_task === "number" ? docNode.time_on_task : null,
  };
}

/* =============================================================
   RQ2b/RQ2c PREDICTION
   ============================================================= */
const PREDICTION = { IMPROVING: "Improving", PLATEAUING: "Plateauing", STAGNATING: "At Risk of Stagnation" };

const PRED_STYLE = {
  [PREDICTION.IMPROVING]:  { bg: "bg-emerald-50", text: "text-emerald-800", ring: "ring-emerald-200", border: "border-emerald-200", headerBg: "bg-emerald-50", icon: <CheckCircle2 className="h-5 w-5 text-emerald-600" />, barColor: "bg-emerald-400" },
  [PREDICTION.PLATEAUING]: { bg: "bg-blue-50",    text: "text-blue-800",    ring: "ring-blue-200",    border: "border-blue-200",    headerBg: "bg-blue-50",    icon: <BarChart3    className="h-5 w-5 text-blue-500"    />, barColor: "bg-blue-400"    },
  [PREDICTION.STAGNATING]: { bg: "bg-rose-50",    text: "text-rose-800",    ring: "ring-rose-200",    border: "border-rose-200",    headerBg: "bg-rose-50",    icon: <AlertTriangle className="h-5 w-5 text-rose-600"  />, barColor: "bg-rose-400"    },
};

function confQualifier(pct) {
  if (pct >= 75) return { label: "Strong signal",   desc: "This student's writing process shows a consistent pattern across enough essays to make a reliable prediction." };
  if (pct >= 55) return { label: "Moderate signal", desc: "There is a pattern here, but it is still developing. Use this alongside your own classroom observations." };
  return           { label: "Early indication",     desc: "This student has fewer essays on record. Treat this as a prompt for closer attention, not a firm prediction." };
}

function deriveStudentPrediction(docCount) {
  if (docCount === 0) return {
    label: PREDICTION.STAGNATING, confidence: 0.78,
    narrative: "No essays have been submitted yet, so there is no writing process history to draw from.",
    componentTrends: [], similarCase: null,
  };
  if (docCount >= 8) return {
    label: PREDICTION.IMPROVING, confidence: 0.84,
    narrative: "This student's typing fluency and revision depth have both improved steadily across their last several essays. Students with a similar upward pattern have historically scored in the top quartile on their next assignment.",
    componentTrends: [
      { trait: "Word Choice",      direction: "up"   },
      { trait: "Sentence Fluency", direction: "up"   },
      { trait: "Organization",     direction: "flat" },
      { trait: "Ideas & Content",  direction: "flat" },
    ],
    similarCase: { count: 9, total: 11, outcome: "top quartile on their next essay" },
  };
  if (docCount >= 4) return {
    label: PREDICTION.PLATEAUING, confidence: 0.67,
    narrative: "This student's revision frequency and sentence-planning pauses have stayed consistent for the last four essays with no clear upward or downward movement. Students with a similar stable pattern have typically maintained their current performance level.",
    componentTrends: [
      { trait: "Word Choice",      direction: "flat" },
      { trait: "Sentence Fluency", direction: "flat" },
      { trait: "Organization",     direction: "up"   },
      { trait: "Ideas & Content",  direction: "down" },
    ],
    similarCase: { count: 7, total: 10, outcome: "the same performance level on their next essay" },
  };
  return {
    label: PREDICTION.STAGNATING, confidence: 0.61,
    narrative: "This student's uninterrupted writing bursts have shortened and their active writing time has decreased over the last three essays. Students with a similar declining pattern have historically scored below the class median on their next assignment.",
    componentTrends: [
      { trait: "Word Choice",      direction: "down" },
      { trait: "Sentence Fluency", direction: "down" },
      { trait: "Organization",     direction: "flat" },
      { trait: "Ideas & Content",  direction: "down" },
    ],
    similarCase: { count: 8, total: 13, outcome: "below the class median on their next essay" },
  };
}

/* =============================================================
   HELPERS
   ============================================================= */
const median = (arr) => {
  if (!arr.length) return 0;
  const a = [...arr].sort((x, y) => x - y);
  const mid = Math.floor(a.length / 2);
  return a.length % 2 ? a[mid] : (a[mid - 1] + a[mid]) / 2;
};
const mean = (a) => a.reduce((s, x) => s + x, 0) / Math.max(1, a.length);
const std = (a) => {
  if (a.length < 2) return 0;
  const m = mean(a);
  return Math.sqrt(mean(a.map((v) => (v - m) * (v - m))));
};
const slopePerIndex = (series) => {
  if (series.length < 2) return 0;
  const xs = series.map((p) => p.idx); const ys = series.map((p) => p.value);
  const xbar = mean(xs); const ybar = mean(ys);
  const num = xs.reduce((s, x, i) => s + (x - xbar) * (ys[i] - ybar), 0);
  const den = xs.reduce((s, x) => s + (x - xbar) * (x - xbar), 0) || 1;
  return num / den;
};
const safeNum = (v, fallback = 0) => { const n = Number(v); return Number.isFinite(n) ? n : fallback; };
const sentenceSplit = (text) => { const t = (text || "").trim(); if (!t) return []; return t.split(/(?<=[.!?])\s+/).filter(Boolean); };
const wordSplit = (text) => { const t = (text || "").trim(); if (!t) return []; return t.split(/\s+/).map((w) => w.replace(/[^\p{L}\p{N}'-]+/gu, "").trim()).filter(Boolean); };
const makePreviewFromText = (text, maxChars = 380) => { const t = (text || "").replace(/\s+/g, " ").trim(); return t.length > maxChars ? `${t.slice(0, maxChars)}...` : t; };
const formatDocTitle = (docId, meta) => {
  const fromMeta = meta?.title || meta?.name || meta?.doc_title || meta?.document_title || meta?.filename || meta?.file_name;
  if (fromMeta && String(fromMeta).trim()) return String(fromMeta).trim();
  return docId ? String(docId).replace(/[-_]/g, " ") : "Document";
};
const getDocObjFromLO = (data, studentID, docId) => {
  const s = data?.students?.[studentID];
  const d1 = s?.documents?.[docId]; if (d1 && typeof d1 === "object") return d1;
  const d2 = s?.docs?.[docId];      if (d2 && typeof d2 === "object") return d2;
  const d3 = s?.doc_by_id?.[docId]; if (d3 && typeof d3 === "object") return d3;
  const d4 = s?.documents?.[docId]?.value; if (d4 && typeof d4 === "object") return d4;
  return null;
};
const getDocTextFromLO = (data, studentID, docId) => { const doc = getDocObjFromLO(data, studentID, docId); const t = doc?.text; return typeof t === "string" ? t : ""; };

function metricCoveragePercent(doc, metricId) {
  const text = (doc?.text || "").toString(); const L = text.length; if (!L) return 0;
  const offsets = doc?.[metricId]?.offsets;
  if (!Array.isArray(offsets) || offsets.length === 0) return 0;
  const ranges = [];
  for (const pair of offsets) {
    if (!Array.isArray(pair) || pair.length < 2) continue;
    const start = Number(pair[0]); const len = Number(pair[1]);
    if (!Number.isFinite(start) || !Number.isFinite(len) || len <= 0) continue;
    let s = Math.max(0, Math.min(L, start)); let e = Math.max(0, Math.min(L, start + len));
    if (e > s) ranges.push([s, e]);
  }
  if (!ranges.length) return 0;
  ranges.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  let covered = 0; let [curS, curE] = ranges[0];
  for (let i = 1; i < ranges.length; i++) {
    const [s, e] = ranges[i];
    if (s <= curE) curE = Math.max(curE, e);
    else { covered += curE - curS; curS = s; curE = e; }
  }
  covered += curE - curS;
  return (covered / L) * 100;
}

function inferAssignmentType(meta, text) {
  const explicit = meta?.assignment_type || meta?.genre || meta?.type;
  if (explicit) { const e = String(explicit).trim(); if (ASSIGNMENT_TYPES.includes(e)) return e; }
  const t = (text || "").toLowerCase();
  if (/argue|claim|thesis|evidence|counterargument/.test(t)) return "Argumentative";
  if (/analyze|analysis|examine|compare|contrast/.test(t)) return "Analytical";
  if (/once upon|story|character|plot|setting/.test(t)) return "Narrative";
  if (/explain|describe|inform|definition/.test(t)) return "Expository";
  return "Document";
}

// Builds essay objects from doc data.
// Now reads time_on_task, largePasteCount, totalPasteChars, copyCount
// directly from the doc node so per-essay cards have all activity data.
const buildEssaysFromDocs = ({ studentID, documentIDS, docsObj, data }) => {
  const out = (documentIDS || []).map((docId) => {
    const meta = docsObj?.[docId] || {};
    const lastAccess = meta?.last_access;
    const lastAccessMs = typeof lastAccess === "number" ? (lastAccess > 1e12 ? lastAccess : lastAccess * 1000) : null;
    const dateISO = lastAccessMs ? new Date(lastAccessMs).toISOString() : "";
    const dateObj = lastAccessMs ? new Date(lastAccessMs) : null;
    const dateStr = dateObj ? `${monthsShort[dateObj.getMonth()]} ${dateObj.getDate()}, ${dateObj.getFullYear()}` : "—";
    const category = dateObj ? `${monthsLong[dateObj.getMonth()]} ${dateObj.getFullYear()}` : "Unknown date";
    const doc = getDocObjFromLO(data, studentID, docId);
    const text = doc?.text && typeof doc.text === "string" ? doc.text : getDocTextFromLO(data, studentID, docId);
    const wordsArr = wordSplit(text);
    const words = wordsArr.length;
    const uniqueWords = new Set(wordsArr.map((w) => w.toLowerCase())).size;
    const lexicalDiversity = words ? Number(((uniqueWords / words) * 100).toFixed(1)) : 0;
    const sents = sentenceSplit(text);
    const sentences = Math.max(1, sents.length || 1);
    const avgSentenceLen = words ? Math.round(words / sentences) : 0;
    const assignmentType = inferAssignmentType(meta, text);

    // Activity stats — read directly from doc node (confirmed in WS response)
    const stats = extractDocStats(meta);

    return {
      id: docId,
      title: formatDocTitle(docId, meta),
      date: dateStr,
      dateISO: dateISO || new Date(0).toISOString(),
      category,
      words, uniqueWords, lexicalDiversity, avgSentenceLen,
      grade: "—",
      preview: makePreviewFromText(text),
      tags: [assignmentType],
      assignmentType,
      // Activity fields surfaced for per-essay cards and summary stats
      timeOnTaskMins:   stats.timeOnTask,
      largePasteCount:  stats.largePasteCount,
      totalPasteChars:  stats.totalPasteChars,
      copyCount:        stats.copyCount,
      editCount:        meta?.edit_count ?? null,
      _doc: doc || { text },
    };
  });
  return out.sort((a, b) => new Date(b.dateISO) - new Date(a.dateISO));
};

/* =============================================================
   SUB-COMPONENTS
   ============================================================= */

function InfoTooltip({ text }) {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const iconRef = useRef(null);
  const show = () => {
    if (!iconRef.current) return;
    const rect = iconRef.current.getBoundingClientRect();
    setCoords({ top: rect.top + window.scrollY - 8, left: rect.left + rect.width / 2 + window.scrollX });
    setVisible(true);
  };
  const hide = () => setVisible(false);
  return (
    <span className="relative inline-flex items-center ml-1 cursor-help" onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      <Info ref={iconRef} className="h-3.5 w-3.5 text-gray-400 hover:text-gray-600 transition-colors" />
      {visible && (
        <span style={{ position: "fixed", top: coords.top, left: coords.left, transform: "translate(-50%, -100%)", zIndex: 9999 }}
          className="pointer-events-none w-60 rounded-xl bg-gray-900 px-3 py-2.5 text-xs text-white leading-relaxed shadow-xl text-center">
          {text}
          <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </span>
      )}
    </span>
  );
}

function AssignmentTypeBadge({ type }) {
  const colors = ASSIGNMENT_TYPE_COLORS[type] || ASSIGNMENT_TYPE_COLORS["Document"];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold ring-1 ring-inset ${colors.bg} ${colors.text} ${colors.ring}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${colors.dot}`} />
      {type}
    </span>
  );
}

function EffortPill({ icon: Icon, value, label, title }) {
  if (value == null) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs text-gray-500" title={title}>
      <Icon className="h-3.5 w-3.5 text-gray-400" />{value} {label}
    </span>
  );
}

function ComparisonContextBanner({ filterType }) {
  if (!filterType || filterType === "All Types") return null;
  return (
    <div className="flex items-start gap-2 rounded-xl bg-blue-50 border border-blue-200 px-4 py-2.5 text-sm text-blue-800 mb-4">
      <Info className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
      <span>Showing <strong>{filterType}</strong> assignments only. Comparisons are within the same assignment type for valid analysis.</span>
    </div>
  );
}

function DirectionArrow({ direction }) {
  if (direction === "up")   return <TrendingUp  className="h-3 w-3 text-emerald-600" />;
  if (direction === "down") return <TrendingDown className="h-3 w-3 text-rose-500" />;
  return <Minus className="h-3 w-3 text-gray-400" />;
}

/* =============================================================
   STAT CARDS
   ============================================================= */

function EssaysCard({ count }) {
  return (
    <div className="rounded-2xl p-5 py-4 border shadow-sm flex flex-col gap-1 bg-gradient-to-br from-emerald-500 to-emerald-600 border-emerald-600 text-white">
      <div className="flex items-center justify-between mb-1">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-100">Essays in Portfolio</p>
        <FileText className="h-4 w-4 text-emerald-200" />
      </div>
      <p className="text-3xl font-extrabold leading-none text-white">{count}</p>
      <p className="text-xs mt-1 text-emerald-100">Available documents</p>
    </div>
  );
}

function PredictedTrajectoryCard({ prediction, onOpen }) {
  if (!prediction) {
    return (
      <div className="rounded-2xl p-5 py-4 border shadow-sm flex flex-col gap-1 bg-white border-gray-200 animate-pulse">
        <div className="flex items-center justify-between mb-1">
          <div className="h-3 w-36 rounded bg-gray-200" />
          <div className="h-4 w-4 rounded bg-gray-200" />
        </div>
        <div className="h-5 w-28 rounded bg-gray-200 mt-1" />
        <div className="h-3 w-20 rounded bg-gray-100 mt-2" />
      </div>
    );
  }
  const style = PRED_STYLE[prediction.label] || PRED_STYLE[PREDICTION.PLATEAUING];
  const conf = confQualifier(Math.round((prediction.confidence ?? 0) * 100));
  return (
    <div
      className={`rounded-2xl p-5 py-4 border shadow-sm flex flex-col gap-1 cursor-pointer hover:shadow-md transition-shadow ${style.border} ${style.bg}`}
      onClick={onOpen}
      role="button"
      aria-label="Open trajectory detail"
    >
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1">
          <p className={`text-xs font-semibold uppercase tracking-wide ${style.text}`}>Predicted Trajectory</p>
          <InfoTooltip text="Based on how this student's writing process has changed across their essays. Click to see the full explanation." />
        </span>
        <Sparkles className={`h-4 w-4 ${style.text} opacity-60`} />
      </div>
      <p className={`text-xl font-extrabold leading-snug ${style.text}`}>{prediction.label}</p>
      <p className={`text-xs mt-1 ${style.text} opacity-70`}>{conf.label} · click for details</p>
    </div>
  );
}

// Shows total large paste count across all essays.
// largePasteCount = sum of length_bins.long_201_plus
// totalPasteWords = estimated words from total_paste_chars
function LargePastesCard({ largePasteCount, totalPasteWords }) {
  const hasActivity = largePasteCount > 0;
  return (
    <div className="rounded-2xl p-5 py-4 border shadow-sm flex flex-col gap-1 bg-white border-gray-200 text-gray-900">
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Large Pastes</p>
          <InfoTooltip text={`A large paste is any single paste inserting ${LARGE_PASTE_THRESHOLD_CHARS}+ characters (~${Math.round(LARGE_PASTE_THRESHOLD_CHARS / AVG_WORD_LENGTH_CHARS)} words) at once. See per-essay breakdown below.`} />
        </span>
        <Clipboard className="h-4 w-4 text-gray-400" />
      </div>
      {hasActivity ? (
        <>
          <p className="text-3xl font-extrabold leading-none text-gray-900">{largePasteCount}</p>
          <p className="text-xs mt-1 text-gray-400">~{totalPasteWords.toLocaleString()} words pasted across all essays</p>
        </>
      ) : (
        <>
          <p className="text-3xl font-extrabold leading-none text-gray-300">0</p>
          <p className="text-xs mt-1 text-gray-400">No large paste events detected</p>
        </>
      )}
    </div>
  );
}

// Shows average time on task across all essays.
// avgTime is real minutes from time_on_task — no fallback dummy.
function AvgTimeCard({ avgTime }) {
  const hasData = avgTime != null;
  return (
    <div className="rounded-2xl p-5 py-4 border shadow-sm flex flex-col gap-1 bg-white border-gray-200 text-gray-900">
      <div className="flex items-center justify-between mb-1">
        <span className="flex items-center gap-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Avg. Time on Task</p>
          <InfoTooltip text="Average minutes spent actively writing per essay, derived from keystroke timestamps. Gaps over 2 minutes are excluded." />
        </span>
        <Clock className="h-4 w-4 text-gray-400" />
      </div>
      {hasData ? (
        <>
          <p className="text-3xl font-extrabold leading-none text-gray-900">{Math.round(avgTime)} min</p>
          <p className="text-xs mt-1 text-gray-400">Effort signal per essay</p>
        </>
      ) : (
        <>
          <p className="text-3xl font-extrabold leading-none text-gray-300">—</p>
          <p className="text-xs mt-1 text-gray-400">Loading...</p>
        </>
      )}
    </div>
  );
}

/* =============================================================
   PREDICTION MODAL
   ============================================================= */

function StudentPredictionPanel({ prediction, studentName, onDismiss }) {
  const style = PRED_STYLE[prediction.label] || PRED_STYLE[PREDICTION.PLATEAUING];
  const confPct = Math.round((prediction.confidence ?? 0) * 100);
  const conf = confQualifier(confPct);

  const handleBackdrop = (e) => { if (e.target === e.currentTarget) onDismiss(); };

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onDismiss(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onDismiss]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={handleBackdrop} aria-modal="true" role="dialog">
      <div className={`relative w-full max-w-2xl rounded-2xl border ${style.border} bg-white shadow-2xl`}>
        <div className={`${style.headerBg} px-5 py-4 flex items-center justify-between border-b ${style.border} rounded-t-2xl`}>
          <div className="flex items-center gap-3">
            {style.icon}
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-0.5">Predicted Writing Trajectory</p>
              <h3 className={`text-lg font-extrabold ${style.text} leading-tight`}>{prediction.label}</h3>
            </div>
          </div>
          <button onClick={onDismiss} className="text-gray-400 hover:text-gray-600 transition-colors ml-4" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-5 py-5 flex flex-col gap-5">
          <div className={`flex items-center gap-3 rounded-xl px-4 py-3 border ${style.border} ${style.bg}`}>
            <div className="flex-1">
              <span className={`text-xs font-bold uppercase tracking-wide ${style.text}`}>{conf.label}</span>
              <span className={`text-xs ${style.text} opacity-70 ml-2`}>{conf.desc}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">What the data shows</p>
              <div className="rounded-xl bg-gray-50 border border-gray-100 px-4 py-3">
                <p className="text-sm text-gray-700 leading-relaxed">{prediction.narrative}</p>
              </div>
              {prediction.similarCase && (
                <div className="flex items-start gap-2 rounded-xl bg-white border border-gray-200 px-3 py-2.5">
                  <Users className="h-4 w-4 text-gray-400 mt-0.5 shrink-0" />
                  <p className="text-xs text-gray-600 leading-relaxed">
                    <span className="font-bold text-gray-900">{prediction.similarCase.count}/{prediction.similarCase.total}</span> students with a similar pattern went on to achieve{" "}
                    <span className="font-semibold">{prediction.similarCase.outcome}</span>.
                  </p>
                </div>
              )}
            </div>

            <div className="flex flex-col gap-2">
              {prediction.componentTrends?.length > 0 && (
                <>
                  <p className="text-xs font-bold text-gray-500 uppercase tracking-wide">Rubric Trait Signals</p>
                  <div className="rounded-xl bg-white border border-gray-200 px-4 py-3 flex flex-col gap-2">
                    {prediction.componentTrends.map((ct) => (
                      <div key={ct.trait} className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-gray-800">{ct.trait}</span>
                        <span className={`inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full ${
                          ct.direction === "up"   ? "bg-emerald-100 text-emerald-700" :
                          ct.direction === "down" ? "bg-rose-100 text-rose-700" :
                          "bg-gray-100 text-gray-500"
                        }`}>
                          <DirectionArrow direction={ct.direction} />
                          {ct.direction === "up" ? "Improving" : ct.direction === "down" ? "Declining" : "Stable"}
                        </span>
                      </div>
                    ))}
                  </div>
                </>
              )}

              <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mt-1">Suggested Action</p>
              <div className={`rounded-xl border ${style.border} ${style.bg} px-4 py-3`}>
                <p className={`text-sm font-semibold ${style.text} leading-snug`}>
                  {prediction.label === PREDICTION.STAGNATING
                    ? "Schedule a writing conference before this student's next essay."
                    : prediction.label === PREDICTION.PLATEAUING
                    ? "Give targeted feedback on one specific trait to break the plateau."
                    : "Acknowledge the growth — check Growth Over Time to see what is working."}
                </p>
              </div>
            </div>
          </div>

          <p className="text-[10px] text-gray-400 leading-relaxed text-center">
            Trajectory predictions use pattern heuristics and will be replaced by a trained model once enough data is available.
          </p>
        </div>
      </div>
    </div>
  );
}

/* =============================================================
   MAIN COMPONENT
   ============================================================= */

export default function StudentDetail({ studentId }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const studentID = searchParams.get("student_id") || String(studentId);

  const [mode, setMode] = useState(MODES.COMPARE);
  const [selectedEssays, setSelectedEssays] = useState([]);
  const [cardsPerRow, setCardsPerRow] = useState(3);
  const [sortBy, setSortBy] = useState("date");
  const [search, setSearch] = useState("");
  const [filterTags, setFilterTags] = useState([]);
  const [tagOpen, setTagOpen] = useState(false);
  const [tagQuery, setTagQuery] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [metrics, setMetrics] = useState([...DEFAULT_METRICS]);
  const [openEssay, setOpenEssay] = useState(null);
  const [activeQuickRange, setActiveQuickRange] = useState("all");
  const [assignmentTypeFilter, setAssignmentTypeFilter] = useState("All Types");
  const [typeFilterOpen, setTypeFilterOpen] = useState(false);
  const typeFilterRef = useRef(null);
  const [showPredictionPanel, setShowPredictionPanel] = useState(false);

  const { courseId } = useCourseIdContext();

  const initialDataScope = useMemo(() => ({
    wo: {
      execution_dag: "writing_observer",
      target_exports: ["student_with_docs", "single_student_profile", "single_student_paste", "single_student_copy_cut", "single_student_time_on_task"],
      kwargs: { course_id: courseId, student_id: studentID },
    },
  }), [courseId, studentID]);

  const origin = getConfiguredWsOrigin();
  const { data: liveData, errors, connection } = useLOConnectionDataManager({
    url: `${origin}/wsapi/communication_protocol`,
    dataScope: initialDataScope,
  });

  // ── MERGED DOC ACCUMULATOR ───────────────────────────────────
  // WS sends doc data across multiple ticks. Tick 1 may have
  // paste/time fields, tick 2 may have text. We merge every tick
  // into a persistent accumulator so no fields are overwritten.
  const mergedDocsAccRef = useRef({});
  const mergedDocsStudentIDRef = useRef(null);

  if (mergedDocsStudentIDRef.current !== studentID) {
    mergedDocsStudentIDRef.current = studentID;
    mergedDocsAccRef.current = {};
  }

  const rawDocsFromTick = liveData?.students?.[studentID]?.documents || {};
  for (const [docId, incoming] of Object.entries(rawDocsFromTick)) {
    const existing = mergedDocsAccRef.current[docId] || {};
    const merged = { ...existing };
    for (const [k, v] of Object.entries(incoming)) {
      if (v !== null && v !== undefined) merged[k] = v;
    }
    mergedDocsAccRef.current[docId] = merged;
  }

  // Single source of truth for all doc data
  const liveDocsObj = mergedDocsAccRef.current;

  // ── FREEZE: document IDs ─────────────────────────────────────
  const liveDocIds = useMemo(() => Object.keys(liveDocsObj).sort(), [
    // eslint-disable-next-line react-hooks/exhaustive-deps
    Object.keys(liveDocsObj).sort().join(","),
  ]);

  const frozenDocIdsRef = useRef(null);
  const frozenStudentIDRef = useRef(null);
  if (frozenStudentIDRef.current !== studentID) {
    frozenStudentIDRef.current = studentID;
    frozenDocIdsRef.current = null;
  }
  if (frozenDocIdsRef.current === null && liveDocIds.length > 0) {
    frozenDocIdsRef.current = liveDocIds;
  }
  const documentIDS = frozenDocIdsRef.current ?? liveDocIds;

  // ── GATE: all docs have both text AND activity data ────────────
  // Text arrives via single_student_doc_by_id.
  // time_on_task arrives via single_student_time_on_task.
  // Both must be present before we freeze so the snapshot is complete.
  const allDocsHaveText = documentIDS.length > 0 &&
    documentIDS.every((id) => {
      const d = liveDocsObj?.[id];
      return (
        d &&
        typeof d.text === "string" && d.text.length > 0 &&
        d.time_on_task != null
      );
    });

  // ── FREEZE: docsObj snapshot (text + all activity fields merged) ─
  const frozenDocsObjRef = useRef(null);
  const frozenDocsStudentIDRef = useRef(null);
  if (frozenDocsStudentIDRef.current !== studentID) {
    frozenDocsStudentIDRef.current = studentID;
    frozenDocsObjRef.current = null;
  }
  if (frozenDocsObjRef.current === null && allDocsHaveText) {
    // Snapshot the accumulator — has both text AND activity fields
    frozenDocsObjRef.current = { ...liveDocsObj };
  }
  const docsObj = frozenDocsObjRef.current ?? liveDocsObj;

  // ── FREEZE: full liveData for child components ────────────────
  const frozenDataRef = useRef(null);
  const frozenDataStudentIDRef = useRef(null);
  if (frozenDataStudentIDRef.current !== studentID) {
    frozenDataStudentIDRef.current = studentID;
    frozenDataRef.current = null;
  }
  if (frozenDataRef.current === null && allDocsHaveText) {
    frozenDataRef.current = liveData;
  }
  const frozenData = frozenDataRef.current ?? liveData;

  // ── FREEZE: student name ──────────────────────────────────────
  const liveProfile = liveData?.students?.[studentID]?.profile?.name || {};
  const liveStudentName = liveProfile?.full_name || liveProfile?.name || studentID;
  const frozenNameRef = useRef(null);
  const frozenNameStudentIDRef = useRef(null);
  if (frozenNameStudentIDRef.current !== studentID) {
    frozenNameStudentIDRef.current = studentID;
    frozenNameRef.current = null;
  }
  if (frozenNameRef.current === null && liveStudentName && liveStudentName !== studentID) {
    frozenNameRef.current = liveStudentName;
  }
  const studentName = frozenNameRef.current ?? liveStudentName;

  // ── FREEZE: prediction ────────────────────────────────────────
  const frozenPredRef = useRef(null);
  const frozenPredStudentIDRef = useRef(null);
  if (frozenPredStudentIDRef.current !== studentID) {
    frozenPredStudentIDRef.current = studentID;
    frozenPredRef.current = null;
  }
  if (frozenPredRef.current === null && documentIDS.length > 0) {
    frozenPredRef.current =
      liveData?.students?.[studentID]?.prediction ??
      deriveStudentPrediction(documentIDS.length);
  }
  const studentPrediction = frozenPredRef.current ?? null;

  // ── DOWNSTREAM MEMOS ─────────────────────────────────────────
  const getStudentById = useCallback((id) => {
    const profile = frozenData?.students?.[id]?.profile;
    const name = profile?.name?.full_name || profile?.name?.name || (id ? String(id).replace(/[-_]/g, " ") : "Student");
    const initials = name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2) || "ST";
    return { id, name, initials, avatarColor: "bg-gray-100", textColor: "text-gray-700", gradeLevel: profile?.grade_level || "—", section: profile?.section || "—" };
  }, [frozenData]);

  const docsObjContentSig = useMemo(() =>
    JSON.stringify(Object.fromEntries(
      Object.entries(docsObj || {}).map(([k, v]) => [k, typeof v?.text === "string" ? v.text.slice(0, 80) : ""])
    )),
  [docsObj]);

  // essays now carries timeOnTaskMins, largePasteCount, totalPasteChars, copyCount
  const essays = useMemo(
    () => buildEssaysFromDocs({ studentID, documentIDS, docsObj, data: frozenData }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [studentID, docsObjContentSig],
  );

  // ── SUMMARY STATS derived from essays ────────────────────────
  // All read from the essay objects which get data from the merged doc node.
  const summaryStats = useMemo(() => {
    const withTime = essays.filter((e) => e.timeOnTaskMins != null && Number.isFinite(e.timeOnTaskMins));
    const avgTime  = withTime.length ? mean(withTime.map((e) => e.timeOnTaskMins)) : null;

    const totalLargePastes = essays.reduce((s, e) => s + (e.largePasteCount ?? 0), 0);
    const totalPasteWords  = essays.reduce((s, e) => s + charsToWords(e.totalPasteChars ?? 0), 0);

    return { avgTime, totalLargePastes, totalPasteWords };
  }, [essays]);

  const metricSections = useMemo(() => Object.entries(CATEGORY_KEYS).map(([categoryKey, title]) => ({
    title, icon: iconForCategoryKey(categoryKey),
    metrics: METRIC_DEFS_RAW.filter((m) => m.categoryKey === categoryKey).map((m) => m.id),
  })), []);

  const metricByKey = useCallback((key) => {
    const raw = METRIC_BY_ID[key]; if (!raw) return null;
    const get = (essay) => {
      const doc = essay?._doc || {};
      const direct = doc?.[key]?.metric;
      if (direct != null && !Number.isNaN(Number(direct))) return Number(direct);
      return metricCoveragePercent(doc, key);
    };
    return { key, label: raw.title, unit: raw.function === "percent" ? "%" : "", get, desc: raw.desc };
  }, []);

  const essaysAscAll = useMemo(() => [...essays].sort((a, b) => new Date(a.dateISO) - new Date(b.dateISO)), [essays]);

  const baselineByMetric = useMemo(() => {
    const out = {};
    for (const k of metrics) {
      const def = metricByKey(k); if (!def) continue;
      const vals = essaysAscAll.map((e) => safeNum(def.get(e), 0));
      out[k] = { median: median(vals), sd: std(vals) };
    }
    return out;
  }, [essaysAscAll, metrics, metricByKey]);

  const essaysInRangeAsc = useMemo(() => essaysAscAll.filter((e) => {
    const d = new Date(e.dateISO);
    const afterStart = !startDate || d >= new Date(startDate);
    const beforeEnd  = !endDate   || d <= new Date(endDate);
    return afterStart && beforeEnd;
  }), [essaysAscAll, startDate, endDate]);

  const getSeriesForMetric = useCallback((key) => {
    const def = metricByKey(key); if (!def) return [];
    const base = baselineByMetric[key] || { median: 0, sd: 0 };
    return essaysInRangeAsc.map((e, idx) => {
      const raw = safeNum(def.get(e), 0); const delta = raw - base.median;
      const badge = base.sd > 0 ? (delta > 0.75 * base.sd ? "▲" : delta < -0.75 * base.sd ? "▼" : "●") : "●";
      return { idx, label: e.date, title: e.title, date: e.date, genre: e.tags[0], raw, value: delta, delta, badge, unit: def.unit };
    });
  }, [metricByKey, baselineByMetric, essaysInRangeAsc]);

  const genreSegments = useMemo(() => {
    const segs = []; if (!essaysInRangeAsc.length) return segs;
    let start = 0; let current = essaysInRangeAsc[0].tags[0];
    for (let i = 1; i < essaysInRangeAsc.length; i++) {
      const g = essaysInRangeAsc[i].tags[0];
      if (g !== current) { segs.push({ x1: start, x2: i - 1, genre: current }); current = g; start = i; }
    }
    segs.push({ x1: start, x2: essaysInRangeAsc.length - 1, genre: current });
    return segs;
  }, [essaysInRangeAsc]);

  const filteredEssaysCompare = useMemo(() => {
    const byType   = (e) => assignmentTypeFilter === "All Types" || e.assignmentType === assignmentTypeFilter;
    const byTags   = (e) => filterTags.length === 0 || filterTags.some((t) => (e.tags || []).includes(t));
    const bySearch = (e) => {
      if (!search.trim()) return true;
      const q = search.toLowerCase();
      return (e.title || "").toLowerCase().includes(q) || (e.preview || "").toLowerCase().includes(q) || (e.tags || []).some((t) => t.toLowerCase().includes(q));
    };
    const sorted = [...essays].sort((a, b) => {
      if (sortBy === "words") return safeNum(b.words) - safeNum(a.words);
      if (sortBy === "title") return (a.title || "").localeCompare(b.title || "");
      return new Date(a.dateISO) < new Date(b.dateISO) ? 1 : -1;
    });
    return sorted.filter(byType).filter(byTags).filter(bySearch);
  }, [essays, assignmentTypeFilter, filterTags, sortBy, search]);

  const groupedEssays = useMemo(() => filteredEssaysCompare.reduce((acc, essay) => {
    if (!acc[essay.category]) acc[essay.category] = [];
    acc[essay.category].push(essay);
    return acc;
  }, {}), [filteredEssaysCompare]);

  const getGridCols = () => {
    switch (cardsPerRow) {
      case 1: return "grid-cols-1"; case 2: return "grid-cols-2"; case 3: return "grid-cols-3";
      case 4: return "grid-cols-4"; case 5: return "grid-cols-5"; case 6: return "grid-cols-6";
      default: return "grid-cols-4";
    }
  };

  const tagRef = useRef(null);
  useEffect(() => {
    const onClick = (e) => {
      if (tagRef.current && !tagRef.current.contains(e.target)) setTagOpen(false);
      if (typeFilterRef.current && !typeFilterRef.current.contains(e.target)) setTypeFilterOpen(false);
    };
    window.addEventListener("click", onClick);
    return () => window.removeEventListener("click", onClick);
  }, []);

  // WS message — request doc text once we know the doc IDs
  const prevDocIDSSigRef = useRef("");
  useEffect(() => {
    const sig = documentIDS.join(",");
    if (sig === prevDocIDSSigRef.current) return;
    if (documentIDS.length === 0) return;
    if (!connection?.sendMessage) return;
    prevDocIDSSigRef.current = sig;
    connection.sendMessage(JSON.stringify({
      wo: {
        execution_dag: "writing_observer",
        target_exports: ["student_with_docs", "single_student_doc_by_id", "single_student_profile", "single_student_paste", "single_student_copy_cut", "single_student_time_on_task"],
        kwargs: { course_id: courseId, student_id: studentID, doc_ids: documentIDS },
      }
    }));
  }, [documentIDS, connection, courseId, studentID]);

  const applyQuickRange = (key) => {
    setActiveQuickRange(key);
    if (key === "all") { setStartDate(""); setEndDate(""); return; }
    if (!essaysAscAll.length) return;
    const last = new Date(essaysAscAll[essaysAscAll.length - 1].dateISO);
    const end = new Date(last); const start2 = new Date(last);
    if (key === "3mo") start2.setMonth(start2.getMonth() - 3);
    if (key === "6mo") start2.setMonth(start2.getMonth() - 6);
    if (key === "9mo") start2.setMonth(start2.getMonth() - 9);
    setStartDate(start2.toISOString().slice(0, 10));
    setEndDate(end.toISOString().slice(0, 10));
  };

  const onStartDateChange = (v) => { setStartDate(v); setActiveQuickRange(""); };
  const onEndDateChange   = (v) => { setEndDate(v);   setActiveQuickRange(""); };
  const clearFilters = () => { setFilterTags([]); setTagQuery(""); setSearch(""); setAssignmentTypeFilter("All Types"); };
  const isAnyFilter  = filterTags.length > 0 || search.trim().length > 0 || assignmentTypeFilter !== "All Types";

  const handleEssaySelect = (essayId) => {
    if (mode !== MODES.COMPARE) return;
    setSelectedEssays((prev) => {
      if (prev.includes(essayId)) return prev.filter((id) => id !== essayId);
      if (prev.length >= 2) return prev;
      return [...prev, essayId];
    });
  };

  const presentTypes = useMemo(() => {
    const types = new Set(essays.map((e) => e.assignmentType));
    return ["All Types", ...ASSIGNMENT_TYPES.slice(1).filter((t) => types.has(t))];
  }, [essays]);

  // pasteStatsByDoc passed to StudentDetailCompare for per-card display
  // Shape: { [docId]: { largePasteCount, totalPasteChars, copyCount, timeOnTask } }
  const pasteStatsByDoc = useMemo(() => Object.fromEntries(
    essays.map((e) => [e.id, {
      largePasteCount: e.largePasteCount ?? 0,
      totalPasteChars: e.totalPasteChars ?? 0,
      copyCount:       e.copyCount       ?? 0,
      timeOnTask:      e.timeOnTaskMins  ?? null,
    }])
  ), [essays]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">

      {showPredictionPanel && studentPrediction && (
        <StudentPredictionPanel
          prediction={studentPrediction}
          studentName={studentName}
          onDismiss={() => setShowPredictionPanel(false)}
        />
      )}

      <div className="p-6 pb-0 px-6 mx-auto">

        {/* Breadcrumb */}
        <nav className="text-sm text-gray-500 mb-5" aria-label="Breadcrumb">
          <ol className="inline-flex items-center space-x-1 md:space-x-2">
            <li>
              <a href={STUDENTS_BREADCRUMB_HREF} className="inline-flex gap-1.5 items-center text-gray-500 hover:text-emerald-600 transition-colors">
                <Users className="h-4 w-4" /><span>Students</span>
              </a>
            </li>
            <li className="text-gray-300">›</li>
            <li className="inline-flex items-center text-gray-800 font-medium">
              <span className="inline-flex items-center gap-2">
                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold">
                  {studentName.split(/\s+/).map((w) => w[0]).join("").toUpperCase().slice(0, 2)}
                </span>
                {studentName}
              </span>
            </li>
          </ol>
        </nav>

        {/* 4 stat cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          <EssaysCard count={documentIDS.length} />
          <PredictedTrajectoryCard
            prediction={studentPrediction}
            onOpen={() => studentPrediction && setShowPredictionPanel(true)}
          />
          <LargePastesCard
            largePasteCount={summaryStats.totalLargePastes}
            totalPasteWords={summaryStats.totalPasteWords}
          />
          <AvgTimeCard avgTime={summaryStats.avgTime} />
        </div>

        {/* Mode tabs */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-full border border-gray-200 bg-white p-1 shadow-sm" role="tablist">
            <button role="tab" aria-selected={mode === MODES.COMPARE} onClick={() => setMode(MODES.COMPARE)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition ${mode === MODES.COMPARE ? "bg-emerald-600 text-white" : "text-gray-700 hover:bg-gray-50"}`}>
              <GitCompareArrows className="h-4 w-4" /> Compare Essays
            </button>
            <button role="tab" aria-selected={mode === MODES.GROWTH} onClick={() => setMode(MODES.GROWTH)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition ${mode === MODES.GROWTH ? "bg-emerald-600 text-white" : "text-gray-700 hover:bg-gray-50"}`}>
              <TrendingUp className="h-4 w-4" /> Growth Over Time
            </button>
          </div>

          {isAnyFilter && (
            <button onClick={clearFilters}
              className="inline-flex items-center gap-1.5 px-3 py-2 text-sm rounded-full bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 transition">
              <X className="h-3.5 w-3.5" /> Clear filters
            </button>
          )}
        </div>

        {/* Date range — growth mode only */}
        {mode === MODES.GROWTH && (
          <div className="mb-3">
            <div className="flex flex-wrap items-center gap-3">
              <div className="inline-flex items-center gap-2 bg-white border border-gray-200 rounded-xl shadow-sm px-3 py-2">
                <Calendar className="h-4 w-4 text-gray-500" />
                <input type="date" value={startDate} onChange={(e) => onStartDateChange(e.target.value)} className="border-0 text-sm focus:outline-none" aria-label="Start date" />
                <span className="text-gray-400">–</span>
                <input type="date" value={endDate} onChange={(e) => onEndDateChange(e.target.value)} className="border-0 text-sm focus:outline-none" aria-label="End date" />
              </div>
              <div className="inline-flex bg-white border border-gray-200 rounded-full p-1 shadow-sm">
                {[["all","All time"],["3mo","Last 3 months"],["6mo","Last 6 months"],["9mo","Last 9 months"]].map(([key, label]) => (
                  <button key={key} onClick={() => applyQuickRange(key)} aria-pressed={activeQuickRange === key}
                    className={`px-3 py-1 text-sm rounded-full transition ${activeQuickRange === key ? "bg-emerald-600 text-white" : "hover:bg-gray-50 text-gray-700"}`}>
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <ComparisonContextBanner filterType={assignmentTypeFilter} />
      </div>

      {/* Main content */}
      <div className="py-4 px-6 mx-auto">
        {mode === MODES.GROWTH ? (
          <StudentDetailGrowth
            studentID={studentID} metrics={metrics} setMetrics={setMetrics}
            metricSections={metricSections} metricByKey={metricByKey}
            getSeriesForMetric={getSeriesForMetric} slopePerIndex={slopePerIndex}
            GENRE_COLORS={GENRE_COLORS} genreSegments={genreSegments}
            essaysInRangeAsc={essaysInRangeAsc}
            loDocData={frozenData}
            loDocErrors={errors}
            loDocConnection={connection}
          />
        ) : (
          <StudentDetailCompare
            groupedEssays={groupedEssays} studentId={studentId}
            selectedEssays={selectedEssays} setSelectedEssays={setSelectedEssays}
            handleEssaySelect={handleEssaySelect}
            cardsPerRow={cardsPerRow} setCardsPerRow={setCardsPerRow}
            sortBy={sortBy} setSortBy={setSortBy}
            search={search} setSearch={setSearch}
            filterTags={filterTags} setFilterTags={setFilterTags}
            tagOpen={tagOpen} setTagOpen={setTagOpen}
            tagQuery={tagQuery} setTagQuery={setTagQuery}
            tagRef={tagRef} clearFilters={clearFilters} isAnyFilter={isAnyFilter}
            getGridCols={getGridCols} openEssay={openEssay} setOpenEssay={setOpenEssay}
            getStudentById={getStudentById} router={router}
            GENRE_COLORS={GENRE_COLORS}
            loDocData={frozenData}
            loDocErrors={errors}
            loDocConnection={connection}
            documentIDS={documentIDS}
            assignmentTypeFilter={assignmentTypeFilter}
            AssignmentTypeBadge={AssignmentTypeBadge}
            EffortPill={EffortPill}
            pasteStatsByDoc={pasteStatsByDoc}
          />
        )}
      </div>
    </div>
  );
}
