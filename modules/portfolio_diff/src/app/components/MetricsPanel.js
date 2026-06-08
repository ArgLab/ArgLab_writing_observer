"use client";

import {
  ArrowLeftRight,
  ChevronDown,
  ChevronUp,
  FileText,
  Gauge,
  Languages,
  ListCollapse,
  MessageSquareText,
  MessagesSquare,
  Quote,
  Speech,
  Trash2,
  Users,
  WholeWord
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

/* ── deterministic seed (for highlight swatches) ── */
const seedFrom = (s) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = ((h ^ s.charCodeAt(i)) * 16777619) >>> 0;
  return h >>> 0;
};
const HIGHLIGHT_CLASSES = [
  "bg-emerald-200/70","bg-sky-200/70","bg-amber-200/70","bg-rose-200/70",
  "bg-indigo-200/70","bg-lime-200/70","bg-violet-200/60","bg-teal-200/70",
  "bg-fuchsia-200/60","bg-orange-200/70",
];
const highlightClassForMetric = (id) =>
  HIGHLIGHT_CLASSES[seedFrom(id || "metric") % HIGHLIGHT_CLASSES.length];

/* ══════════════════════════════════════════════════════════════
   6+1 TRAIT MAPPING
   Every metric is mapped to both its internal category AND its
   6+1 Trait rubric label so both grouping modes work from one
   source of truth.
   ══════════════════════════════════════════════════════════════ */
const TRAIT_FOR_CATEGORY = {
  language:          "Word Choice",
  argumentation:     "Ideas & Content",
  statements:        "Ideas & Content",
  transitions:       "Organization",
  pos:               "Sentence Fluency",
  sentence_type:     "Sentence Fluency",
  source_information:"Ideas & Content",
  dialogue:          "Voice",
  tone:              "Voice",
  details:           "Ideas & Content",
  other:             "Conventions",
};

// Canonical display label for each internal category key
const CATEGORY_LABELS = {
  language:          "Language",
  argumentation:     "Argumentation",
  statements:        "Statements",
  transitions:       "Transition Words",
  pos:               "Parts of Speech",
  sentence_type:     "Sentence Types",
  source_information:"Source Information",
  dialogue:          "Dialogue",
  tone:              "Tone",
  details:           "Details",
  other:             "Other",
};

// Canonical trait order for 6+1 grouping
const TRAIT_ORDER = [
  "Ideas & Content",
  "Organization",
  "Voice",
  "Word Choice",
  "Sentence Fluency",
  "Conventions",
];

const TRAIT_STYLE = {
  "Ideas & Content":  { dot:"bg-amber-400",  header:"bg-amber-50 text-amber-800 border-amber-200",  badge:"bg-amber-50 text-amber-700 ring-amber-200" },
  "Organization":     { dot:"bg-blue-400",   header:"bg-blue-50 text-blue-800 border-blue-200",     badge:"bg-blue-50 text-blue-700 ring-blue-200" },
  "Voice":            { dot:"bg-rose-400",   header:"bg-rose-50 text-rose-800 border-rose-200",     badge:"bg-rose-50 text-rose-700 ring-rose-200" },
  "Word Choice":      { dot:"bg-violet-400", header:"bg-violet-50 text-violet-800 border-violet-200",badge:"bg-violet-50 text-violet-700 ring-violet-200" },
  "Sentence Fluency": { dot:"bg-teal-400",   header:"bg-teal-50 text-teal-800 border-teal-200",     badge:"bg-teal-50 text-teal-700 ring-teal-200" },
  "Conventions":      { dot:"bg-slate-400",  header:"bg-slate-50 text-slate-800 border-slate-200",  badge:"bg-slate-50 text-slate-700 ring-slate-200" },
};

