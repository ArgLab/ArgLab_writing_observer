"use client";

import {
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Clock,
  Download,
  FileText,
  Search,
  Users,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Loader,
  Info,
  X,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useRef, useState } from "react";
import {
  useLOConnectionDataManager,
  LO_CONNECTION_STATUS,
} from "lo_event/lo_event/lo_assess/components/components.jsx";
import { useCourseIdContext } from "@/app/providers/CourseIdProvider";
import { getConfiguredWsOrigin } from "@/app/utils/ws";

const SEVEN_DAYS_SECS  = 7  * 24 * 60 * 60;
const THIRTY_DAYS_SECS = 30 * 24 * 60 * 60;

const RISK = {
  AT_RISK:  "At-Risk",
  IMPROVING:"Improving",
  ON_TRACK: "On-Track",
  REVIEW:   "Under Review",
};

const TREND = { UP: "up", FLAT: "flat", DOWN: "down" };

const TREND_STATE = {
  IMPROVING: "Improving",
  STABLE:    "Stable",
  DECLINING: "Declining",
  AT_RISK:   "At-Risk",
};

const TREND_STATE_STYLE = {
  [TREND_STATE.IMPROVING]: {
    badge:     "text-emerald-800 bg-emerald-100 ring-1 ring-inset ring-emerald-200",
    rowBorder: "border-l-4 border-l-emerald-400",
    label:     "↑ Improving",
  },
  [TREND_STATE.STABLE]: {
    badge:     "text-gray-700 bg-gray-100 ring-1 ring-inset ring-gray-200",
    rowBorder: "border-l-4 border-l-gray-300",
    label:     "→ Stable",
  },
  [TREND_STATE.DECLINING]: {
    badge:     "text-orange-800 bg-orange-100 ring-1 ring-inset ring-orange-200",
    rowBorder: "border-l-4 border-l-orange-400",
    label:     "↓ Declining",
  },
  [TREND_STATE.AT_RISK]: {
    badge:     "text-red-800 bg-red-100 ring-1 ring-inset ring-red-200",
    rowBorder: "border-l-4 border-l-red-500",
    label:     "⚠ At-Risk",
  },
};

const PREDICTION = {
  ON_TRACK:   "On Track",
  SLOW_GROWTH:"Slow Growth",
  STAGNATING: "At Risk of Stagnation",
  DECLINING:  "Declining",
};

const PREDICTION_STYLE = {
  [PREDICTION.ON_TRACK]:   { bg: "bg-emerald-50", text: "text-emerald-800", ring: "ring-emerald-200", icon: <TrendingUp    className="h-3.5 w-3.5" />, modalBorder: "border-emerald-200", modalHeader: "bg-emerald-50" },
  [PREDICTION.SLOW_GROWTH]:{ bg: "bg-yellow-50",  text: "text-yellow-800",  ring: "ring-yellow-200",  icon: <Minus         className="h-3.5 w-3.5" />, modalBorder: "border-yellow-200",  modalHeader: "bg-yellow-50"  },
  [PREDICTION.STAGNATING]: { bg: "bg-orange-50",  text: "text-orange-800",  ring: "ring-orange-200",  icon: <AlertTriangle className="h-3.5 w-3.5" />, modalBorder: "border-orange-200",  modalHeader: "bg-orange-50"  },
  [PREDICTION.DECLINING]:  { bg: "bg-red-50",     text: "text-red-800",     ring: "ring-red-200",     icon: <TrendingDown  className="h-3.5 w-3.5" />, modalBorder: "border-red-200",     modalHeader: "bg-red-50"     },
};

const DUMMY_TREND_STATES = [
  TREND_STATE.DECLINING,  TREND_STATE.IMPROVING, TREND_STATE.AT_RISK,
  TREND_STATE.STABLE,     TREND_STATE.IMPROVING, TREND_STATE.DECLINING,
  TREND_STATE.AT_RISK,    TREND_STATE.STABLE,    TREND_STATE.DECLINING,
  TREND_STATE.IMPROVING,  TREND_STATE.AT_RISK,   TREND_STATE.STABLE,
  TREND_STATE.DECLINING,
];

