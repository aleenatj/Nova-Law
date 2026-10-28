import React, { useMemo, useState, useCallback, useLayoutEffect, useRef, useEffect } from "react";
import { Layout } from "@/components";
import { api, ApiError, tokenManager } from "@/lib/api";
import { toastManager, createErrorToast } from "@/utils/toasts";
import CountrySelect from "@/components/ui/country-select/CountrySelect";
import { engageWelcomeContent, engageSection2Welcome } from "@/config/engageWelcome";
import {
  getEngageSectionConfig,
  ENGAGE_SECTIONS_BUILT,
  MAX_ENGAGE_SECTION_NAV,
  type QuestionDef,
  type SectionConfig,
  type OptionItem,
} from "@/config/engageConfig";
import {
  ENGAGE_ACTIVE_SECTION_EVENT,
  ENGAGE_ACTIVE_SECTION_STORAGE_KEY,
  ENGAGE_CLIENT_NAME_SUB_FIRST,
  ENGAGE_NAVIGATE_SECTION_EVENT,
  ENGAGE_PARTNER_NAME_SUB_FIRST,
  ENGAGE_Q_ID_CLIENT_NAME,
  ENGAGE_Q_ID_PARTNER_NAME,
} from "@/pages/engage/engagePageIds";
import { FormButton } from "@/utils/formComponents";
import {
  formatUkNationalInsuranceInput,
  isCompleteUkNationalInsuranceValue,
} from "@/pages/engage/engageFormShared";

type Rule = { identifier: string; operator: string; value: string };

type WelcomeBundle =
  | { variant: "section1"; data: typeof engageWelcomeContent }
  | { variant: "section2"; data: typeof engageSection2Welcome };

function getPartnerFirstName(
  answers: Record<string, string | Record<string, string>>
): string {
  const v = answers[ENGAGE_Q_ID_PARTNER_NAME];
  if (typeof v === "object" && v && typeof v[ENGAGE_PARTNER_NAME_SUB_FIRST] === "string") {
    const t = v[ENGAGE_PARTNER_NAME_SUB_FIRST].trim();
    if (t) return t;
  }
  return "your partner";
}

/** Client first name from section 1 “What is your name?” — search `questions["105"]` / `105.1`. */
function getClientFirstName(
  answers: Record<string, string | Record<string, string>>
): string {
  const v = answers[ENGAGE_Q_ID_CLIENT_NAME];
  if (typeof v === "object" && v && typeof v[ENGAGE_CLIENT_NAME_SUB_FIRST] === "string") {
    return v[ENGAGE_CLIENT_NAME_SUB_FIRST].trim();
  }
  return "";
}

/** Section 2 welcome title: `Thank you, {name}` — drops `{name}` if not yet captured. */
function formatSection2WelcomeTitle(
  title: string,
  answers: Record<string, string | Record<string, string>>
): string {
  const name = getClientFirstName(answers);
  if (name) return title.replace(/\{name\}/g, name);
  return title.replace(/\s*,?\s*\{name\}\s*/g, "").replace(/\s+/g, " ").trim();
}

/** Interpolate partner / client names in question and option text (matches engage.json placeholders). */
function formatEngageQuestion(
  text: string,
  answers: Record<string, string | Record<string, string>>
): string {
  const name = getClientFirstName(answers);
  return text
    .replace(/\[X\]/g, getPartnerFirstName(answers))
    .replace(/\{partner_name\}/g, getPartnerFirstName(answers))
    .replace(/\{name\}/g, name);
}

const DOB_MIN_AGE_MESSAGE =
  "Please check your date of birth - you need to be 18 years of age to instruct us";

/** Whole years since date of birth from `YYYY-MM-DD` (local calendar). */
function ageFromIsoDateString(iso: string): number | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]) - 1;
  const d = Number(m[3]);
  const birth = new Date(y, mo, d);
  if (birth.getFullYear() !== y || birth.getMonth() !== mo || birth.getDate() !== d) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const md = today.getMonth() - birth.getMonth();
  if (md < 0 || (md === 0 && today.getDate() < birth.getDate())) age -= 1;
  return age;
}

const TOOLTIP_GAP_PX = 8;
const TOOLTIP_VIEWPORT_PAD = 12;

