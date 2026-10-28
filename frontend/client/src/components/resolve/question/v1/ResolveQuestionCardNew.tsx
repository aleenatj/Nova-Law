import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Tooltip } from "@/components/ui/tooltip";
import LoadingGif from "@/assets/landingpage/resolveloading.gif";
import ArrowIcon from "@/assets/resolve-images/arrow.svg";
import {
  FormInput,
  FormButton,
  createFieldProps,
} from "@/utils/formComponents";
import { useFormValidation, ValidationRule } from "@/utils/formValidator";
import {
  QuestionOption,
  QuestionAnswer,
  QuestionRule,
  QuestionData,
  ResolveResult,
} from "@/lib/types";
import { INPUT_MAX_LENGTH } from "@/lib/constants";


// Import all resolve images using import.meta.glob
const resolveImages = import.meta.glob("/src/assets/resolve-images/*.svg", {
  eager: true,
});

// Dynamic image mapping based on version and question identifier
const getImageForQuestion = (
  questionId: string,
  version: string = "1",
  questionTitle: string = ""
): { src: string; alt: string } => {
  // Format: version_questionId.svg (e.g., 1_2.svg, 1_3.svg)
  const imagePath = `/src/assets/resolve-images/${version}_${questionId}.svg`;

  // Try to get the image from the glob import
  const imageModule = resolveImages[imagePath] as
    | { default: string }
    | undefined;

  if (imageModule) {
    return {
      src: imageModule.default,
      alt: questionTitle || `Question ${questionId}`,
    };
  }

  // Fallback to default image if specific version_questionId.svg doesn't exist
  const defaultImagePath = "/src/assets/resolve-images/1_1.svg";
  const defaultImageModule = resolveImages[defaultImagePath] as
    | { default: string }
    | undefined;

  return {
    src: defaultImageModule?.default || "/src/assets/resolve-images/1_1.svg",
    alt: questionTitle || `Question ${questionId}`,
  };
};

// Helper function to normalize values for comparison by handling placeholder patterns
// This ensures that values with {partner_name} match values with actual partner names
// Strategy: Remove placeholder patterns and any text that follows them to compare the base structure
const normalizeValueForComparison = (value: string): string => {
  if (!value) return "";
  let normalized = String(value).trim();
  // Replace placeholder patterns with a normalized token to enable matching
  // This handles cases where stored answer has {partner_name} but option has replaced value
  normalized = normalized.replace(/\{partner_name\}/gi, "").replace(/\{name\}/gi, "");
  
  // Remove extra whitespace that might result from placeholder removal
  normalized = normalized.replace(/\s+/g, " ").trim();
  return normalized;
};
// Helper function to render HTML content safely
const renderHtmlContent = (htmlString: string | null) => {
  if (!htmlString) {
    return null;
  }
  
  // Check if the string contains HTML tags
  const hasHtmlTags = /<[^>]*>/g.test(htmlString);

  if (hasHtmlTags) {
    // Return JSX with dangerouslySetInnerHTML for HTML content
    return <div dangerouslySetInnerHTML={{ __html: htmlString }} />;
  } else {
    // Return plain text for non-HTML content
    return <div>{htmlString}</div>;
  }
};

// Helper function to get the selected option's additional title and description
const getSelectedOptionAdditionalInfo = (
  questionData: QuestionData,
  currentAnswer: string | string[]
): { title: string | null; description: string | null } => {
  if (!currentAnswer || (questionData.input_type !== "radio" && questionData.input_type !== "checkbox")) {
    return { title: null, description: null };
  }

  // For checkboxes, check all selected values; for radio, check the single value
  const selectedValues = Array.isArray(currentAnswer) ? currentAnswer : [currentAnswer];
  const titles: string[] = [];
  const descriptions: string[] = [];
  
  for (const optionGroup of questionData.options) {
    for (const [key, optionData] of Object.entries(optionGroup)) {
      // Check if this option is selected and has both additional_title and additional_description
      if (selectedValues.includes(optionData.value) && optionData.additional_title && optionData.additional_description) {
        titles.push(optionData.additional_title);
        descriptions.push(optionData.additional_description);
      }
    }
  }
  
  // Return both title and description joined together, or null if none found
  return {
    title: titles.length > 0 ? titles.join('\n\n') : null,
    description: descriptions.length > 0 ? descriptions.join('\n\n') : null
  };
};

