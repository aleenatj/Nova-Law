import engageRaw from "./engage.json";
import {
  ENGAGE_ACCOUNT_COL_AC_NUMBER_Q_ID,
  ENGAGE_ACCOUNT_COL_NAME_Q_ID,
  ENGAGE_ACCOUNT_COL_THIRD_PARTY_NAME_Q_ID,
  ENGAGE_ACCOUNT_COL_WHOSE_Q_ID,
  ENGAGE_ACCOUNT_FORM_ID,
  ENGAGE_ACCOUNT_HUB_Q_ID,
  ENGAGE_ACCOUNT_JSON_KEY,
  ENGAGE_CHILDREN_HUB_QUESTION_ID,
  ENGAGE_FAMILY_HOME_HUB_COHAB,
  ENGAGE_FAMILY_HOME_HUB_OWNER,
  ENGAGE_FAMILY_HOME_HUB_RENTED,
  ENGAGE_INCOME_FORM_ID,
  ENGAGE_INCOME_HUB_Q_ID,
  ENGAGE_INCOME_JSON_KEY,
  ENGAGE_JSON_KEY_CHILDREN_ROWS,
  ENGAGE_JSON_KEY_FAMILY_HOMES_ROWS,
  ENGAGE_PROCEEDINGS_FORM_ID,
  ENGAGE_PROCEEDINGS_HUB_Q_ID,
  ENGAGE_PROCEEDINGS_JSON_KEY,
  ENGAGE_S7_ASSETS_COL_NAME_Q_ID,
  ENGAGE_S7_ASSETS_COL_TYPE_Q_ID,
  ENGAGE_S7_ASSETS_COL_VALUE_JOINT_Q_ID,
  ENGAGE_S7_ASSETS_COL_VALUE_PARTNER_Q_ID,
  ENGAGE_S7_ASSETS_COL_VALUE_YOURS_Q_ID,
  ENGAGE_S7_ASSETS_COL_WHOSE_Q_ID,
  ENGAGE_S7_ASSETS_FORM_ID,
  ENGAGE_S7_ASSETS_HUB_Q_ID,
  ENGAGE_S7_ASSETS_JSON_KEY,
  ENGAGE_S7_BUSINESSES_COL_NAME_Q_ID,
  ENGAGE_S7_BUSINESSES_COL_THIRD_NAME_Q_ID,
  ENGAGE_S7_BUSINESSES_COL_TYPE_Q_ID,
  ENGAGE_S7_BUSINESSES_COL_VALUE_Q_ID,
  ENGAGE_S7_BUSINESSES_FORM_ID,
  ENGAGE_S7_BUSINESSES_HUB_Q_ID,
  ENGAGE_S7_BUSINESSES_JSON_KEY,
  ENGAGE_S7_LIABILITIES_COL_JOINT_Q_ID,
  ENGAGE_S7_LIABILITIES_COL_NAME_Q_ID,
  ENGAGE_S7_LIABILITIES_COL_PARTNER_Q_ID,
  ENGAGE_S7_LIABILITIES_COL_TYPE_Q_ID,
  ENGAGE_S7_LIABILITIES_COL_YOURS_Q_ID,
  ENGAGE_S7_LIABILITIES_FORM_ID,
  ENGAGE_S7_LIABILITIES_HUB_Q_ID,
  ENGAGE_S7_LIABILITIES_JSON_KEY,
  ENGAGE_S7_PENSIONS_COL_PROVIDER_Q_ID,
  ENGAGE_S7_PENSIONS_COL_TYPE_Q_ID,
  ENGAGE_S7_PENSIONS_COL_VALUE_PARTNER_Q_ID,
  ENGAGE_S7_PENSIONS_COL_VALUE_YOURS_Q_ID,
  ENGAGE_S7_PENSIONS_FORM_ID,
  ENGAGE_S7_PENSIONS_HUB_Q_ID,
  ENGAGE_S7_PENSIONS_JSON_KEY,
  ENGAGE_S7_PROPERTY_COL_ADDRESS_Q_ID,
  ENGAGE_S7_PROPERTY_COL_SHARE_PARTNER_Q_ID,
  ENGAGE_S7_PROPERTY_COL_SHARE_THIRD_Q_ID,
  ENGAGE_S7_PROPERTY_COL_SHARE_YOURS_Q_ID,
  ENGAGE_S7_PROPERTY_COL_THIRD_NAME_FALLBACK_Q_ID,
  ENGAGE_S7_PROPERTY_COL_THIRD_NAME_Q_ID,
  ENGAGE_S7_PROPERTY_FORM_ID,
  ENGAGE_S7_PROPERTY_HUB_Q_ID,
  ENGAGE_S7_PROPERTY_JSON_KEY,
  ENGAGE_SECTION7_HUB_IDS,
} from "@/pages/engage/engagePageIds";