/** Tooltip prefers sitting to the left of the (?) so its right edge aligns with the question; flips right if no room on the left. */
function RadioOptionTooltip({
  open,
  html,
  onMouseEnter,
  onMouseLeave,
  onToggle,
  onKeyToggle,
}: {
  open: boolean;
  html: string;
  onMouseEnter: () => void;
  onMouseLeave: () => void;
  onToggle: () => void;
  onKeyToggle: () => void;
}) {
  const wrapRef = useRef<HTMLSpanElement>(null);
  const tipRef = useRef<HTMLDivElement>(null);
  const [side, setSide] = useState<"left" | "right">("left");

  useLayoutEffect(() => {
    if (!open) return;
    const update = () => {
      const wrap = wrapRef.current;
      const tip = tipRef.current;
      if (!wrap || !tip) return;
      const tr = wrap.getBoundingClientRect();
      const vw = window.innerWidth;
      const tipW = tip.getBoundingClientRect().width;
      const spaceLeft = tr.left - TOOLTIP_VIEWPORT_PAD;
      const spaceRight = vw - tr.right - TOOLTIP_VIEWPORT_PAD;
      const fitsLeft = spaceLeft >= tipW + TOOLTIP_GAP_PX;
      const fitsRight = spaceRight >= tipW + TOOLTIP_GAP_PX;
      if (fitsLeft) setSide("left");
      else if (fitsRight) setSide("right");
      else setSide(spaceLeft >= spaceRight ? "left" : "right");
    };
    update();
    let raf1 = 0;
    let raf2 = 0;
    raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(update);
    });
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      cancelAnimationFrame(raf1);
      cancelAnimationFrame(raf2);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [open, html]);

  return (
    <span
      ref={wrapRef}
      className="relative ml-1.5 inline-flex shrink-0 align-middle"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <span
        role="button"
        tabIndex={0}
        onClick={(e) => {
          e.preventDefault();
          onToggle();
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") onKeyToggle();
        }}
        className="w-4 h-4 rounded-full bg-black text-white flex items-center justify-center text-[10px] font-medium shrink-0 cursor-pointer hover:opacity-90"
        aria-label="More information"
      >
        ?
      </span>
      {open && (
        <div
          ref={tipRef}
          className={`absolute top-1/2 z-20 w-48 sm:w-80 max-w-[min(20rem,calc(100vw-2rem))] p-5 bg-white rounded-[15px] text-left ${
            side === "left"
              ? "right-full mr-2 -translate-y-1/2"
              : "left-full ml-2 -translate-y-1/2"
          }`}
          style={{
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.1)",
            fontFamily: "Georgia, 'Times New Roman', serif",
          }}
        >
          {side === "left" ? (
            <div
              className="absolute -right-2 top-1/2 -translate-y-1/2 w-0 h-0 border-y-[8px] border-l-[8px] border-r-0 border-y-transparent border-l-white"
              aria-hidden
            />
          ) : (
            <div
              className="absolute -left-2 top-1/2 -translate-y-1/2 w-0 h-0 border-y-[8px] border-r-[8px] border-l-0 border-y-transparent border-r-white"
              aria-hidden
            />
          )}
          <div
            className={`text-novaNeutral-800 text-[15px] leading-relaxed [&_strong]:font-bold [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1 [&_p]:mb-2 ${RICH_HTML_LINKS}`}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </div>
      )}
    </span>
  );
}

/** Check if a question is visible given current answers and its rules. Rules are OR: show when any rule matches. */
function isQuestionVisible(
  q: QuestionDef,
  answers: Record<string, string | Record<string, string>>
): boolean {
  const rules = q.rules as Rule[] | undefined;
  if (!rules || rules.length === 0) return true;
  return rules.some((r) => {
    const val = answers[r.identifier];
    const compare = typeof val === "object" ? undefined : (val as string);
    if (r.operator === "is") return compare === r.value;
    if (r.operator === "is not") return compare !== r.value;
    return false;
  });
}

/** Get option key and label from backend format { key: { value: "Label" } }. */
function getOptionKeyAndLabel(opt: OptionItem): [string, string] {
  const key = Object.keys(opt)[0];
  const label = opt[key]?.value ?? key;
  return [key, label];
}

/** Selected option data for a radio question (string answer). */
function getSelectedOptionData(
  q: QuestionDef,
  answer: string | Record<string, string> | undefined
): { key: string; data: Exclude<OptionItem[string], undefined> } | null {
  if (typeof answer !== "string" || !q.options?.length) return null;
  const opt = q.options.find((o) => Object.keys(o)[0] === answer);
  if (!opt) return null;
  const key = Object.keys(opt)[0];
  const data = opt[key];
  if (!data) return null;
  return { key, data };
}

const BELOW_CARD_ADDITIONAL_WRAP =
  "bg-white rounded-xl shadow-sm border border-novaNeutral-100 p-6 mt-4";
/** hover  */
const RICH_HTML_LINKS =
  "[&_a]:text-novaDarkOrange [&_a]:underline [&_a:hover]:underline-none [&_a]:decoration-novaDarkOrange";
const BELOW_CARD_ADDITIONAL_RICH = `text-novaNeutral-700 text-sm leading-relaxed [&_strong]:font-bold ${RICH_HTML_LINKS} [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1 [&_p]:mb-2 [&_p:last-child]:mb-0`;
/** Flatten form answer (object of sub-ids to values) for storing under parent id. */
function getFormAnswer(answers: Record<string, string>, subIds: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  subIds.forEach((id) => {
    if (answers[id] !== undefined && answers[id] !== "") out[id] = answers[id];
  });
  return out;
}

/** One answer entry from GET /v1/engage (`{ "value": "..." }` or legacy single-key objects). */
function extractEngageAnswerValue(entry: unknown): string {
  if (entry == null) return "";
  if (typeof entry === "string") return entry;
  if (typeof entry === "object" && entry !== null) {
    const o = entry as Record<string, unknown>;
    if ("value" in o && o.value != null) return String(o.value);
    const vals = Object.values(o);
    if (vals.length === 1 && vals[0] != null) return String(vals[0]);
  }
  return "";
}

