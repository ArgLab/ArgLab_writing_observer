"use client";

import React, { useMemo, useState } from "react";
import {
  X,
  Calendar,
  Search,
  ChevronDown,
  Info,
  Maximize2,
  GitCompareArrows,
  Clock,
  FileText,
  AlertCircle,
  CheckCircle2,
  BookOpen,
  Pencil,
  Clipboard,
} from "lucide-react";

import { SingleEssayModal } from "./SingleEssayModel";

/* =========================================================
   RUBRIC ALIGNMENT
========================================================= */
const METRIC_TEACHER_DESC = {
  academic_language:            "Words that signal academic or formal register (e.g. 'analyze', 'demonstrate')",
  informal_language:            "Casual or conversational words that may not suit the assignment genre",
  latinate_words:               "Longer, Latin-derived words often associated with sophisticated vocabulary",
  opinion_words:                "Words that express the writer's personal stance or judgment",
  emotion_words:                "Words that convey feeling — useful in narrative, potentially limiting in argument",
  argument_words:               "Words that signal reasoning and argumentation (e.g. 'because', 'therefore')",
  explicit_argument:            "Phrases that make the writer's claim or position directly visible to the reader",
  statements_of_opinion:        "Sentences where the writer expresses a personal view rather than a fact",
  statements_of_fact:           "Sentences that assert something as objectively true",
  transition_words:             "Words and phrases that connect ideas within and across sentences",
  positive_transition_words:    "Transitions that add or reinforce ('also', 'furthermore', 'in addition')",
  contrastive_transition_words: "Transitions that contrast ideas ('however', 'on the other hand')",
  conditional_transition_words: "Transitions that show conditions ('if', 'unless', 'provided that')",
  consequential_transition_words:"Transitions that show cause-effect ('therefore', 'as a result')",
  citations:                    "Moments where the student references an outside source",
  attributions:                 "Phrases that credit a speaker or source ('According to...', 'Smith argues...')",
  quoted_words:                 "Exact words taken directly from a source and placed in quotation marks",
  information_sources:          "Overall use of external information and evidence",
  sentences:                    "Total number of sentences — a basic measure of text length and density",
  paragraphs:                   "Total number of paragraphs — reflects structural organization",
  simple_sentences:             "Sentences with a single main clause — easier to read but less complex",
  complex_sentences:            "Sentences with a main clause and one or more subordinate clauses",
  compound_sentences:           "Sentences joining two independent clauses — shows coordination ability",
  compound_complex_sentences:   "Sentences combining compound and complex structures — highest complexity",
  polysyllabic_words:           "Longer words (3+ syllables) — a rough indicator of vocabulary complexity",
  low_frequency_words:          "Uncommon words not found in everyday language — signals advanced vocabulary",
  positive_tone:                "Language that carries a generally optimistic or affirmative feeling",
  negative_tone:                "Language that carries a critical, pessimistic, or opposing feeling",
  concrete_details:             "Specific, tangible examples rather than vague or abstract statements",
  main_idea_sentences:          "Sentences that introduce or summarize a central point",
  supporting_idea_sentences:    "Sentences that develop or expand on a main idea",
  supporting_detail_sentences:  "Sentences that provide specific evidence or examples",
  direct_speech_verbs:          "Verbs that introduce direct dialogue ('said', 'asked', 'replied')",
  indirect_speech:              "Reported speech — summarizing what someone said rather than quoting directly",
  character_trait_words:        "Words describing character qualities — important in narrative writing",
  explicit_claims:              "Direct statements of position or argument",
  social_awareness:             "Language indicating awareness of community, society, or broader context",
};