type Rule = { identifier: string; operator: string; value: string };
type QuestionRule = Rule | Rule[];

export type OptionItem = {
  [key: string]:
    | {
        value: string;
        tooltip?: string;
        additional_description?: string;
        render_additional_below_card?: boolean;
        show_text_input?: boolean;
      }
    | undefined;
};

export interface FormFieldQuestion {
  id: string;
  question: string;
  placeholder: string;
  input_type: string;
  required: boolean;
  min_length?: number;
  max_length?: number;
  question_order: number;
}

export interface QuestionDef {
  id: string;
  question: string;
  title?: string;
  description?: string;
  question_tooltip?: string;
  placeholder?: string;
  input_type: string;
  required: boolean;
  question_order: number;
  rows?: number;
  options?: OptionItem[];
  rules?: QuestionRule[];
  form_fields?: { questions: Record<string, FormFieldQuestion> };
  /** Repeatable “add row” groups (e.g. section 5 children). */
  form_id?: string;
  /** Extra HTML shown with some textarea questions. */
  additional_content?: string;
}

export interface SectionConfig {
  section: { id: string; title: string; required: boolean };
  questionOrder: string[];
  questions: Record<string, QuestionDef>;
}

type RawQuestionVersion = Record<string, unknown> & {
  section?: string;
  question_order?: number;
  options?: unknown[];
  rules?: unknown[];
  form_fields?: { questions?: Record<string, Record<string, unknown>> };
  form_id?: string;
  additional_content?: string;
};

type EngageJson = {
  sections: Record<string, { title: string; required: boolean; rules?: unknown[] }>;
  questions: Record<string, { versions?: Record<string, RawQuestionVersion> }>;
  forms?: Record<string, { title?: string; questions?: string[] }>;
};

const raw = engageRaw as EngageJson;

function getVersion(vwrap: { versions?: Record<string, RawQuestionVersion> }): RawQuestionVersion | null {
  const vers = vwrap.versions;
  if (!vers) return null;
  return vers["1"] ?? vers[Object.keys(vers).sort()[0]] ?? null;
}

/** Backend sometimes stores all radio keys in one object per array slot; the UI expects one key per entry. */
function normalizeOptions(rawOpts: unknown): OptionItem[] {
  if (!Array.isArray(rawOpts)) return [];
  const out: OptionItem[] = [];
  for (const item of rawOpts) {
    if (!item || typeof item !== "object") continue;
    const o = item as Record<string, unknown>;
    for (const k of Object.keys(o)) {
      const val = o[k];
      if (!val || typeof val !== "object") continue;
      out.push({ [k]: val } as OptionItem);
    }
  }
  return out;
}

function normalizeRules(rawRules: unknown): QuestionRule[] | undefined {
  if (!Array.isArray(rawRules) || rawRules.length === 0) return undefined;
  return rawRules as QuestionRule[];
}