const iconForCategory = (catKey) => {
  const map = {
    language: Languages, argumentation: MessagesSquare, statements: MessageSquareText,
    transitions: ArrowLeftRight, pos: Speech, sentence_type: WholeWord,
    source_information: Quote, dialogue: Users, tone: Gauge, details: ListCollapse,
  };
  return map[catKey] || FileText;
};

/* ── full metric definitions ── */
const mk = (id, title, catKey, fn, desc) => ({
  id, title,
  icon: iconForCategory(catKey),
  categoryKey: catKey,
  category: CATEGORY_LABELS[catKey],
  trait: TRAIT_FOR_CATEGORY[catKey],
  function: fn,
  desc,
});

const METRIC_DEFS = [
  mk("academic_language",    "Academic Language",    "language",          "percent","Percent of tokens flagged academic"),
  mk("informal_language",    "Informal Language",    "language",          "percent","Percent of tokens flagged informal"),
  mk("latinate_words",       "Latinate Words",       "language",          "percent","Percent of tokens flagged latinate"),
  mk("opinion_words",        "Opinion Words",        "language",          "total",  "Total opinion-word signals"),
  mk("emotion_words",        "Emotion Words",        "language",          "percent","Percent emotion words"),
  mk("argument_words",       "Argument Words",       "argumentation",     "percent","Percent argument words"),
  mk("explicit_argument",    "Explicit Argument",    "argumentation",     "percent","Percent explicit argument markers"),
  mk("statements_of_opinion","Statements of Opinion","statements",        "percent","Percent of sentences classified as opinion"),
  mk("statements_of_fact",   "Statements of Fact",   "statements",        "percent","Percent of sentences classified as fact"),
  mk("transition_words",     "Transition Words",     "transitions",       "counts", "Transition counts (by type)"),
  mk("positive_transition_words",     "Positive Transitions",      "transitions","total","Total positive transitions"),
  mk("conditional_transition_words",  "Conditional Transitions",   "transitions","total","Total conditional transitions"),
  mk("consequential_transition_words","Consequential Transitions",  "transitions","total","Total consequential transitions"),
  mk("contrastive_transition_words",  "Contrastive Transitions",   "transitions","total","Total contrastive transitions"),
  mk("counterpoint_transition_words", "Counterpoint Transitions",  "transitions","total","Total counterpoint transitions"),
  mk("comparative_transition_words",  "Comparative Transitions",   "transitions","total","Total comparative transitions"),
  mk("cross_referential_transition_words","Cross-Referential Transitions","transitions","total","Total cross-referential transitions"),
  mk("illustrative_transition_words", "Illustrative Transitions",  "transitions","total","Total illustrative transitions"),
  mk("negative_transition_words",     "Negative Transitions",      "transitions","total","Total negative transitions"),
  mk("emphatic_transition_words",     "Emphatic Transitions",      "transitions","total","Total emphatic transitions"),
  mk("evenidentiary_transition_words","Evidentiary Transitions",   "transitions","total","Total evidentiary transitions"),
  mk("general_transition_words",      "General Transitions",       "transitions","total","Total general transitions"),
  mk("ordinal_transition_words",      "Ordinal Transitions",       "transitions","total","Total ordinal transitions"),
  mk("purposive_transition_words",    "Purposive Transitions",     "transitions","total","Total purposive transitions"),
  mk("periphrastic_transition_words", "Periphrastic Transitions",  "transitions","total","Total periphrastic transitions"),
  mk("hypothetical_transition_words", "Hypothetical Transitions",  "transitions","total","Total hypothetical transitions"),
  mk("summative_transition_words",    "Summative Transitions",     "transitions","total","Total summative transitions"),
  mk("introductory_transition_words", "Introductory Transitions",  "transitions","total","Total introductory transitions"),
  mk("adjectives",               "Adjectives",                "pos",           "total","Total adjectives"),
  mk("adverbs",                  "Adverbs",                   "pos",           "total","Total adverbs"),
  mk("nouns",                    "Nouns",                     "pos",           "total","Total nouns"),
  mk("proper_nouns",             "Proper Nouns",              "pos",           "total","Total proper nouns"),
  mk("verbs",                    "Verbs",                     "pos",           "total","Total verbs"),
  mk("numbers",                  "Numbers",                   "pos",           "total","Total numbers"),
  mk("prepositions",             "Prepositions",              "pos",           "total","Total prepositions"),
  mk("coordinating_conjunction", "Coordinating Conjunctions", "pos",           "total","Total coordinating conjunctions"),
  mk("subordinating_conjunction","Subordinating Conjunctions","pos",           "total","Total subordinating conjunctions"),
  mk("auxiliary_verb",           "Auxiliary Verbs",           "pos",           "total","Total auxiliary verbs"),
  mk("pronoun",                  "Pronouns",                  "pos",           "total","Total pronouns"),
  mk("simple_sentences",                      "Simple Sentences",                   "sentence_type","total","Total simple sentences"),
  mk("simple_with_complex_predicates",        "Simple + Complex Predicates",        "sentence_type","total","Total simple (complex predicates)"),
  mk("simple_with_compound_predicates",       "Simple + Compound Predicates",       "sentence_type","total","Total simple (compound predicates)"),
  mk("simple_with_compound_complex_predicates","Simple + Compound-Complex Predicates","sentence_type","total","Total simple (compound complex predicates)"),
  mk("compound_sentences",        "Compound Sentences",        "sentence_type", "total","Total compound sentences"),
  mk("complex_sentences",         "Complex Sentences",         "sentence_type", "total","Total complex sentences"),
  mk("compound_complex_sentences","Compound-Complex Sentences","sentence_type", "total","Total compound-complex sentences"),
  mk("information_sources","Information Sources","source_information","percent","Percent source references"),
  mk("attributions",       "Attributions",       "source_information","percent","Percent attributions"),
  mk("citations",          "Citations",          "source_information","percent","Percent citations"),
  mk("quoted_words",       "Quoted Words",       "source_information","percent","Percent quoted words"),
  mk("direct_speech_verbs","Direct Speech Verbs","dialogue",          "percent","Percent direct speech verbs"),
  mk("indirect_speech",    "Indirect Speech",    "dialogue",          "percent","Percent indirect speech"),
  mk("positive_tone",      "Positive Tone",      "tone",              "percent","Percent positive tone"),
  mk("negative_tone",      "Negative Tone",      "tone",              "percent","Percent negative tone"),
  mk("concrete_details",         "Concrete Details",         "details","percent","Percent concrete details"),
  mk("main_idea_sentences",      "Main Idea Sentences",      "details","total",  "Total main idea sentences"),
  mk("supporting_idea_sentences","Supporting Idea Sentences","details","total",  "Total supporting idea sentences"),
  mk("supporting_detail_sentences","Supporting Detail Sentences","details","total","Total supporting detail sentences"),
  mk("polysyllabic_words",  "Polysyllabic Words",  "other","percent","Percent polysyllabic tokens"),
  mk("low_frequency_words", "Low Frequency Words", "other","percent","Percent low-frequency tokens"),
  mk("sentences",           "Sentences",           "other","total",  "Total sentences"),
  mk("paragraphs",          "Paragraphs",          "other","total",  "Total paragraphs"),
  mk("character_trait_words","Character Trait Words","other","percent","Percent character trait tokens"),
  mk("in_past_tense",       "In Past Tense",       "other","percent","Percent past tense scope"),
  mk("explicit_claims",     "Explicit Claims",     "other","percent","Percent explicit claims"),
  mk("social_awareness",    "Social Awareness",    "other","percent","Percent social awareness"),
];


