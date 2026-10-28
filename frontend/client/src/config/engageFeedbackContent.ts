export type QuestionType = "radio" | "dropdown" | "checkbox";

export interface OptionEntry {
  key: number;
  label: string;
}

export interface QuestionDef {
  id: string;
  type: QuestionType;
  title: string;
  subtitle?: string;
  options: OptionEntry[];
  showSubQuestionsWhenNotKey?: number;
  showTextFieldWhenKey?: number;
  textFieldMaxLength?: number;
  showImprovementTextArea?: boolean;
  improvementPromptPositive?: string;
  improvementPromptNegative?: string;
}

export interface EngageFeedbackContent {
  introParagraphs: string[];
  questions: QuestionDef[];
}

export const engageFeedbackContent: EngageFeedbackContent = {
  introParagraphs: [
    "Thank you for completing your Nova Engage guided pathway. Your submission has been automatically emailed to your family law specialist.",
    "We have emailed you a password protected PDF copy of your submission. You can unlock your PDF with the memorable word we asked you for.",
    "Finally, we would be really grateful if you could complete our 60 second feedback form to allow us to make Nova Engage even better.",
    "Thank you!",
  ],
  questions: [
    {
      id: "time_value_feedback",
      type: "radio",
      title: "How do you feel about the length of time it has taken you to complete Nova Engage?",
      options: [
        { key: 1, label: "It has been a valuable use of my time" },
        { key: 2, label: "It has been an acceptable use of my time" },
        { key: 3, label: "It has been a waste of my time" },
      ],
    },
    {
      id: "completion_time",
      type: "dropdown",
      title: "How long did it take you overall to complete your Nova Engage submission?",
      options: [
        { key: 1, label: "30 mins" },
        { key: 2, label: "45 mins" },
        { key: 3, label: "1 hour" },
        { key: 4, label: "1 hour 15 mins" },
        { key: 5, label: "1 hour 30 mins" },
        { key: 6, label: "2 hours" },
        { key: 7, label: "2 hours 30 mins" },
        { key: 8, label: "3 hours" },
        { key: 9, label: "More than 3 hours" },
      ],
    },
    {
      id: "session_count",
      type: "dropdown",
      title: "How many sessions did it take you to complete your Nova Engage submission?",
      options: [
        { key: 1, label: "1" },
        { key: 2, label: "2" },
        { key: 3, label: "3" },
        { key: 4, label: "4" },
        { key: 5, label: "5" },
        { key: 6, label: "6" },
        { key: 7, label: "7" },
        { key: 8, label: "8" },
        { key: 9, label: "9" },
        { key: 10, label: "10" },
      ],
    },
    {
      id: "help_level",
      type: "radio",
      title: "Which of the following best describes your use of Nova Engage?",
      options: [
        { key: 1, label: "I completed it without any help" },
        { key: 2, label: "I needed a small amount of help to complete Nova Engage" },
        { key: 3, label: "I needed a significant amount of help to complete Nova Engage" },
        { key: 4, label: "I had somebody else complete Nova Engage on my behalf." },
      ],
      showSubQuestionsWhenNotKey: 1,
    },
    {
      id: "helper_type",
      type: "checkbox",
      title: "Who helped you with Nova Engage?",
      options: [
        { key: 1, label: "A relative" },
        { key: 2, label: "A friend or work colleague" },
        { key: 3, label: "A court-appointed Litigation Friend" },
        { key: 4, label: "A McKenzie friend" },
        { key: 5, label: "An advice centre worker or volunteer" },
        { key: 6, label: "The technical support helpline at Family Law Lab" },
      ],
    },
    {
      id: "help_reason",
      type: "checkbox",
      title: "Would you be willing to tell us why you needed help completing Nova Engage?",
      subtitle: "Select any that apply. This information is completely anonymous – we cannot identify you.",
      options: [
        { key: 1, label: "A problem with internet accessibility" },
        { key: 2, label: "A problem with my device" },
        { key: 3, label: "I didn't understand the questions or the information provided" },
        { key: 4, label: "Physical impairment" },
        { key: 5, label: "Mental health challenges" },
        { key: 6, label: "A short term or long-standing illness" },
        { key: 7, label: "Other" },
      ],
    },
    {
      id: "preparedness_level",
      type: "radio",
      title: "Having used Nova Engage, how prepared do you feel for your legal consultation?",
      options: [
        { key: 1, label: "Highly prepared" },
        { key: 2, label: "Very prepared" },
        { key: 3, label: "Prepared" },
        { key: 4, label: "Fairly prepared" },
        { key: 5, label: "No difference" },
      ],
    },
    {
      id: "age_range",
      type: "dropdown",
      title: "Which age range do you fall into?",
      options: [
        { key: 1, label: "18 to 24" },
        { key: 2, label: "25 to 34" },
        { key: 3, label: "35 to 44" },
        { key: 4, label: "45 to 54" },
        { key: 5, label: "55 to 64" },
        { key: 6, label: "65 to 74" },
        { key: 7, label: "75+" },
      ],
    },
    {
      id: "gender",
      type: "radio",
      title: "What is your gender?",
      options: [
        { key: 1, label: "Female" },
        { key: 2, label: "Male" },
        { key: 3, label: "I'd rather not say" },
        { key: 4, label: "Other" },
      ],
      showTextFieldWhenKey: 4,
      textFieldMaxLength: 100,
    },
    {
      id: "overall_experience",
      type: "radio",
      title: "How would you rate your overall experience of using Nova Engage?",
      options: [
        { key: 1, label: "Highly positive" },
        { key: 2, label: "Positive" },
        { key: 3, label: "Satisfactory" },
        { key: 4, label: "Unsatisfactory" },
        { key: 5, label: "Poor" },
      ],
      showImprovementTextArea: true,
      improvementPromptPositive: "Thanks. Is there something we could do to make Nova Engage better?",
      improvementPromptNegative: "Sorry to hear that. What could we have done to make Nova Engage better?",
      textFieldMaxLength: 500,
    },
    {
      id: "recommendation_score",
      type: "dropdown",
      title: "On a scale of 1 to 10 how likely you recommend Nova Engage to a friend with family law issues?",
      subtitle: "1 – least likely, 10 – most likely",
      options: [
        { key: 10, label: "10" },
        { key: 9, label: "9" },
        { key: 8, label: "8" },
        { key: 7, label: "7" },
        { key: 6, label: "6" },
        { key: 5, label: "5" },
        { key: 4, label: "4" },
        { key: 3, label: "3" },
        { key: 2, label: "2" },
        { key: 1, label: "1" },
        
      ],
    },
  ],
};
