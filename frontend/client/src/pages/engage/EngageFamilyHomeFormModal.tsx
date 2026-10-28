import React, { useCallback, useEffect, useMemo, useState } from "react";
import CountrySelect from "@/components/ui/country-select/CountrySelect";
import EngageCountrySelect from "@/components/ui/country-select/EngageCountrySelect";
import { NovaDatePicker } from "@/components/ui/date-picker";
import type { QuestionDef, SectionConfig } from "@/config/engageConfig";
import {
  ageFromIsoDateString,
  formatEngageQuestion,
  getOptionKeyAndLabel,
  getSelectedOptionData,
  isQuestionVisible,
  RadioOptionTooltip,
  RICH_HTML_LINKS,
} from "./engageFormShared";
import { ENGAGE_FAMILY_FORM2_COMPOSITE_ADDRESS_Q_ID, ENGAGE_FAMILY_HOME_HUB_COHAB } from "./engagePageIds";

const BELOW_CARD_ADDITIONAL_RICH = `text-novaNeutral-700 text-sm leading-relaxed [&_strong]:font-bold ${RICH_HTML_LINKS} [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-1 [&_p]:mb-2 [&_p:last-child]:mb-0`;

function cloneDraft(
  d: Record<string, string | Record<string, string>> | null | undefined
): Record<string, string | Record<string, string>> {
  if (!d) return {};
  try {
    return JSON.parse(JSON.stringify(d)) as Record<string, string | Record<string, string>>;
  } catch {
    return { ...d };
  }
}

function getCompositeAddressEntries(
  q: QuestionDef
): Array<{ key: string; spec: Record<string, unknown> }> {
  if (!q.options?.length) return [];
  const out: Array<{ key: string; spec: Record<string, unknown> }> = [];
  for (const opt of q.options) {
    const k = Object.keys(opt)[0];
    const raw = opt[k];
    if (!raw || typeof raw !== "object") continue;
    const o = raw as Record<string, unknown>;
    if (typeof o.input_type === "string") out.push({ key: k, spec: o });
  }
  return out;
}

function getAddressFieldLabel(spec: Record<string, unknown>, key: string): string {
  if (typeof spec.label === "string") return spec.label;
  if (typeof spec.value === "string") return spec.value;
  return key;
}

function isCompositeAddressQuestion(q: QuestionDef, id: string): boolean {
  return (
    (id === ENGAGE_FAMILY_HOME_HUB_COHAB || id === ENGAGE_FAMILY_FORM2_COMPOSITE_ADDRESS_Q_ID) &&
    getCompositeAddressEntries(q).length > 0
  );
}

/** Radio options (including JSON that uses input_type "text" with value-style options, e.g. 231). */
function isRadioChoiceQuestion(q: QuestionDef, id: string): boolean {
  if (!q.options?.length) return false;
  if (isCompositeAddressQuestion(q, id)) return false;
  if (q.input_type === "radio") return true;
  if (q.input_type === "text") return true;
  return false;
}

function validateIsoDateField(required: boolean, str: string): string | null {
  const s = str.trim();
  if (required && !s) return "This field is required.";
  if (!s) return null;
  if (ageFromIsoDateString(s) === null) return "Please enter a valid date.";
  return null;
}