const DUMMY_PREDICTIONS = [
  { label: PREDICTION.STAGNATING, topFeature: "Declining burst length over last 3 essays" },
  { label: PREDICTION.ON_TRACK,   topFeature: "Consistent within-word fluency gains across essays" },
  { label: PREDICTION.DECLINING,  topFeature: "Active writing time has dropped significantly" },
  { label: PREDICTION.SLOW_GROWTH,topFeature: "Stable revision rate, no significant change in editing behavior" },
  { label: PREDICTION.ON_TRACK,   topFeature: "Sentence-planning pauses have shortened across recent essays" },
  { label: PREDICTION.DECLINING,  topFeature: "Uninterrupted burst length has shortened over 4 essays" },
  { label: PREDICTION.STAGNATING, topFeature: "No recent writing activity detected" },
  { label: PREDICTION.SLOW_GROWTH,topFeature: "Minor improvement in revision depth but pace has slowed" },
  { label: PREDICTION.DECLINING,  topFeature: "Active writing time has dropped significantly" },
  { label: PREDICTION.ON_TRACK,   topFeature: "Consistent within-word fluency gains across essays" },
  { label: PREDICTION.STAGNATING, topFeature: "Declining burst length over last 3 essays" },
  { label: PREDICTION.SLOW_GROWTH,topFeature: "Stable revision rate, no significant change in editing behavior" },
  { label: PREDICTION.DECLINING,  topFeature: "Uninterrupted burst length has shortened over 4 essays" },
];

/* ─────────────────────────────────────────────
   TRAJECTORY EXPLANATION
───────────────────────────────────────────── */
function getTrajectoryExplanation(prediction, docCount, studentName) {
  const label = prediction?.label;
  const name  = studentName || "This student";

  if (label === PREDICTION.ON_TRACK)
    return `${name}'s writing process has shown consistent upward movement across recent essays. Typing fluency, revision depth, and time spent planning have all trended positively. Students with a similar pattern typically maintain or build on this momentum into the end of the year.`;
  if (label === PREDICTION.SLOW_GROWTH)
    return `${name}'s writing process is improving, but slowly. Some positive signals are present: revision depth is stable and sentence-planning pauses have shortened slightly. The pace of change is not yet consistent enough to indicate strong upward momentum. Continued monitoring over the next few essays will clarify the trajectory.`;
  if (label === PREDICTION.STAGNATING) {
    if (docCount === 0)
      return `${name} has no writing on record. Without any essays, there is no process data to draw from, which itself is a signal worth following up on.`;
    return `${name}'s writing process shows signs of stagnation. Uninterrupted writing bursts have shortened, active writing time has decreased, and revision behavior has not changed in ways associated with growth. Students with a similar pattern have historically performed below the class median on subsequent assignments.`;
  }
  if (label === PREDICTION.DECLINING)
    return `${name}'s writing process is showing a clear downward trend. Active writing time has dropped, burst length has shortened across recent essays, and revision behavior has become less engaged. Without intervention, students with this pattern typically see a measurable drop in their next assessment.`;
  return `There is not enough data yet to form a reliable trajectory for ${name}. More essays will improve the signal.`;
}

/* ─────────────────────────────────────────────
   TRAJECTORY MODAL
───────────────────────────────────────────── */
function TrajectoryModal({ student, onClose }) {
  if (!student) return null;
  const { prediction, documents, fullname } = student;
  const style = PREDICTION_STYLE[prediction?.label] || PREDICTION_STYLE[PREDICTION.SLOW_GROWTH];
  const explanation = getTrajectoryExplanation(prediction, documents, fullname);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={onClose}
      aria-modal="true"
      role="dialog"
    >
      <div
        className={`relative w-full max-w-md rounded-2xl border ${style.modalBorder} bg-white shadow-2xl`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={`${style.modalHeader} px-5 py-4 flex items-center justify-between border-b ${style.modalBorder} rounded-t-2xl`}>
          <div className="flex items-center gap-2.5 min-w-0">
            <span className={`shrink-0 ${style.text}`}>{style.icon}</span>
            <div className="min-w-0">
              <p className="text-[10px] font-bold uppercase tracking-wide text-gray-500">Trajectory Forecast</p>
              <h3 className={`text-base font-extrabold ${style.text} leading-tight truncate`}>
                {prediction?.label ?? "Unknown"} &middot; {fullname}
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="shrink-0 ml-3 inline-flex items-center justify-center h-7 w-7 rounded-lg border border-gray-200 bg-white text-gray-400 hover:text-gray-700 hover:bg-gray-50 transition-colors shadow-sm"
            aria-label="Close"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
        <div className="px-5 py-4">
          <p className="text-sm text-gray-700 leading-relaxed">{explanation}</p>
          <p className="mt-3 text-[10px] text-gray-400 italic">
            Based on keystroke-derived writing process patterns. Use alongside your own classroom knowledge.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   PURE HELPERS
───────────────────────────────────────────── */
function deepMerge(a, b) {
  const aObj = a && typeof a === "object" && !Array.isArray(a);
  const bObj = b && typeof b === "object" && !Array.isArray(b);
  if (aObj && bObj) {
    const out = { ...a };
    for (const k of Object.keys(b)) out[k] = deepMerge(a[k], b[k]);
    return out;
  }
  return b;
}

function latestLastAccessSec(availableDocuments) {
  if (!availableDocuments) return null;
  const docs = Object.values(availableDocuments);
  if (!docs.length) return null;
  let max = null;
  for (const d of docs) {
    const v = d?.last_access;
    if (v == null) continue;
    const n = Number(v);
    if (Number.isNaN(n)) continue;
    if (max == null || n > max) max = n;
  }
  return max;
}

function formatLastActivity(lastAccessSec) {
  if (!lastAccessSec) return "Never";
  const nowSec  = Date.now() / 1000;
  const diffSec = Math.max(0, nowSec - Number(lastAccessSec));
  const mins    = Math.floor(diffSec / 60);
  const hrs     = Math.floor(diffSec / 3600);
  const days    = Math.floor(diffSec / 86400);

  if (mins < 1)  return "Just now";
  if (mins < 60) return `${mins} min ago`;
  if (hrs < 24)  return `${hrs} hr${hrs === 1 ? "" : "s"} ago`;
  if (days <= 6) return `${days} day${days === 1 ? "" : "s"} ago`;

  try {
    return new Date(Number(lastAccessSec) * 1000).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
    });
  } catch { return "Unknown"; }
}