function normalizeFormFields(
  ff: { questions?: Record<string, Record<string, unknown>> } | undefined
): { questions: Record<string, FormFieldQuestion> } | undefined {
  if (!ff?.questions) return undefined;
  const questions: Record<string, FormFieldQuestion> = {};
  for (const [subId, sub] of Object.entries(ff.questions)) {
    questions[subId] = {
      id: subId,
      question: String(sub.question ?? ""),
      placeholder: sub.placeholder != null ? String(sub.placeholder) : "",
      input_type: String(sub.input_type ?? "text"),
      required: Boolean(sub.required),
      min_length: typeof sub.min_length === "number" ? sub.min_length : undefined,
      max_length: typeof sub.max_length === "number" ? sub.max_length : undefined,
      question_order: Number(sub.question_order ?? 0),
    };
  }
  return { questions };
}

function normalizeQuestion(qid: string, v: RawQuestionVersion): QuestionDef {
  const qt = v.question_tooltip ?? v.tooltip;
  return {
    id: qid,
    question: String(v.question ?? ""),
    title: v.title != null ? String(v.title) : undefined,
    description: v.description != null ? String(v.description) : undefined,
    question_tooltip: qt != null ? String(qt) : undefined,
    placeholder: v.placeholder != null ? String(v.placeholder) : "",
    input_type: String(v.input_type ?? "text"),
    required: Boolean(v.required),
    question_order: Number(v.question_order ?? 0),
    rows: typeof v.rows === "number" ? v.rows : undefined,
    options: normalizeOptions(v.options),
    rules: normalizeRules(v.rules),
    form_fields: normalizeFormFields(v.form_fields),
    form_id: v.form_id != null ? String(v.form_id) : undefined,
    additional_content:
      v.additional_content != null ? String(v.additional_content) : undefined,
  };
}

const normalizedById: Record<string, QuestionDef> = {};
const idsBySection: Record<string, string[]> = {};

for (const [qid, qwrap] of Object.entries(raw.questions)) {
  const v = getVersion(qwrap);
  if (!v || !v.section) continue;
  normalizedById[qid] = normalizeQuestion(qid, v);
  const sec = v.section;
  if (!idsBySection[sec]) idsBySection[sec] = [];
  idsBySection[sec].push(qid);
}

for (const sec of Object.keys(idsBySection)) {
  idsBySection[sec].sort(
    (a, b) =>
      (normalizedById[a]?.question_order ?? 0) - (normalizedById[b]?.question_order ?? 0)
  );
}

const sectionIdsSorted = Object.keys(raw.sections).sort(
  (a, b) => Number(a) - Number(b)
);

/** All section slugs that have at least one question in engage.json. */
export const ENGAGE_SECTIONS_BUILT = new Set(
  sectionIdsSorted.filter((id) => (idsBySection[id]?.length ?? 0) > 0)
);

export const ENGAGE_STEPS: { title: string }[] = sectionIdsSorted.map((id) => ({
  title: raw.sections[id]?.title ?? `Section ${id}`,
}));

export const MAX_ENGAGE_SECTION_NAV = sectionIdsSorted.length;

/** Per-child question block in engage.json (Name → follow-ups through 213). */
export const ENGAGE_CHILDREN_FORM_GROUP_ID = "1";

export const ENGAGE_MAX_CHILDREN_ROWS = 1;

/** Section 6 — one of these cards hosts the “Add family home” table + modal (rules pick exactly one). */
export const ENGAGE_FAMILY_HOME_HUB_IDS = ["221", "222", "223"] as const;

/** Owner-occupied family home questions (222–249). */
export const ENGAGE_FAMILY_HOME_FORM_GROUP_OWNER = "2";

/** Rented family home questions (250–264). */
export const ENGAGE_FAMILY_HOME_FORM_GROUP_RENTED = "3";

export const ENGAGE_MAX_FAMILY_HOME_ROWS = 1;

export type EngageSection7Column = {
  questionId: string;
  header: string;
  /** Second field merged into one table cell (e.g. duplicate third-party name rules). */
  fallbackQuestionId?: string;
};

