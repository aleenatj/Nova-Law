/**
 * Question IDs, option values, and keys used by the Engage route page.
 * Align with `engage.json` / `engageConfig` identifiers.
 *
 * How to find a value in `engage.json`:
 * - Question ids: search `"<id>":` under the top-level `"questions"` object (e.g. `"194":`).
 * - Form groups: search `"forms"` → `"<formId>"` → `"questions"` arrays list question ids in order.
 * - Section slugs: top-level `"sections"` keys (`"1"`, `"2"`, …).
 */

// —— Section 1 “About you” —— search `questions["105"]`, `questions["110"]` (not 109: that is date of birth)
export const ENGAGE_Q_ID_CLIENT_NAME = "105";
export const ENGAGE_CLIENT_NAME_SUB_FIRST = "105.1";
/** Partner name composite; search `questions["110"]` + `form_fields` for `110.1`. */
export const ENGAGE_Q_ID_PARTNER_NAME = "110";
export const ENGAGE_PARTNER_NAME_SUB_FIRST = "110.1";

// —— Children hub table (section 5) —— form 1: name block 194 (194.1–194.3); DOB 196; gender 197
export const ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT = "193";
/** Same as `ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT` (hub JSON for the children table); search `questions["193"]`. */
export const ENGAGE_CHILDREN_HUB_QUESTION_ID = ENGAGE_CHILD_Q_ID_CHILDREN_OBJECT;
export const ENGAGE_CHILD_FORM_NAME_PART_1 = "194.1";
export const ENGAGE_CHILD_FORM_NAME_PART_2 = "194.2";
export const ENGAGE_CHILD_FORM_NAME_PART_3 = "194.3";
/** Parent id for the name `form` in `forms["1"]`; search `questions["194"]`. */
export const ENGAGE_CHILD_Q_ID_NAME = "194";
export const ENGAGE_CHILD_Q_ID_DOB = "196";
export const ENGAGE_CHILD_Q_ID_GENDER = "197";
/** “Please give details about these other children”; search `questions["217"]`, section 5. */
export const ENGAGE_CHILD_Q_ID_OTHER_CHILDREN_DETAILS = "217";
/** Health / SEN / disability branch (input shape may vary); search `questions["209"]`, `forms["1"]`. */
export const ENGAGE_CHILD_Q_ID_CONDITIONAL_HEALTH = "209";

// —— Relationship context & family home (status q220; hub cards q221–q223) ——
export const ENGAGE_Q_ID_RELATIONSHIP = "100";
export const ENGAGE_Q_ID_FAMILY_HOME = "220";

/** JSON hub question ids for family-home rows (owner / cohab / rented variants); search `questions["221"]`…`["223"]`. */
export const ENGAGE_FAMILY_HOME_HUB_OWNER = "221";
export const ENGAGE_FAMILY_HOME_HUB_COHAB = "222";
export const ENGAGE_FAMILY_HOME_HUB_RENTED = "223";

export const ENGAGE_FAMILY_HOME_VALUE_RENTED = "rented";
export const ENGAGE_FAMILY_HOME_VALUE_OWNER = "owner_occupied";

export const ENGAGE_RELATIONSHIP_PARENTAL = "parental_relationship";
export const ENGAGE_RELATIONSHIP_COHABITATION = "cohabitation";

/** UI mode for table columns (derived from q218 + q100), not raw API values alone */
export const ENGAGE_FAMILY_UI_MODE_OWNER = "owner";
export const ENGAGE_FAMILY_UI_MODE_RENTED = "rented";

// —— Family home table column question ids (forms 2 / 3 in engage.json) ——
export const ENGAGE_FAMILY_COL_Q223 = "225";
export const ENGAGE_FAMILY_COL_Q226 = "229";
export const ENGAGE_FAMILY_COL_Q239 = "252";
export const ENGAGE_FAMILY_COL_Q240 = "253";
export const ENGAGE_FAMILY_COL_Q244 = "259";
export const ENGAGE_FAMILY_COL_Q251 = "266";
export const ENGAGE_FAMILY_COL_Q254 = "269";
export const ENGAGE_FAMILY_COL_Q259 = "274";

/**
 * Secondary id checked with `ENGAGE_FAMILY_HOME_HUB_COHAB` for composite address UI; search `questions["250"]`, `form_id` `"2"`.
 */
export const ENGAGE_FAMILY_FORM2_COMPOSITE_ADDRESS_Q_ID = "250";

