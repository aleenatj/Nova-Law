import React, { useState, useEffect, useCallback, useRef } from "react";
import { createPortal } from "react-dom";
import { api } from "../../lib/api";
import { createSuccessToast, createErrorToast, toastManager } from "../../utils/toasts";
import { FormButton } from "@/utils/formComponents";
import ArrowIcon from "@/assets/resolve-images/arrow.svg";
import accountSetupBackground from "@/assets/landingpage/accountsetupbackground.webp";
import { KycQuestion, KycRule, KycAnswer, KycFormData } from "@/lib/kyc.types";
import { toTitleCase } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";

// Component-specific types
interface KycFormNewProps {
  data: Record<string, KycFormData>;
  isOpen: boolean;
  onClose: () => void;
  caseId?: string;
  viewMode?: boolean;
  onSubmit?: () => void;
}

interface MessageItem {
  success: boolean;
  message: string;
}

interface ApiResponse {
  success: boolean;
  message?: string | MessageItem[];
}

// Helper: get the key for a display value from options
function getOptionKeyFromDisplayValue(options: KycQuestion[], displayValue: string): string | null {
  for (const opt of options) {
    if (typeof opt === "object" && opt !== null) {
      const [key, val] = Object.entries(opt)[0];
      if (val === displayValue) return key;
    }
  }
  return null;
}

// Helper: get the display value for a key from options
function getOptionDisplayValueFromKey(options: KycQuestion[], key: string): string | null {
  for (const opt of options) {
    if (typeof opt === "object" && opt !== null) {
      const [k, val] = Object.entries(opt)[0];
      if (k === key) return val as string;
    }
  }
  return null;
}

// Helper: check if a rule is satisfied given the parent answer
function isRuleSatisfied(rule: KycRule, parentValue: any, parentOptions: KycQuestion[]): boolean {
  if (parentValue === undefined || parentValue === null || parentValue === "") return false;
  if (Array.isArray(parentValue) && parentValue.length === 0) return false;

  let parentKeys: string[] = [];
  if (Array.isArray(parentValue)) {
    parentKeys = parentValue.map(val => {
      const key = getOptionKeyFromDisplayValue(parentOptions, val);
      return key || val;
    }).filter(Boolean) as string[];
  } else {
    const key = getOptionKeyFromDisplayValue(parentOptions, parentValue);
    parentKeys = [key || parentValue];
  }

  if (rule.operator === "in") {
    const ruleValues = Array.isArray(rule.value) ? rule.value : [rule.value];
    return parentKeys.some(key => ruleValues.includes(key));
  }
  return false;
}