export type EngageSection7RepeatableDef = {
  hubId: (typeof ENGAGE_SECTION7_HUB_IDS)[number];
  formId: string;
  jsonKey: string;
  addButtonLabel: string;
  modalTitleAdd: string;
  modalTitleEdit: string;
  tableColumns: EngageSection7Column[];
};

export const ENGAGE_SECTION7_REPEATABLES: readonly EngageSection7RepeatableDef[] = [
  {
    hubId: ENGAGE_S7_PROPERTY_HUB_Q_ID,
    formId: ENGAGE_S7_PROPERTY_FORM_ID,
    jsonKey: ENGAGE_S7_PROPERTY_JSON_KEY,
    addButtonLabel: "Add Property",
    modalTitleAdd: "Add property",
    modalTitleEdit: "Edit property",
    tableColumns: [
      { questionId: ENGAGE_S7_PROPERTY_COL_ADDRESS_Q_ID, header: "Address" },
      { questionId: ENGAGE_S7_PROPERTY_COL_SHARE_YOURS_Q_ID, header: "Your share of the property" },
      { questionId: ENGAGE_S7_PROPERTY_COL_SHARE_PARTNER_Q_ID, header: "Partner's share of the property" },
      { questionId: ENGAGE_S7_PROPERTY_COL_SHARE_THIRD_Q_ID, header: "Third party's share of the property" },
      {
        questionId: ENGAGE_S7_PROPERTY_COL_THIRD_NAME_Q_ID,
        header: "What is the third party's name?",
        fallbackQuestionId: ENGAGE_S7_PROPERTY_COL_THIRD_NAME_FALLBACK_Q_ID,
      },
    ],
  },
  {
    hubId: ENGAGE_ACCOUNT_HUB_Q_ID,
    formId: ENGAGE_ACCOUNT_FORM_ID,
    jsonKey: ENGAGE_ACCOUNT_JSON_KEY,
    addButtonLabel: "Add Account",
    modalTitleAdd: "Add account",
    modalTitleEdit: "Edit account",
    tableColumns: [
      { questionId: ENGAGE_ACCOUNT_COL_NAME_Q_ID, header: "Account Name" },
      { questionId: ENGAGE_ACCOUNT_COL_AC_NUMBER_Q_ID, header: "A/C number" },
      { questionId: ENGAGE_ACCOUNT_COL_WHOSE_Q_ID, header: "Whose account are you telling us about?" },
      { questionId: ENGAGE_ACCOUNT_COL_THIRD_PARTY_NAME_Q_ID, header: "Name of the third party" },
    ],
  },
  {
    hubId: ENGAGE_S7_ASSETS_HUB_Q_ID,
    formId: ENGAGE_S7_ASSETS_FORM_ID,
    jsonKey: ENGAGE_S7_ASSETS_JSON_KEY,
    addButtonLabel: "Add Asset",
    modalTitleAdd: "Add asset",
    modalTitleEdit: "Edit asset",
    tableColumns: [
      { questionId: ENGAGE_S7_ASSETS_COL_TYPE_Q_ID, header: "Asset type" },
      { questionId: ENGAGE_S7_ASSETS_COL_NAME_Q_ID, header: "Asset name" },
      { questionId: ENGAGE_S7_ASSETS_COL_WHOSE_Q_ID, header: "Whose asset?" },
      { questionId: ENGAGE_S7_ASSETS_COL_VALUE_YOURS_Q_ID, header: "Your asset's value" },
      { questionId: ENGAGE_S7_ASSETS_COL_VALUE_PARTNER_Q_ID, header: "Partner's asset value" },
      { questionId: ENGAGE_S7_ASSETS_COL_VALUE_JOINT_Q_ID, header: "Joint asset value with partner" },
    ],
  },
  {
    hubId: ENGAGE_S7_BUSINESSES_HUB_Q_ID,
    formId: ENGAGE_S7_BUSINESSES_FORM_ID,
    jsonKey: ENGAGE_S7_BUSINESSES_JSON_KEY,
    addButtonLabel: "Add Business",
    modalTitleAdd: "Add business",
    modalTitleEdit: "Edit business",
    tableColumns: [
      { questionId: ENGAGE_S7_BUSINESSES_COL_NAME_Q_ID, header: "Business name" },
      { questionId: ENGAGE_S7_BUSINESSES_COL_TYPE_Q_ID, header: "Business type" },
      { questionId: ENGAGE_S7_BUSINESSES_COL_VALUE_Q_ID, header: "Value of business overall" },
      { questionId: ENGAGE_S7_BUSINESSES_COL_THIRD_NAME_Q_ID, header: "Name of third party" },
    ],
  },
  {
    hubId: ENGAGE_S7_LIABILITIES_HUB_Q_ID,
    formId: ENGAGE_S7_LIABILITIES_FORM_ID,
    jsonKey: ENGAGE_S7_LIABILITIES_JSON_KEY,
    addButtonLabel: "Add Liability",
    modalTitleAdd: "Add liability",
    modalTitleEdit: "Edit liability",
    tableColumns: [
      { questionId: ENGAGE_S7_LIABILITIES_COL_TYPE_Q_ID, header: "Type" },
      { questionId: ENGAGE_S7_LIABILITIES_COL_NAME_Q_ID, header: "Name" },
      { questionId: ENGAGE_S7_LIABILITIES_COL_YOURS_Q_ID, header: "Your liability" },
      { questionId: ENGAGE_S7_LIABILITIES_COL_PARTNER_Q_ID, header: "Partner's liability" },
      { questionId: ENGAGE_S7_LIABILITIES_COL_JOINT_Q_ID, header: "Joint Liability" },
    ],
  },
  {
    hubId: ENGAGE_S7_PENSIONS_HUB_Q_ID,
    formId: ENGAGE_S7_PENSIONS_FORM_ID,
    jsonKey: ENGAGE_S7_PENSIONS_JSON_KEY,
    addButtonLabel: "Add Pension",
    modalTitleAdd: "Add pension",
    modalTitleEdit: "Edit pension",
    tableColumns: [
      { questionId: ENGAGE_S7_PENSIONS_COL_TYPE_Q_ID, header: "Type" },
      { questionId: ENGAGE_S7_PENSIONS_COL_PROVIDER_Q_ID, header: "Provider" },
      { questionId: ENGAGE_S7_PENSIONS_COL_VALUE_YOURS_Q_ID, header: "Your pension's value" },
      { questionId: ENGAGE_S7_PENSIONS_COL_VALUE_PARTNER_Q_ID, header: "Partner's pension value" },
    ],
  },
];

