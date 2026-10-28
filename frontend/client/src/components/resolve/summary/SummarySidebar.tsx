import React, { useEffect, useRef } from "react";
import { CheckCircle, ArrowRight } from "lucide-react";
import { AnsweredQuestion } from "@/lib/types";
import { replacePlaceholders } from "@/lib/utils";

interface SummarySidebarProps {
  answeredQuestions: AnsweredQuestion[];
  totalQuestions: number;
  currentQuestionIndex: number;
  onQuestionClick?: (questionId: string, questionNumber: number) => void;
  userName?: string;
  partnerName?: string;
  isCompleted?: boolean;
}

export function SummarySidebar({
  answeredQuestions,
  totalQuestions,
  currentQuestionIndex,
  onQuestionClick,
  userName = "",
  partnerName = "your partner",
  isCompleted = false,
}: SummarySidebarProps) {
  const answeredCount = answeredQuestions.length;
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Sort answered questions by question number for better display
  const sortedAnsweredQuestions = [...answeredQuestions].sort(
    (a, b) => a.questionNumber - b.questionNumber
  );

  // Auto-scroll to the last answered question when a new question is added
  useEffect(() => {
    if (sidebarRef.current && !isCompleted && answeredCount > 0) {
      // Find the last answered question (highest question number)
      const lastQuestion = sortedAnsweredQuestions[sortedAnsweredQuestions.length - 1];
      if (lastQuestion) {
        const lastQuestionElement = sidebarRef.current.querySelector(
          `[data-question-index="${lastQuestion.questionNumber - 1}"]`
        );
        
        if (lastQuestionElement) {
          // Scroll to the last question with a slight delay to ensure DOM is updated
          setTimeout(() => {
            lastQuestionElement.scrollIntoView({
              behavior: 'smooth',
              block: 'end',
            });
          }, 100);
        }
      }
    }
  }, [answeredCount, isCompleted, sortedAnsweredQuestions]);

  const handleQuestionClick = (questionId: string, questionNumber: number) => {
    if (onQuestionClick && !isCompleted) {
      onQuestionClick(questionId, questionNumber);
    }
  };

  return (
    <div className=" w-80 xl:w-80 bg-white border-l border-novaNeutral-200 h-full overflow-y-auto">
      <div ref={sidebarRef} className="p-4 sm:p-6">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-novaNeutral-900 mb-2">
            Your Answers
          </h2>
          <p className="text-sm text-novaNeutral-600">
            {answeredCount} of {totalQuestions} questions answered
          </p>
        </div>

        {/* Answered Questions */}
        <div className="space-y-3 mb-6">
          {sortedAnsweredQuestions.map((question) => (
            <div
              key={question.questionId}
              data-question-index={question.questionNumber - 1}
              className={`bg-gray-50 rounded-lg p-4 border border-gray-200 transition-colors ${
                !isCompleted ? "hover:bg-novaGray-50 cursor-pointer group" : ""
              } ${
                currentQuestionIndex === question.questionNumber - 1 && !isCompleted
                  ? "ring-2 ring-novaPrimary-500 bg-novaPrimary-50 cursor-pointer"
                  : "cursor-default"
              }`}
              onClick={() =>
                handleQuestionClick(
                  question.questionId,
                  question.questionNumber
                )
              }
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-novaPrimary-600 bg-novaPrimary-100 px-2 py-1 rounded-full">
                    Q{question.questionNumber}
                  </span>
                  <h3 className="font-semibold text-novaNeutral-900 text-sm leading-tight flex-1">
                    {question.questionTitle}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-novaSuccess-500" />
                  {currentQuestionIndex === question.questionNumber - 1 && !isCompleted && (
                    <ArrowRight className="w-4 h-4 text-novaPrimary-500" />
                  )}
                </div>
              </div>

              <div className="mb-2">
                {question.answer.trim().split(/\s+/).length === 1 ? (
                  <p
                    className="text-sm text-novaNeutral-700 font-medium break-all"
                    style={{ wordBreak: "break-all", overflowWrap: "break-word", maxWidth: "100%" }}
                    title={replacePlaceholders(question.answer, userName, partnerName)}
                  >
                    {replacePlaceholders(question.answer, userName, partnerName)}
                  </p>
                ) : (
                  <p 
                    className="text-sm text-novaNeutral-700 font-medium break-words"
                    style={{ overflowWrap: "break-word", maxWidth: "100%" }}
                    title={replacePlaceholders(question.answer, userName, partnerName)}
                  >
                    {replacePlaceholders(question.answer, userName, partnerName)}
                  </p>
                )}
              </div>

              <div className="flex justify-end">
                {!isCompleted && (
                  <span className="text-xs text-novaPrimary-600 font-medium group-hover:text-novaPrimary-800">
                    Click to view
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        {!isCompleted && answeredCount > 0 && (
          <div className="bg-novaPrimary-50 rounded-lg p-4 border border-novaPrimary-200 cursor-default">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-5 h-5 bg-novaPrimary-100 rounded-full flex items-center justify-center">
                <span className="text-novaPrimary-600 text-xs font-bold">i</span>
              </div>
              <h4 className="font-semibold text-novaPrimary-900 text-sm">
                Navigation
              </h4>
            </div>
            <p className="text-xs text-novaPrimary-800 leading-relaxed">
              Click on any answered question above to navigate directly to that
              question.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