const KycFormNew: React.FC<KycFormNewProps> = ({ data, isOpen, onClose, caseId, viewMode = false, onSubmit }) => {
  const { refreshUserFromStorage } = useAuth();
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [allAnswersInitiallyFilled, setAllAnswersInitiallyFilled] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const modalContentRef = useRef<HTMLDivElement>(null);

  // Focus trap: when KYC modal is open, keep Tab focus inside the modal
  useEffect(() => {
    if (!isOpen || !modalContentRef.current) return;

    const getFocusables = (root: HTMLElement): HTMLElement[] => {
      const selector = 'button:not([disabled]), [href], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
      return Array.from(root.querySelectorAll<HTMLElement>(selector)).filter(
        el => el.offsetParent !== null && !el.hasAttribute('aria-hidden')
      );
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !modalContentRef.current) return;
      const focusables = getFocusables(modalContentRef.current);
      if (focusables.length === 0) return;
      const current = document.activeElement as HTMLElement;
      if (!modalContentRef.current.contains(current)) return;

      const first = focusables[0];
      const last = focusables[focusables.length - 1];

      if (e.shiftKey) {
        if (current === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (current === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    const handleFocusIn = (e: FocusEvent) => {
      if (!modalContentRef.current) return;
      const target = e.target as Node | null;
      if (target && !modalContentRef.current.contains(target)) {
        const root = modalContentRef.current;
        setTimeout(() => {
          const focusables = getFocusables(root);
          if (focusables.length > 0) focusables[0].focus();
        }, 0);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('focusin', handleFocusIn);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('focusin', handleFocusIn);
    };
  }, [isOpen]);

  // Scroll to top when question changes
  useEffect(() => {
    scrollContainerRef.current?.scrollTo({ top: 0, behavior: 'instant' });
  }, [currentQuestionIndex]);

  // Prepopulate form data from existing answers or default values
  useEffect(() => {
    const initialFormData: Record<string, any> = {};
    Object.entries(data).forEach(([questionKey, questionData]) => {
      // Handle form type questions with nested sub-questions
      if (questionData.input_type?.toLowerCase() === 'form' && questionData.form_fields?.questions) {
        Object.entries(questionData.form_fields.questions).forEach(([subKey, subQuestionData]) => {
          if (subQuestionData.answer && subQuestionData.answer.length > 0) {
            const subInputType = subQuestionData.input_type?.toLowerCase();
            if (subInputType === 'checkbox') {
              let answerKeys: string[] = [];
              if (subQuestionData.answer.length > 1) {
                answerKeys = subQuestionData.answer.map((ans: KycAnswer) => ans.value);
              } else if (subQuestionData.answer.length === 1 && typeof subQuestionData.answer[0].value === 'string') {
                answerKeys = subQuestionData.answer[0].value.split(',').map(key => key.trim());
              }
              const displayValues = answerKeys
                .map(key => getOptionDisplayValueFromKey(subQuestionData.options, key))
                .filter((value): value is string => value !== null);
              if (displayValues.length > 0) {
                initialFormData[subKey] = displayValues;
              }
            } else if (subInputType === 'radio') {
              const answerValue = subQuestionData.answer[0].value;
              const displayValue = getOptionDisplayValueFromKey(subQuestionData.options, answerValue);
              initialFormData[subKey] = displayValue || answerValue;
            } else {
              const answerValue = subQuestionData.answer[0].value;
              initialFormData[subKey] = answerValue;
            }
          }
        });
      } else if (questionData.answer && questionData.answer.length > 0) {
        if (questionData.input_type?.toLowerCase() === 'checkbox') {
          let answerKeys: string[] = [];
          if (questionData.answer.length > 1) {
            answerKeys = questionData.answer.map((ans: KycAnswer) => ans.value);
          } else if (questionData.answer.length === 1 && typeof questionData.answer[0].value === 'string') {
            answerKeys = questionData.answer[0].value.split(',').map(key => key.trim());
          }
          const displayValues = answerKeys
            .map(key => getOptionDisplayValueFromKey(questionData.options, key))
            .filter((value): value is string => value !== null);
          if (displayValues.length > 0) {
            initialFormData[questionKey] = displayValues;
          }
        } else if (questionData.input_type?.toLowerCase() === 'radio') {
          const answerValue = questionData.answer[0].value;
          const displayValue = getOptionDisplayValueFromKey(questionData.options, answerValue);
          initialFormData[questionKey] = displayValue || answerValue;
        } else {
          const answerValue = questionData.answer[0].value;
          initialFormData[questionKey] = answerValue;
        }
      } else if (questionData.default) {
        const defaultKey = questionData.default;
        const defaultDisplayValue = getOptionDisplayValueFromKey(questionData.options, defaultKey);
        if (defaultDisplayValue) {
          if (questionData.input_type?.toLowerCase() === 'checkbox') {
            initialFormData[questionKey] = [defaultDisplayValue];
          } else {
            initialFormData[questionKey] = defaultDisplayValue;
          }
        }
      }
    });
    setFormData(initialFormData);

    setTimeout(() => {
      const formQuestions = Object.entries(data)
        .sort(([, a], [, b]) => a.question_order - b.question_order);
      const isVisible = (questionData: KycFormData): boolean => {
        if (!questionData.rules || questionData.rules.length === 0) return true;
        return questionData.rules.every(rule => {
          const parentValue = initialFormData[rule.identifier];
          const parentOptions = data[rule.identifier]?.options || [];
          return isRuleSatisfied(rule, parentValue, parentOptions);
        });
      };
      const visibleQuestions = formQuestions.filter(([key, questionData]) => isVisible(questionData));
      const allFilled = visibleQuestions.every(([questionKey, questionData]) => {
        if (!questionData.required) return true;
        const currentValue = initialFormData[questionKey] ?? '';
        if (Array.isArray(currentValue)) {
          return currentValue.length > 0;
        }
        return currentValue !== '' && currentValue !== null && currentValue !== undefined;
      });
      setAllAnswersInitiallyFilled(allFilled && visibleQuestions.length > 0);
    }, 0);
  }, [data]);

  const getParentValue = useCallback((identifier: string) => formData[identifier], [formData]);
  const getParentOptions = useCallback((identifier: string) => data[identifier]?.options || [], [data]);

  const isQuestionVisible = useCallback((questionData: KycFormData): boolean => {
    if (!questionData.rules || questionData.rules.length === 0) return true;
    return questionData.rules.every(rule => {
      const parentValue = getParentValue(rule.identifier);
      const parentOptions = getParentOptions(rule.identifier);
      return isRuleSatisfied(rule, parentValue, parentOptions);
    });
  }, [getParentValue, getParentOptions]);

  // When a parent answer changes, clear answers for hidden child questions
  useEffect(() => {
    const newFormData = { ...formData };
    let changed = false;
    Object.entries(data).forEach(([questionKey, questionData]) => {
      if (questionData.rules && questionData.rules.length > 0) {
        if (!isQuestionVisible(questionData) && newFormData[questionKey] !== undefined) {
          newFormData[questionKey] = undefined;
          changed = true;
        }
      }
    });
    if (changed) setFormData(newFormData);
  }, [formData, data, isQuestionVisible]);

  if (!isOpen) return null;

  // Sort questions by question_order and filter visible
  const formQuestions = Object.entries(data)
    .sort(([, a], [, b]) => a.question_order - b.question_order);

  const visibleQuestions = formQuestions.filter(([key, questionData]) => isQuestionVisible(questionData));

  // Get only parent questions for navigation (child questions will render inline)
  // This includes:
  // - Questions without rules (always visible standalone questions)
  // - Questions with variant !== 'child' that are currently visible (conditional parent questions)
  const getParentQuestionsList = () => {
    return formQuestions.filter(([key, questionData]) => {
      // Exclude child questions - they render inline below their parent
      if (questionData.variant === 'child') {
        return false;
      }
      // For all other questions (parent or standalone), check if they're visible
      return isQuestionVisible(questionData);
    }).map(([key, questionData]) => ({ key, data: questionData }));
  };

  // Get visible child questions for a specific parent question
  const getVisibleChildQuestionsForParent = (parentKey: string) => {
    return visibleQuestions.filter(([key, questionData]) => 
      questionData.variant === 'child' &&
      questionData.rules && 
      questionData.rules.length > 0 && 
      questionData.rules.some(rule => rule.identifier === parentKey)
    );
  };

  const parentQuestionsList = getParentQuestionsList();
  const currentQuestion = parentQuestionsList[currentQuestionIndex];
  const totalQuestions = parentQuestionsList.length;

  // Check if current question and its visible children are answered (for required validation)
  const isCurrentQuestionAnswered = () => {
    if (!currentQuestion) return true;
    const { key, data: questionData } = currentQuestion;
    
    // Check if it's a form type question with sub-questions
    if (questionData.input_type?.toLowerCase() === 'form' && questionData.form_fields?.questions) {
      const subQuestions = questionData.form_fields.questions;
      for (const [subKey, subQuestionData] of Object.entries(subQuestions)) {
        if (subQuestionData.required) {
          const subValue = formData[subKey] ?? '';
          if (Array.isArray(subValue)) {
            if (subValue.length === 0) return false;
          } else if (subValue === '' || subValue === null || subValue === undefined) {
            return false;
          }
        }
      }
      return true;
    }
    
    // Check parent question
    if (questionData.required) {
      const currentValue = formData[key] ?? '';
      if (Array.isArray(currentValue)) {
        if (currentValue.length === 0) return false;
      } else if (currentValue === '' || currentValue === null || currentValue === undefined) {
        return false;
      }
    }
    
    // Check visible child questions
    const childQuestions = getVisibleChildQuestionsForParent(key);
    for (const [childKey, childData] of childQuestions) {
      if (childData.required) {
        const childValue = formData[childKey] ?? '';
        if (Array.isArray(childValue)) {
          if (childValue.length === 0) return false;
        } else if (childValue === '' || childValue === null || childValue === undefined) {
          return false;
        }
      }
    }
    
    return true;
  };

  // Handle input change
  const handleInputChange = (questionKey: string, value: any) => {
    if (viewMode) return;
    setFormData(prev => {
      const newFormData = { ...prev, [questionKey]: value };
      Object.entries(data).forEach(([childKey, childData]) => {
        if (childData.rules && childData.rules.some(rule => rule.identifier === questionKey)) {
          if (!isQuestionVisible(childData)) {
            newFormData[childKey] = undefined;
          }
        }
      });
      return newFormData;
    });
  };

  // Save current question answer to backend (PATCH request - fire and forget)
  const saveAnswerToBackend = (questionKey: string, questionData: KycFormData) => {
    if (viewMode || !caseId) return;
    
    // Build answers array including child questions
    const answersToSave: Array<{ question_identifier: string; answer: any }> = [];

    const isEmpty = (v: unknown) => v === undefined || v === null || v === "" ||
      (Array.isArray(v) && v.length === 0);

    // Handle form type questions with sub-questions
    if (questionData.input_type?.toLowerCase() === 'form' && questionData.form_fields?.questions) {
      const subQuestions = questionData.form_fields.questions;
      for (const [subKey, subQuestionData] of Object.entries(subQuestions)) {
        const subValue = formData[subKey];
        if (isEmpty(subValue)) {
          answersToSave.push({ question_identifier: subKey, answer: [] });
        } else {
          let subAnswer: any;
          const subInputType = subQuestionData.input_type?.toLowerCase();
          if (subInputType === 'radio') {
            const optionKey = getOptionKeyFromDisplayValue(subQuestionData.options, subValue);
            subAnswer = { value: optionKey ?? subValue };
          } else if (subInputType === 'checkbox' && Array.isArray(subValue)) {
            const keys = subValue
              .map(displayValue => getOptionKeyFromDisplayValue(subQuestionData.options, displayValue))
              .filter((key): key is string => key !== null);
            subAnswer = keys.map(key => ({ value: key }));
          } else if (Array.isArray(subValue)) {
            subAnswer = { value: subValue.join(', ') };
          } else {
            subAnswer = { value: String(subValue) };
          }
          answersToSave.push({
            question_identifier: subKey,
            answer: subAnswer
          });
        }
      }
    } else {
      const value = formData[questionKey];
      if (isEmpty(value)) {
        answersToSave.push({ question_identifier: questionKey, answer: [] });
      } else {
      // Build the answer for this question
      let answer: any;
      if (questionData.input_type?.toLowerCase() === 'radio') {
        const optionKey = getOptionKeyFromDisplayValue(questionData.options, value);
        answer = { value: optionKey ?? value };
      } else if (questionData.input_type?.toLowerCase() === 'checkbox' && Array.isArray(value)) {
        const keys = value
          .map(displayValue => getOptionKeyFromDisplayValue(questionData.options, displayValue))
          .filter((key): key is string => key !== null);
        answer = keys.map(key => ({ value: key }));
      } else if (Array.isArray(value)) {
        answer = { value: value.join(', ') };
      } else {
        answer = { value: String(value) };
      }
      
      // Add parent question answer
      answersToSave.push({
        question_identifier: questionKey,
        answer: answer
      });

      // Add visible child questions' answers
      const childQuestions = getVisibleChildQuestionsForParent(questionKey);
      for (const [childKey, childData] of childQuestions) {
        const childValue = formData[childKey];
        if (isEmpty(childValue)) {
          answersToSave.push({ question_identifier: childKey, answer: [] });
        } else {
          let childAnswer: any;
          if (childData.input_type?.toLowerCase() === 'radio') {
            const optionKey = getOptionKeyFromDisplayValue(childData.options, childValue);
            childAnswer = { value: optionKey ?? childValue };
          } else if (childData.input_type?.toLowerCase() === 'checkbox' && Array.isArray(childValue)) {
            const keys = childValue
              .map(displayValue => getOptionKeyFromDisplayValue(childData.options, displayValue))
              .filter((key): key is string => key !== null);
            childAnswer = keys.map(key => ({ value: key }));
          } else if (Array.isArray(childValue)) {
            childAnswer = { value: childValue.join(', ') };
          } else {
            childAnswer = { value: String(childValue) };
          }
          answersToSave.push({
            question_identifier: childKey,
            answer: childAnswer
          });
        }
      }
      }
    }

    if (answersToSave.length === 0) return;

    // Fire and forget PATCH request
    const patchRequest = {
      case_id: caseId,
      answers: answersToSave
    };

    api.patch('/v1/customer/kyc', patchRequest)
      .then((response: any) => {
        if (!response.success && response.message) {
          // Silently log errors, don't show toast for intermediate saves
          console.warn('KYC PATCH response:', response.message);
        }
      })
      .catch((err) => {
        // Silently log errors for intermediate saves
        console.warn('Failed to save KYC answer:', err);
      });
  };

  // Navigate to next question
  const handleNext = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      // Save current question answer before navigating (fire and forget)
      if (currentQuestion && !viewMode) {
        saveAnswerToBackend(currentQuestion.key, currentQuestion.data);
      }
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  // Navigate to previous question
  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  // Check if all required visible questions are answered
  const areAllRequiredQuestionsAnswered = () => {
    return visibleQuestions.every(([questionKey, questionData]) => {
      // Handle form type questions with sub-questions
      if (questionData.input_type?.toLowerCase() === 'form' && questionData.form_fields?.questions) {
        const subQuestions = questionData.form_fields.questions;
        for (const [subKey, subQuestionData] of Object.entries(subQuestions)) {
          if (subQuestionData.required) {
            const subValue = formData[subKey] ?? '';
            if (Array.isArray(subValue)) {
              if (subValue.length === 0) return false;
            } else if (subValue === '' || subValue === null || subValue === undefined) {
              return false;
            }
          }
        }
        return true;
      }
      
      if (!questionData.required) return true;
      const currentValue = formData[questionKey] ?? '';
      if (Array.isArray(currentValue)) {
        return currentValue.length > 0;
      }
      return currentValue !== '' && currentValue !== null && currentValue !== undefined;
    });
  };

  // Render input for a question
  const renderQuestionInput = (questionKey: string, questionData: KycFormData) => {
    const currentValue = formData[questionKey] ?? '';
    const inputType = questionData.input_type?.toLowerCase();
    const isPostcodeQuestion = questionKey === "9";

    if (viewMode) {
      switch (inputType) {
        case 'checkbox': {
          let checkedValues: string[] = [];
          if (Array.isArray(currentValue)) {
            checkedValues = currentValue;
          } else if (typeof currentValue === "string" && currentValue) {
            checkedValues = currentValue.split(",").map((v: string) => v.trim());
          }
          return (
            <div className="space-y-2">
              {checkedValues.length > 0
                ? checkedValues.map((ans, idx) => (
                    <div key={idx} className="p-3 bg-[#FFEA9E] border border-novaNeutral-400 rounded-lg text-[16px] sm:text-[18px] font-roman">
                      {ans}
                    </div>
                  ))
                : <span className="italic text-novaNeutral-400 text-[16px]">No answer</span>}
            </div>
          );
        }
        case 'form': {
          const formFields = questionData.form_fields?.questions;
          if (!formFields) {
            return <span className="italic text-novaNeutral-400 text-[16px]">No form fields</span>;
          }
          const sortedSubQuestions = Object.entries(formFields)
            .sort(([, a], [, b]) => a.question_order - b.question_order);
          return (
            <div className="space-y-3">
              {sortedSubQuestions.map(([subKey, subQuestionData]) => {
                const subValue = formData[subKey] ?? '';
                return (
                  <div key={subKey}>
                    <p className="text-[14px] text-novaNeutral-600 mb-1 font-roman">
                      {subQuestionData.question || subQuestionData.placeholder}
                    </p>
                    <div className="p-3 bg-[#FFEA9E] border border-novaNeutral-400 rounded-lg text-[16px] sm:text-[18px] font-roman">
                      {subValue
                        ? subValue
                        : <span className="italic text-novaNeutral-400">No answer</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        }
        case 'radio':
        case 'text':
        case 'textarea':
        default:
          return (
            <div className="p-3 bg-[#FFEA9E] border border-novaNeutral-400 rounded-lg text-[16px] sm:text-[18px] font-roman">
              {currentValue
                ? currentValue
                : <span className="italic text-novaNeutral-400">No answer</span>}
            </div>
          );
      }
    }

    switch (inputType) {
      case 'text':
        return (
          <div className="space-y-1">
            <p className="text-[16px] sm:text-[18px] text-novaNeutral-600 mb-3 font-roman">
              {questionData.placeholder || questionData.question || 'Enter your answer'}
              {questionData.required && (
                <span className="text-novaCaution-500 ml-1">*</span>
              )}
            </p>
            <input
              type="text"
              maxLength={questionData.max_length || 50}
              placeholder={questionData.placeholder || 'Enter your answer'}
              value={currentValue || ""}
              onChange={(e) => {
                const value = e.target.value;
                if (isPostcodeQuestion) {
                  const alphanumericWithSpace = /^[a-zA-Z0-9\- ]*$/;
                  if (value === "" || alphanumericWithSpace.test(value)) {
                    handleInputChange(questionKey, value.toUpperCase());
                  }
                  return;
                }
                if (value === "" || value.trim().length > 0) {
                  handleInputChange(questionKey, toTitleCase(value));
                } else {
                  handleInputChange(questionKey, "");
                }
              }}
              className="w-full px-3 sm:px-4 py-3 sm:py-3.5 text-[16px] sm:text-[18px] font-roman border border-novaNeutral-300 rounded-[8px] focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:border-transparent"
              disabled={viewMode}
            />
            {questionData.max_length && currentValue.length >= questionData.max_length && (
              <div className="text-xs text-novaCaution-500 mt-1">Limit reached</div>
            )}
          </div>
        );

      case 'radio':
        return (
          <div className="space-y-3">
            <p className="text-[16px] sm:text-[18px] text-novaNeutral-600 mb-3 font-roman">
              Select one option:
              {questionData.required && (
                <span className="text-novaCaution-500 ml-1">*</span>
              )}
            </p>
            <div className="space-y-2" data-kyc-options>
              {questionData.options?.map((option, optionIndex) => {
                const optionValue = typeof option === 'object' && option !== null
                  ? Object.values(option)[0] as string
                  : (option as any).value;
                const isSelected = currentValue === optionValue;

                return (
                  <div
                    key={`${questionKey}-${optionIndex}`}
                    role="radio"
                    aria-checked={isSelected}
                    tabIndex={viewMode ? -1 : 0}
                    className={`flex outline-none rounded-lg cursor-pointer transition-colors border border-novaNeutral-400 focus:outline-none ${
                      isSelected
                        ? "focus:ring-0 focus:ring-offset-0 focus-visible:ring-0 focus-visible:ring-offset-0 focus-visible:border-novaNeutral-400 bg-[#FFEA9E]"
                        : "focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:border-novaPrimary-500 bg-white hover:bg-novaNeutral-50"
                    }`}
                    onKeyDown={(e) => {
                      if (viewMode) return;
                      if (e.key === " ") {
                        e.preventDefault();
                        e.stopPropagation();
                        handleInputChange(questionKey, optionValue);
                      }
                      // Enter = next question (handled by card handleKeyDown)
                    }}
                    onClick={(e) => { (e.currentTarget as HTMLElement).focus(); }}
                  >
                    <label
                      className={`flex-1 flex items-center p-4 rounded-lg cursor-pointer transition-colors border-0 ${
                        isSelected ? "bg-[#FFEA9E]" : "bg-transparent hover:bg-transparent"
                      }`}
                    >
                      <input
                        type="radio"
                        name={`question-${questionKey}`}
                        value={optionValue}
                        checked={isSelected}
                        onChange={(e) => handleInputChange(questionKey, e.target.value)}
                        className="sr-only"
                        tabIndex={-1}
                        aria-hidden
                        disabled={viewMode}
                      />
                      <div className="flex-1">
                        <div className="text-[16px] sm:text-[18px] text-novaNeutral-900 font-roman" style={{ lineHeight: "1.4rem" }}>
                          {replacePartnerName(optionValue)}
                        </div>
                      </div>
                      {isSelected && (
                        <span className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-[#FF9A50] text-white" aria-hidden>
                          <i className="fas fa-check text-sm !text-white" />
                        </span>
                      )}
                    </label>
                  </div>
                );
              })}
            </div>
          </div>
        );

      case 'checkbox': {
        const exclusiveOption = questionData.options?.find(opt => {
          if (typeof opt === 'object' && opt !== null) {
            const key = Object.keys(opt)[0].toLowerCase();
            return key === 'no_i_havent_used_any_other_dispute_resolution_process';
          }
          return false;
        });
        const exclusiveOptionDisplayValue = exclusiveOption 
          ? (typeof exclusiveOption === 'object' ? Object.values(exclusiveOption)[0] as string : null)
          : null;
        
        const isExclusiveOptionSelected = exclusiveOptionDisplayValue && 
          Array.isArray(currentValue) && 
          currentValue.includes(exclusiveOptionDisplayValue);
        
        const isAnyOtherOptionSelected = exclusiveOptionDisplayValue && 
          Array.isArray(currentValue) && 
          currentValue.some(v => v !== exclusiveOptionDisplayValue);

        const toggleCheckbox = (optionValue: string, isChecked: boolean, isExclusiveOption: boolean, isDisabledByMutualExclusivity: boolean) => {
          if (viewMode || isDisabledByMutualExclusivity) return;
          let newValue: string[];
          if (!isChecked) {
            if (isExclusiveOption) {
              newValue = [optionValue];
            } else {
              const filtered = Array.isArray(currentValue)
                ? currentValue.filter(v => v !== exclusiveOptionDisplayValue)
                : [];
              newValue = [...filtered, optionValue];
            }
          } else {
            newValue = Array.isArray(currentValue)
              ? currentValue.filter(v => v !== optionValue)
              : [];
          }
          handleInputChange(questionKey, newValue);
        };

        return (
          <div className="space-y-2">
            <p className="text-[16px] sm:text-[18px] text-novaNeutral-600 mb-2 font-roman">
              Select all that apply.
              {questionData.required && (
                <span className="text-novaCaution-500 ml-1">*</span>
              )}
            </p>
            <div className="space-y-2" data-kyc-options>
              {questionData.options?.map((option, optionIndex) => {
                const optionValue = typeof option === 'object' && option !== null
                  ? Object.values(option)[0] as string
                  : (option as any).value;
                const isChecked = Array.isArray(currentValue)
                  ? currentValue.includes(optionValue)
                  : currentValue === optionValue;
                const isExclusiveOption = optionValue === exclusiveOptionDisplayValue;
                
                const isDisabledByMutualExclusivity = exclusiveOptionDisplayValue && (
                  (isExclusiveOptionSelected && !isExclusiveOption) ||
                  (isAnyOtherOptionSelected && isExclusiveOption)
                );
                const isDisabled = viewMode || !!isDisabledByMutualExclusivity;

                return (
                  <div key={`${questionKey}-${optionIndex}`}>
                    <div
                      role="checkbox"
                      aria-checked={isChecked}
                      aria-disabled={isDisabled}
                      tabIndex={isDisabled ? -1 : 0}
                      className={`group flex-1 flex outline-none rounded-lg cursor-pointer transition-colors focus:outline-none ${
                        isChecked
                          ? "focus-visible:ring-0 focus-visible:ring-offset-0"
                          : "focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
                        } ${isDisabledByMutualExclusivity ? 'cursor-not-allowed opacity-50' : ''}`}
                      onKeyDown={(e) => {
                        if (isDisabled) return;
                        if (e.key === " ") {
                          e.preventDefault();
                          e.stopPropagation();
                          toggleCheckbox(optionValue, isChecked, isExclusiveOption, !!isDisabledByMutualExclusivity);
                        }
                        // Enter = next question (handled by card handleKeyDown)
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
                        <div className="flex-1 text-[16px] sm:text-[18px] font-normal font-roman text-novaNeutral-900 leading-snug whitespace-normal">
                          {replacePartnerName(optionValue)}
                        </div>
                        <input
                          type="checkbox"
                          value={optionValue}
                          checked={isChecked}
                          onChange={(e) => {
                            if (isDisabledByMutualExclusivity) return;
                            
                            let newValue: string[];
                            
                            if (e.target.checked) {
                              if (isExclusiveOption) {
                                newValue = [optionValue];
                              } else {
                                const filtered = Array.isArray(currentValue)
                                  ? currentValue.filter(v => v !== exclusiveOptionDisplayValue)
                                  : [];
                                newValue = [...filtered, optionValue];
                              }
                            } else {
                              newValue = Array.isArray(currentValue)
                                ? currentValue.filter(v => v !== optionValue)
                                : [];
                            }
                            
                            handleInputChange(questionKey, newValue);
                          }}
                          className="sr-only"
                          tabIndex={-1}
                          aria-hidden
                          disabled={viewMode || !!isDisabledByMutualExclusivity}
                        />
                      </label>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      }

      case 'textarea': {
        const maxLength = questionData.max_length || 500;
        const currentLength = (currentValue || "").length;
        return (
          <div className="space-y-2">
            <p className="text-[16px] sm:text-[16px] text-novaNeutral-600 font-roman">
              {questionData.question || questionData.placeholder || 'Write your answer here.'}
              {questionData.required && (
                <span className="text-novaCaution-500 ml-1">*</span>
              )}
            </p>
            <textarea
              value={currentValue || ""}
              maxLength={maxLength}
              onChange={(e) => {
                const value = e.target.value;
                if (value === "" || value.trim().length > 0) {
                  handleInputChange(questionKey, value);
                } else {
                  handleInputChange(questionKey, "");
                }
              }}
              rows={4}
              className="w-full px-3 sm:px-4 py-3 sm:py-3.5 text-[16px] sm:text-[18px] font-roman border border-novaNeutral-300 rounded-[8px] focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:border-transparent resize-none"
              disabled={viewMode}
            />
            <div className="flex justify-end">
              <span className={`text-xs ${currentLength >= maxLength ? 'text-novaCaution-500' : 'text-novaNeutral-500 -mt-2'}`}>
                {maxLength - currentLength} characters remaining
              </span>
            </div>
          </div>
        );
      }

      case 'form': {
        // Render nested form fields by reusing renderQuestionInput
        const formFields = questionData.form_fields?.questions;
        if (!formFields) {
          return <div className="text-novaNeutral-500">No form fields available</div>;
        }

        // Sort sub-questions by question_order
        const sortedSubQuestions = Object.entries(formFields)
          .sort(([, a], [, b]) => a.question_order - b.question_order);

        return (
          <div className="space-y-4">
            {sortedSubQuestions.map(([subKey, subQuestionData]) => (
              <div key={subKey}>
                {renderQuestionInput(subKey, subQuestionData as unknown as KycFormData)}
              </div>
            ))}
          </div>
        );
      }

      default:
        return (
          <div className="space-y-2">
            <input
              type="text"
              placeholder={questionData.placeholder || 'Enter your answer'}
              value={currentValue || ""}
              onChange={(e) => {
                const value = e.target.value;
                if (value === "" || value.trim().length > 0) {
                  handleInputChange(questionKey, toTitleCase(value));
                } else {
                  handleInputChange(questionKey, "");
                }
              }}
              className="w-full px-3 sm:px-4 py-3 sm:py-3.5 text-[16px] sm:text-[18px] font-roman border border-novaNeutral-300 rounded-[8px] focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:border-transparent"
              disabled={viewMode}
            />
          </div>
        );
    }
  };

  const handleSubmit = async () => {
    if (viewMode) return;
    if (!caseId) return;
    setIsSubmitting(true);
    
    try {
      const answers = visibleQuestions.map(([questionKey, questionData]) => {
        const value = formData[questionKey];
        if (value === undefined || value === null || value === "") return null;
        if (questionData.input_type?.toLowerCase() === 'radio') {
          const optionKey = getOptionKeyFromDisplayValue(questionData.options, value);
          return {
            question_identifier: questionKey,
            answer: {
              value: optionKey ?? value
            }
          };
        } else if (questionData.input_type?.toLowerCase() === 'checkbox' && Array.isArray(value)) {
          const keys = value
            .map(displayValue => getOptionKeyFromDisplayValue(questionData.options, displayValue))
            .filter((key): key is string => key !== null);
          return {
            question_identifier: questionKey,
            answer: keys.map(key => ({ value: key }))
          };
        } else if (Array.isArray(value)) {
          return {
            question_identifier: questionKey,
            answer: {
              value: value.join(', ')
            }
          };
        } else {
          return {
            question_identifier: questionKey,
            answer: {
              value: String(value)
            }
          };
        }
      }).filter(Boolean);

      const requestBody = {
        case_id: caseId,
        answers: answers
      };
      const response = await api.post('/v1/customer/kyc', requestBody) as ApiResponse;

      const showToastsWithDelay = async (
        messages: MessageItem[],
        isSuccess: boolean
      ) => {
        const delay = 400;
        for (let i = 0; i < messages.length; i++) {
          const messageItem = messages[i];
          await new Promise((resolve) =>
            setTimeout(resolve, i === 0 ? 0 : delay)
          );
          if (isSuccess) {
            if (messageItem.success) {
              const toast = createSuccessToast("Success", messageItem.message);
              toastManager.addToast(toast);
            } else {
              const toast = createErrorToast("Error", messageItem.message);
              toastManager.addToast(toast);
            }
          } else {
            const toast = createErrorToast("Error", messageItem.message);
            toastManager.addToast(toast);
          }
        }
      };

      if (response.success) {
        if (onSubmit) {
          onSubmit();
        }
        // Refresh user from API so profile icon initial updates when name was changed in KYC
        try {
          const meResponse = await api.get<{ data?: { first_name?: string; last_name?: string; id?: string; [key: string]: unknown } }>("/v1/user/me");
          const userFromApi = meResponse.data;
          const stored = localStorage.getItem("user");
          if (stored && userFromApi) {
            const current = JSON.parse(stored);
            const updated = {
              ...current,
              ...userFromApi,
              user_id: (userFromApi as { id?: string })?.id ?? current.user_id,
            };
            localStorage.setItem("user", JSON.stringify(updated));
            refreshUserFromStorage();
          }
        } catch {
          // Non-blocking: profile initial will update on next login
        }
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          const toast = createSuccessToast(
            "Success",
            response.message || "Alignment Check form submitted successfully"
          );
          toastManager.addToast(toast);
        }
      } else {
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          const toast = createErrorToast(
            "Error",
            response.message || "Failed to submit Alignment Check form"
          );
          toastManager.addToast(toast);
        }
      }
    } catch (error) {
      const toast = createErrorToast("Error", "Failed to submit KYC form. Please try again.");
      toastManager.addToast(toast);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get partner name for question text replacement
  // Question 2 may be form type with sub-keys 2.1 (first name), 2.3 (surname)
  const getPartnerName = () => {
    const partnerFirstName = formData["2.1"];
    const legacyFullName = formData["2"] ||
      Object.entries(data).find(([k]) => k === "2")?.[1]?.answer?.[0]?.value;
    const fullName = typeof partnerFirstName === "string" && partnerFirstName
      ? partnerFirstName
      : legacyFullName;
    if (!fullName || (typeof fullName !== "string" && typeof fullName !== "number")) {
      return "Partner";
    }
    const nameStr = String(fullName).trim();
    const firstName = nameStr.split(/\s+/)[0] || nameStr;
    return firstName.charAt(0).toUpperCase() + firstName.slice(1);
  };

  // Replace {partner_name} placeholder in text
  const replacePartnerName = (text: string | undefined): string => {
    if (!text) return "";
    return text.replace(/{partner_name}/g, getPartnerName());
  };

  // Get button text
  const getButtonText = () => {
    if (currentQuestionIndex === totalQuestions - 1) {
      return viewMode ? "Close" : "Submit";
    }
    if (!currentQuestion?.data.required) {
      const currentValue = formData[currentQuestion?.key] ?? '';
      const hasAnswer = Array.isArray(currentValue) ? currentValue.length > 0 : currentValue !== '';
      return hasAnswer ? "Next" : "Skip";
    }
    return "Next";
  };

  // Handle button click
  const handleButtonClick = () => {
    if (currentQuestionIndex === totalQuestions - 1) {
      if (viewMode) {
        onClose();
      } else {
        handleSubmit();
      }
    } else {
      handleNext();
    }
  };

  // Can proceed to next
  const canProceed = () => {
    if (!currentQuestion) return false;
    if (viewMode) return true;
    if (!currentQuestion.data.required) return true;
    return isCurrentQuestionAnswered();
  };

  // Handle Enter key to go to next question (but not for textareas)
  const handleKeyDown = (e: React.KeyboardEvent) => {
    const target = e.target as HTMLElement;
    // Don't handle Enter in textarea (allow normal behavior) or on buttons (let Back/Next handle their own click)
    if (e.key === 'Enter' && target.tagName !== 'TEXTAREA' && target.tagName !== 'BUTTON') {
      e.preventDefault();
      if (canProceed() && !isSubmitting) {
        handleButtonClick();
      }
    }
  };

  // Render child question input inline
  const renderChildQuestionInline = (childKey: string, childData: KycFormData) => {
    const childQuestionText = replacePartnerName(childData.question);
    
    return (
      <div key={childKey} className="mt-2 pt-2">
        {/* Child question label/description if exists */}
        {childQuestionText && (
          <div className="font-roman text-novaNeutral-600 text-[14px] sm:text-[16px] leading-relaxed text-left mb-3">
            {childQuestionText}
            {!viewMode && childData.required && (
              <span className="text-md ml-1 text-novaCaution-500">*</span>
            )}
          </div>
        )}
        {/* Child input */}
        {renderQuestionInput(childKey, childData)}
      </div>
    );
  };

  // Render current question card
  const renderQuestionCard = () => {
    if (!currentQuestion) return null;

    const { key, data: questionData } = currentQuestion;
    const questionText = replacePartnerName(questionData.question) || questionData.title;
    
    // Get visible child questions for this parent
    const visibleChildQuestions = getVisibleChildQuestionsForParent(key);

    return (
      <div className="flex justify-center w-full overflow-y-auto">
        <div className="w-full max-w-[904px] min-h-[400px]">
          <div
            ref={cardRef}
            className="relative bg-transparent sm:border-[18px] border-[10px] rounded-[28px]"
            style={{ borderColor: 'rgba(252, 210, 176, 0.8)' }}
            onKeyDown={handleKeyDown}
          >
            <div className="bg-white rounded-[18px] sm:rounded-[10px] px-6 py-8 sm:px-16 sm:py-12 flex flex-col">
              {/* Progress indicator */}
              <div className="flex items-center justify-between mb-6">
                <p className="text-[20px] sm:text-[24px] leading-[1.4] text-novaBlack font-nineties tracking-wide text-left">
                  {currentQuestionIndex + 1}/{totalQuestions} Steps
                </p>
                {/* Question badge */}
                <div className="flex items-center gap-3 mb-4">
                  {/* <span className="text-xs font-semibold text-novaDarkOrange bg-novaActive rounded-full px-3 py-1">
                    {isChild ? "Follow-up" : `Question ${currentQuestionIndex + 1}`}
                  </span> */}
                  <button
                    onClick={onClose}
                    className="text-novaBlack hover:text-novaNeutral-300 transition-colors p-2 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 rounded"
                    aria-label="Close"
                  >
                    <i className="fas fa-times text-xl"></i>
                  </button>
                </div>
              </div>

              {/* Question title */}
              <h1 id="kyc-modal-title" className="text-[28px] sm:text-[36px] leading-[1.1] font-normal font-nineties text-left mb-4 text-novaBlack">
                {replacePartnerName(questionData.title) || ""}
              </h1>

              {/* Question description */}
              {/* {questionText && (
                <div className="font-roman text-novaNeutral-600 text-[16px] sm:text-[18px] leading-relaxed text-left mb-6">
                  {questionText}
                  {!viewMode && currentQuestion.data.required && (
                  <span className="text-md ml-1 text-novaCaution-500">*</span>
                )}
                </div>
              )} */}

              {/* Input */}
              <div className="mt-2 space-y-6">
                {renderQuestionInput(key, questionData)}
                
                {/* Render visible child questions inline */}
                {visibleChildQuestions.map(([childKey, childData]) => 
                  renderChildQuestionInline(childKey, childData)
                )}
              </div>

              {/* Navigation buttons */}
              <div className="mt-8 flex items-center gap-4">
                {currentQuestionIndex > 0 && (
                  <FormButton
                    type="button"
                    variant="custom"
                    onClick={handlePrevious}
                    className="px-5 py-2.5 h-[44px] text-[18px] bg-transparent sm:text-[20px] font-normal rounded-full border border-novaBlack text-novaBlack sm:hover:bg-novaBlack sm:hover:text-white transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
                  >
                    {/* <i className="fas fa-arrow-left mr-2"></i> */}
                    Back
                  </FormButton>
                )}
                
                <FormButton
                  type="button"
                  variant="primary"
                  onClick={handleButtonClick}
                  disabled={!canProceed() || isSubmitting}
                  className={`px-5 py-2.5 bg-novaBlack text-white text-[18px] sm:text-[20px] font-normal rounded-full transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white ${
                    (!canProceed() || isSubmitting)
                      ? "opacity-50 cursor-not-allowed"
                      : ""
                  }`}
                >
                  {isSubmitting ? (
                    <span className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Submitting...
                    </span>
                  ) : (
                    <div className="flex items-center gap-2">
                      {getButtonText()}
                      {currentQuestionIndex < totalQuestions - 1 && (
                        <img src={ArrowIcon} alt="arrow" className="w-5 h-4" />
                      )}
                    </div>
                  )}
                </FormButton>
              </div>

              {/* Progress bar */}
              <div className="mt-8">
                <div className="w-full bg-novaNeutral-200 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-novaOrange to-novaRed h-2 rounded-full transition-all duration-300"
                    style={{ width: `${((currentQuestionIndex + 1) / totalQuestions) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };


  return createPortal(
    <div
      ref={scrollContainerRef}
      className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4 overflow-y-auto"
      style={{
      backgroundImage: `url(${accountSetupBackground})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
    }}>
      <div ref={modalContentRef} className="w-full max-w-[960px] my-auto" role="dialog" aria-modal="true" aria-labelledby="kyc-modal-title">
        {/* Header */}
        {/* <div className="flex items-center justify-between mb-4 px-2">
          <div className="flex items-center gap-3">
            <i className="fas fa-clipboard-list text-novaDarkOrange text-xl"></i>
            <h2 className="text-lg sm:text-xl font-semibold text-white">
              {viewMode ? "KYC Form Details" : "Know Your Case Form"}
            </h2>
          </div>
          
        </div> */}

        {/* Question Card */}
        {renderQuestionCard()}
      </div>
    </div>,
    document.body
  );
};

export default KycFormNew;