export type EngageChildTableRow = {
  answers: Record<string, string | Record<string, string>>;
};

export type EngageFamilyHomeTableRow = {
  answers: Record<string, string | Record<string, string>>;
};

export type EngageSection7TableRow = {
  answers: Record<string, string | Record<string, string>>;
};

export function getQuestionIdsForFormId(config: SectionConfig, formId: string): string[] {
  return config.questionOrder.filter((id) => config.questions[id]?.form_id === formId);
}

/** Question ids for a modal form from `engage.json` `forms` (authoritative order). */
export function getEngageFormQuestionIdsFromJson(formId: string): string[] {
  const f = (raw as EngageJson).forms?.[formId];
  if (!f?.questions?.length) return [];
  return [...f.questions];
}

export function parseEngageSection7Table(
  raw: string | Record<string, string> | undefined,
  jsonKey: string
): EngageSection7TableRow[] {
  if (typeof raw !== "string" || !raw.trim()) return [];
  try {
    const p = JSON.parse(raw) as unknown;
    if (p && typeof p === "object" && !Array.isArray(p) && jsonKey in p) {
      const rows = (p as Record<string, unknown>)[jsonKey];
      if (!Array.isArray(rows)) return [];
      return rows.map((item) => {
        if (!item || typeof item !== "object") return { answers: {} };
        if (
          "answers" in item &&
          typeof (item as EngageSection7TableRow).answers === "object" &&
          (item as EngageSection7TableRow).answers !== null
        ) {
          return item as EngageSection7TableRow;
        }
        return { answers: item as Record<string, string | Record<string, string>> };
      });
    }
  } catch {
    /* ignore */
  }
  return [];
}

