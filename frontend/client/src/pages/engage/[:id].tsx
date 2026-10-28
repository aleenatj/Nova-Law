import React, { useMemo, useState, useCallback, useRef, useEffect } from "react";
import { Layout, NovaDatePicker } from "@/components";
import { api, ApiError, tokenManager } from "@/lib/api";
import { toastManager, createErrorToast } from "@/utils/toasts";
import { useLocation, useParams } from "wouter";
import CountrySelect from "@/components/ui/country-select/CountrySelect";
import EngageCountrySelect from "@/components/ui/country-select/EngageCountrySelect";
import { engageWelcomeContent, engageSection2Welcome } from "@/config/engageWelcome";
import {
  getEngageSectionConfig,
  ENGAGE_SECTIONS_BUILT,
  ENGAGE_STEPS,
  MAX_ENGAGE_SECTION_NAV,
  ENGAGE_CHILDREN_FORM_GROUP_ID,
  ENGAGE_FAMILY_HOME_FORM_GROUP_OWNER,
  ENGAGE_FAMILY_HOME_FORM_GROUP_RENTED,
  ENGAGE_FAMILY_HOME_HUB_IDS,
  ENGAGE_SECTION7_REPEATABLES,
  getEngageFormQuestionIdsFromJson,
  getQuestionIdsForFormId,
  parseEngageChildrenTable,
  parseEngageFamilyHomeTable,
  parseEngageSection7Table,
  pickFamilyForm2TargetHubForIndexedHydrate,
  resolveEngageIndexedRepeatableMeta,
  serializeEngageChildrenTable,
  serializeEngageFamilyHomeTable,
  serializeEngageIndexedRepeatableRows,
  serializeEngageSection7Table,
  type EngageFamilyHomeTableRow,
  type EngageIndexedRepeatableMeta,
  type EngageSection7Column,
  type EngageSection7TableRow,
  type QuestionDef,
  type SectionConfig,
} from "@/config/engageConfig";
import { FormButton } from "@/utils/formComponents";
import { EngageChildFormModal } from "./EngageChildFormModal";
import { EngageFamilyHomeFormModal } from "./EngageFamilyHomeFormModal";
import {
  ageFromIsoDateString,
  DOB_MIN_AGE_MESSAGE,
  formatEngageQuestion,
  formatSection2WelcomeTitle,
  formatUkNationalInsuranceInput,
  isCompleteUkNationalInsuranceValue,
  getOptionKeyAndLabel,
  getSelectedOptionData,
  isQuestionVisible,
  parseEngageCheckboxKeys,
  toggleEngageCheckboxKey,
  RadioOptionTooltip,
  RICH_HTML_LINKS,
} from "./engageFormShared";
import {
  ENGAGE_ACTIVE_SECTION_EVENT,
  ENGAGE_ACTIVE_SECTION_STORAGE_KEY,
  ENGAGE_CASE_LIST_CATEGORY,
  ENGAGE_CASE_LIST_LIMIT,
  ENGAGE_CASE_LIST_PAGE,
  ENGAGE_CASE_LIST_STATUS,
  ENGAGE_CHILD_FORM_NAME_PART_1,
  ENGAGE_CHILD_FORM_NAME_PART_2,
  ENGAGE_CHILD_FORM_NAME_PART_3,
  ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT,
  ENGAGE_CHILD_Q_ID_DOB,
  ENGAGE_CHILD_Q_ID_GENDER,
  ENGAGE_FAMILY_FORM2_INDEXED_BUCKET_ID,
  ENGAGE_NAVIGATE_SECTION_EVENT,
  ENGAGE_SECTION7_HUB_IDS,
  ENGAGE_SECTION7_REPEATABLE_FORM_IDS,
  ENGAGE_FAMILY_COL_Q223,
  ENGAGE_FAMILY_COL_Q226,
  ENGAGE_FAMILY_COL_Q239,
  ENGAGE_FAMILY_COL_Q240,
  ENGAGE_FAMILY_COL_Q244,
  ENGAGE_FAMILY_COL_Q251,
  ENGAGE_FAMILY_COL_Q254,
  ENGAGE_FAMILY_COL_Q259,
  ENGAGE_FAMILY_HOME_HUB_COHAB,
  ENGAGE_FAMILY_HOME_HUB_OWNER,
  ENGAGE_FAMILY_HOME_HUB_RENTED,
  ENGAGE_FAMILY_HOME_VALUE_OWNER,
  ENGAGE_FAMILY_HOME_VALUE_RENTED,
  ENGAGE_FAMILY_UI_MODE_OWNER,
  ENGAGE_FAMILY_UI_MODE_RENTED,
  ENGAGE_Q_ID_FAMILY_HOME,
  ENGAGE_Q_ID_RELATIONSHIP,
  ENGAGE_RELATIONSHIP_COHABITATION,
  ENGAGE_RELATIONSHIP_PARENTAL,
  ENGAGE_SECTION_SLUG_1,
  ENGAGE_SECTION_SLUG_2,
  ENGAGE_SECTION_SLUG_7,
  ENGAGE_SECTION_SLUG_8,
  ENGAGE_SECTION_SLUG_10,
  ENGAGE_SESSION_CASE_ID_KEY,
  ENGAGE_PROCEEDINGS_ADD_BUTTON_LABEL,
  ENGAGE_PROCEEDINGS_COL_ISSUE_DATE_Q_ID,
  ENGAGE_PROCEEDINGS_COL_STATUS_Q_ID,
  ENGAGE_PROCEEDINGS_FORM_ID,
  ENGAGE_PROCEEDINGS_HUB_Q_ID,
  ENGAGE_PROCEEDINGS_JSON_KEY,
  ENGAGE_PROCEEDINGS_MODAL_TITLE_ADD,
  ENGAGE_PROCEEDINGS_MODAL_TITLE_EDIT,
  ENGAGE_PROCEEDINGS_TABLE_HEADER_ISSUE_DATE,
  ENGAGE_PROCEEDINGS_TABLE_HEADER_STATUS,
  ENGAGE_INCOME_COL_NAME_Q_ID,
  ENGAGE_INCOME_COL_NET_PARTNER_Q_ID,
  ENGAGE_INCOME_COL_NET_YOURS_Q_ID,
  ENGAGE_INCOME_COL_SOURCE_Q_ID,
  ENGAGE_INCOME_FORM_ID,
  ENGAGE_INCOME_HUB_Q_ID,
  ENGAGE_INCOME_JSON_KEY,
} from "./engagePageIds";
import { renderHtmlContent } from "@/utils";

type WelcomeBundle =
  | { variant: "section1"; data: typeof engageWelcomeContent }
  | { variant: "section2"; data: typeof engageSection2Welcome };

const BELOW_CARD_ADDITIONAL_WRAP =
  "bg-white rounded-xl shadow-sm border border-novaNeutral-100 p-6 mt-4";
const BELOW_CARD_ADDITIONAL_RICH = `text-novaNeutral-700 text-sm leading-relaxed [&_strong]:font-bold ${RICH_HTML_LINKS} [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1 [&_p]:mb-2 [&_p:last-child]:mb-0`;
/** Flatten form answer (object of sub-ids to values) for storing under parent id. */
function getFormAnswer(answers: Record<string, string>, subIds: string[]): Record<string, string> {
  const out: Record<string, string> = {};
  subIds.forEach((id) => {
    if (answers[id] !== undefined && answers[id] !== "") out[id] = answers[id];
  });
  return out;
}

function formatChildTableName(a: Record<string, string | Record<string, string>>): string {
  const v = a[ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT];
  if (typeof v !== "object" || !v) return "—";
  const o = v as Record<string, string>;
  const parts = [o[ENGAGE_CHILD_FORM_NAME_PART_1], o[ENGAGE_CHILD_FORM_NAME_PART_2], o[ENGAGE_CHILD_FORM_NAME_PART_3]]
    .map((s) => (typeof s === "string" ? s.trim() : ""))
    .filter(Boolean);
  return parts.length > 0 ? parts.join(" ") : "—";
}

function childRowGenderLabel(
  a: Record<string, string | Record<string, string>>,
  q195: QuestionDef | undefined
): string {
  const key = typeof a[ENGAGE_CHILD_Q_ID_GENDER] === "string" ? a[ENGAGE_CHILD_Q_ID_GENDER] : "";
  if (!key) return "—";
  if (!q195?.options) return key;
  const opt = q195.options.find((o) => Object.keys(o)[0] === key);
  return opt ? getOptionKeyAndLabel(opt)[1] : key;
}

function formatChildTableDob(a: Record<string, string | Record<string, string>>): string {
  const s = typeof a[ENGAGE_CHILD_Q_ID_DOB] === "string" ? a[ENGAGE_CHILD_Q_ID_DOB].trim() : "";
  if (!s) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (m) return `${m[3]}/${m[2]}/${m[1]}`;
  return s;
}