function deriveRisk(docCount, lastAccessSec) {
  const nowSec  = Date.now() / 1000;
  const diffSec = lastAccessSec ? nowSec - Number(lastAccessSec) : Infinity;
  if (docCount === 0)                                  return RISK.AT_RISK;
  if (diffSec > THIRTY_DAYS_SECS)                      return RISK.AT_RISK;
  if (docCount >= 8 && diffSec < SEVEN_DAYS_SECS)      return RISK.IMPROVING;
  if (docCount >= 3 && diffSec < SEVEN_DAYS_SECS * 2)  return RISK.ON_TRACK;
  return RISK.REVIEW;
}

function deriveTrend(docCount, lastAccessSec) {
  const nowSec  = Date.now() / 1000;
  const diffSec = lastAccessSec ? nowSec - Number(lastAccessSec) : Infinity;
  if (docCount === 0 || diffSec > THIRTY_DAYS_SECS) return TREND.DOWN;
  if (docCount >= 8 && diffSec < SEVEN_DAYS_SECS)   return TREND.UP;
  return TREND.FLAT;
}

function TrendStateBadge({ trendState }) {
  const style = TREND_STATE_STYLE[trendState] || TREND_STATE_STYLE[TREND_STATE.STABLE];
  return (
    <span className={`inline-flex items-center px-2.5 py-1 text-xs font-semibold rounded-full w-fit ${style.badge}`}>
      {style.label}
    </span>
  );
}