export function serializeEngageSection7Table(
  jsonKey: string,
  rows: EngageSection7TableRow[]
): string {
  return JSON.stringify({ [jsonKey]: rows });
}

export function parseEngageChildrenTable(
  raw: string | Record<string, string> | undefined
): EngageChildTableRow[] {
  if (typeof raw !== "string" || !raw.trim()) return [];
  try {
    const p = JSON.parse(raw) as unknown;
    if (p && typeof p === "object" && !Array.isArray(p) && ENGAGE_JSON_KEY_CHILDREN_ROWS in p) {
      const ch = (p as { [key: string]: unknown })[ENGAGE_JSON_KEY_CHILDREN_ROWS];
      if (!Array.isArray(ch)) return [];
      return ch.map((item) => {
        if (!item || typeof item !== "object") return { answers: {} };
        if (
          "answers" in item &&
          typeof (item as EngageChildTableRow).answers === "object" &&
          (item as EngageChildTableRow).answers !== null
        ) {
          return item as EngageChildTableRow;
        }
        return { answers: item as Record<string, string | Record<string, string>> };
      });
    }
  } catch {
    /* ignore */
  }
  return [];
}

export function serializeEngageChildrenTable(children: EngageChildTableRow[]): string {
  return JSON.stringify({ [ENGAGE_JSON_KEY_CHILDREN_ROWS]: children });
}

export function parseEngageFamilyHomeTable(
  raw: string | Record<string, string> | undefined
): EngageFamilyHomeTableRow[] {
  if (typeof raw !== "string" || !raw.trim()) return [];
  try {
    const p = JSON.parse(raw) as unknown;
    if (p && typeof p === "object" && !Array.isArray(p) && ENGAGE_JSON_KEY_FAMILY_HOMES_ROWS in p) {
      const homes = (p as { [key: string]: unknown })[ENGAGE_JSON_KEY_FAMILY_HOMES_ROWS];
      if (!Array.isArray(homes)) return [];
      return homes.map((item) => {
        if (!item || typeof item !== "object") return { answers: {} };
        if (
          "answers" in item &&
          typeof (item as EngageFamilyHomeTableRow).answers === "object" &&
          (item as EngageFamilyHomeTableRow).answers !== null
        ) {
          return item as EngageFamilyHomeTableRow;
        }
        return { answers: item as Record<string, string | Record<string, string>> };
      });
    }
  } catch {
    /* ignore */
  }
  return [];
}

export function serializeEngageFamilyHomeTable(homes: EngageFamilyHomeTableRow[]): string {
  return JSON.stringify({ [ENGAGE_JSON_KEY_FAMILY_HOMES_ROWS]: homes });
}

export type EngageIndexedRepeatableMeta =
  | { storage: "children"; hubId: string }
  | { storage: "wrapped"; hubId: string; jsonKey: string }
  | { storage: "family"; hubId: string }
  | { storage: "familyForm2Pending" };