function validateSingleQuestion(
  q: QuestionDef,
  id: string,
  val: string | Record<string, string> | undefined,
  _mergedAnswers: Record<string, string | Record<string, string>>
): string | null {
  if (q.input_type === "form" && q.form_fields) {
    const subQs = Object.values(q.form_fields.questions).sort(
      (a, b) => a.question_order - b.question_order
    );
    for (const sub of subQs) {
      const subVal = typeof val === "object" && val ? val[sub.id] : undefined;
      const str = typeof subVal === "string" ? subVal : "";
      if (sub.required && !str.trim()) return `Please complete: ${sub.question || sub.id}.`;
      if (!str.trim()) continue;
      if (sub.min_length && str.length < sub.min_length)
        return `${sub.question}: minimum ${sub.min_length} character(s).`;
      if (sub.max_length && str.length > sub.max_length)
        return `${sub.question}: maximum ${sub.max_length} character(s).`;
    }
    return null;
  }

  if (isCompositeAddressQuestion(q, id)) {
    const entries = getCompositeAddressEntries(q);
    const obj = typeof val === "object" && val && !Array.isArray(val) ? val : {};
    for (const { key, spec } of entries) {
      const req = Boolean(spec.required);
      const s = typeof obj[key] === "string" ? obj[key] : "";
      if (req && !s.trim()) return `Please complete: ${getAddressFieldLabel(spec, key)}.`;
      const minL = typeof spec.min_length === "number" ? spec.min_length : undefined;
      const maxL = typeof spec.max_length === "number" ? spec.max_length : undefined;
      if (!s.trim()) continue;
      if (minL && s.length < minL) return `${getAddressFieldLabel(spec, key)}: too short.`;
      if (maxL && s.length > maxL) return `${getAddressFieldLabel(spec, key)}: too long.`;
    }
    return null;
  }

  if (q.input_type === "date") {
    const str = typeof val === "string" ? val : "";
    return validateIsoDateField(q.required, str);
  }

  if (isRadioChoiceQuestion(q, id)) {
    const str = typeof val === "string" ? val : "";
    if (q.required && !str.trim()) return "Please select an option.";
    return null;
  }

  if (q.input_type === "number") {
    const str = typeof val === "string" ? val : "";
    if (q.required && !str.trim()) return "This field is required.";
    return null;
  }

  if (q.input_type === "textarea") {
    const str = typeof val === "string" ? val : "";
    if (q.required && !str.trim()) return "This field is required.";
    const qDef = q as QuestionDef & { min_length?: number; max_length?: number };
    if (str.trim()) {
      if (qDef.min_length && str.length < qDef.min_length)
        return `Minimum ${qDef.min_length} character(s).`;
      if (qDef.max_length && str.length > qDef.max_length)
        return `Maximum ${qDef.max_length} character(s).`;
    }
    return null;
  }

  if (q.input_type === "text") {
    const str = typeof val === "string" ? val : "";
    if (q.required && !str.trim()) return "This field is required.";
    const qDef = q as QuestionDef & { min_length?: number; max_length?: number };
    if (str.trim()) {
      if (qDef.min_length && str.length < qDef.min_length)
        return `Minimum ${qDef.min_length} character(s).`;
      if (qDef.max_length && str.length > qDef.max_length)
        return `Maximum ${qDef.max_length} character(s).`;
    }
    return null;
  }

  if (q.input_type === "country" || q.input_type === "selectbox") {
    const str = typeof val === "string" ? val : "";
    if (q.required && !str.trim()) return "This field is required.";
    return null;
  }

  if (q.input_type === "file") {
    const str = typeof val === "string" ? val : "";
    if (q.required && !str.trim()) return "Please choose a file.";
    return null;
  }

  if (q.input_type === "radio" && !q.options?.length) {
    const str = typeof val === "string" ? val : "";
    if (q.required && !str.trim()) return "This field is required.";
    return null;
  }

  return null;
}