function PredictionBadge({ prediction }) {
  const style = PREDICTION_STYLE[prediction?.label] || PREDICTION_STYLE[PREDICTION.SLOW_GROWTH];
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold rounded-md w-fit ring-1 ring-inset ${style.bg} ${style.text} ${style.ring}`}>
      {style.icon}
      {prediction?.label ?? "Unknown"}
    </span>
  );
}

/* ─────────────────────────────────────────────
   MAIN COMPONENT
───────────────────────────────────────────── */
export default function WritingPortfolioDashboard() {
  const [query,           setQuery]           = useState("");
  const [focusFilter,     setFocusFilter]     = useState("All");
  const [pageSize,        setPageSize]        = useState(10);
  const [page,            setPage]            = useState(1);
  const [sortKey,         setSortKey]         = useState("id");
  const [sortDir,         setSortDir]         = useState("asc");
  const [selected,        setSelected]        = useState(new Set());
  const [trajectoryModal, setTrajectoryModal] = useState(null);

  const { courseId } = useCourseIdContext();

  const decoded = {};
  decoded.course_id   = courseId;
  decoded.student_id  = [{ user_id: "tc-testcase-Alberta" }];
  decoded.document    = [{ doc_id: "fake-google-doc-id-1" }];
  decoded.nlp_options = ["academic_language"];

  const dataScope = {
    wo: {
      execution_dag:  "writing_observer",
      target_exports: ["roster", "document_list", 'document_sources', 'document_list', 'time_on_task', 'activity', 'paste_metrics', 'copy_cut_metrics'],
      kwargs: decoded,
    },
  };

  
  const origin = getConfiguredWsOrigin();
  const { data: liveData, errors, connection } = useLOConnectionDataManager({
    url: `${origin}/wsapi/communication_protocol`,
    dataScope,
  });

  console.log("liveData: ", liveData)

  const frozenStudentsMapRef = useRef(null);
  const frozenCourseIdRef    = useRef(null);

  if (frozenCourseIdRef.current !== courseId) {
    frozenCourseIdRef.current    = courseId;
    frozenStudentsMapRef.current = null;
  }

  const liveStudentsMap = useMemo(() => {
    if (!liveData) return {};
    const flat = liveData?.students ?? {};
    if (flat && Object.keys(flat).length) return flat;
    const roster = liveData?.wo?.roster?.students        ?? {};
    const docs   = liveData?.wo?.document_list?.students ?? {};
    const merged = { ...roster };
    for (const [k, v] of Object.entries(docs)) merged[k] = deepMerge(merged[k] ?? {}, v ?? {});
    return merged;
  }, [liveData]);

  if (frozenStudentsMapRef.current === null && Object.keys(liveStudentsMap).length > 0) {
    frozenStudentsMapRef.current = liveStudentsMap;
  }

  const studentsMap = frozenStudentsMapRef.current ?? liveStudentsMap;

  const DATA = useMemo(() => {
    const list = Object.values(studentsMap || {});
    return list.map((s, idx) => {
      const profile            = s?.profile ?? {};
      const nameObj            = profile?.name ?? {};
      const availableDocuments = s?.availableDocuments ?? {};
      const docCount           = Object.keys(availableDocuments).length;
      const lastAccessSec      = latestLastAccessSec(availableDocuments);
      const lastActivity       = formatLastActivity(lastAccessSec);
      const risk               = deriveRisk(docCount, lastAccessSec);
      const trend              = deriveTrend(docCount, lastAccessSec);
      const dummyTrendState    = DUMMY_TREND_STATES[idx % DUMMY_TREND_STATES.length];
      const dummyPred          = DUMMY_PREDICTIONS[idx % DUMMY_PREDICTIONS.length];
      const prediction         = s?.prediction  ?? dummyPred;
      const trendState         = s?.trend_state ?? dummyTrendState;

      return {
        id:            s?.user_id ?? `student-${idx + 1}`,
        firstname:     nameObj?.given_name  || `Student ${idx + 1}`,
        lastname:      nameObj?.family_name || "",
        fullname:      nameObj?.full_name   || `Student ${idx + 1}`,
        documents:     docCount,
        lastAccessSec: lastAccessSec ?? null,
        lastActivity, risk, trend, trendState, prediction,
      };
    });
  }, [studentsMap]);

  const metrics = useMemo(() => {
    const totalStudents = DATA.length;
    let totalDocuments = 0, studentsWithDocs = 0;
    for (const s of DATA) {
      const docs = Number(s.documents) || 0;
      totalDocuments += docs;
      if (docs > 0) studentsWithDocs += 1;
    }
    const coverage      = totalStudents === 0 ? 0 : Math.round((studentsWithDocs / totalStudents) * 100);
    const atRiskCount   = Math.min(4, totalStudents);
    const topGrowthCount= Math.min(3, totalStudents);
    const noActivityCount=Math.min(6, totalStudents);
    const active7d      = Math.min(7, totalStudents);
    const noActivity30d = Math.min(6, totalStudents);
    return { totalStudents, totalDocuments, active7d, atRiskCount, topGrowthCount, noActivityCount, noActivity30d, coverage };
  }, [DATA]);

  const toggleSort = (key) => {
    if (key === sortKey) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
  };

  const filtered = useMemo(() => {
    let rows = DATA.slice();
    if (query.trim()) {
      const q = query.toLowerCase();
      rows = rows.filter((r) => {
        const full = `${r.firstname || ""} ${r.lastname || ""}`.toLowerCase();
        return full.includes(q) || String(r.id).toLowerCase().includes(q);
      });
    }
    if (focusFilter === "At-Risk")            rows = rows.filter((r) => r.trendState === TREND_STATE.AT_RISK);
    if (focusFilter === "Top Growth")         rows = rows.filter((r) => r.trendState === TREND_STATE.IMPROVING);
    if (focusFilter === "No Recent Activity") rows = rows.filter((r) => {
      const nowSec = Date.now() / 1000;
      return !r.lastAccessSec || nowSec - r.lastAccessSec > THIRTY_DAYS_SECS;
    });

    rows.sort((a, b) => {
      if (sortKey === "lastActivity") {
        const aT = a.lastAccessSec ?? -Infinity;
        const bT = b.lastAccessSec ?? -Infinity;
        return sortDir === "asc" ? aT - bT : bT - aT;
      }
      if (sortKey === "prediction") {
        const order = { [PREDICTION.STAGNATING]: 0, [PREDICTION.DECLINING]: 1, [PREDICTION.SLOW_GROWTH]: 2, [PREDICTION.ON_TRACK]: 3 };
        return sortDir === "asc"
          ? (order[a.prediction?.label] ?? 4) - (order[b.prediction?.label] ?? 4)
          : (order[b.prediction?.label] ?? 4) - (order[a.prediction?.label] ?? 4);
      }
      const A = a[sortKey]; const B = b[sortKey];
      if (A < B) return sortDir === "asc" ? -1 : 1;
      if (A > B) return sortDir === "asc" ?  1 : -1;
      return 0;
    });
    return rows;
  }, [DATA, query, focusFilter, sortKey, sortDir]);

  const total      = filtered.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage   = Math.min(page, totalPages);
  const start      = (safePage - 1) * pageSize;
  const rows       = filtered.slice(start, start + pageSize);
  const allIdsOnPage      = (pr) => pr.map((s) => s.id);
  const allSelectedOnPage = rows.length > 0 && rows.every((r) => selected.has(r.id));

  const isConnecting = connection?.status === LO_CONNECTION_STATUS.CONNECTING
    || connection?.status === LO_CONNECTION_STATUS.RECONNECTING;
  const hasErrors   = errors && Object.keys(errors).length > 0;
  const hasStudents = (DATA?.length ?? 0) > 0;
  const showLoading = !hasErrors && !hasStudents;

  const exportSelectedToCsv = () => {
    const esc = (v) => {
      const s = v == null ? "" : String(v);
      return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const headers = ["ID","First Name","Last Name","Documents","Last Activity","Recent Pattern","Trajectory Forecast"];
    const selectedRows = DATA.filter((r) => selected.has(r.id));
    const lines = [
      headers.map(esc).join(","),
      ...selectedRows.map((r) => [
        r.id, r.firstname, r.lastname, r.documents, r.lastActivity, r.trendState,
        r.prediction?.label ?? "Unknown",
      ].map(esc).join(",")),
    ];
    const blob = new Blob([lines.join("\r\n")], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = `students_export_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  };

  /* ── RENDER HELPERS ─────────────────────── */
  const renderLoading = () => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3">
        <div className="h-3 w-3 rounded-full bg-emerald-600 animate-pulse" />
        <div className="text-sm text-gray-700">{isConnecting ? "Connecting to data source..." : "Loading roster..."}</div>
      </div>
      <div className="mt-6 h-10 rounded-md border border-gray-200 bg-gray-50 animate-pulse" />
      <div className="mt-3 space-y-2">
        {[0,1,2,3,4].map((i) => <div key={i} className="h-12 rounded-md border border-gray-200 bg-gray-50 animate-pulse" />)}
      </div>
    </div>
  );

  const renderError = () => (
    <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-6">
      <div className="text-sm text-red-800 font-semibold">Failed to load dashboard data</div>
      <pre className="mt-2 text-xs text-red-700 whitespace-pre-wrap">{JSON.stringify(errors, null, 2)}</pre>
    </div>
  );

  const renderBulkBar = () => (
    <div className="bg-emerald-50 border-t border-b border-emerald-200 px-4 py-2 flex items-center justify-between">
      <div className="text-sm text-emerald-900"><b>{selected.size}</b> selected</div>
      <button onClick={exportSelectedToCsv}
        className="inline-flex items-center gap-2 px-3 py-1.5 text-sm rounded-md bg-white border border-gray-300 hover:bg-gray-50">
        <Download className="h-4 w-4" /> Export
      </button>
    </div>
  );

  /* ── WELCOME BANNER ─────────────────────── */
  const renderWelcomeBanner = () => {
    const now     = new Date();
    const hour    = now.getHours();
    const greeting =
      hour < 12 ? "Good morning" :
      hour < 17 ? "Good afternoon" :
                  "Good evening";
    const dayName = now.toLocaleDateString("en-US", { weekday: "long" });
    const dateStr = now.toLocaleDateString("en-US", { month: "long", day: "numeric" });

    return (
      <div className="p-6 pb-0">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-500 shadow-lg">
          {/* Decorative rings */}
          <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-white/5" />
          <div className="pointer-events-none absolute -right-8  -top-8  h-44 w-44 rounded-full bg-white/5" />
          <div className="pointer-events-none absolute bottom-0 left-1/2 h-56 w-56 rounded-full bg-black/5 translate-y-1/2" />

          <div className="relative flex flex-col gap-8 p-7 md:p-9 lg:flex-row lg:items-center lg:justify-between">

            {/* LEFT: greeting + subtitle + pills */}
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-emerald-200 tracking-widest uppercase mb-1.5">
                {dayName}, {dateStr}
              </p>
              <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
                {greeting}! 👋
              </h1>
              <p className="mt-2 text-emerald-100/90 text-p max-w-md leading-relaxed">
                Here's a live snapshot of your class: writing activity, growth signals, and students who may need your attention today.
              </p>

              {/* Supporting-context pills — bolder numbers, secondary labels */}
              <div className="mt-4 flex flex-wrap gap-2">
                {[
                  { icon: <Users     className="h-3.5 w-3.5 shrink-0" />, value: metrics.totalStudents, label: "students enrolled" },
                  { icon: <FileText  className="h-3.5 w-3.5 shrink-0" />, value: metrics.totalDocuments, label: "essays logged"      },
                  { icon: <CheckCircle className="h-3.5 w-3.5 shrink-0" />, value: `${metrics.coverage}%`, label: "roster coverage"  },
                ].map(({ icon, value, label }) => (
                  <span key={label} className="inline-flex items-center gap-1.5 rounded-full bg-white/10 border border-white/20 px-3 py-1.5 text-xs text-emerald-100">
                    {icon}
                    <span className="font-extrabold text-white">{value}</span>
                    <span className="font-medium">{label}</span>
                  </span>
                ))}
              </div>

              {/* Tablet fallback: show at-risk count inline when stat cards are hidden */}
              <div className="lg:hidden mt-4 inline-flex items-center gap-2 rounded-xl bg-amber-500/20 border border-amber-400/30 px-4 py-2.5">
                <AlertTriangle className="h-4 w-4 text-amber-300 shrink-0" />
                <span className="text-2xl font-extrabold text-amber-100 tabular-nums leading-none">{metrics.atRiskCount}</span>
                <span className="text-xs font-semibold text-amber-200 leading-tight">students need<br />attention</span>
              </div>
            </div>

            {/* RIGHT: three large headline stats — white cards, order: Active / Need Attention / Top Growth */}
            <div className="hidden lg:grid grid-cols-3 gap-3 shrink-0">

              {/* 1. Active This Week */}
              <div className="flex flex-col justify-between rounded-xl bg-white border border-gray-200 shadow-sm p-5 min-w-[140px]">
                <div className="mb-3 flex items-center gap-4">
                  <Clock className="h-4 w-4 text-emerald-500" />
                  <p className="text-[11px] font-bold uppercase tracking-widest text-gray-500 leading-tight">Active This Week</p>
                </div>
                <p className="text-5xl font-extrabold text-gray-900 leading-none tabular-nums">{metrics.active7d}</p>
                <p className="mt-2 text-[11px] text-gray-400 font-medium">of {metrics.totalStudents} students</p>
              </div>

              {/* 2. Need Attention */}
              <div className="flex flex-col justify-between rounded-xl bg-white border border-amber-200 shadow-sm p-5 min-w-[140px]">
                <div className="mb-3 flex items-center gap-4">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  <p className="text-[11px] font-bold uppercase tracking-widest text-amber-600 leading-tight">Need Attention</p>
                </div>
                <p className="text-5xl font-extrabold text-amber-600 leading-none tabular-nums">{metrics.atRiskCount}</p>
                <p className="mt-2 text-[11px] text-amber-500 font-medium">{metrics.noActivity30d} inactive 30+ days</p>
              </div>

              {/* 3. Top Growth */}
              <div className="flex flex-col justify-between rounded-xl bg-white border border-emerald-200 shadow-sm p-5 min-w-[140px]">
                <div className="mb-3 flex items-center gap-4">
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                  <p className="text-[11px] font-bold uppercase tracking-widest text-emerald-600 leading-tight">Top Growth</p>
                </div>
                <p className="text-5xl font-extrabold text-emerald-600 leading-none tabular-nums">{metrics.topGrowthCount}</p>
                <p className="mt-2 text-[11px] text-emerald-500 font-medium">improving trajectory</p>
              </div>

            </div>
          </div>
        </div>
      </div>
    );
  };

  /* ── HEADER BAR (filters + search together) ─ */
  const renderHeaderBar = () => (
    <div className="mb-3">
      <div className="flex flex-col gap-3 pt-1 pb-2 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Student Overview &amp; Signals</h2>
          <p className="text-sm text-gray-500 mt-0.5">Filter by group or search by name to focus your review.</p>
        </div>

        {/* Filters + search on the same row */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Focus filter pills */}
          <div className="inline-flex rounded-full border border-gray-200 bg-white p-1 shadow-sm gap-0.5">
            {[
              { label: "All",               color: "bg-emerald-600" },
              { label: "At-Risk",           color: "bg-red-600",   count: metrics.atRiskCount     },
              { label: "Top Growth",        color: "bg-emerald-600",count: metrics.topGrowthCount  },
              { label: "No Recent Activity",color: "bg-slate-600", count: metrics.noActivityCount  },
            ].map(({ label, color, count }) => (
              <button key={label}
                onClick={() => { setFocusFilter(label); setPage(1); }}
                className={`px-3 py-1.5 text-sm rounded-full transition whitespace-nowrap ${
                  focusFilter === label ? `${color} text-white` : "text-gray-700 hover:bg-gray-50"
                }`}>
                {label}
                {count > 0 && (
                  <span className={`ml-1.5 inline-flex items-center justify-center h-4 w-4 rounded-full text-[10px] font-bold ${
                    focusFilter === label ? "bg-white/20 text-white" : "bg-gray-100 text-gray-600"
                  }`}>{count}</span>
                )}
              </button>
            ))}
          </div>

          {/* Search — grouped with filters */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => { setQuery(e.target.value); setPage(1); }}
              onKeyDown={(e) => e.stopPropagation()}
              onClick={(e) => e.stopPropagation()}
              className="h-[38px] w-52 pl-8 pr-3 text-sm bg-white border border-gray-200 rounded-full shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-400"
              placeholder="Search name or ID..."
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
            />
          </div>
        </div>
      </div>
    </div>
  );

  /* ── TABLE ─────────────────────────────────── */
  const renderTable = () => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-200 mb-8">
      {/* Table header row */}
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-base font-semibold text-gray-900">Students</h3>
          <span className="text-xs text-gray-400 font-medium bg-gray-100 rounded-full px-2 py-0.5">{total.toLocaleString()}</span>
        </div>
      </div>

      {selected.size > 0 && renderBulkBar()}

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              <th className="pl-6 pr-3 py-3 text-left w-[44px]">
                <input type="checkbox" className="rounded border-gray-300 h-4 w-4"
                  checked={allSelectedOnPage}
                  onChange={(e) => {
                    const next = new Set(selected);
                    if (e.target.checked) allIdsOnPage(rows).forEach((id) => next.add(id));
                    else allIdsOnPage(rows).forEach((id) => next.delete(id));
                    setSelected(next);
                  }} />
              </th>
              {[
                { key: "fullname",     label: "Student",            align: "text-left"   },
                { key: "documents",    label: "Docs",               align: "text-center" },
                { key: "lastActivity", label: "Last Active",        align: "text-left"   },
                { key: "risk",         label: "Recent Pattern",     align: "text-left",  tooltip: "How the student's writing behavior has trended recently"     },
                { key: "prediction",   label: "Trajectory Forecast",align: "text-left",  tooltip: "Model-predicted direction based on keystroke process features" },
              ].map((c) => (
                <th key={c.key}
                  className={`px-4 py-3 ${c.align} text-xs font-semibold text-gray-500 uppercase tracking-wider`}
                  title={c.tooltip}>
                  <button onClick={() => toggleSort(c.key)}
                    className="inline-flex items-center gap-1 hover:text-gray-700 transition-colors"
                    aria-label={`Sort by ${c.label}`}>
                    <span>{c.label}</span>
                    {sortKey === c.key
                      ? sortDir === "asc" ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />
                      : <ChevronDown className="h-3.5 w-3.5 text-gray-300" />}
                  </button>
                </th>
              ))}
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-100">
            {rows.map((student) => (
              <tr key={student.id}
                className={`odd:bg-white even:bg-gray-50/60 hover:bg-emerald-50/50 transition-colors duration-100 ${
                  TREND_STATE_STYLE[student.trendState]?.rowBorder ?? ""
                }`}>

                {/* Checkbox */}
                <td className="pl-6 pr-3 py-3.5">
                  <input type="checkbox" className="rounded border-gray-300 h-4 w-4"
                    checked={selected.has(student.id)}
                    onChange={(e) => {
                      const next = new Set(selected);
                      if (e.target.checked) next.add(student.id); else next.delete(student.id);
                      setSelected(next);
                    }} />
                </td>

                {/* Student — name only, no avatar bubble */}
                <td className="px-4 py-3.5">
                  <Link href={`students?student_id=${student.id}`} className="group">
                    <div className="text-sm font-semibold text-gray-900 group-hover:text-emerald-700 transition-colors leading-tight">
                      {student.fullname}
                    </div>
                    <div className="text-xs text-gray-400 mt-0.5">{student.id}</div>
                  </Link>
                </td>

                {/* Docs */}
                <td className="px-4 py-3.5 text-center">
                  <span className="text-sm font-medium text-gray-700">{student.documents}</span>
                </td>

                {/* Last Active */}
                <td className="px-4 py-3.5">
                  <span className="text-sm text-gray-600">{student.lastActivity}</span>
                </td>

                {/* Recent Pattern */}
                <td className="px-4 py-3.5">
                  <TrendStateBadge trendState={student.trendState} />
                </td>

                {/* Trajectory Forecast + hover-reveal Why? */}
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <PredictionBadge prediction={student.prediction} />
                    <button
                      onClick={() => setTrajectoryModal(student)}
                      className="group/why inline-flex items-center gap-1 rounded-md px-1.5 py-1 text-gray-400 hover:text-emerald-700 hover:bg-emerald-50 transition-all duration-150 shrink-0"
                      title="See why this trajectory was predicted"
                    >
                      <Info className="h-3.5 w-3.5 shrink-0" />
                      <span className="text-xs font-semibold max-w-0 overflow-hidden opacity-0 group-hover/why:max-w-[2rem] group-hover/why:opacity-100 transition-all duration-200 whitespace-nowrap">
                        Why?
                      </span>
                    </button>
                  </div>
                </td>

                {/* Actions */}
                <td className="px-4 py-3.5 text-right">
                  <Link href={`students?student_id=${student.id}`}>
                    <button className="inline-flex items-center gap-1 text-sm font-semibold text-emerald-700 hover:text-emerald-900 transition-colors whitespace-nowrap">
                      View Portfolio
                      <ChevronDown className="h-3.5 w-3.5 rotate-[-90deg]" />
                    </button>
                  </Link>
                </td>
              </tr>
            ))}

            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-sm text-gray-400">
                  No students match your current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ── */}
      <div className="px-6 py-4 border-t border-gray-100 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

        {/* Result range + rows-per-page */}
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <span className="font-medium text-gray-700">
            {total === 0
              ? "No results"
              : `${start + 1}\u2013${Math.min(start + pageSize, total)} of ${total.toLocaleString()}`}
          </span>
          <span className="text-gray-200 select-none">|</span>
          <div className="flex items-center gap-1.5">
            <label className="text-gray-400 text-xs">Rows</label>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              className="h-7 rounded-md border border-gray-200 bg-white px-2 text-xs text-gray-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer"
            >
              {[10, 25, 50, 100].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>
        </div>

        {/* Page number buttons */}
        {totalPages > 1 && (() => {
          const WINDOW = 2;
          const pages = [];
          for (let i = 1; i <= totalPages; i++) {
            if (i === 1 || i === totalPages || (i >= safePage - WINDOW && i <= safePage + WINDOW)) {
              pages.push(i);
            } else if (pages[pages.length - 1] !== "...") {
              pages.push("...");
            }
          }
          return (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={safePage <= 1}
                className="inline-flex items-center justify-center h-8 w-8 rounded-lg border border-gray-200 bg-white text-gray-500 hover:border-emerald-400 hover:text-emerald-700 hover:bg-emerald-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                aria-label="Previous page"
              >&#8249;</button>

              {pages.map((p, idx) =>
                p === "..." ? (
                  <span key={`e-${idx}`} className="inline-flex items-center justify-center h-8 w-8 text-gray-400 text-sm select-none">&hellip;</span>
                ) : (
                  <button key={p} onClick={() => setPage(p)}
                    className={`inline-flex items-center justify-center h-8 w-8 rounded-lg text-sm font-medium transition-colors ${
                      p === safePage
                        ? "bg-emerald-600 text-white border border-emerald-600 shadow-sm"
                        : "border border-gray-200 bg-white text-gray-600 hover:border-emerald-400 hover:text-emerald-700 hover:bg-emerald-50"
                    }`}
                    aria-current={p === safePage ? "page" : undefined}
                  >{p}</button>
                )
              )}

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePage >= totalPages}
                className="inline-flex items-center justify-center h-8 w-8 rounded-lg border border-gray-200 bg-white text-gray-500 hover:border-emerald-400 hover:text-emerald-700 hover:bg-emerald-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors text-sm font-medium"
                aria-label="Next page"
              >&#8250;</button>
            </div>
          );
        })()}
      </div>
    </div>
  );

  /* ── ROOT ─────────────────────────────────── */
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {trajectoryModal && (
        <TrajectoryModal
          student={trajectoryModal}
          onClose={() => setTrajectoryModal(null)}
        />
      )}

      {renderWelcomeBanner()}

      <div className="px-6 pt-6 pb-2 space-y-0">
        {hasErrors ? renderError() : showLoading ? renderLoading() : (
          <>
            {renderHeaderBar()}
            {renderTable()}
          </>
        )}
      </div>
    </div>
  );
}