// Helper function to get parent question title
const getParentQuestionTitle = (
  questionData: QuestionData,
  allQuestionData: Record<string, QuestionData>
): string | null => {
  if (questionData.variant !== "child" || !questionData.rules || questionData.rules.length === 0) {
    return null;
  }
  
  // Get the first parent question identifier from rules
  const parentQuestionId = questionData.rules[0]?.identifier;
  if (!parentQuestionId || !allQuestionData[parentQuestionId]) {
    return null;
  }
  
  const parentQuestion = allQuestionData[parentQuestionId];
  return parentQuestion.title || parentQuestion.question;
};

// Helper function to check if a child question should be shown based on parent answer
const shouldShowChildQuestion = (
  childQuestion: QuestionData,
  allAnswers: Record<string, string | string[]>,
  allQuestionData: Record<string, QuestionData>
): boolean => {
  if (!childQuestion.rules || childQuestion.rules.length === 0) {
    return true; // Show if no rules
  }

  return childQuestion.rules.some((rule) => {
    const parentAnswer = allAnswers[rule.identifier];
    if (!parentAnswer) return false;

    // Get parent question data to convert display values back to option keys
    const parentQuestionData = allQuestionData[rule.identifier];
    if (!parentQuestionData) return false;
    
    // Handle both single values and arrays (for checkboxes)
    const parentAnswerValues = Array.isArray(parentAnswer) ? parentAnswer : [parentAnswer];
    
    // Convert display values back to option keys
    const selectedOptionKeys: string[] = [];
    if (parentQuestionData.options) {
      for (const optionGroup of parentQuestionData.options) {
        for (const [key, optionData] of Object.entries(optionGroup)) {
          if (parentAnswerValues.includes(optionData.value)) {
            selectedOptionKeys.push(key);
          }
        }
      }
    }
    
    if (selectedOptionKeys.length === 0) return false;
    
    if (rule.operator === "in") {
      const allowedValues = Array.isArray(rule.value) ? rule.value : [rule.value];
      // Check if any of the selected option keys match the allowed values
      return selectedOptionKeys.some(key => allowedValues.includes(key));
    }
    
    // For "is" operator, check if any of the selected option keys match the rule value
    return selectedOptionKeys.includes(rule.value);
  });
};

interface ResolveQuestionCardProps {
  questionData: QuestionData;
  questionId: string;
  currentAnswer: string | string[];
  onInputChange: (value: string | string[]) => void;
  onNext: () => void;
  onPrevious?: () => void;
  canProceed: boolean;
  currentQuestionIndex: number;
  totalQuestions: number;
  /** Original question order (1-based) for step display; when set, step numbering stays fixed when questions are filtered by rules */
  currentQuestionStepNumber?: number;
  allAnswers?: Record<string, string | string[]>; // Add all answers for conditional logic
  allQuestionData?: Record<string, QuestionData>; // Add all question data for conditional logic
  isCompleting?: boolean; // Add loading state for completion
  resolveId?: string; // Resolve ID for logging
  onMarketingConsentChange?: (hasConsent: boolean) => void; // Callback for marketing consent changes
}

