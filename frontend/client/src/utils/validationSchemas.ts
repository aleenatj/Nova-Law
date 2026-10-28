import { FormValidationSchema, PATTERNS } from "./formValidator";

// Signup Form Validation Schema
export const signupValidationSchema: FormValidationSchema = {
  firstName: {
    required: true,
    minLength: 1,
    maxLength: 50,
  },
  lastName: {
    required: true,
    minLength: 1,
    maxLength: 50,
  },
  email: {
    required: true,
    pattern: PATTERNS.EMAIL,
  },
  phone: {
    required: false,
    pattern: PATTERNS.PHONE,
  },
  password: {
    required: true,
    minLength: 8,
    maxLength: 64,
    pattern: PATTERNS.PASSWORD,
  },
  confirmPassword: {
    required: true,
    custom: (value: string) => {
      // This will be handled by cross-field validation
      return null;
    },
  },
};

// Sign In Form Validation Schema
export const signInValidationSchema: FormValidationSchema = {
  username: {
    required: true,
    pattern: PATTERNS.EMAIL,
  },
  password: {
    required: true,
    minLength: 8, // More lenient for sign in
  },
};