/* ── Teacher-friendly metric descriptions (exported for use in other pages) ── */
export const METRIC_TEACHER_DESC = {
  academic_language:             "Words signalling formal register — e.g. 'analyze', 'demonstrate'",
  informal_language:             "Casual words that may not suit the assignment genre",
  latinate_words:                "Longer Latin-derived words linked to sophisticated vocabulary",
  opinion_words:                 "Words expressing the writer's personal stance or judgment",
  emotion_words:                 "Words conveying feeling — useful in narrative, limiting in argument",
  argument_words:                "Words signalling reasoning — e.g. 'because', 'therefore'",
  explicit_argument:             "Phrases making the writer's claim directly visible to the reader",
  statements_of_opinion:         "Sentences where the writer expresses a personal view",
  statements_of_fact:            "Sentences asserting something as objectively true",
  transition_words:              "Words and phrases connecting ideas within and across sentences",
  positive_transition_words:     "Additive transitions — e.g. 'furthermore', 'in addition'",
  conditional_transition_words:  "Conditional transitions — e.g. 'if', 'unless'",
  consequential_transition_words:"Cause-and-effect transitions — e.g. 'therefore', 'as a result'",
  contrastive_transition_words:  "Contrasting transitions — e.g. 'however', 'on the other hand'",
  counterpoint_transition_words: "Transitions introducing a counterpoint or concession",
  comparative_transition_words:  "Comparison transitions — e.g. 'similarly', 'likewise'",
  cross_referential_transition_words: "Transitions pointing back or forward in the text",
  illustrative_transition_words: "Example transitions — e.g. 'for instance', 'such as'",
  negative_transition_words:     "Transitions signalling negation or contrast",
  emphatic_transition_words:     "Emphatic transitions — e.g. 'indeed', 'above all'",
  evenidentiary_transition_words:"Transitions introducing evidence or support",
  general_transition_words:      "Common connective words used broadly",
  ordinal_transition_words:      "Sequence transitions — e.g. 'first', 'next', 'finally'",
  purposive_transition_words:    "Purpose transitions — e.g. 'in order to', 'so that'",
  periphrastic_transition_words: "Transition phrases using indirect phrasing",
  hypothetical_transition_words: "Hypothetical transitions — e.g. 'suppose that'",
  summative_transition_words:    "Summary transitions — e.g. 'in conclusion', 'overall'",
  introductory_transition_words: "Transitions that open a point or section",
  adjectives:                    "Describing words — how the student characterises people and things",
  adverbs:                       "Modifying words that qualify verbs, adjectives, or other adverbs",
  nouns:                         "The things and concepts the student writes about",
  proper_nouns:                  "Named people, places, or organisations — signals specific detail",
  verbs:                         "Action or state words — reflect the energy and precision of writing",
  numbers:                       "Numeric references — can signal use of data or evidence",
  prepositions:                  "Words showing relationships in time or space",
  coordinating_conjunction:      "Words joining equal clauses — e.g. 'and', 'but', 'or'",
  subordinating_conjunction:     "Words creating complex sentences — e.g. 'although', 'because'",
  auxiliary_verb:                "Helping verbs that shape tense and mood — e.g. 'would', 'could'",
  pronoun:                       "Words replacing nouns — affect clarity and point of view",
  simple_sentences:              "Single-clause sentences — easier to read but less complex",
  simple_with_complex_predicates:"Simple sentences with a richer predicate structure",
  simple_with_compound_predicates:"Simple sentences with more than one action or state",
  simple_with_compound_complex_predicates: "Simple sentences with the highest predicate complexity",
  compound_sentences:            "Two independent clauses joined — shows coordination",
  complex_sentences:             "A main clause with at least one subordinate clause",
  compound_complex_sentences:    "The most structurally complex sentence type",
  information_sources:           "Overall use of outside evidence and references",
  attributions:                  "Credit given to a speaker or source — e.g. 'According to...'",
  citations:                     "Direct references to an outside source",
  quoted_words:                  "Exact words borrowed from a source in quotation marks",
  direct_speech_verbs:           "Verbs introducing dialogue — e.g. 'said', 'asked', 'replied'",
  indirect_speech:               "Reported speech summarising rather than quoting",
  positive_tone:                 "Language carrying an optimistic or affirmative feeling",
  negative_tone:                 "Language carrying a critical or opposing feeling",
  concrete_details:              "Specific, tangible examples rather than vague abstractions",
  main_idea_sentences:           "Sentences introducing or summarising a central point",
  supporting_idea_sentences:     "Sentences developing or expanding on a main idea",
  supporting_detail_sentences:   "Sentences providing specific evidence or examples",
  polysyllabic_words:            "Words of three or more syllables — rough measure of vocabulary complexity",
  low_frequency_words:           "Uncommon words not in everyday language — signals advanced vocabulary",
  sentences:                     "Total sentences — a basic measure of text length",
  paragraphs:                    "Total paragraphs — reflects structural organisation",
  character_trait_words:         "Words describing character qualities — important in narrative writing",
  in_past_tense:                 "Past-tense scope — important for narrative coherence",
  explicit_claims:               "Direct statements of position or argument",
  social_awareness:              "Language indicating awareness of community or broader context",
};

