import React from "react";
import { Button } from "../ui/button";
import { FormButton, renderHtmlContent } from "@/utils";
import { useRole } from "@/contexts/RoleContext";

interface ResolveQuestion {
  question_type: string;
  variant: string;
  title: string;
  description: string;
  placeholder: string;
  question: string;
  options: string[];
  required: boolean;
  input_type: string;
  rules: string[];
  question_order: number;
  answer_type: string;
  answer: string[];
  question_status: string;
  version: string;
}

interface ResolveResult {
  result_type: string;
  title: string;
  summary: string;
  version: string;
}

interface ResolveDetailsModalProps {
  data: Record<string, ResolveQuestion> & { 
    resolve_status?: string; 
    question_data?: Record<string, ResolveQuestion>;
    result?: ResolveResult | null;
  };
  isOpen: boolean;
  onClose: () => void;
  caseId?: string;
  resolveId?: string;
  showViewCaseButton?: boolean;
}

const ResolveDetailsModal: React.FC<ResolveDetailsModalProps> = ({ 
  isOpen, 
  onClose, 
  caseId,
  data,
  resolveId,
  showViewCaseButton = false
}) => {
  const { currentRole } = useRole();
  const resolveStatus = (data as any).resolve_status || "";
  const resolveResult = (data as any).result as ResolveResult | null | undefined;
  if (!isOpen) return null;
  const questionData = (data as any).question_data || data;
  const questions = (Object.values(questionData) as ResolveQuestion[]).sort(
    (a, b) => a.question_order - b.question_order
  );

  // Get partner name from question 2
  const partnerName = questions[1]?.answer && Array.isArray(questions[1].answer) && questions[1].answer.length > 0
    ? (typeof questions[1].answer[0] === "string"
        ? questions[1].answer[0]
        : (questions[1].answer[0] as any)?.value || "")
    : "";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div
        role="dialog"
        aria-describedby="resolve-details-description"
        aria-labelledby="resolve-details-title"
        data-state="open"
        className="
          w-full max-w-2xl max-h-[80vh]
          flex flex-col 
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
        <div className="flex flex-col space-y-1.5 text-center sm:text-left flex-shrink-0 mb-4">
          <div className="flex items-center justify-between">
            <h2 id="resolve-details-title" className="text-lg font-semibold leading-[1] tracking-wide flex items-center gap-2 mb-4">
              <i className="fas fa-check-circle text-novaDarkOrange"></i>
              Your recommendation details
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
          <p id="resolve-details-description" className="text-sm hidden sm:block text-muted-foreground px-1">
            You can review below the information you shared with us which informed your personalised recommendation. If you’d like to update anything, please contact a Nova Navigator who will be happy to help.          </p>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-1">
          <div className="space-y-3 mb-3">
            {(() => {
              // Filter answered questions first
              const answeredQuestions = questions.filter((q) => {
                // Filter out unanswered questions
                if (!q.answer || !Array.isArray(q.answer) || q.answer.length === 0) {
                  return false;
                }
                // Also check if answer values are not empty
                const answerKeys = q.answer
                  .map((ans: string | { value?: string }) => typeof ans === "string" ? ans : (ans?.value || ""))
                  .filter((val: string) => val.trim().length > 0);
                return answerKeys.length > 0;
              });

              // Show empty state if no answered questions
              if (answeredQuestions.length === 0) {
                return (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <i className="fas fa-question-circle text-4xl text-novaNeutral-200 mb-3"></i>
                    <p className="text-novaNeutral-400 text-sm">No questions answered</p>
                  </div>
                );
              }

              // Render answered questions
              return answeredQuestions.map((q) => {
                // Extract all answer keys/values
                const answerKeys = q.answer
                  .map((ans: string | { value?: string }) => typeof ans === "string" ? ans : (ans?.value || ""))
                  .filter((val: string) => val.trim().length > 0);

                // Build options lookup map
                const optionsMap: Record<string, string> = {};
                if (q.options && Array.isArray(q.options) && q.options.length > 0) {
                  const optionsObj = q.options[0] as any;
                  Object.keys(optionsObj).forEach(key => {
                    if (optionsObj[key]?.value) {
                      optionsMap[key] = optionsObj[key].value;
                    }
                  });
                }

                // Get display values - either from options or use the raw value
                const displayValues = answerKeys.map((key: string) => {
                  if (Object.keys(optionsMap).length > 0 && optionsMap[key]) {
                    return optionsMap[key];
                  }
                  // For text/number inputs, just return the value as-is
                  return key;
                });

                return (
                  <div key={q.question_order} className="bg-white rounded-xl shadow-md border border-novaNeutral-100 flex flex-col gap-2 transition-all sm:p-5 p-3">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-xs font-semibold text-novaDarkOrange bg-novaActive rounded-full sm:text-xs text-[11px] px-2 py-0.5">
                        Question {q.question_order}
                      </span>
                    </div>
                    <div className="font-medium italic text-novaTextGray mb-2 sm:text-sm text-xs break-words">
                      {renderHtmlContent(q.question.replace(/\{partner_name\}/g, partnerName))}
                    </div>
                    <div className="bg-novaNeutral-50 rounded-lg px-4 py-2 text-novaTextGray border border-novaNeutral-200 sm:text-sm text-xs break-words">
                      {displayValues.map((val: string, valIdx: number) => (
                        <div key={valIdx}>
                          {val.replace(/\{partner_name\}/g, partnerName)}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              });
            })()}
            {/* {resolveStatus === "Completed" && resolveResult && (
              <div className="bg-white rounded-xl shadow-md border border-novaNeutral-100 flex flex-col gap-3 transition-all sm:p-5 p-3">
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-xs font-semibold text-green-600 bg-green-50 rounded-full sm:text-xs text-[11px] px-2 py-0.5">
                    Resolve Result
                  </span>
                </div>
                <div className="flex flex-col gap-2">
                  <div className="font-semibold text-novaTextGray text-base sm:text-lg">
                    {resolveResult.title}
                  </div>
                  {resolveResult.summary && (
                    <div 
                      className="text-sm text-novaTextGray leading-loose break-words"
                      dangerouslySetInnerHTML={{ __html: resolveResult.summary }}
                    />
                  )}
                </div>
              </div>
            )} */}

          </div>
          
          {/* What happens next section - Only for customers */}
          {currentRole === "Customer" && (
            <div className="mt-6 pt-6 border-t border-novaNeutral-200">
              <h3 className="text-base font-semibold text-novaNeutral-900 mb-3">
                What happens next
              </h3>
              <p className="text-sm text-novaNeutral-700 mb-4">
                You don't need to do anything here.
              </p>
              <p className="text-sm text-novaNeutral-700 mb-3">
                Your recommendation is shown in <i>My Nova Recommendations</i>. From there, you can:
              </p>
              <ul className="list-disc list-inside space-y-2 text-sm text-novaNeutral-700 ml-2">
                <li>review your recommended pathway</li>
                <li>explore Nova Experts with relevant experience</li>
                <li>decide if and when you'd like to move forward</li>
              </ul>
            </div>
          )}
        </div>
        

        {/* Footer */}
        <div className="flex sm:flex-row justify-end sm:space-x-2 gap-3 flex-shrink-0 pt-4 border-t border-gray-200">
        {resolveStatus === "Completed" && caseId && showViewCaseButton && (
          <div className="flex justify-end gap-2">
            <FormButton 
              variant="gradient" 
              className="inline-flex items-center gap-2 text-sm px-4 py-2" 
              onClick={() => {
                window.location.href = `/case/${caseId}`;
              }}
            >
              <i className="fas fa-folder-open"></i>
              View case
            </FormButton>
            </div>
        )}
        {currentRole === "Customer" && resolveStatus !== "Completed" && (
          <div className="flex justify-end">
            <FormButton
              variant="primary"
              className="inline-flex items-center gap-2 text-sm px-4 py-2"
              onClick={() => {
                if (resolveId) {
                  window.location.href = `/resolve/${encodeURIComponent(resolveId)}`;
                }
              }}
            >
              <i className="fas fa-edit"></i>
              Edit
            </FormButton>
          </div>
        )}
          <FormButton 
            variant="custom" 
            onClick={onClose}
            className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 h-10 px-4 py-2 border border-novaNeutral-500 bg-white hover:bg-novaBlack text-novaNeutral-700 hover:text-white"
          >
            Close
          </FormButton>
        </div>
      </div>
    </div>
  );
};

export default ResolveDetailsModal;
