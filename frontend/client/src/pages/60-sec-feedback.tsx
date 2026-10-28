import React, { useState, useCallback } from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import CustomSelect from "@/components/ui/select/v1/CustomSelect";
import { FormButton } from "@/utils/formComponents";
import { api } from "@/lib/api";
import { engageFeedbackContent, type QuestionDef } from "@/config/engageFeedbackContent";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";

interface EngageFeedbackPayload {
  time_value_feedback?: number;
  completion_time?: number;
  session_count?: number;
  help_level?: number;
  helper_type?: number[];
  help_reason?: number[];
  preparedness_level?: number;
  age_range?: number;
  gender?: number;
  gender_other?: string;
  overall_experience?: number;
  improvement_feedback?: string;
  recommendation_score?: number;
}

const questions = engageFeedbackContent.questions;

function SixtySecFeedbackPage() {
  const [timeValueFeedback, setTimeValueFeedback] = useState<number | null>(null);
  const [completionTime, setCompletionTime] = useState<number | null>(1);
  const [sessionCount, setSessionCount] = useState<number | null>(1);
  const [helpLevel, setHelpLevel] = useState<number | null>(null);
  const [helperType, setHelperType] = useState<number[]>([]);
  const [helpReason, setHelpReason] = useState<number[]>([]);
  const [preparednessLevel, setPreparednessLevel] = useState<number | null>(null);
  const [ageRange, setAgeRange] = useState<number | null>(1);
  const [gender, setGender] = useState<number | null>(null);
  const [genderOther, setGenderOther] = useState("");
  const genderQuestion = questions.find((q) => q.id === "gender");
  const genderOtherMaxLength = genderQuestion?.textFieldMaxLength ?? 50;
  const [overallExperience, setOverallExperience] = useState<number | null>(null);
  const [improvementFeedback, setImprovementFeedback] = useState("");
  const [recommendationScore, setRecommendationScore] = useState<number | null>(10);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [genderOtherError, setGenderOtherError] = useState<string | null>(null);

  const showHelperQuestions = helpLevel != null && helpLevel !== 1;
  const showImprovementArea = overallExperience != null;
  const isPositiveExperience = overallExperience != null && overallExperience <= 3;
  const overallQuestion = questions.find((q) => q.id === "overall_experience");
  const improvementPlaceholder = showImprovementArea
    ? isPositiveExperience
      ? overallQuestion?.improvementPromptPositive ?? "Thanks. Is there something we could do to make Nova Engage better?"
      : overallQuestion?.improvementPromptNegative ?? "Sorry to hear that. What could we have done to make Nova Engage better?"
    : "";
  const improvementMaxLength = overallQuestion?.textFieldMaxLength ?? 255;

  const getValue = useCallback(
    (id: string): number | number[] | null => {
      switch (id) {
        case "time_value_feedback":
          return timeValueFeedback;
        case "completion_time":
          return completionTime;
        case "session_count":
          return sessionCount;
        case "help_level":
          return helpLevel;
        case "helper_type":
          return helperType;
        case "help_reason":
          return helpReason;
        case "preparedness_level":
          return preparednessLevel;
        case "age_range":
          return ageRange;
        case "gender":
          return gender;
        case "overall_experience":
          return overallExperience;
        case "recommendation_score":
          return recommendationScore;
        default:
          return null;
      }
    },
    [
      timeValueFeedback,
      completionTime,
      sessionCount,
      helpLevel,
      helperType,
      helpReason,
      preparednessLevel,
      ageRange,
      gender,
      overallExperience,
      recommendationScore,
    ]
  );

  const setValue = useCallback((id: string, value: number | number[] | null) => {
    switch (id) {
      case "time_value_feedback":
        setTimeValueFeedback(value as number | null);
        break;
      case "completion_time":
        setCompletionTime(value as number | null);
        break;
      case "session_count":
        setSessionCount(value as number | null);
        break;
      case "help_level": {
        const num = value as number | null;
        setHelpLevel(num);
        if (num === 1) {
          setHelperType([]);
          setHelpReason([]);
        }
        break;
      }
      case "helper_type":
        setHelperType(Array.isArray(value) ? value : []);
        break;
      case "help_reason":
        setHelpReason(Array.isArray(value) ? value : []);
        break;
      case "preparedness_level":
        setPreparednessLevel(value as number | null);
        break;
      case "age_range":
        setAgeRange(value as number | null);
        break;
      case "gender":
        setGender(value as number | null);
        break;
      case "overall_experience":
        setOverallExperience(value as number | null);
        break;
      case "recommendation_score":
        setRecommendationScore(value as number | null);
        break;
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: EngageFeedbackPayload = {};
    if (timeValueFeedback != null) payload.time_value_feedback = timeValueFeedback;
    if (completionTime != null) payload.completion_time = completionTime;
    if (sessionCount != null) payload.session_count = sessionCount;
    if (helpLevel != null) payload.help_level = helpLevel;
    if (helpLevel != null && helpLevel !== 1) {
      if (helperType.length > 0) payload.helper_type = helperType;
      if (helpReason.length > 0) payload.help_reason = helpReason;
    }
    if (preparednessLevel != null) payload.preparedness_level = preparednessLevel;
    if (ageRange != null) payload.age_range = ageRange;
    if (gender != null) payload.gender = gender;
    if (gender === 4 && genderOther.length > genderOtherMaxLength) {
      setGenderOtherError(`Gender (other) must be ${genderOtherMaxLength} characters or less.`);
      return;
    }

    setGenderOtherError(null);
    if (genderOther.trim()) payload.gender_other = genderOther.trim();
    if (overallExperience != null) payload.overall_experience = overallExperience;
    if (improvementFeedback.trim()) payload.improvement_feedback = improvementFeedback.trim();
    if (recommendationScore != null) payload.recommendation_score = recommendationScore;

    setSubmitting(true);
    try {
      await api.post("/v1/engage-feedback", payload);
      setSubmitted(true);
    } catch (err) {
      console.error("Failed to submit feedback", err);
    } finally {
      setSubmitting(false);
    }
  };

  const renderQuestion = (q: QuestionDef) => {
    const value = getValue(q.id);
    if (q.id === "helper_type" || q.id === "help_reason") {
      if (!showHelperQuestions) return null;
    }

    if (q.type === "radio") {
      const isGenderQuestion = q.id === "gender";
      const showGenderOtherHere = isGenderQuestion && value === 4;
      return (
        <div key={q.id} className="mb-8">
          <p className="text-[12px] sm:text-[14px] text-novaNeutral-800 mb-3 font-medium">
            {q.title}
          </p>
          <div className="space-y-2">
            {q.options.map((opt) => {
              const isSelected = value === opt.key;
              return (
                <label
                  key={opt.key}
                  className={`flex items-center p-3 w-full max-w-lg border border-novaNeutral-400 rounded-lg cursor-pointer transition-colors ${
                    isSelected ? "bg-[#FFEA9E]" : "bg-white hover:bg-novaNeutral-50"
                  }`}
                >
                  <input
                    type="radio"
                    name={q.id}
                    value={opt.key}
                    checked={isSelected}
                    onChange={() => setValue(q.id, opt.key)}
                    className="sr-only"
                  />
                  <div className="flex-1 text-[12px] sm:text-[14px] text-novaNeutral-900 font-normal">
                    {opt.label}
                  </div>
                </label>
              );
            })}
          </div>
          {showGenderOtherHere && (
            <div className="mt-3 max-w-lg">
              <input
                type="text"
                value={genderOther}
                onChange={(e) => {
                  setGenderOther(e.target.value);
                  if (genderOtherError) setGenderOtherError(null);
                }}
                className={`w-full px-3 py-2 border rounded-lg text-novaNeutral-900 focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 ${
                  genderOtherError ? "border-red-500" : "border-novaNeutral-300"
                }`}
                maxLength={genderOtherMaxLength}
                placeholder="Other"
              />
              {genderOther.length >= genderOtherMaxLength && (
                <p className="mt-1 text-xs text-red-600">Reached maximum limit of {genderOtherMaxLength} characters.</p>
              )}
              {genderOtherError && (
                <p className="mt-1 text-xs text-red-600">{genderOtherError}</p>
              )}
            </div>
          )}
          {q.id === "overall_experience" && showImprovementArea && (
            <div className="mt-3 max-w-lg">
              <label className="block text-[12px] sm:text-[14px] text-novaNeutral-800 mb-2 font-medium">
                {improvementPlaceholder}
              </label>
              <textarea
                value={improvementFeedback}
                onChange={(e) => {
                  setImprovementFeedback(e.target.value);
                  if (improvementFeedback.length >= improvementMaxLength) setImprovementFeedback(`Reached maximum limit of ${improvementMaxLength} characters.`);
                }}
                placeholder="Your feedback..."
                rows={4}
                className={`w-full px-3 py-2 border rounded-lg text-novaNeutral-900 focus:ring-2 focus:ring-novaPrimary-500 focus:border-novaPrimary-500 min-h-[100px] ${
                  improvementFeedback.length >= improvementMaxLength ? "border-red-500" : "border-novaNeutral-300"
                }`}
                maxLength={improvementMaxLength}
              />
              {improvementFeedback.length >= improvementMaxLength && (
                <p className="mt-1 text-xs text-red-600">Reached maximum limit of {improvementMaxLength} characters.</p>
              )}
            </div>
          )}
        </div>
      );
    }

    if (q.type === "dropdown") {
      const options = q.options.map((o) => ({ value: String(o.key), label: o.label }));
      const currentVal = value != null ? String(value) : "";
      return (
        <div key={q.id} className="mb-8">
          <label className="block text-[12px] sm:text-[14px] text-novaNeutral-700 mb-1 font-medium">
            {q.title}
          </label>
          {q.subtitle && (
            <p className="text-sm text-novaNeutral-600 mb-1">{q.subtitle}</p>
          )}
          <div className="w-full max-w-lg md:[&_.absolute.overflow-y-auto]:max-h-40 [&_.absolute.overflow-y-auto]:max-h-28">
            <CustomSelect
              value={currentVal}
              onChange={(v) => setValue(q.id, v ? Number(v) : null)}
              options={options}
              triggerClassName="rounded-lg h-[46px]"
            />
          </div>
        </div>
      );
    }

    if (q.type === "checkbox") {
      const selectedKeys = Array.isArray(value) ? value : [];
      return (
        <div key={q.id} className="mb-8">
          <p className="text-[12px] sm:text-[14px] text-novaNeutral-800 mb-4 font-medium">
            {q.title}
          </p>
          <div className="space-y-4">
            {q.options.map((opt) => {
              const isChecked = selectedKeys.includes(opt.key);
              return (
                <label
                  key={opt.key}
                  className="group flex gap-3 cursor-pointer items-center"
                >
                  <span
                    className={`mt-0.5 flex h-[27px] w-[27px] flex-shrink-0 items-center justify-center rounded-md border border-novaNeutral-300 transition-colors ${
                      isChecked ? "bg-white" : ""
                    }`}
                  >
                    {isChecked && (
                      <span className="block h-[15px] w-[15px] rounded-full bg-[#FF9A50]" />
                    )}
                  </span>
                  <div className="flex-1 text-[12px] sm:text-[14px] font-normal text-novaNeutral-900 leading-snug">
                    {opt.label}
                  </div>
                  <input
                    type="checkbox"
                    name={`${q.id}_${opt.key}`}
                    checked={isChecked}
                    onChange={() => {
                      const next = isChecked
                        ? selectedKeys.filter((k) => k !== opt.key)
                        : [...selectedKeys, opt.key];
                      setValue(q.id, next);
                    }}
                    className="sr-only"
                  />
                </label>
              );
            })}
          </div>
          {q.subtitle && (
            <p className="mt-2 text-[12px] sm:text-[13px] text-novaNeutral-600">
              {q.subtitle}
            </p>
          )}
        </div>
      );
    }

    return null;
  };

  const pageBgStyle = { background: "linear-gradient(to bottom, #FFF4E0 0%, #FFD9D9 100%)" };

  if (submitted) {
    return (
      <div className="min-h-screen flex flex-col">
        <LandingHeader />
        <main
          className="flex-1 flex items-center justify-center p-6 min-h-[calc(100vh-80px)]"
          style={pageBgStyle}
        >
          <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8 text-center">
            <h2 className="text-2xl font-semibold text-novaNeutral-900 mb-4">Thank you</h2>
            <p className="text-novaNeutral-700">Your feedback has been submitted successfully.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <LandingHeader />
      <main
        className="flex-1 sm:min-h-[calc(100vh-80px)] min-h-[calc(100vh-145px)]"
        style={pageBgStyle}
      >
        <div className="p-4 sm:p-8 md:p-10 max-w-6xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-6 py-12 sm:p-8 sm:py-14 md:p-10 md:pb-20 md:pt-14">
            <h2 className="text-[32px] md:text-[38px] font-nineties text-novaBlack mb-4 md:mb-8 text-center" style={{ WebkitTextStroke: "0.5px #07161E" }}>Nova Engage 60 second feedback</h2>
            <div className="mb-8 text-[15px] sm:text-[16px] leading-relaxed text-novaNeutral-800 space-y-4 w-[90%] mx-auto">
              <p>{engageFeedbackContent.introParagraphs[0]}</p>
              <p className="font-semibold">{engageFeedbackContent.introParagraphs[1]}</p>
              <p>{engageFeedbackContent.introParagraphs[2]}</p>
              <p>{engageFeedbackContent.introParagraphs[3]}</p>
            </div>
            <div className="flex justify-center">
              <form
                onSubmit={handleSubmit}
                className="w-full max-w-xl"
                onKeyDown={(e) => {
                  if (e.key !== "Enter") return;
                  const target = e.target as HTMLElement;
                  if (target.tagName === "TEXTAREA") return;
                  const isSubmitButton =
                    (target as HTMLButtonElement).type === "submit" ||
                    target.closest?.("button[type='submit']");
                  if (!isSubmitButton) e.preventDefault();
                }}
              >
                {questions.map(renderQuestion)}
                <div className="pt-4">
                  <FormButton
                    type="submit"
                    variant="primary"
                    size="lg"
                    loading={submitting}
                    loadingText="Submitting..."
                    disabled={submitting}
                  >
                    Submit
                  </FormButton>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>
      <LandingFooter />
    </div>
  );
}

export default SixtySecFeedbackPage;
