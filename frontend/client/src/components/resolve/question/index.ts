// Dynamic version loader for ResolveQuestionCard
import { ResolveQuestionCard as ResolveQuestionCardV1 } from './v1/ResolveQuestionCard';
import { ResolveQuestionCard as ResolveQuestionCardNew } from './v1/ResolveQuestionCardNew';
// Export the v1 component
export { ResolveQuestionCardV1 };

// Function to get the appropriate ResolveQuestionCard version
export const getResolveQuestionCard = (version: string) => {
  switch (version) {
    // case '1':
    //   return ResolveQuestionCardV1;
    case '1':
      return ResolveQuestionCardNew;
    // Future versions can be added here
    // case '2':
    //   return require('./v2/ResolveQuestionCard').ResolveQuestionCardV2;
    default:
      // Fallback to v1 if version is not recognized
      return ResolveQuestionCardV1;
  }
};

// Default export for backward compatibility
export { ResolveQuestionCardV1 as ResolveQuestionCard };