export function ResolveQuestionCard({
  questionData,
  questionId,
  currentAnswer,
  onInputChange,
  onNext,
  onPrevious,
  canProceed,
  currentQuestionIndex,
  totalQuestions,
  currentQuestionStepNumber,
  allAnswers = {},
  allQuestionData = {},
  isCompleting = false,
  resolveId,
  onMarketingConsentChange,
}: ResolveQuestionCardProps) {
  // Ref for the card container to enable scrolling
  const cardRef = useRef<HTMLDivElement>(null);
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);
  const [hasAgreedToUserAgreement, setHasAgreedToUserAgreement] = useState(false);
  const [hasAgreedToMarketing, setHasAgreedToMarketing] = useState(false);
  
  // Sync marketing consent with parent on mount and when it changes
  useEffect(() => {
    onMarketingConsentChange?.(hasAgreedToMarketing);
  }, [hasAgreedToMarketing, onMarketingConsentChange]);

  // When Tab is pressed and focus is outside the card (e.g. body) or on the card's Next/Back buttons, move focus to first option/answer. Do not intercept when focus is in the resolve header or in the info modal so those buttons can receive focus.
  useEffect(() => {
    if (!questionId || isCompleting) return;
    const getFirstFocusable = (): HTMLElement | null =>
      cardRef.current?.querySelector<HTMLElement>(
        "[data-resolve-first-focus], input:not([type='hidden']), textarea, [role='radio'], [role='checkbox']"
      ) ?? null;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== "Tab" || e.shiftKey) return;
      const card = cardRef.current;
      if (!card) return;
      const active = document.activeElement as Node | null;
      const header = document.querySelector("[data-resolve-header]");
      const isInHeader = !!active && !!header?.contains(active);
      if (isInHeader) return; // Let Tab work normally so Back and Save and Exit get focus
      const infoModal = document.querySelector("[data-resolve-info-modal]");
      const isInInfoModal = !!active && !!infoModal?.contains(active);
      if (isInInfoModal) return; // Let Tab work normally so modal Back/Next get focus
      const isInsideCard = !!active && card.contains(active);
      const navButtons = card.querySelector("[data-resolve-nav-buttons]");
      const isOnCardNavButtons = !!active && !!navButtons?.contains(active);
      if (isInsideCard && !isOnCardNavButtons) return;
      const first = getFirstFocusable();
      if (first) {
        e.preventDefault();
        e.stopPropagation();
        requestAnimationFrame(() => first.focus({ preventScroll: false }));
      }
    };
    document.addEventListener("keydown", handleKeyDown, true);
    return () => document.removeEventListener("keydown", handleKeyDown, true);
  }, [questionId, isCompleting]);

  // Scroll to top of card on every render
  // useEffect(() => {
  //   if (cardRef.current) {
  //     cardRef.current.scrollIntoView({ 
  //       behavior: 'smooth', 
  //       block: 'start' 
  //     });
  //   }
  // }, [questionId, currentQuestionIndex]); // Re-run when question changes

  // Add keyboard event handler – same guards as the Next/Complete button (including user agreement on email question)
  // When focus is on an option (label or input inside data-resolve-options), Enter selects the option (or goes to next if already selected); otherwise Enter goes to next question
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key !== "Enter") return;
    // Enter = next question everywhere (options use Space to select/toggle)
    const isLastEmailQuestion = questionId === "21" && currentQuestionIndex === totalQuestions - 1;
    const emailRequirementsMet = !isEmailQuestion || (isEmailValid && hasAgreedToUserAgreement);
    const canProceedWithEnter =
      canProceed &&
      !isCompleting &&
      emailRequirementsMet &&
      !isLastEmailQuestion;
    if (canProceedWithEnter) {
      e.preventDefault();
      onNext();
    }
    // Always prevent default on email question when agreement not checked, so Enter never submits without agreement
    if (isEmailQuestion && !hasAgreedToUserAgreement) {
      e.preventDefault();
    }
  };

  // Email validation function
  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Check if this is an email question that needs validation
  const isEmailQuestion = questionId === "21";
  const isEmailValid = isEmailQuestion && currentAnswer ? isValidEmail(currentAnswer as string) : true;

  // Same guards as Next button for when Enter is allowed to go to next question (used by radio option: Enter again on selected option)
  const isLastEmailQuestion = questionId === "21" && currentQuestionIndex === totalQuestions - 1;
  const emailRequirementsMet = !isEmailQuestion || (isEmailValid && hasAgreedToUserAgreement);
  const canProceedWithEnter =
    canProceed &&
    !isCompleting &&
    emailRequirementsMet &&
    !isLastEmailQuestion;

  // Get the selected option's additional title and description
  const { title: selectedOptionTitle, description: selectedOptionDescription } = getSelectedOptionAdditionalInfo(questionData, currentAnswer);
  useEffect(() => {
    setIsInfoModalOpen(false);
  }, [questionId]);

  const closeInfoModal = () => {
    setIsInfoModalOpen(false);
  };

  // Check if the question has been answered
  const hasAnswer = () => {
    if (!currentAnswer) return false;
    if (Array.isArray(currentAnswer)) {
      return currentAnswer.length > 0;
    }
    if (typeof currentAnswer === 'string') {
      return currentAnswer.trim().length > 0;
    }
    return false;
  };

  // Determine button text based on question requirement and answer status
  const getButtonText = () => {
    // Last question is always "Complete"
    if (currentQuestionIndex === totalQuestions - 1) {
      return "Next";
    }
    
    // Required questions always show "Next"
    if (questionData.required) {
      return "Next";
    }
    
    // Optional questions show "Skip" if not answered, "Next" if answered
    return hasAnswer() ? "Next" : "Skip";
  };

  // Render different input types based on question input_type
  const renderInput = () => {
    if (!questionData) return null;

    // Get placeholder text - prioritize API placeholder, fallback to question text
    const placeholderText =
      questionData.placeholder || questionData.question || "";

    switch (questionData.input_type) {
      case "text":
      case "number":
      case "textarea":
        return (
          <div className="space-y-2">
            {/* Show label only if there's a placeholder */}
            {/* {questionData.placeholder && (
              <label className="block text-[16px] sm:text-[18px] text-novaNeutral-700 mb-2 font-roman">
                {questionData.placeholder}{" "}
                {questionData.required && (
                  <span className="text-novaCaution-500">*</span>
                )}
              </label>
            )} */}
            <div className="relative">
              <input
                data-resolve-first-focus
                type={isEmailQuestion ? "email" : questionData.input_type}
                value={currentAnswer as string}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyPress={handleKeyPress}
                onKeyDown={(e) => {
                  if (questionData.input_type === "number" && ["-", "e", "E", "+"].includes(e.key)) {
                    e.preventDefault();
                  }
                }}
                maxLength={INPUT_MAX_LENGTH.RESOLVE_QUESTION_TEXT}
                min={questionData.input_type === "number" ? 0 : undefined}
                max={questionData.input_type === "number" ? 99 : undefined}
                placeholder={placeholderText}
                className={`w-full px-3 sm:px-4 py-3 sm:py-3.5 text-[16px] sm:text-[18px] font-roman border rounded-[8px] focus:outline-none focus-visible:ring-2 focus-visible:border-transparent ${
                isEmailQuestion && currentAnswer && !isEmailValid
                  ? "border-novaCaution-500 focus-visible:ring-novaCaution-500"
                  : "border-novaNeutral-300 focus-visible:ring-novaPrimary-500"
              }`}
              />
            </div>
            {((currentAnswer as string)?.length || 0) >= INPUT_MAX_LENGTH.RESOLVE_QUESTION_TEXT && (
              <div className="text-xs text-novaCaution-500 mt-1">Limit reached</div>
            )}
            {questionData.input_type === "number" && (Number(currentAnswer as string) > 99) && (
              <div className="text-xs text-novaCaution-500 mt-1">Maximum value is 99</div>
            )}
            {!questionData.placeholder && questionData.required && (
              <p className="text-sm text-novaCaution-500">* Required field</p>
            )}
            {/* Email validation error message */}
            {isEmailQuestion && currentAnswer && !isEmailValid && (
              <p className="text-sm text-novaCaution-500">
                Please enter a valid email address
              </p>
            )}
          </div>
        );

      case "radio":
        return (
          <div className="space-y-3">
            <p className="text-[16px] sm:text-[18px] text-novaNeutral-600 mb-3 font-roman">
              Select one option:
              {questionData.required && (
                <span className="text-novaCaution-500 ml-1">*</span>
              )}
            </p>
            <div className="space-y-2" onKeyPress={handleKeyPress} data-resolve-options>
              {questionData.options.map((optionGroup, groupIndex) =>
                Object.entries(optionGroup).map(([key, option], optionIndex) => {
                  // Compare values, handling placeholder patterns like {partner_name}
                  const answerStr = String(currentAnswer || "").trim();
                  const optionStr = String(option.value || "").trim();
                  
                  // Try exact match first
                  let isSelected = answerStr === optionStr;
                  
                  // If exact match fails and placeholders are involved, try normalized comparison
                  if (!isSelected) {
                    const hasPlaceholderPattern = /\{partner_name\}|\{name\}/.test(answerStr) || 
                                                  /\{partner_name\}|\{name\}/.test(optionStr);
                    
                    if (hasPlaceholderPattern) {
                      // Normalize both values by removing placeholder patterns
                      const normalizedAnswer = normalizeValueForComparison(answerStr);
                      const normalizedOptionValue = normalizeValueForComparison(optionStr);
                      
                      // Compare normalized values - they should match if they represent the same option
                      isSelected = normalizedAnswer !== "" && 
                                  normalizedOptionValue !== "" && 
                                  normalizedAnswer === normalizedOptionValue;
                    }
                  }

                  const selectThisOption = () => {
                    onInputChange(option.value);
                    if (option.additional_description && option.additional_title) {
                      setIsInfoModalOpen(true);
                    } else {
                      setIsInfoModalOpen(false);
                    }
                  };
                  const isFirstOption = groupIndex === 0 && optionIndex === 0;

                  return (
                    <div key={key} className="flex items-center gap-2">
                      <div
                        {...(isFirstOption ? { "data-resolve-first-focus": true } : {})}
                        role="radio"
                        aria-checked={isSelected}
                        tabIndex={0}
                        className={`flex-1 flex outline-none rounded-lg cursor-pointer transition-colors border border-novaNeutral-400 focus:outline-none ${
                          isSelected
                            ? "focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-novaNeutral-400 bg-[#FFEA9E]"
                            : "focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:border-novaPrimary-500 bg-white hover:bg-novaNeutral-50"
                        }`}
                        onKeyDown={(e) => {
                          if (e.key === " ") {
                            e.preventDefault();
                            e.stopPropagation();
                            selectThisOption();
                            requestAnimationFrame(() => (e.currentTarget as HTMLElement).focus());
                          }
                          // Enter = next question (handled by handleKeyPress on container)
                        }}
                        onClick={(e) => {
                          e.currentTarget.focus();
                        }}
                      >
                        <label
                          className={`flex-1 flex items-center p-4 rounded-lg cursor-pointer transition-colors border-0 ${
                            isSelected
                              ? "bg-[#FFEA9E]"
                              : "bg-transparent hover:bg-transparent"
                          }`}
                        >
                          <input
                            type="radio"
                            name={questionId}
                            value={option.value}
                            checked={isSelected}
                            tabIndex={-1}
                            aria-hidden
                            onChange={(e) => {
                              onInputChange(e.target.value);
                              if (option.additional_description && option.additional_title) {
                                setIsInfoModalOpen(true);
                              } else {
                                setIsInfoModalOpen(false);
                              }
                            }}
                            className="sr-only"
                          />
                          <div className="flex-1">
                            <div
                              className="text-[18px] text-novaNeutral-900 font-roman"
                              style={{ lineHeight: "1.4rem" }}
                            >
                              {option.value}
                            </div>
                          </div>
                          {isSelected && (
                            <span className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-[#FF9A50] text-white" aria-hidden>
                              <i className="fas fa-check text-sm !text-white" />
                            </span>
                          )}
                        </label>
                      </div>
                      {option.tooltip && (
                        <Tooltip content={option.tooltip} position="right-mobile">
                          <div
                            className="flex-shrink-0 flex items-center justify-center w-5 h-5 text-novaNeutral-500 hover:text-novaNeutral-600 cursor-help"
                            tabIndex={-1}
                            aria-hidden
                          >
                            <i className="fas fa-question-circle text-sm"></i>
                          </div>
                        </Tooltip>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );
  
        case "checkbox":
          return (
            <div className="space-y-2">
              <p className="text-[16px] sm:text-[18px] text-novaNeutral-600 mb-2 font-roman">
                Select all that apply.
                {questionData.required && (
                  <span className="text-novaCaution-500 ml-1">*</span>
                )}
              </p>
              <div className="space-y-2" onKeyPress={handleKeyPress} data-resolve-options>
                {questionData.options.map((optionGroup, groupIndex) =>
                  Object.entries(optionGroup).map(([key, option], optionIndex) => {
                    const selectedValues = Array.isArray(currentAnswer)
                      ? currentAnswer.map(v => normalizeValueForComparison(String(v)))
                      : [];
                    const normalizedOptionValue = normalizeValueForComparison(String(option.value || ""));
                    const isChecked = normalizedOptionValue !== "" && selectedValues.includes(normalizedOptionValue);
                    const isFirstOption = groupIndex === 0 && optionIndex === 0;

                    const toggleThisOption = () => {
                      const newValues = isChecked
                        ? selectedValues.filter((val) => val !== option.value)
                        : [...selectedValues, option.value];
                      onInputChange(newValues);
                      if (!isChecked && option.additional_description && option.additional_title) {
                        setIsInfoModalOpen(true);
                      } else if (isChecked && (!option.additional_description || !option.additional_title)) {
                        setIsInfoModalOpen(false);
                      }
                    };

                  return (
                    <div key={key} className="flex items-center gap-2">
                      <div
                        {...(isFirstOption ? { "data-resolve-first-focus": true } : {})}
                        role="checkbox"
                        aria-checked={isChecked}
                        tabIndex={0}
                        className={`flex-1 flex outline-none rounded-lg cursor-pointer transition-colors focus:outline-none ${
                        isChecked
                          ? "focus-visible:ring-0 focus-visible:ring-offset-0"
                          : "focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
                        }`}
                        onKeyDown={(e) => {
                          if (e.key === " ") {
                            e.preventDefault();
                            e.stopPropagation();
                            toggleThisOption();
                          }
                          // Enter = next question (handled by handleKeyPress on container)
                        }}
                        onClick={(e) => { (e.currentTarget as HTMLElement).focus(); }}
                      >
                        <label className="group flex-1 flex gap-2 cursor-pointer hover:bg-transparent items-center py-1">
                          <span
                            className={`mt-0.5 flex h-[27px] w-[27px] items-center justify-center rounded-md border border-novaNeutral-300 transition-colors ${
                              isChecked ? "bg-white" : ""
                            }`}
                          >
                            {isChecked && (
                              <span className="block h-[15px] w-[15px] rounded-full bg-[#FF9A50]" />
                            )}
                          </span>
                          <div className="flex-1 text-[18px] font-normal font-roman text-novaNeutral-900 leading-snug whitespace-normal">
                            {option.value}
                          </div>
                          <input
                            type="checkbox"
                            name={`${questionId}_${key}`}
                            value={option.value}
                            checked={isChecked}
                            tabIndex={-1}
                            aria-hidden
                            onChange={(e) => {
                              const newValues = isChecked
                                ? selectedValues.filter((val) => val !== option.value)
                                : [...selectedValues, option.value];
                              onInputChange(newValues);
                              if (!isChecked && option.additional_description && option.additional_title) {
                                setIsInfoModalOpen(true);
                              } else if (isChecked && (!option.additional_description || !option.additional_title)) {
                                setIsInfoModalOpen(false);
                              }
                            }}
                            className="sr-only"
                          />
                        </label>
                      </div>
                      {option.tooltip && (
                        <Tooltip content={option.tooltip} position="right-mobile">
                          <div
                            className="flex-shrink-0 flex items-center justify-center w-5 h-5 text-novaNeutral-400 hover:text-novaNeutral-600 cursor-help"
                            tabIndex={-1}
                            aria-hidden
                          >
                            <i className="fas fa-question-circle text-sm"></i>
                          </div>
                        </Tooltip>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );

      default:
        return (
          <div className="space-y-2">
            {/* Show label only if there's a question */}
            {questionData.question && (
              <label className="block text-[16px] sm:text-[18px] text-novaNeutral-700 mb-2 font-roman">
                {questionData.question}{" "}
                {questionData.required && (
                  <span className="text-novaCaution-500">*</span>
                )}
              </label>
            )}
            <>
              <input
                data-resolve-first-focus
                type="text"
                value={currentAnswer as string}
                onChange={(e) => onInputChange(e.target.value)}
                maxLength={INPUT_MAX_LENGTH.RESOLVE_QUESTION_DEFAULT}
                onKeyPress={handleKeyPress}
                placeholder={placeholderText}
                className="w-full px-4 py-3 border border-novaNeutral-300 rounded-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:border-transparent"
              />
              {(typeof currentAnswer === "string" && currentAnswer.length >= INPUT_MAX_LENGTH.RESOLVE_QUESTION_DEFAULT) && (
                <div className="text-xs text-novaCaution-500 mt-1">Limit reached</div>
              )}
            </>
          </div>
        );
    }
  };

  if (!questionData) {
    return (
      <div className="flex justify-center items-center w-full min-h-screen">
        <div className="text-center">
          <p className="text-novaNeutral-600">No question data available</p>
        </div>
      </div>
    );
  }

  // Get dynamic image based on version and question ID, using question title for alt text
  const image = getImageForQuestion(
    questionId,
    questionData.version,
    questionData.title
  );

  // Display title: question title -> parent question title -> question text
  const displayTitle = questionData.title || getParentQuestionTitle(questionData, allQuestionData);
  // Display description: question description -> question text (if no description)
  const displayDescription = questionData.description || questionData.question;

  // Render loading card when completing
  if (isCompleting) {
    return (
      <div className="flex justify-center w-full overflow-y-auto">
        <div className="w-full max-w-[904px]">
          <div
            ref={cardRef}
            className="relative bg-transparent sm:border-[18px] border-[10px] rounded-[27px]"
            style={{ borderColor: 'rgba(252, 215, 176, 0.5)' }}
          >
            <div className="bg-[#f6f6f6] rounded-[18px] sm:rounded-[10px] px-6 py-8 sm:px-20 sm:py-24 flex flex-col">
              <div className="flex flex-col items-center justify-center text-center">
                  <img
                    src={LoadingGif}
                    className="w-40 sm:w-48 lg:w-[220px] h-auto object-contain mb-4"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = "/src/assets/resolve-images/1_1.svg";
                    }}
                  />
                  <h2 className="max-w-[90%] md:max-w-[70%] mb-2 text-[40px] md:text-[64px] font-nineties leading-[1.1] font-normal text-novaBlack">
                    Finding the best path for you
                  </h2>
                  <p className="text-[16px] sm:text-[18px] leading-[1.4] text-novaBlack font-roman mt-5">
                    This should only take a moment
                  </p>
              </div>

                
            </div>
          </div>
        </div>
      </div>
    );
  }


  return (
    <>
      <div className="flex justify-center w-full overflow-y-auto">
        <div className="w-full max-w-[904px] min-h-[594px]">
          <div
            ref={cardRef}
            className="relative bg-transparent sm:border-[18px] border-[10px] rounded-[27px]"
            style={{ borderColor: 'rgba(252, 215, 176, 0.5)' }}
          >
            <div className="bg-white rounded-[18px] sm:rounded-[10px] px-6 py-8 sm:px-20 sm:py-16 flex flex-col gap-8">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2">
                <div className="flex-1 md:max-w-[520px]">
                  <p className="text-[24px] leading-[1.4] text-novaBlack mb-8 md:mb-[100px] font-nineties tracking-wide text-left">
                    {currentQuestionStepNumber != null
                      ? `${currentQuestionStepNumber + 1}/${totalQuestions + 1}`
                      : `${currentQuestionIndex + 2}/${totalQuestions + 1}`}{" "}
                    Steps
                  </p>
                  <div className="md:hidden flex justify-center mb-8">
                    <img
                      src={image.src}
                      alt={image.alt}
                      className="w-[180px] h-auto object-contain"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = "/src/assets/resolve-images/1_1.svg";
                      }}
                    />
                  </div>
                  <h1 className="text-[32px] sm:text-[40px] leading-[1] font-normal font-nineties text-left mb-4">
                    {displayTitle}
                  </h1>
                  <div className="font-roman text-novaNeutral-600 text-[16px] sm:text-[18px] leading-relaxed text-left mb-4 break-words">
                    {renderHtmlContent(displayDescription)}
                  </div>
                  <div className="mt-4 space-y-6">
                    {renderInput()}
                  </div>

                  {isEmailQuestion && (
                    <div className="flex flex-col gap-4 mt-8 mb-2">
                      <div className="flex items-center gap-3 text-left">
                        <input
                          id="user-agreement-checkbox"
                          type="checkbox"
                          className="h-4 w-4 accent-novaPrimary-500 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
                          checked={hasAgreedToUserAgreement}
                          onChange={(e) => setHasAgreedToUserAgreement(e.target.checked)}
                          onKeyDown={(e) => {
                            if (e.key === " ") {
                              e.preventDefault();
                              setHasAgreedToUserAgreement((prev) => !prev);
                            }
                          }}
                        />
                        <label className="text-sm font-novaBlack w-[90%]" htmlFor="user-agreement-checkbox">
                          I agree to Nova&apos;s{" "}
                          <a
                            href="/user-agreement"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-novaPurple-600"
                          >
                            User Agreement
                          </a>{" "}
                          &amp;{" "}
                          <a
                            href="/privacy-policy"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-novaPurple-600"
                          >
                            Privacy Policy
                          </a>
                          <span className="text-novaCaution-500"> *</span>
                        </label>
                      </div>
                      {/* <div className="flex gap-3 text-left">
                      <input
                        id="marketing-checkbox"
                        type="checkbox"
                        checked={hasAgreedToMarketing}
                        onChange={(e) => setHasAgreedToMarketing(e.target.checked)}
                        className="h-4 w-4 accent-novaPrimary-500 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
                        onKeyDown={(e) => {
                          if (e.key === " ") {
                            e.preventDefault();
                            setHasAgreedToMarketing((prev) => !prev);
                          }
                        }}
                      />
                      <label className="text-sm font-novaBlack w-[90%]" htmlFor="marketing-checkbox">
                        I agree to receive marketing communications from Nova by email. We won’t share your details with third parties and you can unsubscribe at any time.
                      </label>
                    </div> */}
                    </div>
                  )}
                </div>

                <div className="hidden md:flex flex-shrink-0 justify-center md:justify-end md:items-start">
                  <img
                    src={image.src}
                    alt={image.alt}
                    className="w-40 sm:w-48 lg:w-[220px] h-auto object-contain"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = "/src/assets/resolve-images/1_1.svg";
                    }}
                  />
                </div>
              </div>

              <div
                className={`mt-8 flex flex-wrap items-center justify-start gap-3 ${
                  isEmailQuestion ? "w-full sm:w-auto" : ""
                }`}
              >
                {onPrevious && currentQuestionIndex > -1 && (
                  <FormButton
                    type="button"
                    variant="custom"
                    onClick={onPrevious}
                    disabled={isCompleting}
                    className={`px-5 py-2 h-[44px] border border-novaBlack bg-transparent text-novaBlack text-[20px] sm:text-[22px] font-normal rounded-full transition-all duration-200 sm:hover:bg-novaBlack sm:hover:text-white sm:hover:border-novaNeutral-500 disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 ${
                      isEmailQuestion ? "flex-1 min-w-0 sm:flex-none" : ""
                    }`}
                  >
                    Back
                  </FormButton>
                )}
                <FormButton
                  type="button"
                  variant="tertiary"
                  onClick={onNext}
                  disabled={
                    !canProceed ||
                    isCompleting ||
                    (isEmailQuestion && !isEmailValid) ||
                    (isEmailQuestion && !hasAgreedToUserAgreement)
                  }
                  className={`px-5 py-2.5 bg-novaBlack text-white text-[20px] sm:text-[22px] font-normal rounded-full transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white ${
                    (!canProceed ||
                      isCompleting ||
                      (isEmailQuestion && !isEmailValid) ||
                      (isEmailQuestion && !hasAgreedToUserAgreement)
                    )
                      ? "opacity-95 cursor-not-allowed"
                      : "sm:hover:bg-gradient-to-r sm:hover:from-[#9A00D2] sm:hover:to-[#F41471] hover:bg-novaNeutral-800"
                  }`}
                >
                  {isCompleting ? (
                    <span className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      <span className="hidden xs:inline">Completing...</span>
                      <span className="xs:hidden">...</span>
                    </span>
                  ) : (
                    <div className="flex items-center gap-2">
                      {isEmailQuestion ? (
                        <>
                          <span className="sm:hidden">
                            See personalised recommendation
                          </span>
                          <span className="hidden sm:inline">
                            See my personalised recommendation
                          </span>
                        </>
                      ) : (
                        getButtonText()
                      )}
                      <img src={ArrowIcon} alt="arrow" className="w-6 h-4" />
                    </div>
                  )}
                </FormButton>
              </div>
            </div>
          </div>
        </div>
      </div>

      {isInfoModalOpen && selectedOptionTitle && selectedOptionDescription && (
        <div
          data-resolve-info-modal
          className="fixed inset-0 sm:inset-0 flex items-end sm:items-center justify-center sm:px-4 sm:py-0"
          onClick={closeInfoModal}
        >
          <div
            className="absolute inset-0 opacity-95 overflow-y-auto"
            style={{
              background:
                "radial-gradient(120% 120% at 35% 20%, #ff8d28bf 0%, #FF9A63 45%, #FF6A48 70%, #F64C7D 90%)",
            }}
          />

          <div
            className="relative w-full 2xl:max-w-[998px] max-w-[800px] mt-20 sm:mt-0 overflow-y-auto sm:rounded-[36px]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mx-auto sm:rounded-[36px] rounded-md sm:border-[16px] border-t-[12px] bg-[#ff7a42] border-[#ff7a42] shadow-[0_28px_80px_rgba(0,0,0,0.18)] overflow-y-auto">
              <div className="bg-[#fefdf0] px-8 py-12 text-center sm:px-14 sm:py-20 rounded-t-[16px] sm:rounded-[20px]">
                <div className="flex flex-col items-start 2xl:w-[65%] md:w-[85%] w-full mx-auto pb-20 sm:pb-5">
                  <h1 className="font-nineties text-left text-[40px] 2xl:text-[62px] mb-6 leading-[1] font-normal text-novaBlack sm:text-[52px]">
                    {selectedOptionTitle || ''}
                  </h1>
                  <div className="space-y-6 text-novaNeutral-900 font-roman text-lg leading-relaxed text-left w-full">
                    {renderHtmlContent(selectedOptionDescription)}
                  </div>

                  <div className="mt-8 flex items-start gap-4 flex-row sm:static sm:mt-8 fixed bottom-0 left-0 right-0 bg-[#fefdf0] px-6 py-4 sm:px-0 sm:py-0 sm:bg-transparent z-10 border-t border-novaNeutral-100 sm:border-none">
                    <FormButton
                      variant="outline"
                      onClick={closeInfoModal}
                      className="inline-flex items-center justify-center rounded-full border-2 border-novaBlack px-6 py-2.5 text-[20px] sm:text-[24px] text-novaBlack transition-colors hover:bg-white/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
                    >
                      Back
                    </FormButton>
                    <FormButton
                      variant="tertiary"
                      onClick={() => {
                        closeInfoModal();
                        if (canProceed && !isCompleting && (!isEmailQuestion || isEmailValid)) {
                          onNext();
                        }
                      }}
                      className="inline-flex items-center justify-center gap-2 rounded-full bg-novaBlack px-6 py-3 text-[20px] sm:text-[24px] text-white transition-colors hover:bg-novaNeutral-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
                    >
                      Next
                      <img src={ArrowIcon} alt="arrow" className="w-6 h-4" />
                    </FormButton>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
