import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Button } from "../ui/button";
import { api } from "../../lib/api";
import { createSuccessToast, createErrorToast, toastManager } from "../../utils/toasts";

interface KycQuestion {
  value: string;
  key?: string;
  [key: string]: any;
}

interface KycRule {
  identifier: string;
  operator: string;
  value: string | string[];
}

interface KycAnswer {
  value: string;
}

interface KycFormFieldQuestion {
  question_type: string;
  variant: string;
  title: string;
  description: string;
  placeholder: string;
  question: string;
  options: KycQuestion[];
  required: boolean;
  input_type: string;
  min_length?: number | null;
  max_length?: number | null;
  rules: KycRule[];
  question_order: number;
  answer_type: string;
  answer: KycAnswer[];
}

interface KycFormFields {
  questions: Record<string, KycFormFieldQuestion>;
}

interface KycFormData {
  question_type: string;
  variant: string;
  title: string;
  description: string;
  placeholder: string;
  question: string;
  options: KycQuestion[];
  required: boolean;
  input_type: string;
  rules: KycRule[];
  question_order: number;
  answer_type: string;
  answer: KycAnswer[];
  question_status: string;
  version: string;
  default?: string;
  form_fields?: KycFormFields;
}

interface KycFormProps {
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

// Helper: get all keys from options
function getAllOptionKeys(options: KycQuestion[]): string[] {
  return options.map(opt => typeof opt === "object" && opt !== null ? Object.keys(opt)[0] : "");
}

// Helper: get all display values from options
function getAllOptionDisplayValues(options: KycQuestion[]): string[] {
  return options.map(opt => typeof opt === "object" && opt !== null ? Object.values(opt)[0] as string : "");
}

// Helper: check if a rule is satisfied given the parent answer
function isRuleSatisfied(rule: KycRule, parentValue: any, parentOptions: KycQuestion[]): boolean {
  // parentValue is display value(s), rule.value is key(s)
  if (parentValue === undefined || parentValue === null || parentValue === "") return false;
  if (Array.isArray(parentValue) && parentValue.length === 0) return false;

  // Convert parentValue (display) to key(s)
  let parentKeys: string[] = [];
  if (Array.isArray(parentValue)) {
    parentKeys = parentValue.map(val => {
      const key = getOptionKeyFromDisplayValue(parentOptions, val);
      // If no key found, the value might already be a key
      return key || val;
    }).filter(Boolean) as string[];
  } else {
    const key = getOptionKeyFromDisplayValue(parentOptions, parentValue);
    // If no key found, the value might already be a key
    parentKeys = [key || parentValue];
  }

  if (rule.operator === "in") {
    const ruleValues = Array.isArray(rule.value) ? rule.value : [rule.value];
    return parentKeys.some(key => ruleValues.includes(key));
  }
  // Add more operators as needed
  return false;
}

const KycForm: React.FC<KycFormProps> = ({ data, isOpen, onClose, caseId, viewMode = false, onSubmit }) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [allAnswersInitiallyFilled, setAllAnswersInitiallyFilled] = useState(false);

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
              initialFormData[subKey] = typeof answerValue === 'string' ? answerValue : String(answerValue ?? '');
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
          // Use display value if found, otherwise use the raw answer value
          initialFormData[questionKey] = displayValue || answerValue;
        } else {
          const answerValue = questionData.answer[0].value;
          initialFormData[questionKey] = answerValue;
        }
      } else if (questionData.default) {
        // If no answer exists but a default is specified, use the default value
        const defaultKey = questionData.default;
        const defaultDisplayValue = getOptionDisplayValueFromKey(questionData.options, defaultKey);
        if (defaultDisplayValue) {
          // For checkbox, wrap in array; for radio/other, use single value
          if (questionData.input_type?.toLowerCase() === 'checkbox') {
            initialFormData[questionKey] = [defaultDisplayValue];
          } else {
            initialFormData[questionKey] = defaultDisplayValue;
          }
        }
      }
    });
    setFormData(initialFormData);

    // After populating, check if all questions already have answers
    // Check only for visible questions, after all answers are loaded in initialFormData
    // We'll use a separate function to check all visible questions have answers (for required questions)
    // We'll run this on first load (could store a flag if needed)
    setTimeout(() => { // delay to ensure formData is set
      const formQuestions = Object.entries(data)
        .sort(([, a], [, b]) => a.question_order - b.question_order);
      const isVisible = (questionData: KycFormData): boolean => {
        if (!questionData.rules || questionData.rules.length === 0) return true;
        // Rules may depend on answers, which are set in initialFormData now
        return questionData.rules.every(rule => {
          const parentValue = initialFormData[rule.identifier];
          const parentOptions = data[rule.identifier]?.options || [];
          return isRuleSatisfied(rule, parentValue, parentOptions);
        });
      };
      const visibleQuestions = formQuestions.filter(([key, questionData]) => isVisible(questionData));
      const allFilled = visibleQuestions.every(([questionKey, questionData]) => {
        if (questionData.input_type?.toLowerCase() === 'form' && questionData.form_fields?.questions) {
          const subQuestions = questionData.form_fields.questions;
          for (const [subKey, subQuestionData] of Object.entries(subQuestions)) {
            if (subQuestionData.required) {
              const subValue = initialFormData[subKey] ?? '';
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
        const currentValue = initialFormData[questionKey] ?? '';
        if (Array.isArray(currentValue)) {
          return currentValue.length > 0;
        }
        return currentValue !== '' && currentValue !== null && currentValue !== undefined;
      });
      setAllAnswersInitiallyFilled(allFilled && visibleQuestions.length > 0);
    }, 0);
  }, [data]);

  // Helper: get parent value for a rule
  const getParentValue = useCallback((identifier: string) => formData[identifier], [formData]);

  // Helper: get parent options for a rule
  const getParentOptions = useCallback((identifier: string) => data[identifier]?.options || [], [data]);

  // Helper: check if a question should be shown based on its rules
  const isQuestionVisible = useCallback((questionData: KycFormData): boolean => {
    if (!questionData.rules || questionData.rules.length === 0) return true;
    // All rules must be satisfied (AND logic)
    return questionData.rules.every(rule => {
      const parentValue = getParentValue(rule.identifier);
      const parentOptions = getParentOptions(rule.identifier);
      return isRuleSatisfied(rule, parentValue, parentOptions);
    });
  }, [getParentValue, getParentOptions]);

  // When a parent answer changes, clear answers for any child questions that depend on it and are now hidden
  useEffect(() => {
    // For each question with rules, if not visible, clear its answer
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
    // eslint-disable-next-line
  }, [formData, data, isQuestionVisible]);

  if (!isOpen) return null;

  // Sort questions by question_order
  const formQuestions = Object.entries(data)
    .sort(([, a], [, b]) => a.question_order - b.question_order);

  // Only show questions that are visible (rules satisfied)
  const visibleQuestions = formQuestions.filter(([key, questionData]) => isQuestionVisible(questionData));

  // Separate parent and child questions
  const parentQuestions = visibleQuestions.filter(([key, questionData]) => 
    !questionData.rules || questionData.rules.length === 0
  );

  // Helper to get child questions for a parent
  const getChildQuestions = (parentKey: string) => {
    return visibleQuestions.filter(([key, questionData]) => 
      questionData.rules && 
      questionData.rules.length > 0 && 
      questionData.rules.some(rule => rule.identifier === parentKey)
    );
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

  // Handle input change, and clear child answers if parent changes
  const handleInputChange = (questionKey: string, value: any) => {
    if (viewMode) return;
    setFormData(prev => {
      const newFormData = { ...prev, [questionKey]: value };
      // For all questions that depend on this question, if their rules are no longer satisfied, clear their answers
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

  // Get partner name for question text replacement
  const getPartnerName = () => {
    // Question 2 may be form type with sub-keys 2.1 (first name), 2.3 (surname)
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

  // Render input for a question
  const renderQuestionInput = (questionKey: string, questionData: KycFormData) => {
    const currentValue = formData[questionKey] ?? '';
    const inputType = questionData.input_type?.toLowerCase();

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
            <div className="bg-novaNeutral-50 rounded-lg text-novaTextGray text-sm border border-novaNeutral-200 sm:text-sm sm:px-4 sm:py-2 px-3 py-1 break-words">
              {checkedValues.length > 0
                ? checkedValues.map((ans, idx) => (
                    <div key={idx}>{replacePartnerName(ans)}</div>
                  ))
                : <span className="italic text-gray-400">No answer</span>}
            </div>
          );
        }
        case 'form': {
          const formFields = questionData.form_fields?.questions;
          if (!formFields) {
            return <span className="italic text-gray-400">No form fields</span>;
          }
          const sortedSubQuestions = Object.entries(formFields)
            .sort(([, a], [, b]) => a.question_order - b.question_order);
          return (
            <div className="space-y-3">
              {sortedSubQuestions.map(([subKey, subQuestionData]) => {
                const subValue = formData[subKey] ?? '';
                return (
                  <div key={subKey}>
                    <p className="text-xs font-medium text-novaTextGray mb-1">
                      {replacePartnerName(subQuestionData.question || subQuestionData.placeholder)}
                    </p>
                    <div className="bg-novaNeutral-50 rounded-lg text-novaTextGray text-sm border border-novaNeutral-200 sm:text-sm sm:px-4 sm:py-2 px-3 py-1 break-words">
                      {subValue
                        ? replacePartnerName(String(subValue))
                        : <span className="italic text-gray-400">No answer</span>}
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
            <div className="bg-novaNeutral-50 rounded-lg text-novaTextGray text-sm border border-novaNeutral-200 sm:text-sm sm:px-4 sm:py-2 px-3 py-1 break-words">
              {currentValue
                ? replacePartnerName(currentValue)
                : <span className="italic text-gray-400">No answer</span>}
            </div>
          );
      }
    }

    // Check if this is a postcode question by identifier (for alpha-numeric with space validation)
    const isPostcodeQuestion = questionKey === "9";
    
    switch (inputType) {
      case 'text':
        return (
          <input
            type="text"
            placeholder={questionData.placeholder || 'Enter your answer'}
            value={currentValue || ""}
            onChange={(e) => {
              const value = e.target.value;
              
              // For postcode questions, only allow alpha-numeric characters and spaces
              if (isPostcodeQuestion) {
                const alphanumericWithSpace = /^[a-zA-Z0-9 ]*$/;
                if (value === "" || alphanumericWithSpace.test(value)) {
                  handleInputChange(questionKey, value.toUpperCase());
                }
                return;
              }
              
              if (value === "" || value.trim().length > 0) {
                handleInputChange(questionKey, value);
              } else {
                handleInputChange(questionKey, "");
              }
            }}
            className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-novaDarkAmber focus:border-transparent border-gray-300"
            disabled={viewMode}
          />
        );
      case 'radio':
        return (
          <div className="space-y-2">
            {questionData.options?.map((option, optionIndex) => {
              const optionValue = typeof option === 'object' && option !== null
                ? Object.values(option)[0] as string
                : (option as any).value;
              const isSelected = currentValue === optionValue;
              return (
                <label key={optionIndex} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name={`question-${questionKey}`}
                    value={(optionValue)}
                    checked={isSelected}
                    onChange={(e) => handleInputChange(questionKey, e.target.value)}
                    className="text-novaDarkOrange focus:ring-novaDarkAmber"
                    disabled={viewMode}
                  />
                  <span className="flex-1 text-sm text-gray-700">{replacePartnerName(optionValue)}</span>
                  {isSelected && (
                    <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-[#FF9A50] text-white" aria-hidden>
                      <i className="fas fa-check text-sm !text-white" />
                    </span>
                  )}
                </label>
              );
            })}
          </div>
        );
      case 'checkbox':
        // Find mutually exclusive options (e.g., "No, I haven't...")
        // These options cannot be selected together with other options
        // Note: "Other" is NOT exclusive - it can be selected with other options
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
        
        // Check if the exclusive option is currently selected
        const isExclusiveOptionSelected = exclusiveOptionDisplayValue && 
          Array.isArray(currentValue) && 
          currentValue.includes(exclusiveOptionDisplayValue);
        
        // Check if any other option is selected (any option other than the exclusive one)
        const isAnyOtherOptionSelected = exclusiveOptionDisplayValue && 
          Array.isArray(currentValue) && 
          currentValue.some(v => v !== exclusiveOptionDisplayValue);

        return (
          <div className="space-y-2">
            {questionData.options?.map((option, optionIndex) => {
              const optionValue = typeof option === 'object' && option !== null
                ? Object.values(option)[0] as string
                : (option as any).value;
              const isChecked = Array.isArray(currentValue)
                ? currentValue.includes(optionValue)
                : currentValue === optionValue;
              const isExclusiveOption = optionValue === exclusiveOptionDisplayValue;
              
              // Disable other options when exclusive option is selected, and disable exclusive option when others are selected
              const isDisabledByMutualExclusivity = exclusiveOptionDisplayValue && (
                (isExclusiveOptionSelected && !isExclusiveOption) ||
                (isAnyOtherOptionSelected && isExclusiveOption)
              );
              
              return (
                <label 
                  key={optionIndex} 
                  className={`flex items-start gap-2 relative group ${
                    isDisabledByMutualExclusivity ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
                  }`}
                  title={isDisabledByMutualExclusivity 
                    ? (isExclusiveOption 
                        ? "Deselect other options to enable this" 
                        : "Deselect the selected option to enable this")
                    : undefined
                  }
                >
                  <input
                    type="checkbox"
                    value={optionValue}
                    checked={isChecked}
                    onChange={(e) => {
                      if (isDisabledByMutualExclusivity) return;
                      
                      let newValue: string[];
                      
                      if (e.target.checked) {
                        if (isExclusiveOption) {
                          // If selecting exclusive option (e.g., "No, I haven't..."), clear all others
                          newValue = [optionValue];
                        } else {
                          // If selecting any other option, remove exclusive option if present
                          const filtered = Array.isArray(currentValue)
                            ? currentValue.filter(v => v !== exclusiveOptionDisplayValue)
                            : [];
                          newValue = [...filtered, optionValue];
                        }
                      } else {
                        // Unchecking - just remove the option
                        newValue = Array.isArray(currentValue)
                          ? currentValue.filter(v => v !== optionValue)
                          : [];
                      }
                      
                      handleInputChange(questionKey, newValue);
                    }}
                    className={`flex-shrink-0 mt-0 focus:ring-novaDarkAmber ${
                      isDisabledByMutualExclusivity 
                        ? 'text-gray-300 cursor-not-allowed' 
                        : 'text-novaDarkOrange'
                    }`}
                    disabled={viewMode || !!isDisabledByMutualExclusivity}
                  />
                  <span className={`text-sm leading-tight ${
                    isDisabledByMutualExclusivity ? 'text-gray-400' : 'text-gray-700'
                  }`}>{replacePartnerName(optionValue)}</span>
                </label>
              );
            })}
          </div>
        );
      case 'textarea':
        return (
          <textarea
            placeholder={questionData.placeholder || 'Enter your answer'}
            value={currentValue || ""}
            onChange={(e) => {
              const value = e.target.value;
              if (value === "" || value.trim().length > 0) {
                handleInputChange(questionKey, value);
              } else {
                handleInputChange(questionKey, "");
              }
            }}
            rows={4}
            className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-novaDarkAmber focus:border-transparent border-gray-300"
            disabled={viewMode}
          />
        );
      default:
        return (
          <input
            type="text"
            placeholder={questionData.placeholder || 'Enter your answer'}
            value={currentValue || ""}
            onChange={(e) => {
              const value = e.target.value;
              if (value === "" || value.trim().length > 0) {
                handleInputChange(questionKey, value);
              } else {
                handleInputChange(questionKey, "");
              }
            }}
            className="w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-novaDarkAmber focus:border-transparent border-gray-300"
            disabled={viewMode}
          />
        );
    }
  };

  const handleSubmit = async () => {
    if (viewMode) return;
    if (!caseId) return;
    setIsSubmitting(true);
    
    try {
      // Only submit answers for visible questions
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
        const delay = 400; // ms
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
         // Only close the popup and call onSubmit after successful submission
         if (onSubmit) {
          onSubmit();
        }
        // Handle array of messages
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          // Fallback for single message (backward compatibility)
          const toast = createSuccessToast(
            "Success",
            response.message || "Alignment check form submitted successfully"
          );
          toastManager.addToast(toast);
        }
        
      } else {
        // Handle error case - don't close the popup
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          const toast = createErrorToast(
            "Error",
            response.message || "Failed to submit KYC form"
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div
        role="dialog"
        aria-describedby="kyc-form-description"
        aria-labelledby="kyc-form-title"
        data-state="open"
        className="
          w-full max-w-2xl max-h-[80vh]
          flex flex-col gap-4
          border-novaNeutral-200 border bg-white p-3 sm:p-6 shadow-lg
          duration-200
          rounded-lg
          data-[state=open]:animate-in
          data-[state=closed]:animate-out
          data-[state=closed]:fade-out-0
          data-[state=open]:fade-in-0
          data-[state=closed]:zoom-out-95
          data-[state=open]:zoom-in-95
          data-[state=closed]:slide-out-to-left-1/2
          data-[state=closed]:slide-out-to-top-[48%]
          data-[state=open]:slide-in-from-left-1/2
          data-[state=open]:slide-in-from-top-[48%]
        "
        tabIndex={-1}
        style={{ pointerEvents: 'auto' }}
      >
        {/* Header */}
        <div className="flex flex-col space-y-1.5 text-center sm:text-left flex-shrink-0">
          <div className="flex items-center justify-between">
            <h2 id="kyc-form-title" className="text-lg font-semibold leading-none tracking-tight flex items-center gap-2">
              <i className="fas fa-clipboard-list text-novaDarkOrange tracking-wide"></i>
              {viewMode ? "Alignment Check Details" : "Alignment Check Form"}
            </h2>
            <Button
              type="button"
              onClick={onClose}
              variant="outline"
              className="border-transparent"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-x h-4 w-4">
                <path d="M18 6 6 18"></path>
                <path d="m6 6 12 12"></path>
              </svg>
              <span className="sr-only">Close</span>
            </Button>
          </div>
          <div className="hidden sm:block">
            {viewMode ?
              <p>Review the responses for this case.This section contains important information about the case.</p> :
              <p id="kyc-form-description" className="text-sm text-muted-foreground">
                Please answer the following questions to help our legal team better understand your situation. This information will be used to match you with the most suitable Experts.
              </p>
            }
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-1">
          <div className="space-y-2">
            {parentQuestions.map(([key, questionData], index) => {
              const childQuestions = getChildQuestions(key);
              return (
                <div key={key} className="bg-white rounded-xl shadow border border-novaNeutral-100 p-3 sm:p-5 flex flex-col gap-2 transition-all">
                  {/* Parent Question */}
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-xs font-semibold text-novaDarkOrange bg-novaActive rounded-full px-3 py-1 sm:text-xs text-[11px] sm:px-3 sm:py-1">
                      Question {index + 1}
                    </span>
                    {!viewMode && questionData.required && <span className="text-xs text-novaCaution-500">*</span>}
                  </div>
                  <div className="font-medium text-novaTextGray mb-2 italic text-sm break-words">
                    {replacePartnerName(questionData.title || questionData.question || "")}
                  </div>
                  <div>
                    {renderQuestionInput(key, questionData)}
                  </div>

                  {/* Child Questions */}
                  {childQuestions.length > 0 && (
                    <div className="mt-4 space-y-3">
                      {childQuestions.map(([childKey, childData]) => {
                        const childValue = formData[childKey];
                        const hasAnswer = childValue !== undefined && 
                                         childValue !== null && 
                                         childValue !== "" && 
                                         !(Array.isArray(childValue) && childValue.length === 0);
                        
                        // In viewMode, skip child questions without answers
                        if (viewMode && !hasAnswer) {
                          return null;
                        }

                        return (
                          <div key={childKey}>
                            {childData.question && childData.question.trim() !== "" && (
                              <>
                                <div className="flex items-center gap-3 mb-2">
                                  {!viewMode && childData.required && <span className="text-xs text-novaCaution-500">*</span>}
                                </div>
                                <div className="text-sm font-medium text-novaTextGray mb-2 break-words">
                                  {replacePartnerName(childData.question)}
                                </div>
                              </>
                            )}
                            {(!childData.question || childData.question.trim() === "") && !viewMode && childData.required && (
                              <div className="flex items-center gap-3 mb-2">
                                <span className="text-xs text-novaCaution-500">*</span>
                              </div>
                            )}
                            <div>
                              {renderQuestionInput(childKey, childData)}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        {/* Show special complete message if all visible/required questions already filled initially AND not in viewMode */}
        {allAnswersInitiallyFilled && !viewMode ? (
          <div className="flex flex-col items-center justify-center flex-shrink-0 pt-3 sm:pt-4 border-t border-gray-200 gap-2">
            <div className="flex flex-row items-center gap-2 text-green-700 bg-green-50 px-4 py-2 rounded-lg text-sm font-semibold">
              <i className="fas fa-check-circle"></i>
              Submitted
            </div>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row sm:justify-end sm:space-x-2 gap-2 sm:gap-3 flex-shrink-0 pt-3 sm:pt-4 border-t border-gray-200">
            {!viewMode && (
              <div className="flex flex-col sm:flex-row sm:items-center sm:mr-auto w-full sm:w-auto">
                <div className="flex items-center text-xs text-gray-400 mb-2 sm:mb-0">
                  <span className="text-novaCaution-500 mr-2">*</span>
                  <span>Required question</span>
                </div>
              </div>
            )}
            <div className="flex flex-row w-full sm:w-auto gap-2">
              <Button
                variant="outline"
                onClick={onClose}
                className="flex-1 sm:flex-none h-9 px-3 py-1.5 sm:h-10 sm:px-4 sm:py-2 inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-novaBlack hover:text-white"
              >
                {viewMode ? "Close" : "Cancel"}
              </Button>
              {!viewMode && (
                <Button
                  onClick={handleSubmit}
                  disabled={isSubmitting || !areAllRequiredQuestionsAnswered()}
                  className="flex-1 sm:flex-none h-9 px-3 py-1.5 sm:h-10 sm:px-4 sm:py-2 inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-full text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-novaDarkOrange hover:bg-novaDarkOrange/90 text-white disabled:bg-gray-400 disabled:hover:bg-gray-400"
                >
                  {isSubmitting ? (
                    <>
                      <i className="fas fa-spinner fa-spin mr-2"></i>
                      Submitting...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-check mr-2"></i>
                      Submit
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KycForm;
