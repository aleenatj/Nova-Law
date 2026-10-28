import React, { useLayoutEffect, useRef, useState } from "react";
import type { OptionItem, QuestionDef } from "@/config/engageConfig";
import {
  ENGAGE_CHILD_FORM_NAME_PART_1,
  ENGAGE_CHILD_Q_ID_NAME,
  ENGAGE_CLIENT_NAME_SUB_FIRST,
  ENGAGE_PARTNER_NAME_SUB_FIRST,
  ENGAGE_Q_ID_CLIENT_NAME,
  ENGAGE_Q_ID_PARTNER_NAME,
} from "@/pages/engage/engagePageIds";

export type Rule = { identifier: string; operator: string; value: string };

export function getPartnerFirstName(
  answers: Record<string, string | Record<string, string>>
): string {
  const v = answers[ENGAGE_Q_ID_PARTNER_NAME];
  if (typeof v === "object" && v && typeof v[ENGAGE_PARTNER_NAME_SUB_FIRST] === "string") {
    const t = v[ENGAGE_PARTNER_NAME_SUB_FIRST].trim();
    if (t) return t;
  }
  return "your partner";
}

export function getClientFirstName(
  answers: Record<string, string | Record<string, string>>
): string {
  const v = answers[ENGAGE_Q_ID_CLIENT_NAME];
  if (typeof v === "object" && v && typeof v[ENGAGE_CLIENT_NAME_SUB_FIRST] === "string") {
    return v[ENGAGE_CLIENT_NAME_SUB_FIRST].trim();
  }
  return "";
}

/** First name from child “Name” composite (`forms["1"]`); search `questions["194"]` → `194.1`. */
export function getChildFirstName(
  answers: Record<string, string | Record<string, string>>
): string {
  const v = answers[ENGAGE_CHILD_Q_ID_NAME];
  if (typeof v === "object" && v && typeof v[ENGAGE_CHILD_FORM_NAME_PART_1] === "string") {
    const t = v[ENGAGE_CHILD_FORM_NAME_PART_1].trim();
    if (t) return t;
  }
  return "";
}

export function formatSection2WelcomeTitle(
  title: string,
  answers: Record<string, string | Record<string, string>>
): string {
  const name = getClientFirstName(answers);
  if (name) return title.replace(/\{name\}/g, name);
  return title.replace(/\s*,?\s*\{name\}\s*/g, "").replace(/\s+/g, " ").trim();
}

export function formatEngageQuestion(
  text: string,
  answers: Record<string, string | Record<string, string>>
): string {
  const name = getClientFirstName(answers);
  const child = getChildFirstName(answers);
  return text
    .replace(/\[X\]/g, getPartnerFirstName(answers))
    .replace(/\{partner_name\}/g, getPartnerFirstName(answers))
    .replace(/\{name\}/g, name)
    .replace(/\{child_first_name\}/g, child || "your child");
}

export const DOB_MIN_AGE_MESSAGE =
  "Please check your date of birth - you need to be 18 years of age to instruct us";

export function ageFromIsoDateString(iso: string): number | null {
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

/** Child date of birth (`questions["196"]`): valid ISO only, no minimum age. */
export function validateChildDateAnswer(required: boolean, str: string): string | null {
  const s = str.trim();
  if (required && !s) return "This field is required.";
  if (!s) return null;
  if (ageFromIsoDateString(s) === null) return "Please enter a valid date of birth.";
  return null;
}

/** Checkbox answers are stored as comma-separated option keys. */
export function parseEngageCheckboxKeys(stored: string | undefined): string[] {
  if (!stored || typeof stored !== "string") return [];
  return stored.split(",").map((s) => s.trim()).filter(Boolean);
}

export function toggleEngageCheckboxKey(stored: string | undefined, key: string, checked: boolean): string {
  const parts = parseEngageCheckboxKeys(stored);
  const next = checked
    ? [...parts, key].filter((k, i, arr) => arr.indexOf(k) === i)
    : parts.filter((k) => k !== key);
  return [...next].sort().join(",");
}

export function isQuestionVisible(
  q: QuestionDef,
  answers: Record<string, string | Record<string, string>>
): boolean {
  const rules = q.rules as Rule[] | undefined;
  if (!rules || rules.length === 0) return true;
  return rules.some((r) => {
    const val = answers[r.identifier];
    const compare = typeof val === "object" ? undefined : (val as string);
    const parts = parseEngageCheckboxKeys(compare);
    if (r.operator === "is") {
      if (compare === undefined || compare === null) return false;
      return parts.length > 0 ? parts.includes(r.value) : false;
    }
    if (r.operator === "is not") {
      if (compare === undefined || compare === null) return true;
      return !parts.includes(r.value);
    }
    return false;
  });
}

export function getOptionKeyAndLabel(opt: OptionItem): [string, string] {
  const key = Object.keys(opt)[0];
  const node = opt[key];
  const label =
    node && typeof node === "object" && "value" in node && typeof (node as { value?: string }).value === "string"
      ? (node as { value: string }).value
      : key;
  return [key, label];
}

export function getSelectedOptionData(
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

const TOOLTIP_GAP_PX = 8;
const TOOLTIP_VIEWPORT_PAD = 12;

export const RICH_HTML_LINKS =
  "[&_a]:text-novaDarkOrange [&_a]:underline [&_a:hover]:underline-none [&_a]:decoration-novaDarkOrange";

export function RadioOptionTooltip({
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

/** UK NI: two letters, six digits, one letter — displayed as AB-12-34-56-C. */
const UK_NI_COMPLETE_REGEX = /^[A-Z]{2}\d{6}[A-Z]$/;

export function formatUkNationalInsuranceInput(raw: string): string {
  const digitsLetters = raw.replace(/[^a-zA-Z0-9]/g, "");
  let f = "";
  for (let i = 0; i < digitsLetters.length && f.length < 9; i++) {
    const ch = digitsLetters[i]!;
    const pos = f.length;
    if (pos < 2) {
      if (/[a-zA-Z]/.test(ch)) f += ch.toUpperCase();
    } else if (pos < 8) {
      if (/\d/.test(ch)) f += ch;
    } else if (/[a-zA-Z]/.test(ch)) {
      f += ch.toUpperCase();
    }
  }
  if (f.length === 0) return "";
  let out = f.slice(0, 2);
  if (f.length > 2) out += "-" + f.slice(2, 4);
  if (f.length > 4) out += "-" + f.slice(4, 6);
  if (f.length > 6) out += "-" + f.slice(6, 8);
  if (f.length > 8) out += "-" + f.slice(8, 9);
  return out;
}

export function isCompleteUkNationalInsuranceValue(value: string): boolean {
  const core = value.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
  return UK_NI_COMPLETE_REGEX.test(core);
}