/**
 * Section map from GET /v1/engage JSON body (`data` field).
 * Only uses the backend envelope shape — no other client-side sources.
 */
function unwrapEngageGetData(res: unknown): Record<
  string,
  Array<Record<string, { version?: string; answer?: unknown }>>
> | null {
  if (!res || typeof res !== "object") return null;
  const r = res as Record<string, unknown>;
  const d = r.data;
  if (d == null) return null;
  if (typeof d === "object" && !Array.isArray(d)) {
    return d as Record<string, Array<Record<string, { version?: string; answer?: unknown }>>>;
  }
  return null;
}

/** Map GET /v1/engage payload (sections → lists of question blocks) into `answers` state. */
function hydrateAnswersFromEngageGet(
  data: Record<string, Array<Record<string, { version?: string; answer?: unknown }>>>
): Record<string, string | Record<string, string>> {
  const out: Record<string, string | Record<string, string>> = {};
  for (const sectionList of Object.values(data)) {
    if (!Array.isArray(sectionList)) continue;
    for (const item of sectionList) {
      if (!item || typeof item !== "object") continue;
      for (const [qid, block] of Object.entries(item)) {
        const raw = block?.answer;
        const list = Array.isArray(raw) ? raw : raw != null ? [raw] : [];
        const str = list.length > 0 ? extractEngageAnswerValue(list[0]) : "";
        const dot = qid.indexOf(".");
        if (dot !== -1) {
          const parent = qid.slice(0, dot);
          const prev = out[parent];
          const obj =
            typeof prev === "object" && prev !== null && !Array.isArray(prev)
              ? { ...(prev as Record<string, string>) }
              : {};
          obj[qid] = str;
          out[parent] = obj;
        } else {
          out[qid] = str;
        }
      }
    }
  }
  return out;
}

/** Resolve encrypted case id for PATCH /v1/engage (session, then ?case_id=; persist query to session). */
function getEngageCaseId(): string | null {
  const fromSession = sessionStorage.getItem("current_case_id");
  if (fromSession) return fromSession;
  const q = new URLSearchParams(window.location.search).get("case_id");
  if (q) {
    sessionStorage.setItem("current_case_id", q);
    return q;
  }
  return null;
}

/** Build PATCH body for the current section from client state (question ids match backend engage.json). */
function buildEngagePatchAnswers(
  config: SectionConfig,
  answers: Record<string, string | Record<string, string>>,
  visibleOrder: string[]
): Array<{ question_identifier: string; answer: { value: string } }> {
  const sectionIds = new Set(config.questionOrder);
  const out: Array<{ question_identifier: string; answer: { value: string } }> = [];

  for (const id of visibleOrder) {
    if (!sectionIds.has(id)) continue;
    const q = config.questions[id];
    if (!q) continue;

    if (q.input_type === "form" && q.form_fields) {
      const obj = answers[id];
      if (typeof obj !== "object" || !obj) continue;
      for (const subId of Object.keys(q.form_fields.questions)) {
        const subVal = obj[subId];
        if (subVal === undefined || subVal === "") continue;
        out.push({ question_identifier: subId, answer: { value: String(subVal) } });
      }
    } else {
      const val = answers[id];
      if (val === undefined || val === "") continue;
      if (typeof val === "object") continue;
      out.push({ question_identifier: id, answer: { value: String(val) } });
    }
  }
  return out;
}

function readInitialEngageSection(): number {
  try {
    const raw = sessionStorage.getItem(ENGAGE_ACTIVE_SECTION_STORAGE_KEY);
    const n = parseInt(raw || "1", 10);
    if (Number.isFinite(n) && n >= 1 && n <= MAX_ENGAGE_SECTION_NAV) return n;
  } catch {
    /* ignore */
  }
  return 1;
}