function formatFamilyHomeIsoDate(iso: unknown): string {
  const s = typeof iso === "string" ? iso.trim() : "";
  if (!s) return "—";
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (m) return `${m[3]}/${m[2]}/${m[1]}`;
  return s;
}

function formatFamilyHomeRadioCell(
  q: QuestionDef | undefined,
  val: string | Record<string, string> | undefined,
  answers: Record<string, string | Record<string, string>>
): string {
  if (typeof val !== "string" || !val.trim()) return "—";
  if (!q?.options?.length) return val;
  const opt = q.options.find((o) => Object.keys(o)[0] === val);
  if (!opt) return val;
  return formatEngageQuestion(getOptionKeyAndLabel(opt)[1], answers);
}

function formatSection7TableCell(
  col: EngageSection7Column,
  rowAnswers: Record<string, string | Record<string, string>>,
  config: SectionConfig,
  globalAnswers: Record<string, string | Record<string, string>>
): string {
  const primary = rowAnswers[col.questionId];
  const fallback = col.fallbackQuestionId ? rowAnswers[col.fallbackQuestionId] : undefined;
  const primaryStr = typeof primary === "string" ? primary.trim() : "";
  const fallbackStr = typeof fallback === "string" ? fallback.trim() : "";
  const useStr = primaryStr || fallbackStr;
  if (!useStr) return "—";
  const q = config.questions[col.questionId];
  if (primaryStr && q?.input_type === "radio" && q.options?.length) {
    return formatFamilyHomeRadioCell(q, primaryStr, globalAnswers);
  }
  if (!primaryStr && fallbackStr && col.fallbackQuestionId) {
    const fq = config.questions[col.fallbackQuestionId];
    if (fq?.input_type === "radio" && fq.options?.length) {
      return formatFamilyHomeRadioCell(fq, fallbackStr, globalAnswers);
    }
    return formatEngageQuestion(fallbackStr, globalAnswers);
  }
  if (q?.input_type === "radio" && q.options?.length) {
    return formatFamilyHomeRadioCell(q, useStr, globalAnswers);
  }
  return formatEngageQuestion(useStr, globalAnswers);
}

/**
 * Which hub question (219 / 220 / 221) stores the family-home JSON for the current answers.
 * Uses AND logic matching engage.json rules (not `isQuestionVisible`, which treats rules as OR).
 */
function resolveFamilyHomeHubQuestionId(
  answers: Record<string, string | Record<string, string>>
): string | null {
  const s218 = answers[ENGAGE_Q_ID_FAMILY_HOME];
  if (typeof s218 !== "string" || !s218.trim()) return null;
  const q100 = typeof answers[ENGAGE_Q_ID_RELATIONSHIP] === "string" ? answers[ENGAGE_Q_ID_RELATIONSHIP] : "";

  if (s218 === ENGAGE_FAMILY_HOME_VALUE_RENTED) {
    if (q100 === ENGAGE_RELATIONSHIP_PARENTAL) return null;
    return ENGAGE_FAMILY_HOME_HUB_RENTED;
  }
  if (s218 === ENGAGE_FAMILY_HOME_VALUE_OWNER) {
    if (q100 === ENGAGE_RELATIONSHIP_COHABITATION) return ENGAGE_FAMILY_HOME_HUB_COHAB;
    if (q100 === ENGAGE_RELATIONSHIP_PARENTAL) return null;
    return ENGAGE_FAMILY_HOME_HUB_OWNER;
  }
  return null;
}

