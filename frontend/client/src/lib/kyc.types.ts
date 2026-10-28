// KYC Form Types

export interface KycQuestion {
  value: string;
  key?: string;
  [key: string]: any;
}

export interface KycRule {
  identifier: string;
  operator: string;
  value: string | string[];
}

export interface KycAnswer {
  value: string;
}

export interface KycFormFieldQuestion {
  question_type: string;
  variant: string;
  title: string;
  description: string;
  placeholder: string;
  question: string;
  options: KycQuestion[];
  required: boolean;
  input_type: string;
  min_length: number | null;
  max_length: number | null;
  rules: KycRule[];
  question_order: number;
  answer_type: string;
  answer: KycAnswer[];
}

export interface KycFormFields {
  questions: Record<string, KycFormFieldQuestion>;
}

export interface KycFormData {
  max_length: number;
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