/* ── Lookup maps (exported for use in other pages) ── */
export const METRIC_BY_ID = Object.fromEntries(METRIC_DEFS.map((m) => [m.id, m]));

export const ALL_KEYS = METRIC_DEFS.map((m) => m.id);

/* ── derived groupings ── */

// category-mode: list of unique category display labels in original order
const CATEGORIES = Array.from(new Set(METRIC_DEFS.map((m) => m.category)));

// trait-mode: for each trait, for each sub-category within it, list metrics
const TRAIT_SUBCATEGORY_MAP = (() => {
  const out = {};
  for (const trait of TRAIT_ORDER) out[trait] = {};          // { catLabel: [metricDef, ...] }
  for (const m of METRIC_DEFS) {
    const trait = m.trait;
    const cat = m.category;
    if (!out[trait]) out[trait] = {};
    if (!out[trait][cat]) out[trait][cat] = [];
    out[trait][cat].push(m);
  }
  return out;
})();

/* ── presets ── */
const DEFAULT_PRESETS = {
  "Core (language + structure)": [
    "academic_language","informal_language","latinate_words",
    "transition_words","citations","sentences","paragraphs",
  ],
  "Sources & Evidence": ["information_sources","attributions","citations","quoted_words"],
};
const PRESETS_STORAGE_KEY = "wo_metric_presets_v1";