/** Maps `338[0]` / `337.1[0]` / `225[0]` to the hub JSON blob and serializer used for that form group. */
export function resolveEngageIndexedRepeatableMeta(baseId: string): EngageIndexedRepeatableMeta | null {
  const rootMatch = /^(\d+)/.exec(baseId);
  const root = rootMatch ? rootMatch[1] : baseId.split(".")[0];

  const childIds = getEngageFormQuestionIdsFromJson(ENGAGE_CHILDREN_FORM_GROUP_ID);
  if (childIds.includes(root)) {
    return { storage: "children", hubId: ENGAGE_CHILDREN_HUB_QUESTION_ID };
  }

  const familyRentedIds = getEngageFormQuestionIdsFromJson(ENGAGE_FAMILY_HOME_FORM_GROUP_RENTED);
  if (familyRentedIds.includes(root)) {
    return { storage: "family", hubId: ENGAGE_FAMILY_HOME_HUB_RENTED };
  }

  const familyOwnerIds = getEngageFormQuestionIdsFromJson(ENGAGE_FAMILY_HOME_FORM_GROUP_OWNER);
  if (familyOwnerIds.includes(root)) {
    return { storage: "familyForm2Pending" };
  }

  for (const def of ENGAGE_SECTION7_REPEATABLES) {
    const ids = getEngageFormQuestionIdsFromJson(def.formId);
    const columnIds = def.tableColumns.flatMap((c) =>
      c.fallbackQuestionId ? [c.questionId, c.fallbackQuestionId] : [c.questionId]
    );
    const allIds = new Set([def.hubId, ...ids, ...columnIds]);
    if (allIds.has(root)) {
      return { storage: "wrapped", hubId: def.hubId, jsonKey: def.jsonKey };
    }
  }

  if (getEngageFormQuestionIdsFromJson(ENGAGE_INCOME_FORM_ID).includes(root)) {
    return { storage: "wrapped", hubId: ENGAGE_INCOME_HUB_Q_ID, jsonKey: ENGAGE_INCOME_JSON_KEY };
  }

  if (getEngageFormQuestionIdsFromJson(ENGAGE_PROCEEDINGS_FORM_ID).includes(root)) {
    return { storage: "wrapped", hubId: ENGAGE_PROCEEDINGS_HUB_Q_ID, jsonKey: ENGAGE_PROCEEDINGS_JSON_KEY };
  }

  return null;
}

/** After flat keys are merged, choose 221 vs 222 for `forms["2"]` indexed fields when ambiguous. */
export function pickFamilyForm2TargetHubForIndexedHydrate(
  out: Record<string, string | Record<string, string>>
): string {
  const len = (id: string) =>
    parseEngageFamilyHomeTable(typeof out[id] === "string" ? out[id] : undefined).length;
  if (len(ENGAGE_FAMILY_HOME_HUB_COHAB) > 0) return ENGAGE_FAMILY_HOME_HUB_COHAB;
  if (len(ENGAGE_FAMILY_HOME_HUB_OWNER) > 0) return ENGAGE_FAMILY_HOME_HUB_OWNER;
  return ENGAGE_FAMILY_HOME_HUB_OWNER;
}

export function serializeEngageIndexedRepeatableRows(
  meta: EngageIndexedRepeatableMeta,
  rows: Array<{ answers: Record<string, string | Record<string, string>> }>
): string {
  switch (meta.storage) {
    case "children":
      return serializeEngageChildrenTable(rows as EngageChildTableRow[]);
    case "wrapped":
      return serializeEngageSection7Table(meta.jsonKey, rows as EngageSection7TableRow[]);
    case "family":
    case "familyForm2Pending":
      return serializeEngageFamilyHomeTable(rows as EngageFamilyHomeTableRow[]);
    default: {
      const _x: never = meta;
      return _x;
    }
  }
}

const sectionConfigCache: Record<string, SectionConfig> = {};

export function getEngageSectionConfig(sectionSlug: string): SectionConfig {
  if (sectionConfigCache[sectionSlug]) return sectionConfigCache[sectionSlug];

  const meta = raw.sections[sectionSlug];
  const order = idsBySection[sectionSlug] ?? [];
  const questions: Record<string, QuestionDef> = {};
  for (const id of order) {
    const q = normalizedById[id];
    if (q) questions[id] = q;
  }

  const cfg: SectionConfig = {
    section: {
      id: sectionSlug,
      title: meta?.title ?? `Section ${sectionSlug}`,
      required: meta?.required ?? true,
    },
    questionOrder: order,
    questions,
  };
  sectionConfigCache[sectionSlug] = cfg;
  return cfg;
}