const ASSIGNMENT_TYPE_COLORS = {
  Narrative:     { bg: "bg-violet-50",  text: "text-violet-700",  ring: "ring-violet-200",  dot: "bg-violet-400" },
  Argumentative: { bg: "bg-amber-50",   text: "text-amber-700",   ring: "ring-amber-200",   dot: "bg-amber-400" },
  Analytical:    { bg: "bg-blue-50",    text: "text-blue-700",    ring: "ring-blue-200",    dot: "bg-blue-400" },
  Expository:    { bg: "bg-teal-50",    text: "text-teal-700",    ring: "ring-teal-200",    dot: "bg-teal-400" },
  Document:      { bg: "bg-emerald-50", text: "text-emerald-700", ring: "ring-emerald-200", dot: "bg-emerald-400" },
  Other:         { bg: "bg-gray-50",    text: "text-gray-600",    ring: "ring-gray-200",    dot: "bg-gray-400" },
};

/* =========================================================
   SUB-COMPONENTS
========================================================= */

function AssignmentTypeBadge({ type }) {
  const colors = ASSIGNMENT_TYPE_COLORS[type] || ASSIGNMENT_TYPE_COLORS["Document"];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold
      ring-1 ring-inset ${colors.bg} ${colors.text} ${colors.ring}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${colors.dot}`} />
      {type}
    </span>
  );
}

function ComparisonTypeMismatchBanner({ typeA, typeB }) {
  if (!typeA || !typeB || typeA === typeB || typeA === "Document" || typeB === "Document") return null;
  return (
    <div className="flex items-start gap-2 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 mb-4 text-sm text-amber-800">
      <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
      <div>
        <span className="font-semibold">Different assignment types selected.</span>{" "}
        You are comparing a <strong>{typeA}</strong> essay with an <strong>{typeB}</strong> essay.
        For valid comparisons, select essays of the same type.{" "}
        <span className="text-amber-600 italic">
          Language-level metrics (word choice, transitions) are most useful across types;
          structural metrics are most meaningful within the same type.
        </span>
      </div>
    </div>
  );
}

function MetricTooltip({ metricId, children }) {
  const [show, setShow] = useState(false);
  const desc = METRIC_TEACHER_DESC[metricId];
  if (!desc) return <>{children}</>;
  return (
    <span className="relative inline-flex items-center gap-1"
      onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      {children}
      <Info className="h-3.5 w-3.5 text-gray-400 cursor-help" />
      {show && (
        <span className="absolute z-50 bottom-full left-0 mb-2 w-64 rounded-lg border border-gray-200
          bg-white shadow-lg px-3 py-2 text-xs text-gray-700 leading-relaxed pointer-events-none">
          {desc}
        </span>
      )}
    </span>
  );
}

const SkeletonCard = () => (
  <div className="bg-white rounded-2xl border border-gray-200 shadow-sm animate-pulse">
    <div className="p-6 h-72 flex flex-col gap-3">
      <div className="h-5 w-40 rounded bg-gray-200" />
      <div className="h-4 w-24 rounded bg-gray-200" />
      <div className="flex-1 space-y-2">
        <div className="h-3.5 w-full rounded bg-gray-200" />
        <div className="h-3.5 w-11/12 rounded bg-gray-200" />
        <div className="h-3.5 w-10/12 rounded bg-gray-200" />
      </div>
      <div className="flex gap-2">
        <div className="h-5 w-20 rounded-full bg-gray-200" />
        <div className="h-5 w-16 rounded-full bg-gray-200" />
      </div>
    </div>
  </div>
);

/* =========================================================
   HELPERS
========================================================= */
function humanizeDocId(docId, index) {
  if (!docId) return "Document";
  if (/fake-google-doc|doc-id/i.test(docId)) return `Essay ${index ?? ""}`.trim();
  return String(docId).replace(/[-_]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function inferAssignmentType(tags, text) {
  if (Array.isArray(tags)) {
    const known = ["Narrative","Argumentative","Analytical","Expository"];
    const match = tags.find((t) => known.includes(t));
    if (match) return match;
  }
  const t = (text || "").toLowerCase();
  if (/argue|claim|thesis|evidence|counterargument/.test(t)) return "Argumentative";
  if (/analyze|analysis|examine|compare|contrast/.test(t)) return "Analytical";
  if (/once upon|story|character|plot|setting/.test(t)) return "Narrative";
  if (/explain|describe|inform|definition/.test(t)) return "Expository";
  return "Document";
}

const AVG_WORD_LENGTH_CHARS = 5;
function charsToWords(chars) { return Math.round(chars / AVG_WORD_LENGTH_CHARS); }

/* =========================================================
   EXPAND BUTTON WITH TOOLTIP
========================================================= */
function ExpandButton({ onClick }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative shrink-0">
      <button
        className="p-1.5 rounded-lg hover:bg-gray-100 transition"
        aria-label="View essay details"
        onClick={onClick}
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
      >
        <Maximize2 className="h-4 w-4 text-gray-400 group-hover:text-gray-600" />
      </button>
      {show && (
        <span className="absolute z-50 bottom-full right-0 mb-2 whitespace-nowrap rounded-lg
          bg-gray-900 px-2.5 py-1.5 text-xs text-white shadow-lg pointer-events-none">
          Open essay detail
          <span className="absolute top-full right-3 border-4 border-transparent border-t-gray-900" />
        </span>
      )}
    </div>
  );
}

/* =========================================================
   MAIN COMPONENT
========================================================= */
export default function StudentDetailCompare({
  groupedEssays,
  studentId,
  selectedEssays,
  setSelectedEssays,
  handleEssaySelect,
  cardsPerRow,
  setCardsPerRow,
  sortBy,
  setSortBy,
  search,
  setSearch,
  filterTags,
  setFilterTags,
  tagOpen,
  setTagOpen,
  tagQuery,
  setTagQuery,
  tagRef,
  baseTags,
  clearFilters,
  isAnyFilter,
  getGridCols,
  getGradeColor,
  strengthAndFocusForEssay,
  loDocData,
  loDocErrors,
  loDocConnection,
  documentIDS,
  assignmentTypeFilter,
  AssignmentTypeBadge: ExternalBadge,
  EffortPill,
  pasteStatsByDoc,
}) {
  const safeGetGridCols = typeof getGridCols === "function" ? getGridCols : () => "grid-cols-3";
  const safeHandleEssaySelect = typeof handleEssaySelect === "function" ? handleEssaySelect : () => {};
  const safeSetSelectedEssays = typeof setSelectedEssays === "function" ? setSelectedEssays : () => {};
  const safeStrengthAndFocus = typeof strengthAndFocusForEssay === "function"
    ? strengthAndFocusForEssay : () => ({ strength: null, focus: null });
  const safePasteStats = pasteStatsByDoc ?? {};

  const [openEssay, setOpenEssay] = useState(null);

  const loStudentID = String(studentId);
  const docsObj = loDocData?.students?.[loStudentID]?.documents || {};
  const expectedDocIds = Array.isArray(documentIDS) ? documentIDS : [];

  const hasAllExpectedDocs =
    expectedDocIds.length > 0 &&
    expectedDocIds.every((id) => {
      const doc = docsObj?.[id];
      return doc && typeof doc === "object" && typeof doc.text === "string" && doc.text.length > 0;
    });

  const connectionLoading = !!(loDocConnection &&
    (loDocConnection.loading || loDocConnection.isLoading || loDocConnection.status === "loading"));

  const isDocsLoading =
    connectionLoading ||
    !loDocData ||
    !loDocData?.students?.[loStudentID] ||
    (expectedDocIds.length > 0 && !hasAllExpectedDocs);

  const isDocsEmpty = !isDocsLoading && Object.keys(docsObj || {}).length === 0;

  const docList = useMemo(() => {
    return Object.entries(docsObj || {}).map(([docId, doc], index) => {
      const text = typeof doc?.text === "string" ? doc.text : "";
      const words = text ? text.trim().split(/\s+/).filter(Boolean).length : 0;
      let dateISO = doc?.dateISO || doc?.date_iso || doc?.date || doc?.submitted_at || doc?.created_at || "";
      if (!dateISO && doc?.last_access != null) {
        const la = Number(doc.last_access);
        if (Number.isFinite(la) && la > 0) { const ms = la > 1e12 ? la : la * 1000; dateISO = new Date(ms).toISOString(); }
      }
      const tagsFromDoc = Array.isArray(doc?.tags) ? doc.tags : Array.isArray(doc?.meta?.tags) ? doc.meta.tags : ["Document"];
      const assignmentType = inferAssignmentType(tagsFromDoc, text);
      const humanTitle = doc?.title || humanizeDocId(docId, index + 1);

      // Read time_on_task directly from doc node (real WS field name).
      // Fall back to time_on_task_mins for backwards compatibility.
      const timeOnTaskMins =
        typeof doc?.time_on_task === "number"     ? doc.time_on_task     :
        typeof doc?.time_on_task_mins === "number" ? doc.time_on_task_mins :
        null;

      const editCount = doc?.edit_count ?? null;

      return {
        id: docId, title: humanTitle,
        date: dateISO ? new Date(dateISO).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "",
        dateISO: dateISO ? new Date(dateISO).toISOString() : "",
        words, grade: doc?.grade != null ? String(doc.grade) : "",
        preview: text, tags: tagsFromDoc.map(String),
        assignmentType, timeOnTaskMins, editCount,
        _raw: doc, _index: index + 1,
      };
    });
  }, [docsObj]);

  const allDocIds = useMemo(() => docList.map((d) => d.id).filter(Boolean), [docList]);
  const docMetaById = useMemo(() => {
    const m = new Map();
    for (const d of docList) m.set(String(d.id), d);
    return m;
  }, [docList]);

  const STANDARD_GENRES = ["Narrative", "Argumentative", "Analytical", "Expository", "Other", "Document"];
  const safeBaseTags = useMemo(() => {
    const presentInDocs = new Set(docList.map((d) => d.assignmentType));
    const standard = STANDARD_GENRES.filter((g) => presentInDocs.has(g));
    const extras = Array.from(presentInDocs).filter((g) => !STANDARD_GENRES.includes(g)).sort();
    return [...standard, ...extras];
  }, [docList]);

  const filteredDocs = useMemo(() => {
    const q = String(search || "").trim().toLowerCase();
    const activeTags = Array.isArray(filterTags) ? filterTags : [];
    return (docList || [])
      .filter((d) => {
        if (activeTags.length > 0) {
          const dtags = Array.isArray(d?.tags) ? d.tags.map(String) : [];
          if (!activeTags.every((t) => dtags.includes(t))) return false;
        }
        if (q) {
          const hay = [d?.title || "", d?.preview || "", Array.isArray(d?.tags) ? d.tags.join(" ") : "", d?.grade || "", d?.date || ""].join(" ").toLowerCase();
          if (!hay.includes(q)) return false;
        }
        return true;
      })
      .sort((a, b) => {
        const mode = String(sortBy || "date");
        if (mode === "words") return (Number(b.words) || 0) - (Number(a.words) || 0);
        if (mode === "title") return String(a.title || "").localeCompare(String(b.title || ""));
        if (mode === "grade") return (Number(b.grade) || 0) - (Number(a.grade) || 0);
        const ad = a?.dateISO ? new Date(a.dateISO).getTime() : 0;
        const bd = b?.dateISO ? new Date(b.dateISO).getTime() : 0;
        return bd - ad;
      });
  }, [docList, search, filterTags, sortBy]);

  const groupedDocs = useMemo(() => {
    return filteredDocs.reduce((acc, d) => {
      const key = d.dateISO ? new Date(d.dateISO).toLocaleString("en-US", { month: "long", year: "numeric" }) : "Undated";
      (acc[key] ||= []).push(d);
      return acc;
    }, {});
  }, [filteredDocs]);

  const selectedMeta = (Array.isArray(selectedEssays) ? selectedEssays : []).map((id) => docMetaById.get(String(id))).filter(Boolean);
  const typeA = selectedMeta[0]?.assignmentType;
  const typeB = selectedMeta[1]?.assignmentType;

  return (
    <div className="flex flex-col min-h-0">
      {isDocsLoading ? (
        <div className={`mt-4 grid ${safeGetGridCols()} gap-4`}>
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : isDocsEmpty ? (
        <div className="mt-6 p-8 bg-white border border-gray-200 rounded-2xl text-center">
          <FileText className="h-8 w-8 text-gray-300 mx-auto mb-3" />
          <div className="text-gray-900 font-semibold">No documents yet</div>
          <div className="text-sm text-gray-500 mt-1">We didn't find any documents for this student.</div>
        </div>
      ) : (
        <>
          {/* Toolbar */}
          <div className="mb-5 p-3 bg-white border border-gray-200 rounded-2xl shadow-sm">
            <div className="flex flex-wrap items-center gap-3">

              {/* Genre filter */}
              <div className="relative" ref={tagRef}>
                <button
                  onClick={(e) => { e.stopPropagation(); typeof setTagOpen === "function" && setTagOpen((v) => !v); }}
                  className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 transition"
                >
                  <BookOpen className="h-4 w-4 text-gray-500" />
                  Genre
                  {Array.isArray(filterTags) && filterTags.length > 0 && (
                    <span className="text-emerald-700 font-semibold">({filterTags.length})</span>
                  )}
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                </button>
                {tagOpen && (
                  <div className="absolute z-20 mt-2 w-56 rounded-xl border border-gray-200 bg-white shadow-lg p-2">
                    <div className="flex items-center gap-2 px-2 py-1.5 mb-2 rounded-lg bg-gray-50">
                      <Search className="h-4 w-4 text-gray-400" />
                      <input
                        placeholder="Search genres..."
                        value={tagQuery || ""}
                        onChange={(e) => typeof setTagQuery === "function" && setTagQuery(e.target.value)}
                        className="w-full bg-transparent text-sm outline-none"
                      />
                    </div>
                    <div className="max-h-48 overflow-auto">
                      {safeBaseTags
                        .filter((t) => String(t).toLowerCase().includes(String(tagQuery || "").toLowerCase()))
                        .map((t) => (
                          <label key={t} className="flex items-center gap-2 px-2 py-1.5 text-sm hover:bg-gray-50 rounded-lg cursor-pointer">
                            <input type="checkbox"
                              checked={Array.isArray(filterTags) ? filterTags.includes(t) : false}
                              onChange={() => {
                                if (typeof setFilterTags !== "function") return;
                                setFilterTags((prev) => {
                                  const p = Array.isArray(prev) ? prev : [];
                                  return p.includes(t) ? p.filter((x) => x !== t) : [...p, t];
                                });
                              }}
                              className="accent-emerald-600 h-4 w-4"
                            />
                            <AssignmentTypeBadge type={t} />
                          </label>
                        ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  value={search || ""}
                  onChange={(e) => typeof setSearch === "function" && setSearch(e.target.value)}
                  placeholder="Search title, text..."
                  className="pl-8 pr-3 py-2 border border-gray-300 rounded-lg text-sm bg-white w-56 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex-1" />

              {/* Sort */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Sort by:</span>
                <select
                  value={sortBy || "date"}
                  onChange={(e) => typeof setSortBy === "function" && setSortBy(e.target.value)}
                  className="pl-3 pr-8 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 appearance-none bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2212%22%20height%3D%2212%22%20viewBox%3D%220%200%2012%2012%22%3E%3Cpath%20fill%3D%22%236b7280%22%20d%3D%22M6%208L1%203h10z%22%2F%3E%3C%2Fsvg%3E')] bg-no-repeat bg-[right_10px_center]"
                >
                  <option value="date">Date</option>
                  <option value="grade">Grade</option>
                  <option value="words">Word Count</option>
                  <option value="title">Title</option>
                </select>
              </div>

              {/* Cards per row */}
              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                {[1,2,3,4].map((n) => (
                  <button key={n}
                    onClick={() => typeof setCardsPerRow === "function" && setCardsPerRow(n)}
                    className={`w-7 h-7 text-xs rounded-md font-semibold transition ${
                      (cardsPerRow ?? 3) === n ? "bg-white text-emerald-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
                    }`}
                  >{n}</button>
                ))}
              </div>
            </div>

            {/* Active filter chips */}
            {isAnyFilter && (
              <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-100">
                {(Array.isArray(filterTags) ? filterTags : []).map((t) => (
                  <span key={`tag-${t}`} className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-emerald-50 text-emerald-800 rounded-full ring-1 ring-emerald-200">
                    {t}
                    <button className="ml-0.5 hover:text-emerald-600"
                      onClick={() => typeof setFilterTags === "function" && setFilterTags((prev) => Array.isArray(prev) ? prev.filter((x) => x !== t) : [])}
                      aria-label={`Remove ${t}`}>
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
                {String(search || "").trim().length > 0 && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                    "{search}"
                    <button onClick={() => typeof setSearch === "function" && setSearch("")}><X className="h-3 w-3" /></button>
                  </span>
                )}
                <button onClick={() => typeof clearFilters === "function" && clearFilters()}
                  className="text-xs text-gray-500 underline underline-offset-2 hover:text-gray-800 ml-1">
                  Clear all
                </button>
              </div>
            )}
          </div>

          {/* Apples-to-apples warning */}
          <ComparisonTypeMismatchBanner typeA={typeA} typeB={typeB} />

          {filteredDocs.length === 0 && (
            <div className="mt-6 p-8 bg-white border border-gray-200 rounded-2xl text-center">
              <Search className="h-8 w-8 text-gray-300 mx-auto mb-3" />
              <div className="text-gray-900 font-semibold">No matching documents</div>
              <div className="text-sm text-gray-500 mt-1">Try adjusting your search or removing filters.</div>
            </div>
          )}

          {/* Grouped essay cards */}
          {Object.entries(groupedDocs).map(([category, list], index) => {
            const wordsAvg = Math.round(list.reduce((s, e) => s + (Number(e.words) || 0), 0) / Math.max(1, list.length));

            return (
              <div key={category} className="mb-10">
                {index !== 0 && <hr className="border-t border-gray-100 mb-6" />}

                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold text-gray-900">{category}</h2>
                  <div className="text-sm text-gray-500">
                    {list.length} {list.length === 1 ? "essay" : "essays"} · avg {wordsAvg.toLocaleString()} words
                  </div>
                </div>

                <div className={`grid ${safeGetGridCols()} gap-4`}>
                  {list.map((essay) => {
                    const isSelected = Array.isArray(selectedEssays) && selectedEssays.includes(essay.id);
                    const { strength, focus } = safeStrengthAndFocus(essay);

                    // Paste stats from pasteStatsByDoc (populated by StudentDetail from merged doc node)
                    const pasteEntry = safePasteStats[essay.id] ?? {};
                    // largePasteCount: prefer the explicit field, fall back to pasteCount for compatibility
                    const largePasteCount = pasteEntry.largePasteCount ?? pasteEntry.pasteCount ?? 0;
                    const totalPasteChars = pasteEntry.totalPasteChars ?? pasteEntry.pasteChars ?? 0;
                    const pasteWords = charsToWords(totalPasteChars);
                    const hasPastes = largePasteCount > 0;

                    // Time on task: prefer from essay object (set by buildEssaysFromDocs reading time_on_task),
                    // fall back to pasteStatsByDoc entry which also carries timeOnTask
                    const timeOnTask = essay.timeOnTaskMins ?? pasteEntry.timeOnTask ?? null;

                    return (
                      <div
                        key={essay.id}
                        onClick={() => safeHandleEssaySelect(essay.id)}
                        className={`group relative bg-white rounded-2xl transition-all duration-150 cursor-pointer
                          shadow-sm hover:shadow-md flex flex-col ${
                          isSelected
                            ? "border-2 border-emerald-500 shadow-emerald-100 shadow-md"
                            : "border border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <div className="p-5 flex flex-col flex-1 gap-3">

                          {/* Header row */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-start gap-2.5">
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => safeHandleEssaySelect(essay.id)}
                                onClick={(e) => e.stopPropagation()}
                                className="mt-0.5 h-4 w-4 accent-emerald-600 shrink-0"
                                aria-label={`Select ${essay.title}`}
                              />
                              <h3 className="font-bold text-gray-900 leading-snug text-base">{essay.title}</h3>
                            </div>
                            <ExpandButton
                              onClick={(e) => {
                                e.stopPropagation();
                                const meta = docMetaById.get(String(essay.id));
                                setOpenEssay({
                                  docId: essay.id,
                                  title: meta?.title || essay.title || "Document",
                                  docIndex: meta?._index || null,
                                  grade: meta?.grade || essay.grade || "",
                                  words: Number(meta?.words ?? essay.words ?? 0),
                                  date: meta?.date || essay.date || "",
                                });
                              }}
                            />
                          </div>

                          {/* Meta row: genre badge, date, word count, time on task */}
                          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                            <AssignmentTypeBadge type={essay.assignmentType} />
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3.5 w-3.5" />
                              {essay.date || "Unknown date"}
                            </span>
                            <span className="flex items-center gap-1">
                              <FileText className="h-3.5 w-3.5" />
                              {(Number(essay.words) || 0).toLocaleString()} words
                            </span>
                            {timeOnTask != null && (
                              <span
                                className="inline-flex items-center gap-1 font-semibold text-emerald-700 bg-emerald-50 ring-1 ring-inset ring-emerald-200 rounded-full px-2 py-0.5"
                                title="Time spent actively writing this essay"
                              >
                                <Clock className="h-3 w-3 text-emerald-500" />
                                {Math.round(timeOnTask)} min
                              </span>
                            )}
                          </div>

                          {/* Preview */}
                          <p className="text-sm text-gray-600 leading-relaxed line-clamp-4 flex-1">{essay.preview || ""}</p>

                          {/* Strength / Focus chips */}
                          {(strength || focus) && (
                            <div className="flex flex-wrap gap-1.5">
                              {strength && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-800 text-xs rounded-full ring-1 ring-emerald-200">
                                  <CheckCircle2 className="h-3 w-3" />
                                  {String(strength.label || "").split("(")[0].trim()}
                                </span>
                              )}
                              {focus && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-50 text-amber-800 text-xs rounded-full ring-1 ring-amber-200">
                                  <AlertCircle className="h-3 w-3" />
                                  {String(focus.label || "").split("(")[0].trim()}
                                </span>
                              )}
                            </div>
                          )}

                          {/* Large paste signal — always shown */}
                          <div className={`flex items-center gap-1.5 rounded-lg px-3 py-2 border ${
                            hasPastes
                              ? "bg-amber-50 border-amber-200"
                              : "bg-gray-50 border-gray-200"
                          }`}>
                            <Clipboard className={`h-3.5 w-3.5 shrink-0 ${hasPastes ? "text-amber-500" : "text-gray-400"}`} />
                            <p className={`text-xs leading-snug ${hasPastes ? "text-amber-800" : "text-gray-500"}`}>
                              <span className="font-semibold">
                                {largePasteCount} large {largePasteCount === 1 ? "paste" : "pastes"}
                              </span>
                              {hasPastes && (
                                <>
                                  {" "}(~{pasteWords} words).{" "}
                                  <button
                                    className="underline underline-offset-2 hover:text-amber-900 font-medium"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      const meta = docMetaById.get(String(essay.id));
                                      setOpenEssay({
                                        docId: essay.id,
                                        title: meta?.title || essay.title || "Document",
                                        docIndex: meta?._index || null,
                                        grade: meta?.grade || essay.grade || "",
                                        words: Number(meta?.words ?? essay.words ?? 0),
                                        date: meta?.date || essay.date || "",
                                      });
                                    }}
                                  >
                                    Open essay for details
                                  </button>
                                </>
                              )}
                            </p>
                          </div>
                        </div>

                        {/* Selected footer */}
                        {isSelected && (
                          <div className="px-5 py-2 border-t border-emerald-100 bg-emerald-50 rounded-b-2xl flex items-center gap-1.5 text-xs text-emerald-700 font-semibold">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Selected for comparison
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </>
      )}

      {/* Bottom bar */}
      <div className="fixed bottom-0 left-0 right-0 z-40 flex flex-col shadow-[0_-4px_20px_rgba(0,0,0,0.12)]">

        {Array.isArray(selectedEssays) && selectedEssays.length < 2 && (
          <div className="w-full bg-slate-50 border-t border-slate-200 px-6 py-2.5">
            <div className="flex items-center gap-2 text-slate-600 text-sm">
              <Info className="h-4 w-4 shrink-0" />
              Select up to 2 essays to compare them side-by-side. For best results, choose essays of the same type (e.g. two Argumentative essays).
            </div>
          </div>
        )}

        <div className="w-full bg-gray-900 text-white px-6 py-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="flex items-center gap-2 shrink-0">
                <div className="flex gap-1">
                  {[0,1].map((i) => (
                    <div key={i} className={`h-2 w-8 rounded-full transition-colors ${
                      (Array.isArray(selectedEssays) ? selectedEssays.length : 0) > i
                        ? "bg-emerald-400" : "bg-white/20"
                    }`} />
                  ))}
                </div>
                <span className="text-sm text-white/70">
                  {Array.isArray(selectedEssays) ? selectedEssays.length : 0}/2
                </span>
              </div>

              <div className="flex items-center gap-2 min-w-0">
                {[0,1].map((i) => {
                  const id = Array.isArray(selectedEssays) ? selectedEssays[i] : undefined;
                  const meta = id ? docMetaById.get(String(id)) : null;
                  const displayName = meta?.title || (id ? humanizeDocId(id, meta?._index) : null);
                  const type = meta?.assignmentType;
                  const typeColors = type ? ASSIGNMENT_TYPE_COLORS[type] : null;
                  return (
                    <div key={i} className={`h-8 px-3 rounded-full flex items-center gap-2 max-w-[200px]
                      text-xs font-medium truncate transition-all ${
                      id ? "bg-white/15 text-white" : "bg-white/5 text-white/30"
                    }`}>
                      {type && typeColors && <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${typeColors.dot}`} />}
                      <span className="truncate">{displayName || `Essay ${i + 1}`}</span>
                      {id && (
                        <button
                          className="shrink-0 hover:text-red-300 transition-colors"
                          onClick={() => safeSetSelectedEssays((prev) => Array.isArray(prev) ? prev.filter((x) => x !== id) : [])}
                          aria-label="Remove from selection"
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>

              {Array.isArray(selectedEssays) && selectedEssays.length > 0 && (
                <button onClick={() => safeSetSelectedEssays([])}
                  className="text-xs text-white/50 hover:text-white/80 underline underline-offset-2 shrink-0">
                  Clear
                </button>
              )}
            </div>

            <button
              onClick={() => {
                const ids = Array.isArray(selectedEssays) ? selectedEssays.join(",") : "";
                window.location.assign(`students/compare?ids=${ids}&student_id=${studentId}`);
              }}
              className={`flex items-center gap-2 px-5 py-2 rounded-xl font-semibold text-sm transition-all shrink-0 ${
                Array.isArray(selectedEssays) && selectedEssays.length >= 2
                  ? "bg-emerald-500 text-white hover:bg-emerald-400 shadow-lg shadow-emerald-900/30"
                  : "bg-white/10 text-white/40 cursor-not-allowed"
              }`}
              disabled={!(Array.isArray(selectedEssays) && selectedEssays.length >= 2)}
            >
              <GitCompareArrows className="h-4 w-4" />
              Compare Essays
            </button>
          </div>
        </div>
      </div>

      <div className="h-28" />

      {openEssay?.docId && (
        <SingleEssayModal
          studentKey={loStudentID}
          docId={openEssay.docId}
          docIds={allDocIds}
          docTitle={openEssay.title}
          docIndex={openEssay.docIndex}
          initialWords={openEssay.words}
          subtitleDate={openEssay.date}
          onClose={() => setOpenEssay(null)}
          initialDocsObj={docsObj}
        />
      )}
    </div>
  );
}