// —— Section 7: repeatable hubs (forms 4–9). Search `forms["4"]` … `forms["9"]`. ——
export const ENGAGE_SECTION7_REPEATABLE_FORM_IDS = new Set(["4", "5", "6", "7", "8", "9"]);
/** Hub question ids for each repeatable (same order as form ids 4–9); search `questions["281"]`, `["303"]`, … */
export const ENGAGE_SECTION7_HUB_IDS = ["281", "303", "321", "337", "355", "376"] as const;

// Form 4 — Additional property — search `forms["4"]`, `questions["281"]`, `"properties"` in serialized JSON
export const ENGAGE_S7_PROPERTY_HUB_Q_ID = "281";
export const ENGAGE_S7_PROPERTY_FORM_ID = "4";
export const ENGAGE_S7_PROPERTY_JSON_KEY = "properties";
export const ENGAGE_S7_PROPERTY_COL_ADDRESS_Q_ID = "282";
export const ENGAGE_S7_PROPERTY_COL_SHARE_YOURS_Q_ID = "290";
export const ENGAGE_S7_PROPERTY_COL_SHARE_PARTNER_Q_ID = "291";
export const ENGAGE_S7_PROPERTY_COL_SHARE_THIRD_Q_ID = "292";
export const ENGAGE_S7_PROPERTY_COL_THIRD_NAME_Q_ID = "293";
export const ENGAGE_S7_PROPERTY_COL_THIRD_NAME_FALLBACK_Q_ID = "294";

// Form 5 — Accounts — search `forms["5"]`, `questions["303"]`
export const ENGAGE_ACCOUNT_FORM_ID = "5";
export const ENGAGE_ACCOUNT_HUB_Q_ID = "303";
export const ENGAGE_ACCOUNT_JSON_KEY = "accounts";
export const ENGAGE_ACCOUNT_COL_NAME_Q_ID = "305";
export const ENGAGE_ACCOUNT_COL_AC_NUMBER_Q_ID = "306";
export const ENGAGE_ACCOUNT_COL_WHOSE_Q_ID = "303";
export const ENGAGE_ACCOUNT_COL_THIRD_PARTY_NAME_Q_ID = "536";

// Form 6 — Assets — search `forms["6"]`, `questions["321"]`
export const ENGAGE_S7_ASSETS_HUB_Q_ID = "321";
export const ENGAGE_S7_ASSETS_FORM_ID = "6";
export const ENGAGE_S7_ASSETS_JSON_KEY = "assets";
export const ENGAGE_S7_ASSETS_COL_TYPE_Q_ID = "321";
export const ENGAGE_S7_ASSETS_COL_NAME_Q_ID = "322";
export const ENGAGE_S7_ASSETS_COL_WHOSE_Q_ID = "324";
export const ENGAGE_S7_ASSETS_COL_VALUE_YOURS_Q_ID = "325";
export const ENGAGE_S7_ASSETS_COL_VALUE_PARTNER_Q_ID = "326";
export const ENGAGE_S7_ASSETS_COL_VALUE_JOINT_Q_ID = "327";

// Form 7 — Businesses — search `forms["7"]`, `questions["337"]`
export const ENGAGE_S7_BUSINESSES_HUB_Q_ID = "337";
export const ENGAGE_S7_BUSINESSES_FORM_ID = "7";
export const ENGAGE_S7_BUSINESSES_JSON_KEY = "businesses";
export const ENGAGE_S7_BUSINESSES_COL_NAME_Q_ID = "338";
export const ENGAGE_S7_BUSINESSES_COL_TYPE_Q_ID = "339";
export const ENGAGE_S7_BUSINESSES_COL_VALUE_Q_ID = "340";
export const ENGAGE_S7_BUSINESSES_COL_THIRD_NAME_Q_ID = "348";

// Form 8 — Liabilities — search `forms["8"]`, `questions["355"]`
export const ENGAGE_S7_LIABILITIES_HUB_Q_ID = "355";
export const ENGAGE_S7_LIABILITIES_FORM_ID = "8";
export const ENGAGE_S7_LIABILITIES_JSON_KEY = "liabilities";
export const ENGAGE_S7_LIABILITIES_COL_TYPE_Q_ID = "357";
export const ENGAGE_S7_LIABILITIES_COL_NAME_Q_ID = "358";
export const ENGAGE_S7_LIABILITIES_COL_YOURS_Q_ID = "361";
export const ENGAGE_S7_LIABILITIES_COL_PARTNER_Q_ID = "362";
export const ENGAGE_S7_LIABILITIES_COL_JOINT_Q_ID = "363";