export function EngageFamilyHomeFormModal({
  open,
  globalAnswers,
  config,
  formQuestionIds,
  initialDraft,
  onClose,
  onSubmit,
  titleAdd = "Add family home",
  titleEdit = "Edit family home",
}: {
  open: boolean;
  globalAnswers: Record<string, string | Record<string, string>>;
  config: SectionConfig;
  formQuestionIds: string[];
  initialDraft: Record<string, string | Record<string, string>> | null;
  onClose: () => void;
  onSubmit: (draft: Record<string, string | Record<string, string>>) => void;
  /** Modal heading when adding / editing (e.g. section 7 repeatables). */
  titleAdd?: string;
  titleEdit?: string;
}) {
  const [draft, setDraft] = useState<Record<string, string | Record<string, string>>>({});
  const [step, setStep] = useState(0);
  const [modalErrors, setModalErrors] = useState<Record<string, string>>({});
  const [openTooltip, setOpenTooltip] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setDraft(cloneDraft(initialDraft));
    setStep(0);
    setModalErrors({});
    setOpenTooltip(null);
  }, [open, initialDraft]);

  const mergedAnswers = useMemo(
    () => ({ ...globalAnswers, ...draft }),
    [globalAnswers, draft]
  );

  const visibleIds = useMemo(() => {
    return formQuestionIds.filter((id) => {
      const q = config.questions[id];
      return q && isQuestionVisible(q, mergedAnswers);
    });
  }, [formQuestionIds, config, mergedAnswers]);

  const batchCount = Math.max(1, Math.ceil(visibleIds.length / 3));

  useEffect(() => {
    if (step >= batchCount) setStep(Math.max(0, batchCount - 1));
  }, [batchCount, step]);

  const currentBatch = useMemo(
    () => visibleIds.slice(step * 3, step * 3 + 3),
    [visibleIds, step]
  );

  const isLastStep = step >= batchCount - 1;

  const setDraftAnswer = useCallback((id: string, value: string | Record<string, string>) => {
    setDraft((prev) => ({ ...prev, [id]: value }));
    setModalErrors((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  }, []);

  const validateBatch = useCallback((): boolean => {
    const nextErr: Record<string, string> = {};
    for (const id of currentBatch) {
      const q = config.questions[id];
      if (!q) continue;
      const msg = validateSingleQuestion(q, id, draft[id], mergedAnswers);
      if (msg) nextErr[id] = msg;
    }
    setModalErrors((prev) => ({ ...prev, ...nextErr }));
    return Object.keys(nextErr).length === 0;
  }, [currentBatch, config.questions, draft, mergedAnswers]);

  const validateFull = useCallback((): boolean => {
    const nextErr: Record<string, string> = {};
    for (const id of visibleIds) {
      const q = config.questions[id];
      if (!q) continue;
      const msg = validateSingleQuestion(q, id, draft[id], mergedAnswers);
      if (msg) nextErr[id] = msg;
    }
    setModalErrors(nextErr);
    return Object.keys(nextErr).length === 0;
  }, [visibleIds, config.questions, draft, mergedAnswers]);

  const handleNext = () => {
    if (!validateBatch()) return;
    if (isLastStep) {
      if (!validateFull()) return;
      onSubmit(draft);
      onClose();
      return;
    }
    setStep((s) => s + 1);
  };

  const handleBack = () => {
    setModalErrors({});
    setStep((s) => Math.max(0, s - 1));
  };

  const handleCancel = () => {
    setModalErrors({});
    onClose();
  };

  if (!open) return null;

  const isEdit = Boolean(initialDraft);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="engage-family-home-modal-title"
    >
      <div className="bg-white rounded-xl shadow-xl border border-novaNeutral-100 max-w-2xl w-full max-h-[min(90vh,900px)] flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-novaNeutral-100 shrink-0">
          <h2 id="engage-family-home-modal-title" className="text-lg font-semibold text-novaNeutral-900">
            {isEdit ? titleEdit : titleAdd}
          </h2>
        </div>

        <div className="px-6 py-5 overflow-y-auto flex-1 space-y-8">
          {currentBatch.map((id) => {
            const q = config.questions[id];
            if (!q) return null;
            const value = draft[id];
            const err = modalErrors[id];
            const selectedOpt = getSelectedOptionData(q, value);
            const belowCardAdditional =
              selectedOpt?.data.render_additional_below_card === true &&
              selectedOpt.data.additional_description
                ? { html: selectedOpt.data.additional_description }
                : null;

            const titleText = formatEngageQuestion(q.question, mergedAnswers);
            const descText = q.description ? formatEngageQuestion(q.description, mergedAnswers) : "";

            return (
              <React.Fragment key={id}>
                <div
                  className={`rounded-xl border p-5 ${
                    err ? "border-novaCaution-400" : "border-novaNeutral-100"
                  }`}
                >
                  <h3 className="text-novaNeutral-900 font-medium mb-2 flex flex-wrap items-center gap-2">
                    <span>{titleText}</span>
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
                  {descText && <p className="text-novaNeutral-600 text-sm mb-3">{descText}</p>}
                  {q.additional_content && (
                    <div
                      className={`mb-4 ${BELOW_CARD_ADDITIONAL_RICH}`}
                      dangerouslySetInnerHTML={{
                        __html: formatEngageQuestion(q.additional_content, mergedAnswers),
                      }}
                    />
                  )}

                  {isRadioChoiceQuestion(q, id) && q.options && q.options.length > 0 && (
                    <div className="space-y-3">
                      {q.options.map((opt, idx) => {
                        const [key, label] = getOptionKeyAndLabel(opt);
                        const labelFormatted = formatEngageQuestion(label, mergedAnswers);
                        const isChecked = (typeof value === "string" && value === key) || false;
                        const optData = opt[Object.keys(opt)[0]];
                        const additionalDesc = optData?.additional_description
                          ? formatEngageQuestion(optData.additional_description, mergedAnswers)
                          : undefined;
                        const showTextInput = optData?.show_text_input === true;
                        return (
                          <div key={idx}>
                            <label
                              className={`flex items-center gap-3 cursor-pointer ${
                                isChecked
                                  ? "text-novaDarkOrange font-medium"
                                  : "text-novaNeutral-800"
                              }`}
                            >
                              <input
                                type="radio"
                                name={`modal-fh-${id}`}
                                checked={isChecked}
                                onChange={() => setDraftAnswer(id, key)}
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
                                    setOpenTooltip(
                                      openTooltip === `${id}-${key}` ? null : `${id}-${key}`
                                    )
                                  }
                                  onKeyToggle={() =>
                                    setOpenTooltip(
                                      openTooltip === `${id}-${key}` ? null : `${id}-${key}`
                                    )
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
                                        (typeof draft[`${id}_${key}`] === "string"
                                          ? draft[`${id}_${key}`]
                                          : "") as string
                                      }
                                      onChange={(e) =>
                                        setDraftAnswer(`${id}_${key}`, e.target.value)
                                      }
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
                      {err && <p className="mt-2 text-sm text-novaCaution-600">{err}</p>}
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
                                        setDraftAnswer(id, next);
                                      }}
                                    />
                                  ) : (
                                    <EngageCountrySelect
                                      id={`modal-fh-select-${sub.id}`}
                                      value={subVal.trim() ? subVal : null}
                                      onChange={(nextCountry) => {
                                        const next = {
                                          ...(typeof value === "object" && value ? value : {}),
                                          [sub.id]: nextCountry,
                                        };
                                        setDraftAnswer(id, next);
                                      }}
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
                                    setDraftAnswer(id, next);
                                  }}
                                  placeholder={sub.placeholder || ""}
                                  maxLength={sub.max_length}
                                  className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange"
                                />
                              )}
                            </div>
                          );
                        })}
                      {err && <p className="mt-1 text-sm text-novaCaution-600">{err}</p>}
                    </div>
                  )}

                  {isCompositeAddressQuestion(q, id) && (
                    <div className="space-y-4">
                      {getCompositeAddressEntries(q).map(({ key, spec }) => {
                        const obj =
                          typeof value === "object" && value && !Array.isArray(value)
                            ? (value as Record<string, string>)
                            : {};
                        const subVal = typeof obj[key] === "string" ? obj[key] : "";
                        const label = getAddressFieldLabel(spec, key);
                        const req = Boolean(spec.required);
                        return (
                          <div key={key}>
                            <label className="block text-sm font-medium text-novaNeutral-700 mb-1">
                              {label}
                              {req && <span className="text-novaCaution-500 ml-0.5">*</span>}
                            </label>
                            <input
                              type="text"
                              value={subVal}
                              onChange={(e) => {
                                const next = { ...obj, [key]: e.target.value };
                                setDraftAnswer(id, next);
                              }}
                              className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange"
                            />
                          </div>
                        );
                      })}
                      {err && <p className="text-sm text-novaCaution-600">{err}</p>}
                    </div>
                  )}

                  {q.input_type === "date" && (
                    <div>
                      <NovaDatePicker
                        value={typeof value === "string" ? value : ""}
                        onChange={(next) => setDraftAnswer(id, next)}
                      />
                      {err && <p className="mt-1 text-sm text-novaCaution-600">{err}</p>}
                    </div>
                  )}

                  {q.input_type === "number" && (
                    <div>
                      <input
                        type="number"
                        inputMode="decimal"
                        value={typeof value === "string" ? value : ""}
                        onChange={(e) => setDraftAnswer(id, e.target.value)}
                        placeholder={q.placeholder || ""}
                        className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange"
                      />
                      {err && <p className="mt-1 text-sm text-novaCaution-600">{err}</p>}
                    </div>
                  )}

                  {q.input_type === "country" && (
                    <div className="max-w-md">
                      <CountrySelect
                        value={typeof value === "string" && value.trim() ? value : null}
                        onChange={(next) => setDraftAnswer(id, next)}
                        error={err}
                      />
                    </div>
                  )}

                  {q.input_type === "selectbox" && (
                    <div className="max-w-md">
                      <EngageCountrySelect
                        id={`modal-fh-select-${id}`}
                        value={typeof value === "string" && value.trim() ? value : null}
                        onChange={(next) => setDraftAnswer(id, next)}
                        error={err}
                      />
                    </div>
                  )}

                  {q.input_type === "textarea" && (
                    <div>
                      <textarea
                        value={typeof value === "string" ? value : ""}
                        onChange={(e) => setDraftAnswer(id, e.target.value)}
                        placeholder={q.placeholder || ""}
                        rows={q.rows ?? 4}
                        maxLength={(q as QuestionDef & { max_length?: number }).max_length}
                        className="w-full max-w-2xl min-h-[100px] px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange text-novaNeutral-800"
                      />
                      {err && <p className="mt-1 text-sm text-novaCaution-600">{err}</p>}
                    </div>
                  )}

                  {q.input_type === "text" &&
                    !isCompositeAddressQuestion(q, id) &&
                    !isRadioChoiceQuestion(q, id) && (
                      <div>
                        <input
                          type="text"
                          value={typeof value === "string" ? value : ""}
                          onChange={(e) => setDraftAnswer(id, e.target.value)}
                          placeholder={q.placeholder || ""}
                          maxLength={(q as QuestionDef & { max_length?: number }).max_length}
                          className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange"
                        />
                        {err && <p className="mt-1 text-sm text-novaCaution-600">{err}</p>}
                      </div>
                    )}

                  {q.input_type === "radio" && (!q.options || q.options.length === 0) && (
                    <div>
                      <input
                        type="text"
                        value={typeof value === "string" ? value : ""}
                        onChange={(e) => setDraftAnswer(id, e.target.value)}
                        placeholder={q.placeholder || ""}
                        className="w-full max-w-md px-2.5 py-1.5 text-sm border border-novaNeutral-300 rounded-lg focus:outline-none focus:border-novaDarkOrange"
                      />
                      {err && <p className="mt-1 text-sm text-novaCaution-600">{err}</p>}
                    </div>
                  )}

                  {q.input_type === "file" && (
                    <div>
                      <input
                        type="file"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          setDraftAnswer(id, f?.name ?? "");
                        }}
                        className="block w-full max-w-md text-sm text-novaNeutral-800"
                      />
                      {typeof value === "string" && value && (
                        <p className="mt-1 text-xs text-novaNeutral-600">Selected: {value}</p>
                      )}
                      {err && <p className="mt-1 text-sm text-novaCaution-600">{err}</p>}
                    </div>
                  )}
                </div>
                {belowCardAdditional && (
                  <div className="bg-white rounded-xl shadow-sm border border-novaNeutral-100 p-6 -mt-4">
                    <div
                      className={BELOW_CARD_ADDITIONAL_RICH}
                      dangerouslySetInnerHTML={{
                        __html: formatEngageQuestion(belowCardAdditional.html, mergedAnswers),
                      }}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        <div className="px-6 py-4 border-t border-novaNeutral-100 flex flex-wrap justify-between gap-3 shrink-0 bg-novaNeutral-50/80">
          <div className="flex gap-2">
            {step > 0 && (
              <button
                type="button"
                onClick={handleBack}
                className="inline-flex items-center px-4 py-2 rounded-full border border-novaNeutral-300 bg-white text-sm font-medium text-novaNeutral-800 hover:bg-novaNeutral-50"
              >
                Back
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-3 ml-auto">
            <button
              type="button"
              onClick={handleCancel}
              className="inline-flex items-center px-4 py-2 rounded-full border border-novaNeutral-300 bg-white text-sm font-medium text-novaNeutral-800 hover:bg-novaNeutral-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleNext}
              className="inline-flex items-center px-5 py-2 rounded-full text-sm font-medium text-white bg-novaDarkOrange hover:opacity-95"
            >
              {isLastStep ? "Submit" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