function safeParseJSON(s) { try { return JSON.parse(s); } catch { return null; } }
function normalizePresetMetrics(arr) {
  const known = new Set(ALL_KEYS);
  return Array.from(new Set((arr || []).filter(Boolean))).filter((id) => known.has(id));
}

/* ══════════════════════════════════════════════════════════════
   TRAIT-MODE SIDEBAR CONTENT
   Trait group -> sub-category group -> metric rows
   ══════════════════════════════════════════════════════════════ */
function TraitGroupedMetrics({ selectedSet, onToggle, onToggleGroup, onToggleTrait }) {
  // trait collapse state
  const [traitCollapsed, setTraitCollapsed] = useState(
    Object.fromEntries(TRAIT_ORDER.map((t) => [t, !["Ideas & Content","Organization"].includes(t)]))
  );
  // sub-category collapse state per trait (default: all open when trait is open)
  const [catCollapsed, setCatCollapsed] = useState({});

  return (
    <div>
      {TRAIT_ORDER.map((trait) => {
        const subcats = TRAIT_SUBCATEGORY_MAP[trait] || {};
        const allMetricIds = Object.values(subcats).flat().map((m) => m.id);
        if (!allMetricIds.length) return null;

        const style = TRAIT_STYLE[trait] || TRAIT_STYLE["Conventions"];
        const isTraitCollapsed = traitCollapsed[trait];
        const selectedInTrait = allMetricIds.filter((id) => selectedSet.has(id)).length;
        const allTraitSelected = selectedInTrait === allMetricIds.length;

        return (
          <div key={trait} className="border-b border-gray-100 last:border-0">
            {/* Trait header */}
            <div
              className={`flex items-center justify-between px-4 py-2.5 cursor-pointer select-none
                border-l-4 ${isTraitCollapsed ? "border-l-transparent" : `border-l-[3px]`}`}
              style={{ borderLeftColor: isTraitCollapsed ? "transparent" : style.dot.replace("bg-","").includes("-") ? undefined : undefined,
                       background: isTraitCollapsed ? undefined : undefined }}
              onClick={() => setTraitCollapsed((c) => ({ ...c, [trait]: !c[trait] }))}
            >
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full shrink-0 ${style.dot}`} />
                <span className="text-xs font-bold text-gray-800">{trait}</span>
                {selectedInTrait > 0 && (
                  <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full ring-1 ring-inset ${style.badge}`}>
                    {selectedInTrait}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => { e.stopPropagation(); onToggleTrait(allMetricIds, allTraitSelected); }}
                  className={`text-[10px] font-medium hover:underline ${style.badge.split(" ").find(c => c.startsWith("text-")) || "text-gray-500"}`}
                >
                  {allTraitSelected ? "none" : "all"}
                </button>
                {isTraitCollapsed
                  ? <ChevronDown className="h-3.5 w-3.5 text-gray-400" />
                  : <ChevronUp className="h-3.5 w-3.5 text-gray-400" />
                }
              </div>
            </div>

            {/* Sub-category groups within trait */}
            {!isTraitCollapsed && (
              <div className="pb-1">
                {Object.entries(subcats).map(([catLabel, metrics]) => {
                  const catKey = `${trait}__${catLabel}`;
                  const isCatCollapsed = catCollapsed[catKey] ?? false;
                  const catIds = metrics.map((m) => m.id);
                  const selectedInCat = catIds.filter((id) => selectedSet.has(id)).length;
                  const allCatSelected = selectedInCat === catIds.length;

                  return (
                    <div key={catLabel}>
                      {/* Sub-category header — indented */}
                      <div
                        className="flex items-center justify-between pl-7 pr-4 py-1.5 cursor-pointer
                          bg-gray-50/60 hover:bg-gray-100/60 border-y border-gray-100 select-none"
                        onClick={() => setCatCollapsed((c) => ({ ...c, [catKey]: !c[catKey] }))}
                      >
                        <div className="flex items-center gap-1.5">
                          <span className="text-[11px] font-semibold text-gray-600">{catLabel}</span>
                          {selectedInCat > 0 && (
                            <span className="text-[9px] text-gray-500">({selectedInCat})</span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); onToggleGroup(catIds, allCatSelected); }}
                            className="text-[10px] text-gray-400 hover:text-gray-600 font-medium hover:underline"
                          >
                            {allCatSelected ? "none" : "all"}
                          </button>
                          {isCatCollapsed
                            ? <ChevronDown className="h-3 w-3 text-gray-300" />
                            : <ChevronUp className="h-3 w-3 text-gray-300" />
                          }
                        </div>
                      </div>

                      {/* Metric rows */}
                      {!isCatCollapsed && (
                        <div>
                          {metrics.map((m) => {
                            const isChecked = selectedSet.has(m.id);
                            return (
                              <label
                                key={m.id}
                                className={`flex items-center gap-2.5 pl-9 pr-4 py-1.5 cursor-pointer
                                  hover:bg-gray-50 transition-colors ${isChecked ? "bg-gray-50/40" : ""}`}
                              >
                                <input
                                  type="checkbox"
                                  checked={isChecked}
                                  onChange={() => onToggle(m.id)}
                                  className="accent-emerald-600 h-3.5 w-3.5 shrink-0"
                                />
                                <span className={`text-xs leading-relaxed ${isChecked ? "text-gray-900 font-medium" : "text-gray-600"}`}>
                                  {m.title}
                                </span>
                                <span
                                  className={`ml-auto shrink-0 inline-block h-2.5 w-2.5 rounded ${highlightClassForMetric(m.id)}`}
                                  title="Highlight color"
                                />
                              </label>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   CATEGORY-MODE SIDEBAR CONTENT (original flat grouping)
   ══════════════════════════════════════════════════════════════ */
function CategoryGroupedMetrics({ selectedMetrics, onToggle }) {
  const [expanded, setExpanded] = useState(
    Object.fromEntries(CATEGORIES.map((c) => [c, true]))
  );

  return (
    <div className="space-y-1">
      {CATEGORIES.map((cat) => {
        const metricsInCat = METRIC_DEFS.filter((m) => m.category === cat);
        return (
          <div key={cat}>
            <button
              onClick={() => setExpanded((e) => ({ ...e, [cat]: !e[cat] }))}
              className="w-full flex items-center justify-between text-left text-sm px-2 py-1.5 hover:bg-gray-50 rounded"
              type="button"
            >
              <span className="font-medium text-gray-700">{cat}</span>
              <ChevronDown className={`h-4 w-4 text-gray-500 transition-transform ${expanded[cat] ? "" : "-rotate-90"}`} />
            </button>
            {expanded[cat] && (
              <div className="mt-1 pl-2 space-y-0.5">
                {metricsInCat.map((m) => (
                  <label
                    key={m.id}
                    className="flex items-center gap-2 px-2 py-1 text-sm rounded hover:bg-gray-50 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedMetrics.includes(m.id)}
                      onChange={() => onToggle(m.id)}
                      className="accent-emerald-600"
                    />
                    <m.icon className="h-3.5 w-3.5 text-gray-500 shrink-0" />
                    <span className="text-gray-700">{m.title}</span>
                    <span
                      className={`ml-auto shrink-0 inline-block h-3 w-3 rounded ${highlightClassForMetric(m.id)}`}
                      title="Highlight color"
                    />
                  </label>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════
   MetricsPanel — main export
   Props:
     metrics        string[]            currently selected metric IDs
     setMetrics     (ids: string[]) => void
     groupBy        "trait" | "category"   default "category"
     stickyTopClassName  default "top-24"
     title          default "Metrics"
     className      outer aside class
     panelClassName inner card class
     useSticky      default true
   ══════════════════════════════════════════════════════════════ */
export function MetricsPanel({
  metrics,
  setMetrics,
  groupBy = "category",
  stickyTopClassName = "top-24",
  title = "Metrics",
  className = "",
  panelClassName = "",
  useSticky = true,
}) {
  const selectedMetrics = Array.isArray(metrics) ? metrics : [];
  const setSelectedMetrics = typeof setMetrics === "function" ? setMetrics : () => {};
  const selectedSet = new Set(selectedMetrics);

  /* ── presets ── */
  const [presets, setPresets] = useState(DEFAULT_PRESETS);
  const [presetName, setPresetName] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    const parsed = safeParseJSON(window.localStorage.getItem(PRESETS_STORAGE_KEY));
    if (parsed && typeof parsed === "object") {
      const merged = { ...DEFAULT_PRESETS };
      for (const [k, v] of Object.entries(parsed)) {
        if (k) merged[k] = normalizePresetMetrics(v);
      }
      setPresets(merged);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(PRESETS_STORAGE_KEY, JSON.stringify(presets));
  }, [presets]);

  const createPreset = useCallback(() => {
    const name = (presetName || "").trim();
    if (!name) return;
    const arr = normalizePresetMetrics(selectedMetrics);
    if (!arr.length) return;
    setPresets((prev) => ({ ...prev, [name]: arr }));
    setPresetName("");
  }, [presetName, selectedMetrics]);

  const deletePreset = useCallback((name) => {
    setPresets((prev) => {
      const next = { ...prev };
      delete next[name];
      return Object.keys(next).length ? next : { ...DEFAULT_PRESETS };
    });
  }, []);

  const applyPreset = useCallback((name) => {
    setSelectedMetrics(normalizePresetMetrics(presets?.[name] || []));
  }, [presets, setSelectedMetrics]);

  /* ── toggle helpers ── */
  const handleToggle = useCallback((id) => {
    setSelectedMetrics((prev) =>
      (prev || []).includes(id) ? prev.filter((x) => x !== id) : [...(prev || []), id]
    );
  }, [setSelectedMetrics]);

  const handleToggleGroup = useCallback((ids, allSelected) => {
    setSelectedMetrics((prev) => {
      const s = new Set(Array.isArray(prev) ? prev : []);
      if (allSelected) ids.forEach((id) => s.delete(id));
      else ids.forEach((id) => s.add(id));
      return Array.from(s);
    });
  }, [setSelectedMetrics]);

  const handleToggleTrait = useCallback((ids, allSelected) => {
    handleToggleGroup(ids, allSelected);
  }, [handleToggleGroup]);

  const selectedCount = selectedMetrics.length;

  return (
    <aside className={`col-span-12 md:col-span-4 xl:col-span-3 ${className}`.trim()}>
      <div
        className={`bg-white rounded-2xl border border-gray-200 shadow-sm h-fit overflow-hidden
          ${useSticky ? `sticky ${stickyTopClassName}` : ""} ${panelClassName}`.trim()}
      >
        {/* ── Presets section ── */}
        <div className="px-4 pt-4 pb-3 border-b border-gray-100">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 text-sm">Presets</h3>
            <span className="text-xs text-gray-400">{Object.keys(presets || {}).length}</span>
          </div>

          <div className="flex items-center gap-2 mb-3">
            <input
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
              placeholder="Preset name"
              className="flex-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg
                focus:outline-none focus:ring-2 focus:ring-emerald-500"
              onKeyDown={(e) => { if (e.key === "Enter") createPreset(); }}
            />
            <button onClick={createPreset} type="button"
              className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-sm hover:bg-emerald-700 shrink-0">
              + Preset
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {Object.entries(presets || {}).map(([name]) => (
              <div key={name}
                className="inline-flex items-center overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
                <button onClick={() => applyPreset(name)} type="button"
                  className="px-2.5 py-1 text-xs text-gray-700 hover:bg-gray-50">
                  {name}
                </button>
                <button onClick={() => deletePreset(name)} type="button"
                  className="px-2 py-1 border-l border-gray-200 hover:bg-gray-50"
                  aria-label={`Delete preset ${name}`}>
                  <Trash2 className="h-3.5 w-3.5 text-gray-400" />
                </button>
              </div>
            ))}
          </div>

          <div className="flex gap-2 mt-2.5">
            <button onClick={() => setSelectedMetrics(ALL_KEYS)} type="button"
              className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:bg-gray-50 text-gray-600">
              Select All
            </button>
            <button onClick={() => setSelectedMetrics([])} type="button"
              className="text-xs px-2 py-1 rounded-full border border-gray-200 hover:bg-gray-50 text-gray-600">
              Deselect All
            </button>
          </div>
        </div>

        {/* ── Metrics header ── */}
        <div className="px-4 py-2.5 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
          <span className="text-xs text-gray-400">{selectedCount} / {METRIC_DEFS.length}</span>
        </div>

        {/* ── Metrics list ── */}
        <div className="max-h-[58vh] overflow-y-auto">
          {groupBy === "trait" ? (
            <TraitGroupedMetrics
              selectedSet={selectedSet}
              onToggle={handleToggle}
              onToggleGroup={handleToggleGroup}
              onToggleTrait={handleToggleTrait}
            />
          ) : (
            <div className="p-3">
              <CategoryGroupedMetrics
                selectedMetrics={selectedMetrics}
                onToggle={handleToggle}
              />
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}