// Form 9 — Pensions — search `forms["9"]`, `questions["376"]`
export const ENGAGE_S7_PENSIONS_HUB_Q_ID = "376";
export const ENGAGE_S7_PENSIONS_FORM_ID = "9";
export const ENGAGE_S7_PENSIONS_JSON_KEY = "pensions";
export const ENGAGE_S7_PENSIONS_COL_TYPE_Q_ID = "376";
export const ENGAGE_S7_PENSIONS_COL_PROVIDER_Q_ID = "379";
export const ENGAGE_S7_PENSIONS_COL_VALUE_YOURS_Q_ID = "380";
export const ENGAGE_S7_PENSIONS_COL_VALUE_PARTNER_Q_ID = "381";

/** Root key for serialized rows on the children hub; see `serializeEngageChildrenTable` in engageConfig. */
export const ENGAGE_JSON_KEY_CHILDREN_ROWS = "children";
/** Root key for serialized family-home rows; see `serializeEngageFamilyHomeTable` in engageConfig. */
export const ENGAGE_JSON_KEY_FAMILY_HOMES_ROWS = "homes";

// —— Session & routing ——
export const ENGAGE_SESSION_CASE_ID_KEY = "current_case_id";

/** Persisted sidebar step; not in engage.json (client-only). */
export const ENGAGE_ACTIVE_SECTION_STORAGE_KEY = "engage_active_section";
export const ENGAGE_ACTIVE_SECTION_EVENT = "engage-active-section-change";
export const ENGAGE_NAVIGATE_SECTION_EVENT = "engage-navigate-section";

/**
 * Internal merge key for indexed `forms["2"]` PATCH paths; not in engage.json.
 * See `resolveEngageIndexedRepeatableMeta` in engageConfig.
 */
export const ENGAGE_FAMILY_FORM2_INDEXED_BUCKET_ID = "__engage_family_form2_idx__";

/** Step numbers as string slugs (sidebar / `activeSection`) */
export const ENGAGE_SECTION_SLUG_1 = "1";
export const ENGAGE_SECTION_SLUG_2 = "2";
export const ENGAGE_SECTION_SLUG_8 = "8";
export const ENGAGE_SECTION_SLUG_7 = "7";
export const ENGAGE_SECTION_SLUG_10 = "10";

// —— Section 10 proceedings repeatable row (form 11); aligns with `forms["11"]` in engage.json ——
export const ENGAGE_PROCEEDINGS_FORM_ID = "11";
/** Hosts JSON rows (`dissolution_proceedings`); first `form_id` 11 question in section 10; search `questions["452"]`. */
export const ENGAGE_PROCEEDINGS_HUB_Q_ID = "452";
export const ENGAGE_PROCEEDINGS_JSON_KEY = "dissolution_proceedings";
export const ENGAGE_PROCEEDINGS_COL_STATUS_Q_ID = "454";
export const ENGAGE_PROCEEDINGS_COL_ISSUE_DATE_Q_ID = "463";
export const ENGAGE_PROCEEDINGS_ADD_BUTTON_LABEL = "Add Proceedings";
export const ENGAGE_PROCEEDINGS_MODAL_TITLE_ADD = "Add Proceedings";
export const ENGAGE_PROCEEDINGS_MODAL_TITLE_EDIT = "Edit Proceedings";
/** Table column headers (match engage.json q454 + q463). */
export const ENGAGE_PROCEEDINGS_TABLE_HEADER_STATUS = "Status in proceedings";
export const ENGAGE_PROCEEDINGS_TABLE_HEADER_ISSUE_DATE =
  "When were the proceedings issued at court?";

// —— Section 8 income sources repeatable table (form 10) ——
export const ENGAGE_INCOME_FORM_ID = "10";
/** JSON rows stored on q403 (“Sources of income”); nested row answers also use 403 inside the blob; search `questions["403"]`. */
export const ENGAGE_INCOME_HUB_Q_ID = "403";
export const ENGAGE_INCOME_COL_SOURCE_Q_ID = "403";
export const ENGAGE_INCOME_COL_NAME_Q_ID = "406";
export const ENGAGE_INCOME_COL_NET_YOURS_Q_ID = "409";
export const ENGAGE_INCOME_COL_NET_PARTNER_Q_ID = "411";
export const ENGAGE_INCOME_JSON_KEY = "income_sources";

/** Defaults when resolving the customer’s first open case */
export const ENGAGE_CASE_LIST_PAGE = "1";
export const ENGAGE_CASE_LIST_LIMIT = "1";
export const ENGAGE_CASE_LIST_CATEGORY = "All";
export const ENGAGE_CASE_LIST_STATUS = "Open";