const EngageForm: React.FC = () => {
  const [activeSection, setActiveSection] = useState(readInitialEngageSection);
  const [answers, setAnswers] = useState<Record<string, string | Record<string, string>>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [openTooltip, setOpenTooltip] = useState<string | null>(null);
  const firstErrorRef = React.useRef<HTMLDivElement | null>(null);

  const sectionSlug = String(activeSection);

  /** Same resolution as GET /v1/engage (query or session); used so we can mark case ready before first effect runs. */
  const initialEngageCaseId =
    typeof window !== "undefined" ? getEngageCaseId() : null;
  const [engageCaseId, setEngageCaseId] = useState<string | null>(initialEngageCaseId);
  /** True once we know the case id (from URL/session now, or from /v1/case after load). */
  const [caseIdReady, setCaseIdReady] = useState(() => initialEngageCaseId !== null);

  /** If no case in session/query, load the customer’s first open case (same listing as case dashboard). */
  useEffect(() => {
    const sync = getEngageCaseId();
    if (sync) {
      setEngageCaseId(sync);
      setCaseIdReady(true);
      return;
    }
    if (!tokenManager.getAccessToken()) {
      setCaseIdReady(true);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const params = new URLSearchParams({
          page: "1",
          limit: "1",
          category: "All",
          case_status: "Open",
        });
        const r = await api.get<{ data?: { cases?: Array<{ id: string }> } }>(
          `/v1/case?${params.toString()}`
        );
        const id = r.data?.cases?.[0]?.id;
        if (!cancelled && id) {
          sessionStorage.setItem("current_case_id", id);
          setEngageCaseId(id);
        }
      } catch {
        /* non-blocking */
      } finally {
        if (!cancelled) setCaseIdReady(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  /** Loads saved answers from GET /v1/engage only (same data PATCH persists). */
  const refetchEngageAnswers = useCallback(async () => {
    const caseId = engageCaseId ?? getEngageCaseId();
    if (!caseId || !tokenManager.getAccessToken()) return;
    try {
      const res = await api.get<unknown>(
        `/v1/engage?case_id=${encodeURIComponent(caseId)}`
      );
      const payload = unwrapEngageGetData(res);
      if (!payload) return;
      const merged = hydrateAnswersFromEngageGet(payload);
      setAnswers((prev) => ({ ...prev, ...merged }));
    } catch {
      /* non-blocking */
    }
  }, [engageCaseId]);

  /** Load saved answers from GET so returning to a section or refreshing shows prior selections. */
  useEffect(() => {
    if (!caseIdReady || !engageCaseId || !tokenManager.getAccessToken()) return;
    void refetchEngageAnswers();
  }, [caseIdReady, engageCaseId, refetchEngageAnswers]);

  /** Sidebar / shell: jump to a step via `ENGAGE_NAVIGATE_SECTION_EVENT`. */
  useEffect(() => {
    const handler = (e: Event) => {
      const ce = e as CustomEvent<{ section?: number }>;
      const n = ce.detail?.section;
      if (typeof n === "number" && n >= 1 && n <= MAX_ENGAGE_SECTION_NAV) {
        setActiveSection(n);
      }
    };
    window.addEventListener(ENGAGE_NAVIGATE_SECTION_EVENT, handler);
    return () => window.removeEventListener(ENGAGE_NAVIGATE_SECTION_EVENT, handler);
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    sessionStorage.setItem(ENGAGE_ACTIVE_SECTION_STORAGE_KEY, String(activeSection));
    window.dispatchEvent(new Event(ENGAGE_ACTIVE_SECTION_EVENT));
  }, [activeSection]);

  const isSectionBuilt = ENGAGE_SECTIONS_BUILT.has(sectionSlug);

  const config = useMemo(
    (): SectionConfig => getEngageSectionConfig(sectionSlug),
    [sectionSlug]
  );

  const welcome = useMemo((): WelcomeBundle | null => {
    if (!isSectionBuilt) return null;
    if (sectionSlug === "1") return { variant: "section1", data: engageWelcomeContent };
    if (sectionSlug === "2") return { variant: "section2", data: engageSection2Welcome };
    return null;
  }, [sectionSlug, isSectionBuilt]);

  const visibleOrder = useMemo(() => {
    return config.questionOrder.filter((id) => {
      const q = config.questions[id];
      return q && isQuestionVisible(q, answers);
    });
  }, [answers, config]);

  const firstErrorId = useMemo(() => {
    for (const id of visibleOrder) {
      if (errors[id]) return id;
      const q = config.questions[id];
      if (q?.form_fields) {
        for (const subId of Object.keys(q.form_fields.questions)) {
          if (errors[subId]) return id;
        }
      }
    }
    return null;
  }, [errors, visibleOrder, config]);

  const setAnswer = useCallback((id: string, value: string | Record<string, string>) => {
    setAnswers((prev) => ({ ...prev, [id]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  }, []);

  const validate = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};
    const touchIds: Record<string, boolean> = {};
    visibleOrder.forEach((id) => {
      const q = config.questions[id];
      if (!q) return;
      const val = answers[id];

      if (!q.required) {
        if (q.input_type === "text" || q.input_type === "textarea") {
          const str = typeof val === "string" ? val : "";
          if (str.trim()) {
            const qDef = q as QuestionDef & { min_length?: number; max_length?: number };
            if (qDef.min_length && str.length < qDef.min_length) {
              newErrors[id] = `Minimum ${qDef.min_length} character(s).`;
              touchIds[id] = true;
            } else if (qDef.max_length && str.length > qDef.max_length) {
              newErrors[id] = `Maximum ${qDef.max_length} character(s).`;
              touchIds[id] = true;
            }
          }
        }
        if (q.input_type === "specialtext") {
          const str = typeof val === "string" ? val : "";
          const core = str.replace(/[^a-zA-Z0-9]/g, "");
          if (core.length > 0 && !isCompleteUkNationalInsuranceValue(str)) {
            newErrors[id] = "Enter a complete National Insurance number.";
            touchIds[id] = true;
          }
        }
        return;
      }

      if (q.input_type === "form" && q.form_fields) {
        const subQs = Object.values(q.form_fields.questions).sort(
          (a, b) => a.question_order - b.question_order
        );
        subQs.forEach((sub) => {
          const subVal = typeof val === "object" && val ? val[sub.id] : undefined;
          const str = typeof subVal === "string" ? subVal : "";
          if (sub.required) {
            if (!str.trim()) {
              newErrors[sub.id] = "This field is required.";
              touchIds[sub.id] = true;
              return;
            }
          } else if (!str.trim()) {
            return;
          }
          if (sub.min_length && str.length < sub.min_length) {
            newErrors[sub.id] = `Minimum ${sub.min_length} character(s).`;
            touchIds[sub.id] = true;
          } else if (sub.max_length && str.length > sub.max_length) {
            newErrors[sub.id] = `Maximum ${sub.max_length} character(s).`;
            touchIds[sub.id] = true;
          }
        });
        if (subQs.some((s) => newErrors[s.id])) touchIds[id] = true;
        return;
      }
      if (q.input_type === "date") {
        const str = typeof val === "string" ? val : "";
        if (q.required && !str.trim()) {
          newErrors[id] = "This field is required.";
          touchIds[id] = true;
          return;
        }
        if (!str.trim()) return;
        const age = ageFromIsoDateString(str);
        if (age === null) {
          newErrors[id] = "Please enter a valid date of birth.";
          touchIds[id] = true;
          return;
        }
        if (age < 18) {
          newErrors[id] = DOB_MIN_AGE_MESSAGE;
          touchIds[id] = true;
        }
        return;
      }
      if (q.input_type === "country") {
        const str = typeof val === "string" ? val : "";
        if (!str.trim()) {
          newErrors[id] = "This field is required.";
          touchIds[id] = true;
        }
        return;
      }
      if (q.input_type === "specialtext") {
        const s = typeof val === "string" ? val : "";
        const core = s.replace(/[^a-zA-Z0-9]/g, "");
        if (!core) {
          newErrors[id] = "This field is required.";
          touchIds[id] = true;
          return;
        }
        if (!isCompleteUkNationalInsuranceValue(s)) {
          newErrors[id] = "Enter a valid National Insurance number (e.g. AB 12 34 56 C).";
          touchIds[id] = true;
        }
        return;
      }
      const str = typeof val === "string" ? val : "";
      if (!str || !str.trim()) {
        newErrors[id] = "This field is required.";
        touchIds[id] = true;
        return;
      }
      const qDef = q as QuestionDef & { min_length?: number; max_length?: number };
      if (qDef.min_length && str.length < qDef.min_length) {
        newErrors[id] = `Minimum ${qDef.min_length} character(s).`;
        touchIds[id] = true;
      } else if (qDef.max_length && str.length > qDef.max_length) {
        newErrors[id] = `Maximum ${qDef.max_length} character(s).`;
        touchIds[id] = true;
      }
    });
    setErrors(newErrors);
    setTouched((prev) => ({ ...prev, ...touchIds }));
    if (Object.keys(newErrors).length > 0) {
      setTimeout(() => firstErrorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100);
    }
    return Object.keys(newErrors).length === 0;
  }, [answers, visibleOrder, config]);

  const handleBlur = useCallback((id: string) => {
    setTouched((prev) => ({ ...prev, [id]: true }));
  }, []);

  const handleSave = useCallback(async () => {
    if (!isSectionBuilt) {
      if (activeSection < MAX_ENGAGE_SECTION_NAV) setActiveSection((n) => n + 1);
      return;
    }
    if (!validate()) return;

    if (!caseIdReady) {
      toastManager.addToast(
        createErrorToast("Cannot save", "Still loading your case. Try again in a moment.")
      );
      return;
    }
    const caseId = engageCaseId ?? getEngageCaseId();
    if (!caseId) {
      toastManager.addToast(
        createErrorToast(
          "Cannot save",
          "No case could be linked. Open Nova Engage from your case timeline, or ensure you have an open case."
        )
      );
      return;
    }

    const patchAnswers = buildEngagePatchAnswers(config, answers, visibleOrder);
    /** Required fields are already valid; empty patch means no new answers to persist (e.g. only optional fields skipped). */
    if (patchAnswers.length === 0) {
      setSaving(true);
      try {
        await refetchEngageAnswers();
        if (activeSection < MAX_ENGAGE_SECTION_NAV) setActiveSection((n) => n + 1);
      } finally {
        setSaving(false);
      }
      return;
    }

    setSaving(true);
    try {
      const res = await api.patch<{ success?: boolean; message?: unknown }>("/v1/engage", {
        case_id: caseId,
        answers: patchAnswers,
      });
      if (res && typeof res === "object" && "success" in res && res.success === false) {
        toastManager.addToast(createErrorToast("Save failed", "Could not save your answers. Please try again."));
        return;
      }
      await refetchEngageAnswers();
      if (activeSection < MAX_ENGAGE_SECTION_NAV) setActiveSection((n) => n + 1);
    } catch (e) {
      if (e instanceof ApiError && e.status === 400) {
        return;
      }
      const msg = e instanceof Error ? e.message : "Could not save your answers.";
      toastManager.addToast(createErrorToast("Save failed", msg));
    } finally {
      setSaving(false);
    }
  }, [validate, isSectionBuilt, activeSection, config, answers, visibleOrder, engageCaseId, caseIdReady, refetchEngageAnswers]);

  return (
    <Layout
      showBackButton
      backButtonLink="/case-dashboard"
      backButtonLabel="Back"
    >
      <div
        className="min-h-full flex"
        style={{ backgroundColor: "var(--nova-inactive)" }}
      >
        {/* Sidebar - Your steps
        <aside className="w-[240px] shrink-0 bg-white rounded-tl-lg rounded-bl-lg shadow-sm p-4 mt-4 ml-4 hidden md:block self-start">
          <h2 className="text-novaNeutral-800 font-semibold flex items-center gap-1">
            Your steps
            <i className="fas fa-chevron-down text-xs" />
          </h2>
          <nav className="mt-4 flex flex-col gap-0.5">
            <div className="py-2 px-3 rounded-md text-white text-sm font-medium bg-novaDarkOrange">
              1. {config.section.title}
            </div>
            {[2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
              <div
                key={n}
                className="py-2 px-3 rounded-md text-novaNeutral-700 text-sm"
              >
                {n}. Section {n}
              </div>
            ))}
          </nav>
        </aside> */}

        {/* Main content - full width */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 pt-6 pb-12 w-full min-w-0 px-4 md:px-[60px] lg:px-[100px] 2xl:px-[180px]">
          <div className="space-y-6 ">
            {welcome?.variant === "section1" && (
            <div className="bg-white rounded-xl shadow-sm border border-novaNeutral-100 p-6 md:p-8">
              <h2 className="text-xl md:text-2xl font-semibold text-novaNeutral-900 mb-4">
                {welcome.data.title}
              </h2>
              <p className="text-novaNeutral-700 text-sm md:text-base leading-relaxed mb-4">
                <div dangerouslySetInnerHTML={{ __html: welcome.data.intro }} />
              </p>
              <h3 className="text-novaNeutral-800 font-medium mt-6 mb-2">
                {welcome.data.subheading}
              </h3>
              <ol className="list-decimal list-outside space-y-3 text-novaNeutral-700 text-sm md:text-base leading-relaxed pl-5">
                {welcome.data.points.map((point, idx) => (
                  <li key={idx} className="space-y-1">
                    <span dangerouslySetInnerHTML={{ __html: (point as { text: string }).text }} />
                    {"items" in point && point.items && (
                      <ul className="list-disc list-outside ml-4 mt-2 space-y-1 pl-5">
                        {point.items.map((item, i) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ol>
              <p className="text-novaNeutral-700 text-sm md:text-base leading-relaxed mt-4">
                <div dangerouslySetInnerHTML={{ __html: welcome.data.closing }} />
              </p>
            </div>
            )}

            {welcome?.variant === "section2" && (
            <div className="bg-white rounded-xl shadow-sm border border-novaNeutral-100 p-6 md:p-8">
              <h2 className="text-xl md:text-2xl font-semibold text-novaNeutral-900 mb-4">
                {formatSection2WelcomeTitle(welcome.data.title, answers)}
              </h2>
              <div
                className="text-novaNeutral-700 text-sm md:text-base leading-relaxed space-y-4 [&_p]:mb-3"
                dangerouslySetInnerHTML={{ __html: welcome.data.intro }}
              />
              <div
                className="text-novaNeutral-700 text-sm md:text-base leading-relaxed mt-6 pt-4 border-t border-novaNeutral-100"
                dangerouslySetInnerHTML={{ __html: welcome.data.closing }}
              />
            </div>
            )}

            {!isSectionBuilt && (
              <div className="bg-white rounded-xl shadow-sm border border-novaNeutral-100 p-8 max-w-3xl">
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-2">
                  {config.section.title ?? "This step"}
                </h2>
                <p className="text-novaNeutral-700 text-sm leading-relaxed">
                  This part of your journey is not in the form yet. You can use the sidebar to open a completed section, or continue to explore the next step when you are ready.
                </p>
              </div>
            )}

            {isSectionBuilt &&
            visibleOrder.map((id) => {
            const q = config.questions[id];
            if (!q) return null;
            const value = answers[id];
            const err = errors[id];
            const isTouched = touched[id];

            const selectedOpt = getSelectedOptionData(q, value);
            const belowCardAdditional =
              selectedOpt?.data.render_additional_below_card === true &&
              selectedOpt.data.additional_description
                ? { html: selectedOpt.data.additional_description }
                : null;

            return (
              <React.Fragment key={id}>
              <div
                ref={firstErrorId === id ? firstErrorRef : undefined}
                className={`bg-white rounded-xl shadow-sm border p-6 ${
                  (errors[id] || (q.form_fields && Object.keys(q.form_fields.questions).some((subId) => errors[subId])))
                    ? "border-novaCaution-400"
                    : "border-novaNeutral-100"
                }`}
              >
                <h3 className="text-novaNeutral-900 font-medium mb-4 flex flex-wrap items-center gap-2">
                  <span>{formatEngageQuestion(q.question, answers)}</span>
                  {q.required && <span className="text-novaCaution-500">*</span>}
                  {q.question_tooltip && (
                    <RadioOptionTooltip
                      open={openTooltip === `title-${id}`}
                      html={q.question_tooltip}
                      onMouseEnter={() => setOpenTooltip(`title-${id}`)}
                      onMouseLeave={() => setOpenTooltip(null)}
                      onToggle={() =>
                        setOpenTooltip(openTooltip === `title-${id}` ? null : `title-${id}`)
                      }
                      onKeyToggle={() =>
                        setOpenTooltip(openTooltip === `title-${id}` ? null : `title-${id}`)
                      }
                    />
                  )}
                </h3>
                {q.description && (
                  <p className="text-novaNeutral-600 text-sm mb-3">{q.description}</p>
                )}

                {q.input_type === "radio" && q.options && (
                  <div className="space-y-3">
                    {q.options.map((opt, idx) => {
                      const [key, label] = getOptionKeyAndLabel(opt);
                      const labelFormatted = formatEngageQuestion(label, answers);
                      const isChecked =
                        (typeof value === "string" && value === key) || false;
                      const optData = opt[Object.keys(opt)[0]];
                      const additionalDesc = optData?.additional_description
                        ? formatEngageQuestion(optData.additional_description, answers)
                        : undefined;
                      const showTextInput = optData?.show_text_input === true;
                      return (
                        <div key={idx}>
                          <label
                            className={`flex items-center gap-3 cursor-pointer ${
                              isChecked ? "text-novaDarkOrange font-medium" : "text-novaNeutral-800"
                            }`}
                          >
                            <input
                              type="radio"
                              name={id}
                              checked={isChecked}
                              onChange={() => setAnswer(id, key)}
                              onBlur={() => handleBlur(id)}
                              className="w-4 h-4 border-2 border-novaNeutral-400 focus:outline-none focus:ring-0"
                              style={{ accentColor: "var(--nova-dark-orange)" }}
                            />
                            <span>{labelFormatted}</span>
                            {optData?.tooltip && (
                              <RadioOptionTooltip
                                open={openTooltip === `${id}-${key}`}
                                html={optData.tooltip}
                                onMouseEnter={() => setOpenTooltip(`${id}-${key}`)}
                                onMouseLeave={() => setOpenTooltip(null)}
                                onToggle={() =>
                                  setOpenTooltip(openTooltip === `${id}-${key}` ? null : `${id}-${key}`)
                                }
                                onKeyToggle={() =>
                                  setOpenTooltip(openTooltip === `${id}-${key}` ? null : `${id}-${key}`)
                                }
                              />
                            )}
                          </label>
                          {isChecked && additionalDesc && !optData?.render_additional_below_card && (
                            <div className="mt-3 ml-7">
                              {showTextInput ? (
                                <div className="p-4 bg-novaNeutral-50 rounded-lg border border-novaNeutral-200">
                                  <p className="text-novaNeutral-700 text-sm leading-relaxed whitespace-pre-line mb-4">
                                    {additionalDesc}
                                  </p>
                                  <textarea
                                    value={(typeof answers[`${id}_${key}`] === "string" ? answers[`${id}_${key}`] : "") as string}
                                    onChange={(e) => setAnswer(`${id}_${key}`, e.target.value)}
                                    placeholder="Tell us more if helpful..."
                                    rows={3}
                                    className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange text-novaNeutral-800"
                                  />
                                </div>
                              ) : (
                                <p className="text-novaNeutral-700 text-sm leading-relaxed whitespace-pre-line">
                                  {additionalDesc}
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {(isTouched || err) && err && (
                      <p className="mt-2 text-sm text-novaCaution-600">{err}</p>
                    )}
                  </div>
                )}

                {q.input_type === "text" && (
                  <div>
                    <input
                      type="text"
                      value={typeof value === "string" ? value : ""}
                      onChange={(e) => setAnswer(id, e.target.value)}
                      onBlur={() => handleBlur(id)}
                      placeholder={q.placeholder || ""}
                      maxLength={(q as QuestionDef & { max_length?: number }).max_length}
                      className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange"
                    />
                    {(isTouched || err) && err && (
                      <p className="mt-1 text-sm text-novaCaution-600">{err}</p>
                    )}
                  </div>
                )}

                {q.input_type === "specialtext" && (
                  <div>
                    <input
                      type="text"
                      inputMode="text"
                      autoComplete="off"
                      spellCheck={false}
                      aria-label={formatEngageQuestion(q.question, answers)}
                      value={formatUkNationalInsuranceInput(typeof value === "string" ? value : "")}
                      onChange={(e) => setAnswer(id, formatUkNationalInsuranceInput(e.target.value))}
                      onBlur={() => handleBlur(id)}
                      placeholder={q.placeholder || "AB-12-34-56-C"}
                      maxLength={13}
                      className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange font-mono tracking-wide"
                    />
                    {(isTouched || err) && err && (
                      <p className="mt-1 text-sm text-novaCaution-600">{err}</p>
                    )}
                  </div>
                )}

                {q.input_type === "date" && (
                  <div>
                    <input
                      type="date"
                      value={typeof value === "string" ? value : ""}
                      onChange={(e) => setAnswer(id, e.target.value)}
                      onBlur={() => handleBlur(id)}
                      className="w-full max-w-xs px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange [color-scheme:light]"
                    />
                    {(isTouched || err) && err && (
                      <p className="mt-1 text-sm text-novaCaution-600">{err}</p>
                    )}
                  </div>
                )}

                {q.input_type === "country" && (
                  <div className="max-w-md">
                    <CountrySelect
                      value={typeof value === "string" && value.trim() ? value : null}
                      onChange={(next) => {
                        setAnswer(id, next);
                        setTouched((p) => ({ ...p, [id]: true }));
                      }}
                      error={(touched[id] || err) && err ? err : undefined}
                    />
                  </div>
                )}

                {q.input_type === "textarea" && (
                  <div>
                    <textarea
                      value={typeof value === "string" ? value : ""}
                      onChange={(e) => setAnswer(id, e.target.value)}
                      onBlur={() => handleBlur(id)}
                      placeholder={q.placeholder || ""}
                      rows={q.rows ?? 4}
                      maxLength={(q as QuestionDef & { max_length?: number }).max_length}
                      className="w-full max-w-2xl min-h-[100px] px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange text-novaNeutral-800"
                    />
                    {(isTouched || err) && err && (
                      <p className="mt-1 text-sm text-novaCaution-600">{err}</p>
                    )}
                  </div>
                )}

                {q.input_type === "form" && q.form_fields && (
                  <div className="space-y-4">
                    {Object.entries(q.form_fields.questions)
                      .sort((a, b) => a[1].question_order - b[1].question_order)
                      .map(([subId, sub]) => {
                        const subVal =
                          typeof value === "object" && value && sub.id in value
                            ? (value as Record<string, string>)[sub.id]
                            : "";
                        const subErr = errors[sub.id];
                        const subTouched = touched[sub.id];
                        return (
                          <div key={sub.id}>
                            <label className="block text-sm font-medium text-novaNeutral-700 mb-1">
                              {sub.question}
                              {sub.required && (
                                <span className="text-novaCaution-500 ml-0.5">*</span>
                              )}
                            </label>
                            {sub.input_type === "country" ? (
                              <div className="max-w-md">
                                <CountrySelect
                                  value={subVal.trim() ? subVal : null}
                                  onChange={(nextCountry) => {
                                    const next = {
                                      ...(typeof value === "object" && value ? value : {}),
                                      [sub.id]: nextCountry,
                                    };
                                    setAnswer(id, next);
                                    setTouched((p) => ({ ...p, [sub.id]: true }));
                                  }}
                                  error={(subTouched || subErr) && subErr ? subErr : undefined}
                                />
                              </div>
                            ) : (
                              <input
                                type="text"
                                value={subVal}
                                onChange={(e) => {
                                  const next = {
                                    ...(typeof value === "object" && value ? value : {}),
                                    [sub.id]: e.target.value,
                                  };
                                  setAnswer(id, next);
                                }}
                                onBlur={() => setTouched((p) => ({ ...p, [sub.id]: true }))}
                                placeholder={sub.placeholder || ""}
                                maxLength={sub.max_length}
                                className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange"
                              />
                            )}
                            {(subTouched || subErr) && subErr && (
                              <p className="mt-1 text-sm text-novaCaution-600">
                                {subErr}
                              </p>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </div>
              {belowCardAdditional && (
                <div className={BELOW_CARD_ADDITIONAL_WRAP}>
                  <div
                    className={BELOW_CARD_ADDITIONAL_RICH}
                    dangerouslySetInnerHTML={{
                      __html: formatEngageQuestion(belowCardAdditional.html, answers),
                    }}
                  />
                </div>
              )}
            </React.Fragment>
            );
          })}
        </div>

        <div className="w-full max-w-6xl mt-8 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            {activeSection > 1 && (
              <button
                type="button"
                onClick={() => setActiveSection((n) => Math.max(1, n - 1))}
                className="inline-flex items-center text-novaNeutral-800 hover:text-novaNeutral-900 text-sm font-medium px-4 py-2 rounded-full border border-novaNeutral-300 bg-white"
              >
                Previous
              </button>
            )}
            <button
              type="button"
              className="text-novaNeutral-600 hover:text-novaNeutral-800 text-sm"
            >
              Cancel All Changes
            </button>
          </div>
          <FormButton
            type="button"
            variant="primary"
            onClick={handleSave}
            loading={saving}
            loadingText="Saving..."
          >
            {activeSection < MAX_ENGAGE_SECTION_NAV ? "Save and Continue" : "Save"}
          </FormButton>
        </div>
      </main>
    </div>
    </Layout>
  );
};

export default EngageForm;
