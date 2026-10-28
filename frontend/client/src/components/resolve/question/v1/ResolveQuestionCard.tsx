import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Tooltip } from "@/components/ui/tooltip";
import { Badge } from "@/components/ui/badge";
import {
  FormInput,
  FormButton,
  createFieldProps,
} from "@/utils/formComponents";
import { useFormValidation, ValidationRule } from "@/utils/formValidator";
import { api } from "@/lib/api";
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

// Helper function to render HTML content safely
const renderHtmlContent = (htmlString: string) => {
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

// Helper function to get the selected option's additional description
const getSelectedOptionDescription = (
  questionData: QuestionData,
  currentAnswer: string | string[]
): string | null => {
  if (!currentAnswer || (questionData.input_type !== "radio" && questionData.input_type !== "checkbox")) {
    return null;
  }

  // For checkboxes, check all selected values; for radio, check the single value
  const selectedValues = Array.isArray(currentAnswer) ? currentAnswer : [currentAnswer];
  const descriptions: string[] = [];
  
  for (const optionGroup of questionData.options) {
    for (const [key, optionData] of Object.entries(optionGroup)) {
      // Check if this option is selected
      if (selectedValues.includes(optionData.value) && optionData.additional_description) {
        descriptions.push(optionData.additional_description);
      }
    }
  }
  
  // Return all descriptions joined together, or null if none found
  return descriptions.length > 0 ? descriptions.join('\n\n') : null;
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
  canProceed: boolean;
  currentQuestionIndex: number;
  totalQuestions: number;
  allAnswers?: Record<string, string | string[]>; // Add all answers for conditional logic
  allQuestionData?: Record<string, QuestionData>; // Add all question data for conditional logic
  isCompleting?: boolean; // Add loading state for completion
}

export function ResolveQuestionCard({
  questionData,
  questionId,
  currentAnswer,
  onInputChange,
  onNext,
  canProceed,
  currentQuestionIndex,
  totalQuestions,
  allAnswers = {},
  allQuestionData = {},
  isCompleting = false,
}: ResolveQuestionCardProps) {
  // Ref for the card container to enable scrolling
  const cardRef = useRef<HTMLDivElement>(null);

  // Scroll to top of card on every render
  // useEffect(() => {
  //   if (cardRef.current) {
  //     cardRef.current.scrollIntoView({ 
  //       behavior: 'smooth', 
  //       block: 'start' 
  //     });
  //   }
  // }, [questionId, currentQuestionIndex]); // Re-run when question changes

  // Add keyboard event handler
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && canProceed) {
      e.preventDefault();
      onNext();
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

  // Get the selected option's additional description
  const selectedOptionDescription = getSelectedOptionDescription(questionData, currentAnswer);

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
      return "Complete";
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
            {questionData.placeholder && (
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                {questionData.placeholder}{" "}
                {questionData.required && (
                  <span className="text-novaCaution-500">*</span>
                )}
              </label>
            )}
            <div className="relative">
              <input
                type={isEmailQuestion ? "email" : questionData.input_type}
                value={currentAnswer as string}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyPress={handleKeyPress}
                maxLength={INPUT_MAX_LENGTH.RESOLVE_QUESTION_TEXT}
                placeholder={placeholderText}
                className={`w-full px-3 sm:px-4 py-2 text-sm sm:text-base sm:py-3 border rounded-lg focus:outline-none focus:ring-2 focus:border-transparent ${
                isEmailQuestion && currentAnswer && !isEmailValid
                  ? "border-novaCaution-500 focus:ring-novaCaution-500"
                  : "border-novaNeutral-300 focus:ring-novaPrimary-500"
              }`}
              />
            </div>
            {((currentAnswer as string)?.length || 0) >= INPUT_MAX_LENGTH.RESOLVE_QUESTION_TEXT && (
              <div className="text-xs text-novaCaution-500 mt-1">Limit reached</div>
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
            <p className="text-sm text-novaNeutral-600 mb-3 font-medium">
              Select one option:
              {questionData.required && (
                <span className="text-novaCaution-500 ml-1">*</span>
              )}
            </p>
            <div className="space-y-2" onKeyPress={handleKeyPress}>
              {questionData.options.map((optionGroup, groupIndex) =>
                Object.entries(optionGroup).map(([key, option]) => (
                  <div key={key} className="flex items-center gap-2">
                    <label
                      className={`flex-1 flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                        currentAnswer === option.value
                          ? "border-novaPrimary-500 bg-novaPrimary-50/50 hover:bg-novaPrimary-50/70"
                          : "border-novaNeutral-200 hover:bg-novaNeutral-50"
                      }`}
                    >
                      <input
                        type="radio"
                        name={questionId}
                        value={option.value}
                        checked={currentAnswer === option.value}
                        onChange={(e) => onInputChange(e.target.value)}
                        className="h-4 w-4 border-novaNeutral-300 focus:ring-novaPrimary-500 accent-novaPrimary-500"
                        style={{ marginTop: 0, accentColor: "novaPrimary-500" }}
                      />
                      <div className="flex-1">
                        <div className="text-sm font-medium text-novaNeutral-900" style={{ lineHeight: "1.4rem" }}>
                          {option.value}
                        </div>
                      </div>
                      {currentAnswer === option.value && (
                        <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-[#FF9A50] text-white" aria-hidden>
                          <i className="fas fa-check text-sm !text-white" />
                        </span>
                      )}
                    </label>
                    {option.tooltip && (
                      <Tooltip content={option.tooltip} position="right-mobile">
                        <div className="flex-shrink-0 flex items-center justify-center w-5 h-5 text-novaNeutral-400 hover:text-novaNeutral-600 cursor-help">
                          <i className="fas fa-question-circle text-sm"></i>
                        </div>
                      </Tooltip>
                    )}
                  </div>
                ))
              )}
            </div>
            
            {/* Show additional description for selected option */}
            {selectedOptionDescription && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="text-sm text-novaNeutral-700">
                  {renderHtmlContent(selectedOptionDescription)}
                </div>
              </div>
            )}
          </div>
        );

      case "checkbox":
        return (
          <div className="space-y-3">
            <p className="text-sm text-novaNeutral-600 mb-3 font-medium">
              Select all that apply:
              {questionData.required && (
                <span className="text-novaCaution-500 ml-1">*</span>
              )}
            </p>
            <div className="space-y-2" onKeyPress={handleKeyPress}>
              {questionData.options.map((optionGroup, groupIndex) =>
                Object.entries(optionGroup).map(([key, option]) => {
                  const selectedValues = Array.isArray(currentAnswer)
                    ? currentAnswer
                    : [];
                  const isChecked = selectedValues.includes(option.value);

                  return (
                    <div key={key} className="flex items-center gap-2">
                      <label
                        className="flex-1 flex items-start space-x-3 p-3 border border-novaNeutral-200 rounded-lg hover:bg-novaNeutral-50 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          name={`${questionId}_${key}`}
                          value={option.value}
                          checked={isChecked}
                          onChange={(e) => {
                            const newValues = isChecked
                              ? selectedValues.filter(
                                  (val) => val !== option.value
                                )
                              : [...selectedValues, option.value];
                            onInputChange(newValues);
                          }}
                          className="mt-1 h-4 w-4 border-novaNeutral-300 rounded accent-black focus:ring-black"
                          style={{
                            accentColor: 'novaPrimary-500'
                          }}
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-novaNeutral-900">
                            {option.value}
                          </div>
                        </div>
                      </label>
                      {option.tooltip && (
                        <Tooltip content={option.tooltip} position="right-mobile">
                          <div className="flex-shrink-0 flex items-center justify-center w-5 h-5 text-novaNeutral-400 hover:text-novaNeutral-600 cursor-help">
                            <i className="fas fa-question-circle text-sm"></i>
                          </div>
                        </Tooltip>
                      )}
                    </div>
                  );
                })
              )}
            </div>
            {/* Show additional description for selected option */}
            {selectedOptionDescription && (
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="text-sm text-novaNeutral-700">
                  {renderHtmlContent(selectedOptionDescription)}
                </div>
              </div>
            )}
          </div>
        );

      default:
        return (
          <div className="space-y-2">
            {/* Show label only if there's a placeholder */}
            {questionData.placeholder && (
              <label className="block text-sm font-medium text-novaNeutral-700 mb-2">
                {questionData.placeholder}{" "}
                {questionData.required && (
                  <span className="text-novaCaution-500">*</span>
                )}
              </label>
            )}
            <>
              <input
                type="text"
                value={currentAnswer as string}
                onChange={(e) => onInputChange(e.target.value)}
                maxLength={INPUT_MAX_LENGTH.RESOLVE_QUESTION_DEFAULT}
                onKeyPress={handleKeyPress}
                placeholder={placeholderText}
                className="w-full px-4 py-3 border border-novaNeutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-novaPrimary-500 focus:border-transparent"
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

  return (
      <div className="flex justify-center w-full">
      <div className="w-full max-w-[760px] sm:w-11/12 md:w-full min-w-0 flex justify-center 2xl:w-4/5">
        <div ref={cardRef} className="bg-white rounded-none sm:rounded-xl shadow-2xl border border-novaNeutral-100 p-4 sm:p-8 pb-16 sm:pb-8 sm:min-h-0">
          {/* Question Header */}
          <div className="flex items-center gap-3 mb-4">
            <Badge
              variant="secondary"
              className="bg-novaPrimary-50 text-novaPrimary-700 border-novaPrimary-200"
            >
              Question {currentQuestionIndex + 1}
            </Badge>
          </div>

          {/* Question Content */}
          <div className="bg-gray-50 rounded-lg border border-gray-200 my-4">
            <div className="rounded-lg text-card-foreground shadow-none border-0 bg-transparent">
              <div className="flex flex-col space-y-1.5 p-4 sm:p-8 pb-6">
                <div className="tracking-tight text-lg sm:text-xl font-semibold text-novaNeutral-900 sm:mb-3 leading-tight">
                  {displayTitle}
                </div>
                <div className="text-gray-600 text-md sm:text-base leading-relaxed">
                  {renderHtmlContent(displayDescription)}
                </div>
                <div className="flex justify-center mt-2">
                  <img
                    src={image.src}
                    alt={image.alt}
                    className="w-48 h-48 object-contain"
                    onError={(e) => {
                      // Fallback to a default image if the specific version_questionId.svg doesn't exist
                      const target = e.target as HTMLImageElement;
                      target.src = "/src/assets/resolve-images/1_1.svg"; // Default fallback
                    }}
                  />
                </div>
              </div>

              {/* Input Section */}
              <div className="p-4 sm:p-6 pt-0 space-y-6">
                {renderInput()}
              </div>
            </div>
          </div>

          {/* Navigation Buttons - Sticky on mobile, normal on desktop */}
          <div className="fixed sm:static bottom-0 left-0 right-0 sm:pt-6 sm:border-t sm:border-novaNeutral-100 bg-white sm:bg-transparent z-40 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] sm:shadow-none">
            <div className="flex items-center justify-end px-8 py-2 sm:p-0 gap-2">
              <div className="flex gap-2 sm:gap-4">
                <FormButton
                  type="button"
                  variant="primary"
                  onClick={onNext}
                  disabled={!canProceed || isCompleting || (isEmailQuestion && !isEmailValid)}
                  className={`bg-novaPrimary-500 text-xs sm:text-base hover:bg-novaPrimary-600 text-white shadow-lg hover:shadow-xl transition-all duration-200 ${
                    isCompleting ? 'opacity-75 cursor-not-allowed' : ''
                  }`}
                >
                  {isCompleting ? (
                    <span className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      <span className="hidden xs:inline">Completing...</span>
                      <span className="xs:hidden">...</span>
                    </span>
                  ) : (
                    <>
                      {getButtonText()}
                      <i className="fas fa-arrow-right ml-2"></i>
                    </>
                  )}
                </FormButton>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