/** Rows for the active hub, or any legacy hub key so previously saved data still shows. */
function getFamilyHomeTableRows(
  answers: Record<string, string | Record<string, string>>,
  familyHubId: string | null
): EngageFamilyHomeTableRow[] {
  if (!familyHubId) return [];
  const direct = parseEngageFamilyHomeTable(
    typeof answers[familyHubId] === "string" ? answers[familyHubId] : undefined
  );
  if (direct.length > 0) return direct;
  for (const hid of ENGAGE_FAMILY_HOME_HUB_IDS) {
    if (hid === familyHubId) continue;
    const alt = parseEngageFamilyHomeTable(
      typeof answers[hid] === "string" ? answers[hid] : undefined
    );
    if (alt.length > 0) return alt;
  }
  return [];
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

/** e.g. `337[0]` → base `337`, row `0`; `337.1[2]` → base `337.1`, row `2`. */
const ENGAGE_INDEXED_QID_RE = /^(.+)\[(\d+)\]$/;

/** One cell in a row: scalar field or nested object (same shape as `hydrateAnswersFromEngageGet` dot-keys). */
function setEngageRowFieldNested(
  row: Record<string, string | Record<string, string>>,
  fullFieldId: string,
  value: string
): void {
  const dot = fullFieldId.indexOf(".");
  if (dot === -1) {
    row[fullFieldId] = value;
    return;
  }
  const parent = fullFieldId.slice(0, dot);
  const prev = row[parent];
  const obj =
    typeof prev === "object" && prev !== null && !Array.isArray(prev)
      ? { ...(prev as Record<string, string>) }
      : {};
  obj[fullFieldId] = value;
  row[parent] = obj;
}

/** Map GET /v1/engage payload (sections → lists of question blocks) into `answers` state. */
function hydrateAnswersFromEngageGet(
  data: Record<string, Array<Record<string, { version?: string; answer?: unknown }>>>
): Record<string, string | Record<string, string>> {
  const out: Record<string, string | Record<string, string>> = {};
  const indexedBuckets = new Map<string, Map<number, Record<string, string | Record<string, string>>>>();
  const indexedMetaByHub = new Map<string, EngageIndexedRepeatableMeta>();

  for (const sectionList of Object.values(data)) {
    if (!Array.isArray(sectionList)) continue;
    for (const item of sectionList) {
      if (!item || typeof item !== "object") continue;
      for (const [qid, block] of Object.entries(item)) {
        const raw = block?.answer;
        const list = Array.isArray(raw) ? raw : raw != null ? [raw] : [];
        const str = list.length > 0 ? extractEngageAnswerValue(list[0]) : "";

        const indexedMatch = ENGAGE_INDEXED_QID_RE.exec(qid);
        if (indexedMatch) {
          const baseId = indexedMatch[1];
          const rowIdx = parseInt(indexedMatch[2], 10);
          const meta = resolveEngageIndexedRepeatableMeta(baseId);
          if (meta) {
            if (meta.storage === "familyForm2Pending") {
              indexedMetaByHub.set(ENGAGE_FAMILY_FORM2_INDEXED_BUCKET_ID, meta);
              if (!indexedBuckets.has(ENGAGE_FAMILY_FORM2_INDEXED_BUCKET_ID)) {
                indexedBuckets.set(ENGAGE_FAMILY_FORM2_INDEXED_BUCKET_ID, new Map());
              }
              const rowMap = indexedBuckets.get(ENGAGE_FAMILY_FORM2_INDEXED_BUCKET_ID)!;
              if (!rowMap.has(rowIdx)) rowMap.set(rowIdx, {});
              setEngageRowFieldNested(rowMap.get(rowIdx)!, baseId, str);
            } else {
              indexedMetaByHub.set(meta.hubId, meta);
              if (!indexedBuckets.has(meta.hubId)) indexedBuckets.set(meta.hubId, new Map());
              const rowMap = indexedBuckets.get(meta.hubId)!;
              if (!rowMap.has(rowIdx)) rowMap.set(rowIdx, {});
              setEngageRowFieldNested(rowMap.get(rowIdx)!, baseId, str);
            }
          }
          continue;
        }

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

  for (const [hubId, rowMap] of Array.from(indexedBuckets.entries())) {
    const meta = indexedMetaByHub.get(hubId);
    if (!meta) continue;
    const rows: EngageSection7TableRow[] = Array.from(rowMap)
      .sort((a, b) => a[0] - b[0])
      .map(([, answers]) => ({ answers }));
    if (hubId === ENGAGE_FAMILY_FORM2_INDEXED_BUCKET_ID) {
      out[pickFamilyForm2TargetHubForIndexedHydrate(out)] = serializeEngageIndexedRepeatableRows(meta, rows);
    } else {
      out[hubId] = serializeEngageIndexedRepeatableRows(meta, rows);
    }
  }

  return out;
}

/** Resolve engage case id preferring route `/engage/:id`, then session fallback. */
function getEngageCaseId(routeId?: string): string | null {
  if (routeId && routeId.trim()) {
    sessionStorage.setItem(ENGAGE_SESSION_CASE_ID_KEY, routeId);
    return routeId;
  }
  const fromSession = sessionStorage.getItem(ENGAGE_SESSION_CASE_ID_KEY);
  if (fromSession) return fromSession;
  return null;
}

/** One table row → PATCH keys `subId[rowIdx]` (and dotted nested sub-ids from nested form objects). */
function appendEngageIndexedRowPatches(
  out: Array<{ question_identifier: string; answer: { value: string } }>,
  rowAnswers: Record<string, string | Record<string, string>>,
  rowIdx: number
): void {
  for (const [key, val] of Object.entries(rowAnswers)) {
    if (val === undefined) continue;
    if (typeof val === "string") {
      out.push({ question_identifier: `${key}[${rowIdx}]`, answer: { value: val } });
    } else if (typeof val === "object" && val !== null && !Array.isArray(val)) {
      for (const [subKey, subVal] of Object.entries(val)) {
        if (typeof subVal !== "string") continue;
        out.push({ question_identifier: `${subKey}[${rowIdx}]`, answer: { value: subVal } });
      }
    }
  }
}

/**
 * Repeatable hub questions store JSON rows in state; PATCH sends one field per cell as `id[index]`
 * instead of the whole hub blob (empty table still PATCHes the legacy JSON string to clear).
 */
function tryExpandRepeatableHubToIndexedPatch(
  id: string,
  answers: Record<string, string | Record<string, string>>,
  out: Array<{ question_identifier: string; answer: { value: string } }>
): boolean {
  const raw = answers[id];
  if (typeof raw !== "string") return false;

  if (id === ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT) {
    const rows = parseEngageChildrenTable(raw);
    if (rows.length === 0) {
      out.push({ question_identifier: id, answer: { value: raw } });
    } else {
      rows.forEach((row, i) => appendEngageIndexedRowPatches(out, row.answers, i));
    }
    return true;
  }

  if ((ENGAGE_FAMILY_HOME_HUB_IDS as readonly string[]).includes(id)) {
    const rows = parseEngageFamilyHomeTable(raw);
    if (rows.length === 0) {
      out.push({ question_identifier: id, answer: { value: raw } });
    } else {
      rows.forEach((row, i) => appendEngageIndexedRowPatches(out, row.answers, i));
    }
    return true;
  }

  const s7def = ENGAGE_SECTION7_REPEATABLES.find((d) => d.hubId === id);
  if (s7def) {
    const rows = parseEngageSection7Table(raw, s7def.jsonKey);
    if (rows.length === 0) {
      out.push({ question_identifier: id, answer: { value: raw } });
    } else {
      rows.forEach((row, i) => appendEngageIndexedRowPatches(out, row.answers, i));
    }
    return true;
  }

  if (id === ENGAGE_INCOME_HUB_Q_ID) {
    const rows = parseEngageSection7Table(raw, ENGAGE_INCOME_JSON_KEY);
    if (rows.length === 0) {
      out.push({ question_identifier: id, answer: { value: raw } });
    } else {
      rows.forEach((row, i) => appendEngageIndexedRowPatches(out, row.answers, i));
    }
    return true;
  }

  if (id === ENGAGE_PROCEEDINGS_HUB_Q_ID) {
    const rows = parseEngageSection7Table(raw, ENGAGE_PROCEEDINGS_JSON_KEY);
    if (rows.length === 0) {
      out.push({ question_identifier: id, answer: { value: raw } });
    } else {
      rows.forEach((row, i) => appendEngageIndexedRowPatches(out, row.answers, i));
    }
    return true;
  }

  return false;
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

    if (tryExpandRepeatableHubToIndexedPatch(id, answers, out)) continue;

    if (q.input_type === "form" && q.form_fields) {
      const obj = answers[id];
      if (typeof obj !== "object" || !obj) continue;
      for (const subId of Object.keys(q.form_fields.questions)) {
        const subVal = obj[subId];
        if (subVal === undefined) continue;
        out.push({ question_identifier: subId, answer: { value: String(subVal) } });
      }
    } else {
      const val = answers[id];
      if (val === undefined) continue;
      if (typeof val === "object") continue;
      out.push({ question_identifier: id, answer: { value: String(val) } });
    }

    /** Optional text under a radio/checkbox option uses `${id}_${optionKey}` in state; must PATCH (including `""` to clear). */
    if ((q.input_type === "radio" || q.input_type === "checkbox") && q.options) {
      for (const opt of q.options) {
        const [key] = getOptionKeyAndLabel(opt);
        const optData = opt[Object.keys(opt)[0]] as { show_text_input?: boolean } | undefined;
        if (optData?.show_text_input !== true) continue;
        const compositeId = `${id}_${key}`;
        const extra = answers[compositeId];
        if (typeof extra !== "string") continue;
        out.push({ question_identifier: compositeId, answer: { value: extra } });
      }
    }
  }
  return out;
}

function readInitialEngageSection(): number {
  try {
    const raw = sessionStorage.getItem(ENGAGE_ACTIVE_SECTION_STORAGE_KEY);
    const n = parseInt(raw || ENGAGE_SECTION_SLUG_1, 10);
    if (Number.isFinite(n) && n >= 1 && n <= MAX_ENGAGE_SECTION_NAV) return n;
  } catch {
    /* ignore */
  }
  return 1;
}

function normalizeSectionTitleKey(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

/**
 * Maps GET `data` section keys to sidebar step numbers using `ENGAGE_STEPS` titles (order-independent).
 */
function getEngagePresentStepsFromData(
  data: Record<string, Array<Record<string, { version?: string; answer?: unknown }>>>
): number[] {
  const present = new Set<number>();
  for (const key of Object.keys(data)) {
    const normalizedKey = normalizeSectionTitleKey(key);
    const idx = ENGAGE_STEPS.findIndex(
      (step) => normalizeSectionTitleKey(step.title) === normalizedKey
    );
    if (idx >= 0) present.add(idx + 1);
  }
  if (present.size === 0) return [];
  return Array.from(present).sort((a, b) => a - b);
}

/**
 * Sidebar enables completed steps (from GET) plus the next step; main view opens on that next step.
 * If nothing maps from payload, falls back to step 1 only (same as empty section map).
 */
function getEngageSidebarEnabledStepsAndActive(
  completedSteps: number[],
  maxNav: number
): { enabledSteps: number[]; activeSection: number } {
  if (completedSteps.length === 0) {
    return { enabledSteps: [1], activeSection: 1 };
  }
  const sorted = [...completedSteps].sort((a, b) => a - b);
  const highestCompleted = sorted[sorted.length - 1];
  const nextSection = highestCompleted < maxNav ? highestCompleted + 1 : maxNav;
  const enabled = new Set(sorted);
  if (nextSection > highestCompleted) enabled.add(nextSection);
  const enabledSteps = Array.from(enabled).sort((a, b) => a - b);
  return { enabledSteps, activeSection: nextSection };
}

const EngageForm: React.FC = () => {
  const params = useParams<{ id?: string }>();
  const routeCaseId = params.id;
  const [, setLocation] = useLocation();
  const [activeSection, setActiveSection] = useState(readInitialEngageSection);
  const [answers, setAnswers] = useState<Record<string, string | Record<string, string>>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [openTooltip, setOpenTooltip] = useState<string | null>(null);
  const [childModalOpen, setChildModalOpen] = useState(false);
  const [childModalEditIndex, setChildModalEditIndex] = useState<number | null>(null);
  const [familyModalOpen, setFamilyModalOpen] = useState(false);
  const [familyModalEditIndex, setFamilyModalEditIndex] = useState<number | null>(null);
  const [s7Modal, setS7Modal] = useState<{
    hubId: string;
    formId: string;
    editIndex: number | null;
  } | null>(null);
  const [incomeModalOpen, setIncomeModalOpen] = useState(false);
  const [incomeModalEditIndex, setIncomeModalEditIndex] = useState<number | null>(null);
  const [proceedingsModalOpen, setProceedingsModalOpen] = useState(false);
  const [proceedingsModalEditIndex, setProceedingsModalEditIndex] = useState<number | null>(null);
  const firstErrorRef = React.useRef<HTMLDivElement | null>(null);

  const sectionSlug = String(activeSection);

  /** Same resolution as GET /v1/engage (query or session); used so we can mark case ready before first effect runs. */
  const initialEngageCaseId =
    typeof window !== "undefined" ? getEngageCaseId(routeCaseId) : null;
  const [engageCaseId, setEngageCaseId] = useState<string | null>(initialEngageCaseId);
  /** True once we know the case id (from URL/session now, or from /v1/case after load). */
  const [caseIdReady, setCaseIdReady] = useState(() => initialEngageCaseId !== null);
  /** Step numbers that appear in GET `data` (by section title). `null` = engage GET not applied yet. */
  const [engageDataPresentSteps, setEngageDataPresentSteps] = useState<number[] | null>(null);
  const engageBackLink = useMemo(() => {
    const idForBack = routeCaseId || engageCaseId;
    if (!idForBack) return "/case-dashboard";
    return `/case/${encodeURIComponent(idForBack)}`;
  }, [routeCaseId, engageCaseId]);

  /** If no case in session/query, load the customer’s first open case (same listing as case dashboard). */
  useEffect(() => {
    const sync = getEngageCaseId(routeCaseId);
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
          page: ENGAGE_CASE_LIST_PAGE,
          limit: ENGAGE_CASE_LIST_LIMIT,
          category: ENGAGE_CASE_LIST_CATEGORY,
          case_status: ENGAGE_CASE_LIST_STATUS,
        });
        const r = await api.get<{ data?: { cases?: Array<{ id: string }> } }>(
          `/v1/case?${params.toString()}`
        );
        const id = r.data?.cases?.[0]?.id;
        if (!cancelled && id) {
          sessionStorage.setItem(ENGAGE_SESSION_CASE_ID_KEY, id);
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
    const caseId = engageCaseId ?? getEngageCaseId(routeCaseId);
    if (!caseId || !tokenManager.getAccessToken()) return;
    try {
      const res = await api.get<unknown>(
        `/v1/engage?case_id=${encodeURIComponent(caseId)}`
      );
      const payload = unwrapEngageGetData(res);
      if (!payload) {
        // Successful GET with no `data` yet — sidebar only allows step 1 (About you).
        setEngageDataPresentSteps([1]);
        setActiveSection(1);
        return;
      }
      const merged = hydrateAnswersFromEngageGet(payload);
      setAnswers((prev) => ({ ...prev, ...merged }));
      const keys = Object.keys(payload);
      if (keys.length === 0) {
        setEngageDataPresentSteps([1]);
        setActiveSection(1);
      } else {
        const present = getEngagePresentStepsFromData(payload);
        const { enabledSteps, activeSection: nextActive } = getEngageSidebarEnabledStepsAndActive(
          present,
          MAX_ENGAGE_SECTION_NAV
        );
        setEngageDataPresentSteps(enabledSteps);
        setActiveSection(nextActive);
      }
    } catch {
      /* non-blocking */
    }
  }, [engageCaseId, routeCaseId]);

  // Prevent full page reloads for internal links rendered from rich HTML snippets.
  const handleInternalLinkNavigation = useCallback(
    (e: React.MouseEvent<HTMLElement>) => {
      const target = e.target as HTMLElement | null;
      const anchor = target?.closest("a");
      if (!anchor) return;
      const href = anchor.getAttribute("href");
      if (!href || href.startsWith("#")) return;
      if (href.startsWith("http://") || href.startsWith("https://") || href.startsWith("mailto:")) {
        return;
      }
      e.preventDefault();
      setLocation(href);
    },
    [setLocation]
  );

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
    if (sectionSlug !== ENGAGE_SECTION_SLUG_7) setS7Modal(null);
  }, [sectionSlug]);

  useEffect(() => {
    if (sectionSlug !== ENGAGE_SECTION_SLUG_8) {
      setIncomeModalOpen(false);
      setIncomeModalEditIndex(null);
    }
    if (sectionSlug !== ENGAGE_SECTION_SLUG_10) {
      setProceedingsModalOpen(false);
      setProceedingsModalEditIndex(null);
    }
  }, [sectionSlug]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
    sessionStorage.setItem(ENGAGE_ACTIVE_SECTION_STORAGE_KEY, String(activeSection));
    window.dispatchEvent(
      new CustomEvent(ENGAGE_ACTIVE_SECTION_EVENT, {
        detail: {
          section: activeSection,
          presentEngageSteps: engageDataPresentSteps,
        },
      })
    );
  }, [activeSection, engageDataPresentSteps]);

  const isSectionBuilt = ENGAGE_SECTIONS_BUILT.has(sectionSlug);

  const config = useMemo(
    (): SectionConfig => getEngageSectionConfig(sectionSlug),
    [sectionSlug]
  );

  const welcome = useMemo((): WelcomeBundle | null => {
    if (!isSectionBuilt) return null;
    if (sectionSlug === ENGAGE_SECTION_SLUG_1) return { variant: "section1", data: engageWelcomeContent };
    if (sectionSlug === ENGAGE_SECTION_SLUG_2) return { variant: "section2", data: engageSection2Welcome };
    return null;
  }, [sectionSlug, isSectionBuilt]);

  const childFormQuestionIds = useMemo(
    () => getQuestionIdsForFormId(config, ENGAGE_CHILDREN_FORM_GROUP_ID),
    [config]
  );

  const familyFormQuestionIdsOwner = useMemo(
    () => getQuestionIdsForFormId(config, ENGAGE_FAMILY_HOME_FORM_GROUP_OWNER),
    [config]
  );
  const familyFormQuestionIdsRented = useMemo(
    () => getQuestionIdsForFormId(config, ENGAGE_FAMILY_HOME_FORM_GROUP_RENTED),
    [config]
  );

  const proceedingsFormQuestionIds = useMemo(
    () => getQuestionIdsForFormId(config, ENGAGE_PROCEEDINGS_FORM_ID),
    [config]
  );

  const visibleOrder = useMemo(() => {
    return config.questionOrder.filter((id) => {
      const q = config.questions[id];
      if (!q || !isQuestionVisible(q, answers)) return false;
      if (q.form_id === ENGAGE_CHILDREN_FORM_GROUP_ID) return false;
      if (
        q.form_id === ENGAGE_FAMILY_HOME_FORM_GROUP_OWNER ||
        q.form_id === ENGAGE_FAMILY_HOME_FORM_GROUP_RENTED
      ) {
        return false;
      }
      /** Hub cards (219–221) render under question 218 instead — avoids duplicate tables/modals. */
      if ((ENGAGE_FAMILY_HOME_HUB_IDS as readonly string[]).includes(id)) return false;
      /** Section 7: form fields (4–9) render in hub tables + modal; hub questions (281, 303, …) must stay in order. */
      if (
        sectionSlug === ENGAGE_SECTION_SLUG_7 &&
        q.form_id &&
        ENGAGE_SECTION7_REPEATABLE_FORM_IDS.has(q.form_id) &&
        !(ENGAGE_SECTION7_HUB_IDS as readonly string[]).includes(id)
      ) {
        return false;
      }
      /** Section 8: render only hub question 399 as repeatable table; other form 10 fields live in modal. */
      if (
        sectionSlug === ENGAGE_SECTION_SLUG_8 &&
        q.form_id === ENGAGE_INCOME_FORM_ID &&
        id !== ENGAGE_INCOME_HUB_Q_ID
      ) {
        return false;
      }
      /** Section 10: only hub q452 (`ENGAGE_PROCEEDINGS_HUB_Q_ID`) as proceedings table; other form 11 fields live in modal. */
      if (
        sectionSlug === ENGAGE_SECTION_SLUG_10 &&
        q.form_id === ENGAGE_PROCEEDINGS_FORM_ID &&
        id !== ENGAGE_PROCEEDINGS_HUB_Q_ID
      ) {
        return false;
      }
      return true;
    });
  }, [answers, config, sectionSlug]);

  const familyHubId = useMemo(
    () => resolveFamilyHomeHubQuestionId(answers),
    [answers]
  );

  /** Hub answers must be PATCHed even though 219–221 are not in `visibleOrder`. */
  const visibleOrderForPatch = useMemo(() => {
    if (familyHubId && !visibleOrder.includes(familyHubId)) {
      return [...visibleOrder, familyHubId];
    }
    return visibleOrder;
  }, [visibleOrder, familyHubId]);

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
    if (familyHubId && errors[familyHubId]) return familyHubId;
    if (sectionSlug === ENGAGE_SECTION_SLUG_7) {
      for (const hid of ENGAGE_SECTION7_HUB_IDS) {
        if (errors[hid]) return hid;
      }
    }
    return null;
  }, [errors, visibleOrder, config, familyHubId, sectionSlug]);

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

      if (id === ENGAGE_PROCEEDINGS_HUB_Q_ID && sectionSlug === ENGAGE_SECTION_SLUG_10) {
        if (config.section.required) {
          const rows = parseEngageSection7Table(
            typeof answers[id] === "string" ? answers[id] : undefined,
            ENGAGE_PROCEEDINGS_JSON_KEY
          );
          if (rows.length === 0) {
            newErrors[id] = "Add your proceedings details.";
            touchIds[id] = true;
          }
        }
        return;
      }

      if (id === ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT) {
        if (q.required) {
          const rows = parseEngageChildrenTable(
            typeof answers[id] === "string" ? answers[id] : undefined
          );
          if (rows.length === 0) {
            newErrors[id] = "Add at least one child.";
            touchIds[id] = true;
          }
        }
        return;
      }

      if (
        sectionSlug === ENGAGE_SECTION_SLUG_7 &&
        (ENGAGE_SECTION7_HUB_IDS as readonly string[]).includes(id)
      ) {
        const def = ENGAGE_SECTION7_REPEATABLES.find((h) => h.hubId === id);
        if (!def) return;
        if (q.required) {
          const rows = parseEngageSection7Table(
            typeof answers[id] === "string" ? answers[id] : undefined,
            def.jsonKey
          );
          if (rows.length === 0) {
            newErrors[id] = "Add at least one entry.";
            touchIds[id] = true;
          }
        }
        return;
      }

      const val = answers[id];

      if (!q.required) {
        if (q.input_type === "text" || q.input_type === "textarea" || q.input_type === "number") {
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
      if (q.input_type === "country" || q.input_type === "selectbox") {
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

    if (familyHubId) {
      const hq = config.questions[familyHubId];
      if (hq?.required) {
        const rows = getFamilyHomeTableRows(answers, familyHubId);
        if (rows.length === 0) {
          newErrors[familyHubId] = "Add at least one family home.";
          touchIds[familyHubId] = true;
        }
      }
    }

    setErrors(newErrors);
    setTouched((prev) => ({ ...prev, ...touchIds }));
    if (Object.keys(newErrors).length > 0) {
      setTimeout(() => firstErrorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 100);
    }
    return Object.keys(newErrors).length === 0;
  }, [answers, visibleOrder, config, familyHubId, sectionSlug]);

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
    const caseId = engageCaseId ?? getEngageCaseId(routeCaseId);
    if (!caseId) {
      toastManager.addToast(
        createErrorToast(
          "Cannot save",
          "No case could be linked. Open Nova Engage from your case timeline, or ensure you have an open case."
        )
      );
      return;
    }

    const patchAnswers = buildEngagePatchAnswers(config, answers, visibleOrderForPatch);
    /** Required fields are already valid; empty patch means no new answers to persist (e.g. only optional fields skipped). */
    if (patchAnswers.length === 0) {
      const sectionFrom = activeSection;
      setSaving(true);
      try {
        await refetchEngageAnswers();
        setEngageDataPresentSteps((prev) => {
          const fromGet = prev ?? [];
          const merged = new Set(fromGet);
          merged.add(sectionFrom);
          if (sectionFrom < MAX_ENGAGE_SECTION_NAV) merged.add(sectionFrom + 1);
          return Array.from(merged).sort((a, b) => a - b);
        });
        if (sectionFrom < MAX_ENGAGE_SECTION_NAV) {
          setActiveSection(sectionFrom + 1);
        }
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
      // Refetch already sets active section to the next step from GET + sidebar rules; do not increment again.
      await refetchEngageAnswers();
    } catch (e) {
      if (e instanceof ApiError && e.status === 400) {
        return;
      }
      const msg = e instanceof Error ? e.message : "Could not save your answers.";
      toastManager.addToast(createErrorToast("Save failed", msg));
    } finally {
      setSaving(false);
    }
  }, [
    validate,
    isSectionBuilt,
    activeSection,
    config,
    answers,
    visibleOrderForPatch,
    engageCaseId,
    caseIdReady,
    refetchEngageAnswers,
    routeCaseId,
  ]);

  return (
    <Layout
      showBackButton
      backButtonLink={engageBackLink}
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
        <main
          className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 pt-6 pb-28 md:pb-32 w-full min-w-0 px-4 md:px-[60px] lg:px-[100px] 2xl:px-[180px]"
          onClick={handleInternalLinkNavigation}
        >
          <div className="gap-4 flex flex-col">
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
            visibleOrder.map((id, index) => {
            const q = config.questions[id];
            if (!q) return null;
            const value = answers[id];
            const err = errors[id];
            const isTouched = touched[id];
            const isLastQuestion = index === visibleOrder.length - 1;
            const lastQuestionFooterClearance =
              isLastQuestion ? (
                <div className="h-24 shrink-0 md:h-28" aria-hidden />
              ) : null;

            if (id === ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT) {
              const rows = parseEngageChildrenTable(
                typeof value === "string" ? value : undefined
              );
              const q195 = config.questions[ENGAGE_CHILD_Q_ID_GENDER];
              return (
                <React.Fragment key={id}>
                  <div
                    ref={firstErrorId === id ? firstErrorRef : undefined}
                    className={`bg-white rounded-xl shadow-sm border p-6 ${
                      err ? "border-novaCaution-400" : "border-novaNeutral-100"
                    }`}
                  >
                    <h3 className="text-novaNeutral-900 font-medium mb-2 flex flex-wrap items-center gap-2">
                      <span>{formatEngageQuestion(q.title || q.question, answers)}</span>
                      {q.required && <span className="text-novaCaution-500">*</span>}
                    </h3>
                    {q.placeholder && (
                      <p className="text-novaNeutral-600 text-sm mb-4">{q.placeholder}</p>
                    )}
                    <div className="overflow-x-auto border border-novaNeutral-100 rounded-lg">
                      <table className="w-full text-sm text-left">
                        <thead className="bg-novaNeutral-50 text-novaNeutral-700 font-medium">
                          <tr>
                            <th className="px-4 py-3">Name</th>
                            <th className="px-4 py-3">Gender</th>
                            <th className="px-4 py-3">Date of birth</th>
                            <th className="px-4 py-3 text-right w-[1%] whitespace-nowrap">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((row, idx) => (
                            <tr key={idx} className="border-t border-novaNeutral-100">
                              <td className="px-4 py-3 text-novaNeutral-900">
                                {formatChildTableName(row.answers)}
                              </td>
                              <td className="px-4 py-3 text-novaNeutral-800">
                                {childRowGenderLabel(row.answers, q195)}
                              </td>
                              <td className="px-4 py-3 text-novaNeutral-800">
                                {formatChildTableDob(row.answers)}
                              </td>
                              <td className="px-4 py-3 text-right whitespace-nowrap space-x-3">
                                <button
                                  type="button"
                                  className="text-novaDarkOrange text-sm font-medium hover:underline"
                                  onClick={() => {
                                    setChildModalEditIndex(idx);
                                    setChildModalOpen(true);
                                  }}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="text-novaNeutral-600 text-sm hover:text-novaCaution-600"
                                  onClick={() => {
                                    const next = rows.filter((_, i) => i !== idx);
                                    setAnswer(id, serializeEngageChildrenTable(next));
                                  }}
                                >
                                  Remove
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {rows.length === 0 && (
                      <p className="text-sm text-novaNeutral-600 mt-3">No children added yet.</p>
                    )}
                    {(
                      <button
                        type="button"
                        onClick={() => {
                          setChildModalEditIndex(null);
                          setChildModalOpen(true);
                        }}
                        className="mt-4 inline-flex items-center px-5 py-2.5 rounded-full text-sm font-medium text-white bg-novaDarkOrange hover:opacity-95"
                      >
                        Add Child
                      </button>
                    )}
                    {(isTouched || err) && err && (
                      <p className="mt-3 text-sm text-novaCaution-600">{err}</p>
                    )}
                    <EngageChildFormModal
                      open={childModalOpen}
                      globalAnswers={answers}
                      config={config}
                      formQuestionIds={childFormQuestionIds}
                      initialDraft={
                        childModalEditIndex !== null && rows[childModalEditIndex]
                          ? rows[childModalEditIndex].answers
                          : null
                      }
                      onClose={() => {
                        setChildModalOpen(false);
                        setChildModalEditIndex(null);
                      }}
                      onSubmit={(draft) => {
                        const current = parseEngageChildrenTable(
                          typeof answers[id] === "string" ? answers[id] : undefined
                        );
                        const nextRows = [...current];
                        if (childModalEditIndex !== null) {
                          nextRows[childModalEditIndex] = { answers: draft };
                        } else {
                          nextRows.push({ answers: draft });
                        }
                        setAnswer(id, serializeEngageChildrenTable(nextRows));
                        setChildModalOpen(false);
                        setChildModalEditIndex(null);
                      }}
                    />
                  </div>
                  {lastQuestionFooterClearance}
                </React.Fragment>
              );
            }

            if ((ENGAGE_SECTION7_HUB_IDS as readonly string[]).includes(id)) {
              const def = ENGAGE_SECTION7_REPEATABLES.find((h) => h.hubId === id);
              if (!def) return null;
              const rawHub = answers[id];
              const rows = parseEngageSection7Table(
                typeof rawHub === "string" ? rawHub : undefined,
                def.jsonKey
              );
              const hubErr = errors[id];
              const hubTouched = touched[id];
              return (
                <React.Fragment key={id}>
                  <div
                    ref={firstErrorId === id ? firstErrorRef : undefined}
                    className={`bg-white rounded-xl shadow-sm border p-6 ${
                      hubErr ? "border-novaCaution-400" : "border-novaNeutral-100"
                    }`}
                  >
                    <h3 className="text-novaNeutral-900 font-medium mb-2 flex flex-wrap items-center gap-2">
                      <span>{formatEngageQuestion(q.title || q.question, answers)}</span>
                      {q.required && <span className="text-novaCaution-500">*</span>}
                    </h3>
                    {q.description && (
                      <p className="text-novaNeutral-600 text-sm mb-4">{q.description}</p>
                    )}
                    <div className="overflow-x-auto border border-novaNeutral-100 rounded-lg">
                      <table className="w-full text-sm text-left min-w-[520px]">
                        <thead className="bg-novaNeutral-50 text-novaNeutral-700 font-medium">
                          <tr>
                            {def.tableColumns.map((col) => (
                              <th key={col.questionId} className="px-4 py-3">
                                {col.header}
                              </th>
                            ))}
                            <th className="px-4 py-3 text-right w-[1%] whitespace-nowrap">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((row, idx) => (
                            <tr key={idx} className="border-t border-novaNeutral-100">
                              {def.tableColumns.map((col) => (
                                <td
                                  key={col.questionId}
                                  className="px-4 py-3 text-novaNeutral-800 align-top"
                                >
                                  {formatSection7TableCell(col, row.answers, config, answers)}
                                </td>
                              ))}
                              <td className="px-4 py-3 text-right whitespace-nowrap align-top space-x-3">
                                <button
                                  type="button"
                                  className="text-novaDarkOrange text-sm font-medium hover:underline"
                                  onClick={() => {
                                    setS7Modal({
                                      hubId: def.hubId,
                                      formId: def.formId,
                                      editIndex: idx,
                                    });
                                  }}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="text-novaNeutral-600 text-sm hover:text-novaCaution-600"
                                  onClick={() => {
                                    const next = rows.filter((_, i) => i !== idx);
                                    setAnswer(id, serializeEngageSection7Table(def.jsonKey, next));
                                  }}
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {rows.length === 0 && (
                      <p className="text-sm text-novaNeutral-600 mt-3">No entries yet.</p>
                    )}
                    <button
                      type="button"
                      onClick={() => {
                        setS7Modal({
                          hubId: def.hubId,
                          formId: def.formId,
                          editIndex: null,
                        });
                      }}
                      className="mt-4 inline-flex items-center px-5 py-2.5 rounded-full text-sm font-medium text-white bg-novaDarkOrange hover:opacity-95"
                    >
                      {def.addButtonLabel}
                    </button>
                    {(hubTouched || hubErr) && hubErr && (
                      <p className="mt-3 text-sm text-novaCaution-600">{hubErr}</p>
                    )}
                  </div>
                  {lastQuestionFooterClearance}
                </React.Fragment>
              );
            }

            if (sectionSlug === ENGAGE_SECTION_SLUG_8 && id === ENGAGE_INCOME_HUB_Q_ID) {
              const rows = parseEngageSection7Table(
                typeof value === "string" ? value : undefined,
                ENGAGE_INCOME_JSON_KEY
              );
              const hubErr = errors[id];
              const hubTouched = touched[id];
              const incomeColumns: EngageSection7Column[] = [
                {
                  questionId: ENGAGE_INCOME_COL_SOURCE_Q_ID,
                  header: "Sources of income",
                },
                {
                  questionId: ENGAGE_INCOME_COL_NAME_Q_ID,
                  header: "Name of income source",
                },
                {
                  questionId: ENGAGE_INCOME_COL_NET_YOURS_Q_ID,
                  header: "Your NET income from this income source in the last 12 months",
                },
                {
                  questionId: ENGAGE_INCOME_COL_NET_PARTNER_Q_ID,
                  header: "Your partner's NET income from this income source in the last 12 months",
                },
              ];
              return (
                <React.Fragment key={id}>
                  <div
                    ref={firstErrorId === id ? firstErrorRef : undefined}
                    className={`bg-white rounded-xl shadow-sm border p-6 ${
                      hubErr ? "border-novaCaution-400" : "border-novaNeutral-100"
                    }`}
                  >
                    <h3 className="text-novaNeutral-900 font-medium mb-2 flex flex-wrap items-center gap-2">
                      <span>{formatEngageQuestion(q.title || q.question, answers)}</span>
                      {q.required && <span className="text-novaCaution-500">*</span>}
                    </h3>
                    {q.description && (
                      <p className="text-novaNeutral-600 text-sm mb-4">{q.description}</p>
                    )}
                    <div className="overflow-x-auto border border-novaNeutral-100 rounded-lg">
                      <table className="w-full text-sm text-left min-w-[920px]">
                        <thead className="bg-novaNeutral-50 text-novaNeutral-700 font-medium">
                          <tr>
                            {incomeColumns.map((col) => (
                              <th key={col.questionId} className="px-4 py-3">
                                {col.header}
                              </th>
                            ))}
                            <th className="px-4 py-3 text-right w-[1%] whitespace-nowrap">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((row, idx) => (
                            <tr key={idx} className="border-t border-novaNeutral-100">
                              {incomeColumns.map((col) => (
                                <td
                                  key={col.questionId}
                                  className="px-4 py-3 text-novaNeutral-800 align-top"
                                >
                                  {formatSection7TableCell(col, row.answers, config, answers)}
                                </td>
                              ))}
                              <td className="px-4 py-3 text-right whitespace-nowrap align-top space-x-3">
                                <button
                                  type="button"
                                  className="text-novaDarkOrange text-sm font-medium hover:underline"
                                  onClick={() => {
                                    setIncomeModalEditIndex(idx);
                                    setIncomeModalOpen(true);
                                  }}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="text-novaNeutral-600 text-sm hover:text-novaCaution-600"
                                  onClick={() => {
                                    const next = rows.filter((_, i) => i !== idx);
                                    setAnswer(id, serializeEngageSection7Table(ENGAGE_INCOME_JSON_KEY, next));
                                  }}
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {rows.length === 0 && (
                      <p className="text-sm text-novaNeutral-600 mt-3">No entries yet.</p>
                    )}
                    <button
                      type="button"
                      onClick={() => {
                        setIncomeModalEditIndex(null);
                        setIncomeModalOpen(true);
                      }}
                      className="mt-4 inline-flex items-center px-5 py-2.5 rounded-full text-sm font-medium text-white bg-novaDarkOrange hover:opacity-95"
                    >
                      Add Income Source
                    </button>
                    {(hubTouched || hubErr) && hubErr && (
                      <p className="mt-3 text-sm text-novaCaution-600">{hubErr}</p>
                    )}
                  </div>
                  <EngageFamilyHomeFormModal
                    open={incomeModalOpen}
                    titleAdd="Add Income Source"
                    titleEdit="Edit Income Source"
                    globalAnswers={answers}
                    config={config}
                    formQuestionIds={getEngageFormQuestionIdsFromJson(ENGAGE_INCOME_FORM_ID)}
                    initialDraft={
                      incomeModalEditIndex !== null && rows[incomeModalEditIndex]
                        ? rows[incomeModalEditIndex].answers
                        : null
                    }
                    onClose={() => {
                      setIncomeModalOpen(false);
                      setIncomeModalEditIndex(null);
                    }}
                    onSubmit={(draft) => {
                      const current = parseEngageSection7Table(
                        typeof answers[id] === "string" ? answers[id] : undefined,
                        ENGAGE_INCOME_JSON_KEY
                      );
                      const nextRows = [...current];
                      if (incomeModalEditIndex !== null) {
                        nextRows[incomeModalEditIndex] = { answers: draft };
                      } else {
                        nextRows.push({ answers: draft });
                      }
                      setAnswer(id, serializeEngageSection7Table(ENGAGE_INCOME_JSON_KEY, nextRows));
                      setIncomeModalOpen(false);
                      setIncomeModalEditIndex(null);
                    }}
                  />
                  {lastQuestionFooterClearance}
                </React.Fragment>
              );
            }

            if (sectionSlug === ENGAGE_SECTION_SLUG_10 && id === ENGAGE_PROCEEDINGS_HUB_Q_ID) {
              const rows = parseEngageSection7Table(
                typeof value === "string" ? value : undefined,
                ENGAGE_PROCEEDINGS_JSON_KEY
              );
              const hubErr = errors[id];
              const hubTouched = touched[id];
              const proceedingsColumns: EngageSection7Column[] = [
                {
                  questionId: ENGAGE_PROCEEDINGS_COL_STATUS_Q_ID,
                  header: ENGAGE_PROCEEDINGS_TABLE_HEADER_STATUS,
                },
                {
                  questionId: ENGAGE_PROCEEDINGS_COL_ISSUE_DATE_Q_ID,
                  header: ENGAGE_PROCEEDINGS_TABLE_HEADER_ISSUE_DATE,
                },
              ];
              return (
                <React.Fragment key={id}>
                  <div
                    ref={firstErrorId === id ? firstErrorRef : undefined}
                    className={`bg-white rounded-xl shadow-sm border p-6 ${
                      hubErr ? "border-novaCaution-400" : "border-novaNeutral-100"
                    }`}
                  >
                    <h3 className="text-novaNeutral-900 font-medium mb-2 flex flex-wrap items-center gap-2">
                      <span>{formatEngageQuestion(config.section.title, answers)}</span>
                      {config.section.required && <span className="text-novaCaution-500">*</span>}
                    </h3>
                    <div className="overflow-x-auto border border-novaNeutral-100 rounded-lg">
                      <table className="w-full text-sm text-left min-w-[560px]">
                        <thead className="bg-novaNeutral-50 text-novaNeutral-700 font-medium">
                          <tr>
                            {proceedingsColumns.map((col) => (
                              <th key={col.questionId} className="px-4 py-3">
                                {col.header}
                              </th>
                            ))}
                            <th className="px-4 py-3 text-right w-[1%] whitespace-nowrap">
                              Actions
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {rows.map((row, idx) => (
                            <tr key={idx} className="border-t border-novaNeutral-100">
                              {proceedingsColumns.map((col) => (
                                <td
                                  key={col.questionId}
                                  className="px-4 py-3 text-novaNeutral-800 align-top"
                                >
                                  {col.questionId === ENGAGE_PROCEEDINGS_COL_ISSUE_DATE_Q_ID
                                    ? formatFamilyHomeIsoDate(row.answers[col.questionId])
                                    : formatSection7TableCell(col, row.answers, config, answers)}
                                </td>
                              ))}
                              <td className="px-4 py-3 text-right whitespace-nowrap align-top space-x-3">
                                <button
                                  type="button"
                                  className="text-novaDarkOrange text-sm font-medium hover:underline"
                                  onClick={() => {
                                    setProceedingsModalEditIndex(idx);
                                    setProceedingsModalOpen(true);
                                  }}
                                >
                                  Edit
                                </button>
                                <button
                                  type="button"
                                  className="text-novaNeutral-600 text-sm hover:text-novaCaution-600"
                                  onClick={() => {
                                    const next = rows.filter((_, i) => i !== idx);
                                    setAnswer(id, serializeEngageSection7Table(ENGAGE_PROCEEDINGS_JSON_KEY, next));
                                  }}
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {rows.length === 0 && (
                      <p className="text-sm text-novaNeutral-600 mt-3">No entries yet.</p>
                    )}
                    {rows.length === 0 && (
                      <button
                        type="button"
                        onClick={() => {
                          setProceedingsModalEditIndex(null);
                          setProceedingsModalOpen(true);
                        }}
                        className="mt-4 inline-flex items-center px-5 py-2.5 rounded-full text-sm font-medium text-white bg-novaDarkOrange hover:opacity-95"
                      >
                        {ENGAGE_PROCEEDINGS_ADD_BUTTON_LABEL}
                      </button>
                    )}
                    {(hubTouched || hubErr) && hubErr && (
                      <p className="mt-3 text-sm text-novaCaution-600">{hubErr}</p>
                    )}
                  </div>
                  <EngageFamilyHomeFormModal
                    open={proceedingsModalOpen}
                    titleAdd={ENGAGE_PROCEEDINGS_MODAL_TITLE_ADD}
                    titleEdit={ENGAGE_PROCEEDINGS_MODAL_TITLE_EDIT}
                    globalAnswers={answers}
                    config={config}
                    formQuestionIds={proceedingsFormQuestionIds}
                    initialDraft={
                      proceedingsModalEditIndex !== null && rows[proceedingsModalEditIndex]
                        ? rows[proceedingsModalEditIndex].answers
                        : null
                    }
                    onClose={() => {
                      setProceedingsModalOpen(false);
                      setProceedingsModalEditIndex(null);
                    }}
                    onSubmit={(draft) => {
                      const current = parseEngageSection7Table(
                        typeof answers[id] === "string" ? answers[id] : undefined,
                        ENGAGE_PROCEEDINGS_JSON_KEY
                      );
                      const nextRows = [...current];
                      if (proceedingsModalEditIndex !== null) {
                        nextRows[proceedingsModalEditIndex] = { answers: draft };
                      } else if (current.length === 0) {
                        nextRows.push({ answers: draft });
                      }
                      setAnswer(id, serializeEngageSection7Table(ENGAGE_PROCEEDINGS_JSON_KEY, nextRows));
                      setProceedingsModalOpen(false);
                      setProceedingsModalEditIndex(null);
                    }}
                  />
                  {lastQuestionFooterClearance}
                </React.Fragment>
              );
            }

            const selectedOpt = getSelectedOptionData(q, value);
            const belowCardAdditional =
              selectedOpt?.data.render_additional_below_card === true &&
              selectedOpt.data.additional_description
                ? { html: selectedOpt.data.additional_description }
                : null;

            const hubQ =
              id === ENGAGE_Q_ID_FAMILY_HOME && familyHubId ? config.questions[familyHubId] : undefined;
            const familyRows =
              id === ENGAGE_Q_ID_FAMILY_HOME && familyHubId ? getFamilyHomeTableRows(answers, familyHubId) : [];
            const familyMode =
              answers[ENGAGE_Q_ID_FAMILY_HOME] === ENGAGE_FAMILY_HOME_VALUE_OWNER
                ? ENGAGE_FAMILY_UI_MODE_OWNER
                : ENGAGE_FAMILY_UI_MODE_RENTED;
            const familyFormIds =
              familyMode === ENGAGE_FAMILY_UI_MODE_OWNER ? familyFormQuestionIdsOwner : familyFormQuestionIdsRented;
            const q223 = config.questions[ENGAGE_FAMILY_COL_Q223];
            const q240 = config.questions[ENGAGE_FAMILY_COL_Q240];
            const q251 = config.questions[ENGAGE_FAMILY_COL_Q251];
            const q254 = config.questions[ENGAGE_FAMILY_COL_Q254];
            const q259 = config.questions[ENGAGE_FAMILY_COL_Q259];
            const familyErr = familyHubId ? errors[familyHubId] : undefined;
            const familyTouched = familyHubId ? touched[familyHubId] : undefined;

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
                                    {renderHtmlContent(additionalDesc)}
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
                                  {renderHtmlContent(additionalDesc)}
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

                {q.input_type === "checkbox" && q.options && (
                  <div className="space-y-3">
                    {q.options.map((opt, idx) => {
                      const [key, label] = getOptionKeyAndLabel(opt);
                      const labelFormatted = formatEngageQuestion(label, answers);
                      const selected = parseEngageCheckboxKeys(typeof value === "string" ? value : undefined);
                      const isChecked = selected.includes(key);
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
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) =>
                                setAnswer(
                                  id,
                                  toggleEngageCheckboxKey(typeof value === "string" ? value : undefined, key, e.target.checked)
                                )
                              }
                              onBlur={() => handleBlur(id)}
                              className="w-4 h-4 border-2 border-novaNeutral-400 rounded focus:outline-none focus:ring-0"
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
                                    value={
                                      (typeof answers[`${id}_${key}`] === "string" ? answers[`${id}_${key}`] : "") as string
                                    }
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

                {q.input_type === "number" && (
                  <div>
                    <input
                      type="number"
                      value={typeof value === "string" ? value : ""}
                      onChange={(e) => setAnswer(id, e.target.value)}
                      onBlur={() => handleBlur(id)}
                      placeholder={q.placeholder || ""}
                      className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange [color-scheme:light]"
                    />
                    {(isTouched || err) && err && (
                      <p className="mt-1 text-sm text-novaCaution-600">{err}</p>
                    )}
                  </div>
                )}

                {q.input_type === "date" && (
                  <div>
                    <NovaDatePicker
                      value={typeof value === "string" ? value : ""}
                      onChange={(next) => setAnswer(id, next)}
                      onBlur={() => handleBlur(id)}
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

                {q.input_type === "selectbox" && (
                  <div className="max-w-md">
                    <EngageCountrySelect
                      id={`select-${id}`}
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
                            {sub.input_type === "country" ||
                            sub.input_type === "country_select" ||
                            sub.input_type === "selectbox" ? (
                              <div className="max-w-md">
                                {sub.input_type === "country" ? (
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
                                ) : (
                                  <EngageCountrySelect
                                    id={`select-${sub.id}`}
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
                                )}
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
              {id === ENGAGE_Q_ID_FAMILY_HOME && familyHubId && hubQ && (
                <div
                  ref={firstErrorId === familyHubId ? firstErrorRef : undefined}
                  className={`bg-white rounded-xl shadow-sm border p-6 mt-4 ${
                    familyErr ? "border-novaCaution-400" : "border-novaNeutral-100"
                  }`}
                >
                  <h3 className="text-novaNeutral-900 font-medium mb-2 flex flex-wrap items-center gap-2">
                    <span>{formatEngageQuestion(hubQ.title || hubQ.question, answers)}</span>
                    {hubQ.required && <span className="text-novaCaution-500">*</span>}
                  </h3>
                  {hubQ.description && (
                    <p className="text-novaNeutral-600 text-sm mb-4">
                      {formatEngageQuestion(hubQ.description, answers)}
                    </p>
                  )}
                  <div className="overflow-x-auto border border-novaNeutral-100 rounded-lg">
                    <table className="w-full text-sm text-left min-w-[560px]">
                      <thead className="bg-novaNeutral-50 text-novaNeutral-700 font-medium">
                        <tr>
                          {familyMode === ENGAGE_FAMILY_UI_MODE_OWNER ? (
                            <>
                              <th className="px-4 py-3">
                                Is the title to the family home freehold or leasehold?
                              </th>
                              <th className="px-4 py-3">When was the family home purchased?</th>
                              <th className="px-4 py-3">NET VALUE of the family home</th>
                              <th className="px-4 py-3">How is the property owned?</th>
                              <th className="px-4 py-3">What is the third party&apos;s name?</th>
                            </>
                          ) : (
                            <>
                              <th className="px-4 py-3">What type of tenancy do you have?</th>
                              <th className="px-4 py-3">In whose name is the tenancy?</th>
                              <th className="px-4 py-3">Number of bedrooms in the family home</th>
                            </>
                          )}
                          <th className="px-4 py-3 text-right w-[1%] whitespace-nowrap">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {familyRows.map((row, idx) => (
                          <tr key={idx} className="border-t border-novaNeutral-100">
                            {familyMode === ENGAGE_FAMILY_UI_MODE_OWNER ? (
                              <>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {formatFamilyHomeRadioCell(q223, row.answers[ENGAGE_FAMILY_COL_Q223], answers)}
                                </td>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {formatFamilyHomeIsoDate(row.answers[ENGAGE_FAMILY_COL_Q226])}
                                </td>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {typeof row.answers[ENGAGE_FAMILY_COL_Q239] === "string" && row.answers[ENGAGE_FAMILY_COL_Q239].trim()
                                    ? row.answers[ENGAGE_FAMILY_COL_Q239]
                                    : "—"}
                                </td>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {formatFamilyHomeRadioCell(q240, row.answers[ENGAGE_FAMILY_COL_Q240], answers)}
                                </td>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {typeof row.answers[ENGAGE_FAMILY_COL_Q244] === "string" && row.answers[ENGAGE_FAMILY_COL_Q244].trim()
                                    ? row.answers[ENGAGE_FAMILY_COL_Q244]
                                    : "—"}
                                </td>
                              </>
                            ) : (
                              <>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {formatFamilyHomeRadioCell(q251, row.answers[ENGAGE_FAMILY_COL_Q251], answers)}
                                </td>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {formatFamilyHomeRadioCell(q254, row.answers[ENGAGE_FAMILY_COL_Q254], answers)}
                                </td>
                                <td className="px-4 py-3 text-novaNeutral-800 align-top">
                                  {formatFamilyHomeRadioCell(q259, row.answers[ENGAGE_FAMILY_COL_Q259], answers)}
                                </td>
                              </>
                            )}
                            <td className="px-4 py-3 text-right whitespace-nowrap align-top space-x-3">
                              <button
                                type="button"
                                className="text-novaDarkOrange text-sm font-medium hover:underline"
                                onClick={() => {
                                  setFamilyModalEditIndex(idx);
                                  setFamilyModalOpen(true);
                                }}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="text-novaNeutral-600 text-sm hover:text-novaCaution-600"
                                onClick={() => {
                                  const hid = familyHubId;
                                  const next = familyRows.filter((_, i) => i !== idx);
                                  setAnswer(hid, serializeEngageFamilyHomeTable(next));
                                }}
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {familyRows.length === 0 && (
                    <p className="text-sm text-novaNeutral-600 mt-3">No family home added yet.</p>
                  )}
                  {familyRows.length === 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        setFamilyModalEditIndex(null);
                        setFamilyModalOpen(true);
                      }}
                      className="mt-4 inline-flex items-center px-5 py-2.5 rounded-full text-sm font-medium text-white bg-novaDarkOrange hover:opacity-95"
                    >
                      Add Family Home
                    </button>
                  )}
                  {(familyTouched || familyErr) && familyErr && (
                    <p className="mt-3 text-sm text-novaCaution-600">{familyErr}</p>
                  )}
                  <EngageFamilyHomeFormModal
                    open={familyModalOpen}
                    globalAnswers={answers}
                    config={config}
                    formQuestionIds={familyFormIds}
                    initialDraft={
                      familyModalEditIndex !== null && familyRows[familyModalEditIndex]
                        ? familyRows[familyModalEditIndex].answers
                        : null
                    }
                    onClose={() => {
                      setFamilyModalOpen(false);
                      setFamilyModalEditIndex(null);
                    }}
                    onSubmit={(draft) => {
                      const hid = familyHubId;
                      if (!hid) return;
                      const current = getFamilyHomeTableRows(answers, hid);
                      const nextRows = [...current];
                      if (familyModalEditIndex !== null) {
                        nextRows[familyModalEditIndex] = { answers: draft };
                      } else {
                        nextRows.push({ answers: draft });
                      }
                      setAnswer(hid, serializeEngageFamilyHomeTable(nextRows));
                      setFamilyModalOpen(false);
                      setFamilyModalEditIndex(null);
                    }}
                  />
                </div>
              )}
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
              {lastQuestionFooterClearance}
            </React.Fragment>
            );
          })}
        </div>

        {sectionSlug === ENGAGE_SECTION_SLUG_7 && s7Modal && (
          <EngageFamilyHomeFormModal
            open
            titleAdd={
              ENGAGE_SECTION7_REPEATABLES.find((h) => h.hubId === s7Modal.hubId)?.modalTitleAdd ??
              "Add"
            }
            titleEdit={
              ENGAGE_SECTION7_REPEATABLES.find((h) => h.hubId === s7Modal.hubId)?.modalTitleEdit ??
              "Edit"
            }
            globalAnswers={answers}
            config={config}
            formQuestionIds={getEngageFormQuestionIdsFromJson(s7Modal.formId)}
            initialDraft={(() => {
              const def = ENGAGE_SECTION7_REPEATABLES.find((h) => h.hubId === s7Modal.hubId);
              if (!def) return null;
              const tableRows = parseEngageSection7Table(
                typeof answers[def.hubId] === "string" ? answers[def.hubId] : undefined,
                def.jsonKey
              );
              if (s7Modal.editIndex !== null && tableRows[s7Modal.editIndex]) {
                return tableRows[s7Modal.editIndex].answers;
              }
              return null;
            })()}
            onClose={() => setS7Modal(null)}
            onSubmit={(draft) => {
              const def = ENGAGE_SECTION7_REPEATABLES.find((h) => h.hubId === s7Modal.hubId);
              if (!def) return;
              const current = parseEngageSection7Table(
                typeof answers[def.hubId] === "string" ? answers[def.hubId] : undefined,
                def.jsonKey
              );
              const nextRows = [...current];
              if (s7Modal.editIndex !== null) {
                nextRows[s7Modal.editIndex] = { answers: draft };
              } else {
                nextRows.push({ answers: draft });
              }
              setAnswer(def.hubId, serializeEngageSection7Table(def.jsonKey, nextRows));
              setS7Modal(null);
            }}
          />
        )}

        <div
          className="fixed bottom-0 left-0 right-0 lg:left-[19rem] z-30 bg-white border-t border-novaNeutral-100 shadow-[0_-4px_6px_0px_rgba(0,0,0,0.08)]"
          role="region"
          aria-label="Form actions"
        >
          <div className="w-full max-w-6xl mx-auto px-4 md:px-[60px] lg:px-[100px] 2xl:px-[180px] py-4 flex flex-wrap items-center justify-between gap-4">
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
              {/* <button
                type="button"
                className="text-novaNeutral-600 hover:text-novaNeutral-800 text-sm"
              >
                Cancel All Changes
              </button> */}
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
        </div>
      </main>
    </div>
    </Layout>
  );
};

export default EngageForm;
