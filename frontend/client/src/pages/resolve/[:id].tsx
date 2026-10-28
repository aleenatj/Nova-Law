import { useState, useEffect } from "react";
import { useParams } from "wouter";
import { SummarySidebar, ResolveSummaryCard } from "@/components/resolve";
import { api, ApiError, tokenManager } from "@/lib/api";
import { getResolveQuestionCard } from "@/components/resolve/question";
import { ResolveLayout } from "@/components/layout/v1";
import ResolveBookingCard from "@/components/resolve/summary/ResolveBookingCard";
import { WelcomeCard } from "@/components/resolve/question/v1/WelcomCard";
import {
  ToastContainer,
  createSuccessToast,
  createErrorToast,
  createInfoToast,
  toastManager,
} from "../../utils/toasts";
import { AlertMessage } from "../../utils/alerts";
import {
  QuestionOption,
  QuestionAnswer,
  QuestionData,
  ResolveResult,
  ResolveData,
  SaveAnswerResponse,
  CompleteResolveResponse,
  AnswerRequest,
  SaveAnswerRequest,
  AnsweredQuestion,
  LawyerProfile,
} from "@/lib/types";
import { replacePlaceholders } from "@/lib/utils";
import { useRole } from "@/contexts/RoleContext";
import { useAuth } from "@/contexts/AuthContext";
import { navigate } from "wouter/use-browser-location";
import { FormButton } from "@/utils";
// Session Storage Keys
const RESOLVE_SESSION_KEY = "resolve_session_data";
const RESOLVE_ID_KEY = "resolveId";
const SHOW_EMAIL_QUESTION_ONLY_KEY = "showEmailQuestionOnly";
const SHOW_RESULT_PAGE_ONLY_KEY = "showResultPageOnly";

// Helper function to extract name from session storage
const getNameFromSession = (questionId: string): string => {
  try {
    const session = sessionStorage.getItem(RESOLVE_SESSION_KEY);
    if (session) {
      const data = JSON.parse(session);
      const answer = data?.question_data?.[questionId]?.answer?.[0]?.value;
      return typeof answer === "string" ? answer : "";
    }
  } catch (e) {}
  return "";
};

// Helper function to find display value for option key
const findDisplayValue = (key: string, options: QuestionOption[]): string => {
  for (const optionGroup of options) {
    for (const [optionKey, optionData] of Object.entries(optionGroup)) {
      if (optionKey === key) {
        return optionData.value;
      }
    }
  }
  return key; // Fallback to key if not found
};

// Helper function to check if answer is valid/non-empty
const isValidAnswer = (answer: string | string[]): boolean => {
  if (!answer) return false;
  return Array.isArray(answer)
    ? answer.length > 0 && answer.some((a) => a && a.trim().length > 0)
    : answer.trim().length > 0;
};

export default function ResolveDetail() {
  const params = useParams();
  const resolveId = params.id;
  const { currentRole, setCurrentRole } = useRole();
  const { user, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolveData, setResolveData] = useState<ResolveData | null>(null);
  const [resolveComplete, setResolveComplete] = useState(false);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [resolveResult, setResolveResult] = useState<ResolveResult | null>(
    null
  );
  const [answeredQuestions, setAnsweredQuestions] = useState<
    AnsweredQuestion[]
  >([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(-1);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [toasts, setToasts] = useState<AlertMessage[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isCompleting, setIsCompleting] = useState(false);
  const [showCompletionToasts, setShowCompletionToasts] = useState(false);
  const [isRegistrationSuccess, setIsRegistrationSuccess] = useState(false);
  const [isResolvePostSent, setIsResolvePostSent] = useState(false);
  const [storedEmail, setStoredEmail] = useState<string | null>(null);
  const [hasMarketingConsent, setHasMarketingConsent] = useState(false);
  const [showEmailQuestionOnly, setShowEmailQuestionOnly] = useState<boolean>(() => {
    try {
      const stored = sessionStorage.getItem(SHOW_EMAIL_QUESTION_ONLY_KEY);
      return stored === "true";
    } catch (e) {
      return false;
    }
  });
  const [showResultPageOnly, setShowResultPageOnly] = useState<boolean>(() => {
    try {
      const stored = sessionStorage.getItem(SHOW_RESULT_PAGE_ONLY_KEY);
      return stored === "true";
    } catch (e) {
      return false;
    }
  });
  // Extract user and partner names from session storage if available
  const [userName, setUserName] = useState<string>(() =>
    getNameFromSession("1")
  );
  const [partnerName, setPartnerName] = useState<string>(() =>
    getNameFromSession("2")
  );
  // Helper function to check if a question should be shown based on rules
  const shouldShowQuestion = (
    questionData: QuestionData,
    allAnswers: Record<string, string | string[]>,
    allQuestionData: Record<string, QuestionData>
  ): boolean => {
    if (!questionData.rules || questionData.rules.length === 0) {
      return true; // Show if no rules
    }

    return questionData.rules.some((rule) => {
      const parentAnswer = allAnswers[rule.identifier];
      if (!parentAnswer) return false;

      // Get parent question data to convert display values back to option keys
      const parentQuestionData = allQuestionData[rule.identifier];
      if (!parentQuestionData) return false;

      // Handle both single values and arrays (for checkboxes)
      const parentAnswerValues = Array.isArray(parentAnswer)
        ? parentAnswer
        : [parentAnswer];

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
        const allowedValues = Array.isArray(rule.value)
          ? rule.value
          : [rule.value];
        return selectedOptionKeys.some((key) => allowedValues.includes(key));
      }

      // For "is" operator, check if any of the selected option keys match the rule value
      return selectedOptionKeys.includes(rule.value);
    });
  };

  const lawyerProfiles: LawyerProfile[] = resolveData?.lawyers
    ? resolveData.lawyers.map((lawyer: any) => ({
        lawyer_name: `${lawyer.first_name} ${lawyer.last_name}`,
        lawyer_photo_url:
          lawyer.photo_url === "None" || !lawyer.photo_url
            ? ""
            : lawyer.photo_url,
        experience: lawyer.experience || "",
        about: lawyer.about || "",
        city: lawyer.city || "",
        county: lawyer.county || "",
        country: lawyer.country || "",
        accredited_specialisations: lawyer.accredited_specialisations || "",
        expert_types: lawyer.expert_types || [],
        relationship_types: lawyer.relationship_types || [],
        matter_types: lawyer.matter_types || [],
        hourly_rate: lawyer.hourly_rate,
        charge_first_consultation: lawyer.charge_first_consultation,
        lawfirms: lawyer.lawfirms || [],
      }))
    : [];

  // Get questions sorted by order and filtered by rules
  const questions = resolveData?.question_data
    ? Object.entries(resolveData.question_data)
        .filter(([, questionData]) =>
          shouldShowQuestion(questionData, answers, resolveData.question_data)
        )
        .sort(([, a], [, b]) => a.question_order - b.question_order)
    : [];

  const currentQuestion = questions[currentQuestionIndex];
  const [questionId, questionData] = currentQuestion || ["", null];

  // Total questions in the full flow (unfiltered) - used for step denominator
  const totalQuestions = resolveData?.question_data ? Object.keys(resolveData.question_data).length : 0;

  // Original step number for the current question (from question_order) so numbering doesn't change when questions are filtered by rules
  const currentQuestionStepNumber = questionData?.question_order ?? currentQuestionIndex + 1;

  // Save resolve data to session storage
  const saveResolveToSession = (data: ResolveData) => {
    try {
      sessionStorage.setItem(RESOLVE_SESSION_KEY, JSON.stringify(data));
      sessionStorage.setItem(RESOLVE_ID_KEY, data.resolve_id);
    } catch (error) {
      console.warn("Failed to save resolve data to session storage:", error);
    }
  };
  // Clear session storage
  const clearResolveSession = () => {
    try {
      sessionStorage.removeItem(RESOLVE_SESSION_KEY);
      sessionStorage.removeItem(RESOLVE_ID_KEY);
      sessionStorage.removeItem(SHOW_EMAIL_QUESTION_ONLY_KEY);
      sessionStorage.removeItem(SHOW_RESULT_PAGE_ONLY_KEY);
    } catch (error) {
      console.warn("Failed to clear resolve session storage:", error);
    }
  };

  // Helper function to save showEmailQuestionOnly state
  const saveShowEmailQuestionOnly = (value: boolean) => {
    try {
      sessionStorage.setItem(SHOW_EMAIL_QUESTION_ONLY_KEY, String(value));
      setShowEmailQuestionOnly(value);
    } catch (error) {
      console.warn("Failed to save showEmailQuestionOnly to session storage:", error);
    }
  };

  // Helper function to save showResultPageOnly state
  const saveShowResultPageOnly = (value: boolean) => {
    try {
      sessionStorage.setItem(SHOW_RESULT_PAGE_ONLY_KEY, String(value));
      setShowResultPageOnly(value);
    } catch (error) {
      console.warn("Failed to save showResultPageOnly to session storage:", error);
    }
  };

  // Helper function to add toast
  const addToast = (toast: AlertMessage) => {
    setToasts((prev) => [...prev, toast]);
    // Auto remove after duration
    if (toast.duration) {
      setTimeout(() => {
        removeToast(toast.id);
      }, toast.duration);
    }
  };
  // Helper function to remove toast
  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  useEffect(() => {
    const fetchResolveData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Handle /resolve-new and /resolve/new routes FIRST - before any other logic
        // This prevents flickering by redirecting immediately without fetching/rendering
        const isResolveNew =
          window.location.pathname === "/resolve-new" ||
          window.location.pathname === "/resolve-new/" ||
          window.location.pathname.endsWith("/resolve-new") ||
          window.location.pathname === "/resolve/new/" ||
          window.location.pathname === "/resolve/new";

        if (isResolveNew) {
          // Directly call API to create new resolve and redirect to new ID
          // Skip session storage checking - always create a new resolve
          try {
            const result = await api.get("/v1/resolve");
            const resolveIdFromResult = (result as any)?.data?.resolve_id;
            if (resolveIdFromResult) {
              // Redirect directly to the new resolve page
              window.location.replace(`/resolve/${resolveIdFromResult}`);
              return; // Exit early to prevent further processing
            }
            // If no resolve ID, fall through to error handling
            setError("Failed to create new resolve");
            setLoading(false);
            return;
          } catch (err) {
            console.error("Error creating new resolve:", err);
            setError("Failed to create new resolve");
            setLoading(false);
            return;
          }
        }

        // Check if user role is allowed to browse resolve URLs
        // Only Guest and Customer can browse resolve URLs
        const isGuest = !isAuthenticated || currentRole === "Guest";
        const isCustomer = currentRole === "Customer";

        // If user is not a guest or customer, redirect to resolve dashboard
        if (!isGuest && !isCustomer) {
          window.location.href = "/resolve-dashboard";
          return;
        }

        let result;
        if (resolveId) {
          // Case 1: ID in params
          const sessionResolveId = sessionStorage.getItem(RESOLVE_ID_KEY) || "";
          if (!isGuest && !isCustomer) {
            window.location.href = "/case-dashboard";
            return;
          }
          
          if (isGuest) {
            // Guest users can only access resolves if URL ID matches session storage ID
            if (sessionResolveId === resolveId) {
              // Guest user with matching session ID - fetch the resolve
              const encodedResolveId = encodeURIComponent(resolveId);
              result = await api.get(`/v1/resolve?resolve_id=${encodedResolveId}`);
            } else {
              // Guest user trying to access a resolve that's not in their session
              // Create a new resolve instead
              clearResolveSession();
              result = await api.get("/v1/resolve");
              const resolveIdFromResult = (result as any)?.data?.resolve_id;
              if (resolveIdFromResult) {
                sessionStorage.setItem(RESOLVE_ID_KEY, resolveIdFromResult);
                // Redirect to the new resolve page
                window.location.replace(`/resolve/${resolveIdFromResult}`);
                return; // Exit early to prevent further processing
              }
            }
          } else {
            // Customer users - API will handle authorization, just fetch the resolve
            const encodedResolveId = encodeURIComponent(resolveId);
            result = await api.get(`/v1/resolve?resolve_id=${encodedResolveId}`);
          }
           
        } else {
          // Case 2: No ID in params - check session storage first
          const sessionResolveId = sessionStorage.getItem(RESOLVE_ID_KEY);

          if (sessionResolveId) {
            // Case 2a: Found ID in session storage - redirect to that resolve
            window.location.href = `/resolve/${sessionResolveId}`;
            return; // Exit early to prevent further processing
          } else {
            // Case 2b: No ID in session - create new resolve
            result = await api.get("/v1/resolve");

            // Store the new resolve ID in session storage
            const resolveIdFromResult = (result as any)?.data?.resolve_id;
            if (resolveIdFromResult) {
              sessionStorage.setItem(RESOLVE_ID_KEY, resolveIdFromResult);
              // Redirect to the new resolve page
              window.location.href = `/resolve/${resolveIdFromResult}`;
              return; // Exit early to prevent further processing
            }
          }
        }

        // Handle the response - check if it's wrapped or direct
        let resolveData: ResolveData;
        if (result && typeof result === "object" && "data" in result) {
          // Response is wrapped: {success: true, data: {...}}
          if ((result as any).success) {
            resolveData = result.data as ResolveData;
          } else {
            throw new Error(
              (result as any).message?.[0]?.message || "API request failed"
            );
          }
        } else if (
          result &&
          typeof result === "object" &&
          "resolve_id" in result
        ) {
          // Response is direct: {resolve_id: "...", title: "...", ...}
          resolveData = result as ResolveData;
        } else {
          throw new Error("Invalid response format");
        }

        // Extract caseId from the result if available
        const extractedCaseId = (result as any)?.data?.case?.id || (result as any)?.case?.id;
        if (extractedCaseId) {
          setCaseId(extractedCaseId);
        }

        setResolveData(resolveData);
      } catch (err: any) {
        // Handle errors
        if (err instanceof ApiError) {
          const isGuest = !isAuthenticated || currentRole === "Guest";

          if (!isGuest) {
            clearResolveSession();
            window.location.href = "/resolve-dashboard";
            return;
          }
          clearResolveSession();
          const result = await api.get("/v1/resolve");
          const resolveIdFromResult = (result as any)?.data?.resolve_id;
          if (resolveIdFromResult) {
            sessionStorage.setItem(RESOLVE_ID_KEY, resolveIdFromResult);
            window.location.replace(`/resolve/${resolveIdFromResult}`);
            return;
          }
          window.location.href = "/resolve-dashboard";
          return;
        }

        // For other errors, redirect to dashboard
        console.error("Error fetching resolve data:", err);
        window.location.href = "/resolve-dashboard";
        setError(
          err instanceof Error ? err.message : "Failed to fetch resolve data"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchResolveData();
  }, [resolveId, user?.id, currentRole, isAuthenticated]);

  // Initialize answers when resolve data is loaded
  useEffect(() => {
    if (resolveData) {
      const existingAnswers: Record<string, string | string[]> = {};
      const initialAnsweredQuestions: AnsweredQuestion[] = [];

      // Extract and update user and partner names from resolve data
      const userNameFromData =
        resolveData.question_data?.["1"]?.answer?.[0]?.value;
      const partnerNameFromData =
        resolveData.question_data?.["2"]?.answer?.[0]?.value;

      if (
        typeof userNameFromData === "string" &&
        userNameFromData !== userName
      ) {
        setUserName(userNameFromData);
      }
      if (
        typeof partnerNameFromData === "string" &&
        partnerNameFromData !== partnerName
      ) {
        setPartnerName(partnerNameFromData);
      }

      if (
        resolveData.question_data &&
        typeof resolveData.question_data === "object"
      ) {
        // Use extracted names or fallback to state values for placeholder replacement
        const currentUserName = userNameFromData || userName || "";
        const currentPartnerName = partnerNameFromData || partnerName || "your partner";
        
        Object.entries(resolveData.question_data).forEach(([id, question]) => {
          if (question.answer && question.answer.length > 0) {
            if (question.input_type === "checkbox") {
              // For checkbox, convert keys back to display values and replace placeholders
              existingAnswers[id] = question.answer.map((answerKey) => {
                const displayValue = findDisplayValue(answerKey.value, question.options);
                return replacePlaceholders(displayValue, currentUserName, currentPartnerName);
              });
            } else if (question.input_type === "radio") {
              // For radio, convert key back to display value and replace placeholders
              const displayValue = findDisplayValue(
                question.answer[0].value,
                question.options
              );
              existingAnswers[id] = replacePlaceholders(displayValue, currentUserName, currentPartnerName);
            } else {
              // For text, number, email, textarea - use value directly (no placeholders typically)
              existingAnswers[id] = question.answer[0].value;
            }

            // Add to answered questions for sidebar only if question should be shown based on rules
            if (
              shouldShowQuestion(
                question,
                existingAnswers,
                resolveData.question_data
              )
            ) {
              // Create filtered questions array using current answers to get correct index
              const filteredQuestions = Object.entries(
                resolveData.question_data
              )
                .filter(([, qData]) =>
                  shouldShowQuestion(
                    qData,
                    existingAnswers,
                    resolveData.question_data
                  )
                )
                .sort(([, a], [, b]) => a.question_order - b.question_order);

              // Find the filtered question index for this question
              const filteredQuestionIndex = filteredQuestions.findIndex(
                ([qId]) => qId === id
              );

              const answeredQuestion = createAnsweredQuestion(
                id,
                question,
                existingAnswers[id],
                filteredQuestionIndex
              );
              initialAnsweredQuestions.push(answeredQuestion);
            }
          }
        });
      }
      setAnswers(existingAnswers);
      setAnsweredQuestions(initialAnsweredQuestions);
      // Save to session storage whenever resolve data changes
      saveResolveToSession(resolveData);
      // If resolve is completed, set the result
      if (resolveData.resolve_status === "Completed" && resolveData.result) {
        setResolveResult(resolveData.result);
        setResolveComplete(true);
        
        // Restore states from session storage if available
        // States are already initialized from session storage, but ensure they're properly set
        // If states aren't set and we have a result, we might need to check registration status
        // For now, rely on the states loaded from session storage on mount
        
        // Don't set question index if resolve is completed - will show completion screen
      } else {
        // Determine which question to show on mount/refresh
        // Show the latest answered question, or WelcomeCard if no questions answered
        // Create filtered questions array based on current answers
        const filteredQuestions = Object.entries(resolveData.question_data)
          .filter(([, qData]) =>
            shouldShowQuestion(qData, existingAnswers, resolveData.question_data)
          )
          .sort(([, a], [, b]) => a.question_order - b.question_order);
        
        // Find the last answered question index
        let lastAnsweredIndex = -1;
        if (filteredQuestions.length > 0 && Object.keys(existingAnswers).length > 0) {
          // Find the highest index of an answered question
          for (let i = filteredQuestions.length - 1; i >= 0; i--) {
            const [qId] = filteredQuestions[i];
            if (existingAnswers[qId] && isValidAnswer(existingAnswers[qId])) {
              lastAnsweredIndex = i;
              break;
            }
          }
          
          // If we found an answered question, show it
          if (lastAnsweredIndex >= 0) {
            setCurrentQuestionIndex(lastAnsweredIndex);
          } else {
            // No answered questions, show WelcomeCard
            setCurrentQuestionIndex(-1);
          }
        } else {
          // No questions or no answers, show WelcomeCard
          setCurrentQuestionIndex(-1);
        }
      }
    }
  }, [resolveData]);

  // Load answered questions from session data when resolve is completed
  useEffect(() => {
    if (resolveComplete && resolveData) {
      const sessionAnsweredQuestions: AnsweredQuestion[] = [];

      Object.entries(resolveData.question_data).forEach(([id, question]) => {
        if (question.answer && question.answer.length > 0) {
          let displayAnswer: string | string[];

          if (question.input_type === "checkbox") {
            displayAnswer = question.answer.map((answerKey) =>
              findDisplayValue(answerKey.value, question.options)
            );
          } else if (question.input_type === "radio") {
            displayAnswer = findDisplayValue(
              question.answer[0].value,
              question.options
            );
          } else {
            displayAnswer = question.answer[0].value;
          }

          // Only add to answered questions if the question should be shown based on rules
          if (
            shouldShowQuestion(question, answers, resolveData.question_data)
          ) {
            // Create filtered questions array using current answers to get correct index
            const filteredQuestions = Object.entries(resolveData.question_data)
              .filter(([, qData]) =>
                shouldShowQuestion(qData, answers, resolveData.question_data)
              )
              .sort(([, a], [, b]) => a.question_order - b.question_order);

            // Find the filtered question index for this question
            const filteredQuestionIndex = filteredQuestions.findIndex(
              ([qId]) => qId === id
            );

            const answeredQuestion = createAnsweredQuestion(
              id,
              question,
              displayAnswer,
              filteredQuestionIndex
            );
            sessionAnsweredQuestions.push(answeredQuestion);
          }
        }
      });

      // Sort by question order
      sessionAnsweredQuestions.sort(
        (a, b) => a.questionNumber - b.questionNumber
      );

      // Only update if we have questions and they're different from current state
      if (sessionAnsweredQuestions.length > 0) {
        setAnsweredQuestions(sessionAnsweredQuestions);
      }
    }
  }, [resolveComplete, resolveData]);

  // Re-evaluate questions when answers change to handle rule-based visibility
  useEffect(() => {
    if (resolveData && !resolveComplete) {
      // Only re-evaluate if we have new answers that might affect rule visibility
      // Don't re-filter already answered questions unless their rules explicitly change
      setAnsweredQuestions((prevAnsweredQuestions) => {
        const newAnsweredQuestions: AnsweredQuestion[] = [];

        // Keep existing answered questions that are still valid
        prevAnsweredQuestions.forEach((answeredQ) => {
          const questionData = resolveData.question_data[answeredQ.questionId];
          if (questionData) {
            // Check if this question should still be shown based on current rules
            if (
              shouldShowQuestion(
                questionData,
                answers,
                resolveData.question_data
              )
            ) {
              newAnsweredQuestions.push(answeredQ);
            }
          }
        });

        // Add any new questions that have been answered and meet their rules
        Object.entries(resolveData.question_data).forEach(([id, question]) => {
          if (question.answer && question.answer.length > 0) {
            // Check if this question is already in our answered questions
            const alreadyExists = newAnsweredQuestions.some(
              (aq) => aq.questionId === id
            );

            if (
              !alreadyExists &&
              shouldShowQuestion(question, answers, resolveData.question_data)
            ) {
              let displayAnswer: string | string[];

              if (question.input_type === "checkbox") {
                displayAnswer = question.answer.map((answerKey) =>
                  findDisplayValue(answerKey.value, question.options)
                );
              } else if (question.input_type === "radio") {
                displayAnswer = findDisplayValue(
                  question.answer[0].value,
                  question.options
                );
              } else {
                displayAnswer = question.answer[0].value;
              }

              // Create filtered questions array using current answers to get correct index
              const filteredQuestions = Object.entries(
                resolveData.question_data
              )
                .filter(([, qData]) =>
                  shouldShowQuestion(qData, answers, resolveData.question_data)
                )
                .sort(([, a], [, b]) => a.question_order - b.question_order);

              // Find the filtered question index for this question
              const filteredQuestionIndex = filteredQuestions.findIndex(
                ([qId]) => qId === id
              );

              const answeredQuestion = createAnsweredQuestion(
                id,
                question,
                displayAnswer,
                filteredQuestionIndex
              );
              newAnsweredQuestions.push(answeredQuestion);
            }
          }
        });

        // Sort by question order
        newAnsweredQuestions.sort(
          (a, b) => a.questionNumber - b.questionNumber
        );
        return newAnsweredQuestions;
      });
    }
  }, [answers, resolveData, resolveComplete]);

  // Adjust current question index when questions are filtered
  useEffect(() => {
    if (questions.length > 0 && currentQuestionIndex >= questions.length) {
      // If current index is beyond the filtered questions, go to the last question
      setCurrentQuestionIndex(Math.max(-1, questions.length - 1));
    }
  }, [questions.length, currentQuestionIndex]);

  // Show email question (21) when showEmailQuestionOnly is true
  useEffect(() => {
    if (showEmailQuestionOnly && resolveComplete && resolveResult && resolveData) {
      // Find the index of question 21 in the filtered questions array
      const emailQuestionIndex = questions.findIndex(([id]) => id === "21");
      if (emailQuestionIndex !== -1) {
        setCurrentQuestionIndex(emailQuestionIndex);
      }
    }
  }, [showEmailQuestionOnly, resolveComplete, resolveResult, resolveData, questions]);

  // Scroll to just below header when question changes
  useEffect(() => {
    // Header height: 145px on mobile, 80px on desktop (sm:h-[80px] h-[145px])
    const headerHeight = window.innerWidth >= 640 ? 80 : 145;
    window.scrollTo({ top: headerHeight, behavior: 'instant' });
  }, [currentQuestionIndex, questionId]);

  // Helper function to format answer for display
  const formatAnswerForDisplay = (answer: string | string[]): string => {
    if (Array.isArray(answer)) {
      return answer.join(", ");
    }
    return answer;
  };

  // Helper function to create answered question object
  const createAnsweredQuestion = (
    questionId: string,
    questionData: QuestionData,
    answer: string | string[],
    filteredQuestionIndex?: number
  ): AnsweredQuestion => {
    // Use filtered question index if provided, otherwise fall back to original order
    const questionNumber =
      filteredQuestionIndex !== undefined
        ? filteredQuestionIndex + 1
        : questionData.question_order;

    return {
      questionId,
      questionTitle: questionData.title,
      questionNumber,
      answer: formatAnswerForDisplay(answer),
      timestamp: new Date().toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      }),
      isCompleted: true,
    };
  };
  // Helper function to retry registration when email question is answered in showEmailQuestionOnly mode
  const retryEmailRegistration = async (emailValue: string) => {
    if (!resolveData) return false;
    
    try {
      const registrationResponse = await api.post("/v1/customer/simple_registration", {
        email: emailValue,
        has_marketing_email_consent: hasMarketingConsent,
        ...(resolveData.resolve_id && { resolve_id: resolveData.resolve_id }),
      }) as any;

      if (registrationResponse?.data?.login_data) {
        const loginData = registrationResponse.data.login_data;
        tokenManager.setTokens(
          loginData.access_token,
          loginData.refresh_token,
          loginData.token_type || "bearer"
        );
        localStorage.setItem("user", JSON.stringify(loginData.user_data));
        
        if (loginData.user_data?.role_code) {
          setCurrentRole(
            typeof loginData.user_data.role_code === "string"
              ? loginData.user_data.role_code.toLowerCase()
              : loginData.user_data.role_code
          );
        }

        if (loginData.redirect_path) {
          localStorage.setItem("redirect_path", loginData.redirect_path);
        }
        
        setIsRegistrationSuccess(true);
        // Registration succeeded - show result page
        saveShowResultPageOnly(true);
        saveShowEmailQuestionOnly(false);
        return true;
      } else {
        setIsRegistrationSuccess(true);
        saveShowResultPageOnly(true);
        saveShowEmailQuestionOnly(false);
        return true;
      }
    } catch (error) {
      if((error as any).status === 409) {
        setIsRegistrationSuccess(true);
        // Store the email for later use
        if (typeof emailValue === 'string') {
          setStoredEmail(emailValue);
        }
        // Status 409 - show result page
        saveShowResultPageOnly(true);
        saveShowEmailQuestionOnly(false);
        return true;
      } else {
        setIsRegistrationSuccess(false);
        // Registration failed - keep showing email question
        saveShowEmailQuestionOnly(true);
        saveShowResultPageOnly(false);
        return false;
      }
    }
  };

  // Helper function to update answered questions immediately
  const updateAnsweredQuestions = (
    questionId: string,
    answer: string | string[]
  ) => {
    if (!resolveData?.question_data[questionId]) return;

    const questionData = resolveData.question_data[questionId];

    // Only add to answered questions if the question should be shown based on rules
    if (!shouldShowQuestion(questionData, answers, resolveData.question_data)) {
      return;
    }

    // Create filtered questions array using current answers to get correct index
    const filteredQuestions = Object.entries(resolveData.question_data)
      .filter(([, qData]) =>
        shouldShowQuestion(qData, answers, resolveData.question_data)
      )
      .sort(([, a], [, b]) => a.question_order - b.question_order);

    // Find the filtered question index for this question
    const filteredQuestionIndex = filteredQuestions.findIndex(
      ([id]) => id === questionId
    );

    const answeredQuestion = createAnsweredQuestion(
      questionId,
      questionData,
      answer,
      filteredQuestionIndex
    );

    setAnsweredQuestions((prev) => {
      const existingIndex = prev.findIndex((q) => q.questionId === questionId);
      if (existingIndex >= 0) {
        // Update existing question - only update if the answer actually changed
        const existingQuestion = prev[existingIndex];
        if (existingQuestion.answer !== answeredQuestion.answer) {
          const updated = [...prev];
          updated[existingIndex] = answeredQuestion;
          return updated;
        }
        return prev; // No change needed
      } else {
        // Add new question
        return [...prev, answeredQuestion];
      }
    });
  };

  // Background save function - no loading states, no waiting
  const saveAnswerInBackground = async (
    questionIdentifier: string,
    answer: string | string[],
    isLastQuestion: boolean
  ) => {
    if (!resolveData || !resolveData.question_data[questionIdentifier]) return;

    // Type for safe messages from the API
    type ToastMessage = { message: string; success?: boolean };

    // Helper to normalize API response message(s) to ToastMessage[]
    const normalizeMessages = (msg: unknown): ToastMessage[] => {
      if (!msg) return [];
      if (Array.isArray(msg)) {
        // If it's already array, try to map it into {message:string}
        return msg
          .map((item) => {
            if (typeof item === "string") return { message: item };
            if (
              typeof item === "object" &&
              item !== null &&
              "message" in item &&
              typeof (item as any).message === "string"
            ) {
              return {
                message: (item as any).message,
                success: (item as any).success,
              };
            }
            return null;
          })
          .filter(Boolean) as ToastMessage[];
      }
      if (typeof msg === "string") {
        return [{ message: msg }];
      }
      if (
        typeof msg === "object" &&
        msg !== null &&
        "message" in msg &&
        typeof (msg as any).message === "string"
      ) {
        return [
          { message: (msg as any).message, success: (msg as any).success },
        ];
      }
      return [];
    };

    // Helper to show toasts for each array message
    const showToastsWithDelay = async (
      messages: ToastMessage[],
      isSuccess: boolean
    ) => {
      const delay = 400;
      for (let i = 0; i < messages.length; i++) {
        const messageItem = messages[i];
        await new Promise((resolve) =>
          setTimeout(resolve, i === 0 ? 0 : delay)
        );
        if (isSuccess) {
          if (messageItem.success !== false) {
            addToast(createSuccessToast("Success", messageItem.message));
          } else {
            addToast(createErrorToast("Error", messageItem.message));
          }
        } else {
          addToast(createErrorToast("Error", messageItem.message));
        }
      }
    };

    try {
      const questionData = resolveData.question_data[questionIdentifier];

      // Convert answer to the expected format based on input type
      let answerArray: QuestionAnswer[];

      if (
        questionData.input_type === "radio" ||
        questionData.input_type === "checkbox"
      ) {
        // For radio/checkbox, we need to find the key that matches the selected value
        const selectedAnswers = Array.isArray(answer) ? answer : [answer];
        const answerKeys = findMatchingOptionKey(
          selectedAnswers,
          questionData.options
        );

        // Convert to the expected format - save as keys
        answerArray = answerKeys.map((key) => ({ value: key }));
      } else {
        // For text, number, email, textarea - send the value directly
        const answerValues = Array.isArray(answer) ? answer : [answer];
        answerArray = answerValues.map((val) => ({ value: val }));
      }

      const saveRequest: SaveAnswerRequest = {
        resolve_id: resolveData.resolve_id,
        answers: [
          {
            answer: answerArray,
            question_identifier: questionIdentifier, // Convert string to number
            version: questionData.version,
          },
        ],
      };

      // Determine if this is the last question
      // const questionIds = Object.keys(resolveData.question_data);
      // const lastQuestionId = questionIds[questionIds.length - 1];
      // const isLastQuestion = questionIdentifier === lastQuestionId;

      if (isLastQuestion) {
        // For POST request (last question), create comprehensive save request with ALL answers
        try {
          // Create a comprehensive save request with ALL answers
          const allAnswers: AnswerRequest[] = [];

          // Add all existing answers from the current state
          Object.entries(resolveData.question_data).forEach(
            ([questionId, question]) => {
              const currentAnswer = answers[questionId];
              const hasCurrentAnswer = isValidAnswer(currentAnswer);

              // Process if we have a current answer OR if there's an original answer in the question data
              if (
                hasCurrentAnswer ||
                (question.answer && question.answer.length > 0)
              ) {
                // Use current answer if available, otherwise use original answer from question data
                const answerToUse = hasCurrentAnswer
                  ? currentAnswer
                  : question.answer.map((a) => a.value);

                // Convert answer to the expected format based on input type
                let answerArray: QuestionAnswer[];

                if (
                  question.input_type === "radio" ||
                  question.input_type === "checkbox"
                ) {
                  // For radio/checkbox, find the key that matches the selected value
                  const selectedAnswers = Array.isArray(answerToUse)
                    ? answerToUse
                    : [answerToUse];
                  const answerKeys = findMatchingOptionKey(
                    selectedAnswers,
                    question.options
                  );
                  answerArray = answerKeys.map((key) => ({ value: key }));
                } else {
                  // For text, number, email, textarea - send the value directly
                  const answerValues = Array.isArray(answerToUse)
                    ? answerToUse
                    : [answerToUse];
                  answerArray = answerValues.map((val) => ({ value: val }));
                }

                allAnswers.push({
                  answer: answerArray,
                  question_identifier: questionId,
                  version: question.version,
                });
              }
            }
          );

          let response: CompleteResolveResponse | null = null;

          // Only send POST if not already sent
          if (!isResolvePostSent) {
            const comprehensiveSaveRequest: SaveAnswerRequest = {
              resolve_id: resolveData.resolve_id,
              answers: allAnswers,
            };

            response = await api.post<CompleteResolveResponse>(
              "/v1/resolve",
              comprehensiveSaveRequest
            );
            setIsResolvePostSent(true);
          }

          // Call simple registration API if email question (21) was answered (works even if POST already sent)
          const emailAnswer = answers["21"];
          let registrationSuccess = true; // Default to true if no email question or user is authenticated
          
          if (emailAnswer && !isAuthenticated) {
            try {
              const registrationResponse = await api.post("/v1/customer/simple_registration", {
                email: Array.isArray(emailAnswer) ? emailAnswer[0] : emailAnswer,
                has_marketing_email_consent: hasMarketingConsent,
                ...(resolveData.resolve_id && { resolve_id: resolveData.resolve_id }),
              }) as any;
              // Console the status code of the registration response (if available)

              if (registrationResponse?.data?.login_data) {
                const loginData = registrationResponse.data.login_data;
                tokenManager.setTokens(
                  loginData.access_token,
                  loginData.refresh_token,
                  loginData.token_type || "bearer"
                );
                localStorage.setItem("user", JSON.stringify(loginData.user_data));
                
                // Store password state
                if (loginData.password_state) {
                  localStorage.setItem("password_state", loginData.password_state);
                }
                // Store case.id if present in response
                if (loginData.case?.id) {
                  sessionStorage.setItem("current_case_id", loginData.case.id);
                }
                
                if (loginData.user_data?.role_code) {
                  setCurrentRole(
                    typeof loginData.user_data.role_code === "string"
                      ? loginData.user_data.role_code.toLowerCase()
                      : loginData.user_data.role_code
                  );
                }

                if (loginData.redirect_path) {
                  localStorage.setItem("redirect_path", loginData.redirect_path);
                }
              } else {
                console.log("no data");
                console.log("no login");
              }

              // Push close_convert_lead event to GTM
              if (typeof window !== 'undefined' && window.dataLayer) {
                window.dataLayer.push({
                  event: 'close_convert_lead',
                  email: (Array.isArray(emailAnswer) ? emailAnswer[0] : emailAnswer) || '',
                  ...(resolveData.resolve_id ? { resolve_id: resolveData.resolve_id } : {}),
                });
              }

              registrationSuccess = true;
              setIsRegistrationSuccess(true);
              // toastManager.addToast(createSuccessToast("Success", "Registration completed successfully"));
              // clearResolveSession();
            } catch (error: any) {
              if (error?.status === 409) {
                // Parse the error response JSON from the error message
                let errorData: any = null;
                let errorMessage: string = "";
                try {
                  const match = error.message?.match(/\{.*\}$/);
                  if (match) {
                    const parsed = JSON.parse(match[0]);
                    errorData = parsed.data;
                    errorMessage = parsed.message || "Registration failed";
                  } else if (error?.data !== undefined) {
                    // Fallback: use error.data if it exists directly
                    errorData = error.data;
                    errorMessage = error.message || "Registration failed";
                  }
                } catch (parseError) {
                  console.error("Failed to parse error response:", parseError);
                  errorMessage = "Registration failed";
                }

                // Check if data is an array with resolve_id (first case)
                if (
                  Array.isArray(errorData) &&
                  errorData.length > 0 &&
                  errorData[0]?.resolve_id
                ) {
                  // Case 1: User exists with resolve_id
                  console.log("User exists with resolve_id:", errorData[0].resolve_id);
                  registrationSuccess = true;
                  setIsRegistrationSuccess(false);
                  // Store the email for later use
                  const emailValue = Array.isArray(emailAnswer) ? emailAnswer[0] : emailAnswer;
                  if (typeof emailValue === 'string') {
                    setStoredEmail(emailValue);
                  }
                } else {
                  // Case 2: Email assigned to different role (empty data array) or other 409 cases without resolve_id
                  console.log("Email already assigned to a different role or no resolve_id");
                  registrationSuccess = false;
                  setIsRegistrationSuccess(false);
                  // Show error toast when there's no resolve_id
                  toastManager.addToast(
                    createErrorToast("Registration Error", errorMessage || "Email already assigned to a different role")
                  );
                }
              } else {
                // Non-409 errors
                registrationSuccess = false;
                setIsRegistrationSuccess(false);
              }
            }
          } else {
            registrationSuccess = true;
            setIsRegistrationSuccess(true);
          }

          // Process response only if POST was sent in this call
          if (response && response.success && response.data) {

            // Update question_data with all the latest answers
            const updatedQuestionData = { ...resolveData.question_data };

            Object.entries(resolveData.question_data).forEach(
              ([questionId, question]) => {
                const currentAnswer = answers[questionId];
                const hasCurrentAnswer = isValidAnswer(currentAnswer);

                if (
                  hasCurrentAnswer ||
                  (question.answer && question.answer.length > 0)
                ) {
                  const answerToUse = hasCurrentAnswer
                    ? currentAnswer
                    : question.answer.map((a) => a.value);

                  // Convert answer to the expected format based on input type
                  let answerArray: QuestionAnswer[];

                  if (
                    question.input_type === "radio" ||
                    question.input_type === "checkbox"
                  ) {
                    const selectedAnswers = Array.isArray(answerToUse)
                      ? answerToUse
                      : [answerToUse];
                    const answerKeys = findMatchingOptionKey(
                      selectedAnswers,
                      question.options
                    );
                    answerArray = answerKeys.map((key) => ({ value: key }));
                  } else {
                    const answerValues = Array.isArray(answerToUse)
                      ? answerToUse
                      : [answerToUse];
                    answerArray = answerValues.map((val) => ({ value: val }));
                  }

                  // Update the question data with the answer
                  updatedQuestionData[questionId] = {
                    ...question,
                    answer: answerArray,
                  };
                }
              }
            );

            // Update resolve data with the completed status, result, and updated question_data
            const updatedResolveData = {
              ...resolveData,
              resolve_status: response.data.resolve_status,
              result: response.data.result,
              lawyers: response.data.lawyers,
              question_data: updatedQuestionData,
            };

            setResolveData(updatedResolveData);
            setResolveResult(response.data.result);

            // Extract and set caseId from the response
            const responseData = response.data as any;
            if (responseData.case && responseData.case.id) {
              setCaseId(responseData.case.id);
            }

            // Save updated data to session storage
            saveResolveToSession(updatedResolveData);

            // Show all success messages from response.message[] with toasts
            const messages = normalizeMessages((response as any).message);
            if (messages.length > 0) {
              setShowCompletionToasts(true);
              await showToastsWithDelay(messages, true);
              // Brief pause after toasts so the last one is visible before completion screen
              await new Promise((resolve) => setTimeout(resolve, 1000));
              setShowCompletionToasts(false);
            } else {
              console.warn("No messages found in response.message");
            }
            // Set resolve complete AFTER toasts are shown
            setResolveComplete(true);
            
            // Set showEmailQuestionOnly and showResultPageOnly based on registration status and resolve result
            if (response.data.result) {
              if (registrationSuccess) {
                // Registration succeeded or status 409 - show result page
                saveShowResultPageOnly(true);
                saveShowEmailQuestionOnly(false);
              } else {
                // Registration failed (other than 409) - show email question only
                saveShowEmailQuestionOnly(true);
                saveShowResultPageOnly(false);
              }
            }
            
            // clearResolveSession();
            // Set isCompleting to false AFTER resolveComplete is set, so loading card stays visible
            setIsCompleting(false);
          } else if (response) {
            // Only process error if POST was sent in this call
            setIsCompleting(false);
            const messages = normalizeMessages((response as any).message);
            if (messages.length > 0) {
              await showToastsWithDelay(messages, false);
            }
          } else {
            // POST was already sent, just stop completing
            setIsCompleting(false);
          }
        } catch (err: any) {
          setIsCompleting(false);
          // Try to extract meaningful message from err.message if it contains JSON
          let errorMessage = "Failed to complete your resolve. Please try again.";
          if (err?.message && typeof err.message === "string") {
            const match = err.message.match(/{.*}/);
            if (match) {
              try {
                const errObj = JSON.parse(match[0]);
                if (errObj && errObj.message) {
                  errorMessage = errObj.message;
                }
              } catch {
                // Fallback to full string if JSON parse fails
                errorMessage = err.message;
              }
            } else {
              errorMessage = err.message;
            }
          }
          // toastManager.addToast(createErrorToast("Error", errorMessage));
          // Show a fallback generic toast
          // addToast(
          //   createErrorToast(
          //     "Completion Failed",
          //     err?.message ||
          //       "Failed to complete your resolve. Please try again."
          //   )
          // );
        }
      } else {
        // For PATCH request (not last question), fire and forget
        const savePromise = api.patch<SaveAnswerResponse>(
          "/v1/resolve",
          saveRequest
        );

        savePromise
          .then((response) => {
            if (!response.success) {
              const messages = normalizeMessages((response as any).message);
              if (messages.length > 0) {
                showToastsWithDelay(messages, false);
              }
            } else if ((response as any).message) {
              const messages = normalizeMessages((response as any).message);
              if (messages.length > 0) {
                // Don't display the success toast for each question success
                // showToastsWithDelay(messages, true);
              }
            }
          })
          .catch((err) => {
            // addToast(
            //   createErrorToast(
            //     "Save Failed",
            //     err?.message || "Failed to save your answer. Please try again."
            //   )
            // );
          });
      }
    } catch (err: any) {
      console.warn("Failed to save answer:", err);
      addToast(
        createErrorToast(
          "Save Failed",
          err?.message || "Failed to save your answer. Please try again."
        )
      );
    }
  };
  // Handle navigation from sidebar
  const handleQuestionNavigation = (
    questionId: string,
    questionNumber: number
  ) => {
    // Find the index of the question in the questions array
    const questionIndex = questions.findIndex(([id]) => id === questionId);

    if (questionIndex !== -1) {
      setCurrentQuestionIndex(questionIndex);
    } else {
      console.warn(`Question with ID ${questionId} not found`);
    }
  };

  const handleNext = async () => {
    if (!questionData || !currentQuestion) return;
    const currentAnswer = answers[questionId];
    // Validate required fields
    if (questionData.required && !isValidAnswer(currentAnswer)) {
      return; // Don't proceed if required field is empty
    }
    
    // Special handling: if in showEmailQuestionOnly mode and answering question 21, retry registration
    if (showEmailQuestionOnly && questionId === "21" && isValidAnswer(currentAnswer) && !isAuthenticated) {
      const emailValue = Array.isArray(currentAnswer) ? currentAnswer[0] : currentAnswer;
      if (typeof emailValue === "string") {
        // Retry registration
        await retryEmailRegistration(emailValue);
        // Don't proceed to next question - state changes will trigger re-render
        return;
      }
    }
    
    // Check if this is the last question (completion)
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    if (isLastQuestion) {
      setIsCompleting(true);
    }
    // Update answered questions immediately for UI feedback
    if (isValidAnswer(currentAnswer)) {
      updateAnsweredQuestions(questionId, currentAnswer);
    } else {
      // If skipping (no valid answer), remove from answered questions if it was previously answered
      setAnsweredQuestions((prev) =>
        prev.filter((q) => q.questionId !== questionId)
      );
    }
    // Save current answer in background (don't wait)
    saveAnswerInBackground(questionId, currentAnswer || "", isLastQuestion);

    // Move to next question immediately (only if not the last question)
    if (!isLastQuestion) {
      setCurrentQuestionIndex((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > -1) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const handleInputChange = (value: string | string[]) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));

    // Immediately update userName and partnerName when questions 1 or 2 are answered
    if (questionId === "1" && typeof value === "string" && value.trim()) {
      setUserName(value.trim());
    } else if (
      questionId === "2" &&
      typeof value === "string" &&
      value.trim()
    ) {
      setPartnerName(value.trim());
    }

    // Update answered questions immediately when input changes (for real-time updates)
    if (isValidAnswer(value)) {
      updateAnsweredQuestions(questionId, value);
    } else {
      // If answer becomes invalid/empty, remove from answered questions list
      setAnsweredQuestions((prev) =>
        prev.filter((q) => q.questionId !== questionId)
      );
    }
  };

  // Helper function to find matching option key for radio/checkbox answers
  const findMatchingOptionKey = (
    selectedAnswers: string[],
    options: QuestionOption[]
  ): string[] => {
    const answerKeys: string[] = [];

    options.forEach((optionGroup) => {
      Object.entries(optionGroup).forEach(([key, optionData]) => {
        // Check both original value and placeholder-replaced value
        const originalValue = optionData.value;
        const replacedValue = replacePlaceholders(
          originalValue,
          userName,
          partnerName
        );

        if (
          selectedAnswers.includes(originalValue) ||
          selectedAnswers.includes(replacedValue)
        ) {
          answerKeys.push(key);
        }
      });
    });

    return answerKeys;
  };

  // Dynamic component renderer based on version
  const renderQuestionCard = () => {
    if (!questionData) return null;

    // Get the appropriate component based on version
    const version = questionData.version || "1";
    const ResolveQuestionCardComponent = getResolveQuestionCard(version);

    // Create a modified questionData with replaced placeholders
    const modifiedQuestionData = {
      ...questionData,
      title: replacePlaceholders(questionData.title, userName, partnerName),
      description: replacePlaceholders(
        questionData.description,
        userName,
        partnerName
      ),
      question: replacePlaceholders(
        questionData.question,
        userName,
        partnerName
      ),
      options: questionData.options.map((optionGroup) => {
        const modifiedGroup: QuestionOption = {};
        Object.entries(optionGroup).forEach(([key, option]) => {
          modifiedGroup[key] = {
            ...option,
            value: replacePlaceholders(option.value, userName, partnerName),
            tooltip: option.tooltip
              ? replacePlaceholders(option.tooltip, userName, partnerName)
              : option.tooltip,
            additional_description: option.additional_description
              ? replacePlaceholders(
                  option.additional_description,
                  userName,
                  partnerName
                )
              : option.additional_description,
          };
        });
        return modifiedGroup;
      }),
    };

    return (
      <ResolveQuestionCardComponent
        questionData={modifiedQuestionData}
        questionId={questionId}
        currentAnswer={answers[questionId] || ""}
        onInputChange={handleInputChange}
        onNext={handleNext}
        canProceed={
          !questionData.required || isValidAnswer(answers[questionId])
        }
        currentQuestionIndex={currentQuestionIndex}
        totalQuestions={totalQuestions}
        currentQuestionStepNumber={currentQuestionStepNumber}
        allQuestionData={resolveData?.question_data ?? {}}
        isCompleting={isCompleting}
        onPrevious={handlePrevious}
        resolveId={resolveId}
        onMarketingConsentChange={setHasMarketingConsent}
      />
    );
  };

  if (loading) {
    return (
      <ResolveLayout resolveId={resolveId} caseId={caseId}>
        <div className="flex justify-center items-center w-full min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-novaPrimary-600 mx-auto mb-4"></div>
            <p className="text-novaNeutral-600">Loading ...</p>
          </div>
        </div>
      </ResolveLayout>
    );
  }
//   const headerActions = (
//     <div className="flex items-center">
//       {(currentRole === "Customer" || currentRole === "Guest") && (
//         <Link href="/resolve-new">
//           <FormButton
//             variant="custom"
//             size="sm"
//             className="bg-novaPrimary-500 hover:bg-novaPrimary-600 text-white flex items-center px-2 py-1 sm:px-3 sm:py-2 text-xs sm:text-sm whitespace-nowrap min-w-0"
//           >
//             <i className="fas fa-plus mr-1 sm:mr-2"></i>
//             <span>
//               <span className="sm:hidden">New</span>
//               <span className="hidden sm:inline">New Resolve</span>
//             </span>
//           </FormButton>
//         </Link>
//       )}
//     </div>
//   );

  // Merged completion and question screens, rendering conditionally
  return (
    // <Layout 
    //   headerActions={headerActions}
    //   showBackButton={true}
    //   backButtonLabel="Back to Sessions"
    //   onBackClick={() => navigate("/resolve-dashboard")}
    // >
      <ResolveLayout
      onPrevious={handlePrevious}
      isPreviousDisabled={currentQuestionIndex === -1 || showEmailQuestionOnly || resolveComplete}
      totalQuestions={totalQuestions}
      currentQuestionIndex={currentQuestionIndex}
      currentQuestionStepNumber={currentQuestionStepNumber}
      answeredQuestionsCount={answeredQuestions.length}
      isResolveComplete={resolveComplete}
      showLawyerShopWindow={Boolean(resolveComplete && resolveResult && showResultPageOnly)}
      // lawyerProfiles={lawyerProfiles}
      lawyerProfiles={resolveData?.lawyers}
      resolveId={resolveId}
      caseId={caseId}
      storedEmail={storedEmail}
      resolveResult={resolveResult}
    >
      {/* Toast Container - show during questions, during completion toasts, or when toasts exist (so result page can show completion toasts) */}
      {(toasts.length > 0 || !resolveComplete || showCompletionToasts) && (
        <ToastContainer alerts={toasts} onDismiss={removeToast} />
      )}

      <div
        className={
          resolveResult && showResultPageOnly
            ? undefined
            : "sm:min-h-[calc(100vh-80px)] min-h-[calc(100vh-145px)]"
        }
      >
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Fixed Header with Progress Bar */}
          {/* <div className="bg-white border-b border-novaNeutral-200 px-4 sm:px-6 py-1.5 sm:py-4 flex-shrink-0">
            <div className="flex items-center justify-between mb-1 sm:mb-2">
              <div className="flex items-center space-x-1">
                {resolveComplete && resolveResult ? (
                  <h1 className="text-sm sm:text-md font-medium text-novaNeutral-900">
                    Resolve Completed
                  </h1>
                ) : (
                  <h1 className="text-sm sm:text-md font-semibold text-novaNeutral-900">
                    Question {currentQuestionStepNumber}/{totalQuestions}
                  </h1>
                )}
              </div>

              <div className="flex items-center space-x-2 sm:space-x-4">
                {resolveComplete && resolveResult ? (
                  <span className="text-xs sm:text-sm font-medium text-novaNeutral-700">
                    100%
                  </span>
                ) : (
                  <span className="text-xs sm:text-sm font-medium text-novaNeutral-700">
                    {totalQuestions > 0
                      ? Math.round(
                          (answeredQuestions.length / totalQuestions) * 100
                        )
                      : 0}
                    %
                  </span>
                )}
                <button
                  onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                  className="xl:hidden rounded-md text-novaNeutral-600 hover:text-novaNeutral-900 hover:bg-novaNeutral-100 focus:outline-none focus:ring-2 focus:ring-novaPrimary-500"
                  aria-label="Toggle sidebar"
                >
                  {!isSidebarOpen && <i className="fas fa-bars"></i>}
                </button>
              </div>
            </div>

            <div className="w-full">
              {resolveComplete && resolveResult ? (
                <ProgressBar
                  current={totalQuestions}
                  total={totalQuestions}
                  showPercentage={false}
                  showLabel={false}
                  className="mb-0"
                  barClassName="bg-novaSuccess-600"
                  height="md"
                />
              ) : (
                <ProgressBar
                  current={answeredQuestions.length}
                  total={totalQuestions}
                  showPercentage={false}
                  showLabel={false}
                  className="mb-0"
                  barClassName="bg-novaPrimary-600"
                  height="md"
                />
              )}
            </div>
          </div> */}

          <div className="">
            <div className="p-4 sm:p-8 md:p-10">
              <div className="flex flex-col">
                {resolveComplete && resolveResult && showResultPageOnly ? (
                  <div className=" flex flex-col">
                    {/* <ResolveSummaryCard
                      summary={resolveResult.summary}
                      resolveId={resolveId}
                      caseId={caseId || ""}
                      lawyer_profiles={
                        resolveData?.lawyers?.map((lawyer: any) => ({
                          lawyer_name: `${lawyer.first_name} ${lawyer.last_name}`,
                          lawyer_photo_url:
                            lawyer.photo_url === "None" || !lawyer.photo_url
                              ? ""
                              : lawyer.photo_url,
                          experience: lawyer.experience || "",
                          about: lawyer.about || "",
                          city: lawyer.city || "",
                          county: lawyer.county || "",
                          country: lawyer.country || "",
                          accredited_specialisations:
                            lawyer.accredited_specialisations || "",
                          expert_types: lawyer.expert_types || [],
                          relationship_types: lawyer.relationship_types || [],
                          matter_types: lawyer.matter_types || [],
                          hourly_rate: lawyer.hourly_rate,
                          charge_first_consultation:
                            lawyer.charge_first_consultation,
                          lawfirms: lawyer.lawfirms || [],
                        })) || []
                      }
                    /> */}
                    <ResolveBookingCard resolveId={resolveId} summary={resolveResult.summary} title={resolveResult.title} caseId={caseId || ""} storedEmail={storedEmail} userName={userName} partnerName={partnerName} affordability={resolveResult.affordability} />
                  </div>
                ) : resolveComplete && resolveResult && showEmailQuestionOnly ? (
                  <div className="flex-1 flex flex-col">
                    {renderQuestionCard()}
                  </div>
                ) : currentQuestionIndex === -1 ? (
                  <div className="flex-1 flex flex-col">
                    <WelcomeCard
                      totalQuestions={totalQuestions}
                      onNext={() => setCurrentQuestionIndex(0)}
                    />
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col">
                    {renderQuestionCard()}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        {/* <div
          className={`
            fixed inset-y-0 right-0 w-80 xl:w-80 bg-white shadow-xl transform transition-transform duration-300 ease-in-out
            z-50 xl:z-auto
            xl:relative xl:translate-x-0 xl:flex-shrink-0 xl:shadow-none xl:h-full xl:overflow-hidden
            ${isSidebarOpen ? "translate-x-0" : "translate-x-full"}
          `}
        >
          <div className="h-full overflow-y-auto">
            <SummarySidebar
              answeredQuestions={answeredQuestions}
              totalQuestions={totalQuestions}
              currentQuestionIndex={currentQuestionIndex}
              onQuestionClick={handleQuestionNavigation}
              userName={userName}
              partnerName={partnerName}
              isCompleted={resolveComplete}
            />
          </div>
        </div> */}

        {/* Mobile Overlay */}
        {isSidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 xl:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
        )}
      </div>
    </ResolveLayout>
  );
}
