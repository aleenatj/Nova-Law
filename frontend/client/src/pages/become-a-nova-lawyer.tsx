import React, { useState, useMemo, useEffect, useRef } from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";
import { createErrorToast, createSuccessToast, FormButton, renderHtmlContent, toastManager } from "@/utils";
import { LawyerSignupQuestionCard } from "@/components/lawyer-signup/LawyerSignupQuestionCard";
import GlobalModalWrapper from "@/components/modal/GlobalModalWrapper";
import { lawyerSignupConfig } from "@/config/lawyer-signup-config";
import accountSetupBackground from "@/assets/landingpage/accountsetupbackground.webp";
import { api } from "@/lib/api";
import "@/styles/landingpage.css";
import Section1 from "@/components/lawyer-landing-page/section1";
import Section2 from "@/components/lawyer-landing-page/section2";
import Section3 from "@/components/lawyer-landing-page/section3";
import Section4 from "@/components/lawyer-landing-page/section4";
import Section5 from "@/components/lawyer-landing-page/section5";
import Section6 from "@/components/lawyer-landing-page/section6";
// Use imported config
const formConfig = lawyerSignupConfig;

// Why join Nova list
const whyJoinNovaList = [
  "Nova helps family lawyers work more effectively while attracting clients who are ready for a constructive process.",
  "Most clients arrive overwhelmed. Nova changes that.",
  "Our platform guides them step by step before they meet you – gathering information, and helping them understand what to expect. You will welcome clients who are clearer, more prepared, and more able to engage meaningfully with your skill-sets.",
  "Nova also filters for intent. People who come through our platform want resolution, not escalation. That means fewer firefights and more cases where your expertise shapes the outcome.",
  "We're building a modern ecosystem around family law – simple, ethical, and human-centred. If that resonates with the way you practise, we'd love to collaborate."
];

// Benefits list for lawyers
const benefitsList = [
  "Work with clients who are ready for advice and solutions.",
  "Nova attracts people who want clarity and constructive progress, not conflict for its own sake.",
  "Better-prepared clients are more open to well-crafted advice.",
  "Better-prepared lawyers are more likely to convert clients.",
  "A steady flow of high-quality cases matched with your skill-sets.",
  "Nova brings you clients who are ready to instruct and already engaged with the benefits of seeing a regulated family lawyer.",
  "We prioritise fairness, transparency, and reducing unnecessary conflict – values shared by the best family lawyers.",
  "Nova's AI tools streamline the early stages, leaving the legal judgement and advice where it belongs - with you.",
  "You didn't train to be a data collector: get back to the role you've worked hard for, the trusted legal adviser."
];

// FAQ for sceptical lawyers
const scepticalLawyerFaqs = [
  {
    question: "Is Nova trying to replace lawyers?",
    answer: "Absolutely not. The human touch remains the gold standard. Nova supports lawyers by preparing clients, reducing admin, and improving early understanding. Legal advice and strategy remains entirely with you."
  },
  {
    question: "Will I get good-quality cases?",
    answer: "Yes. Nova's platform identifies intent and readiness, so the clients reaching you want a clear path forward and are prepared to follow professional guidance."
  },
  {
    question: "How much admin does Nova actually remove?",
    answer: "A significant amount. Clients come to you with structured information, early clarity, and a realistic picture of the process, which saves time in the first meeting and beyond."
  },
  {
    question: "Do I lose control of the client relationship?",
    answer: "Not at all. Nova simply prepares clients so that when they reach you, the relationship begins in a calmer, more productive place."
  },
  {
    question: "What does the partnership involve?",
    answer: "You set your rates and work on your own terms. Nova introduces clients, supports the early stages, and provides tools that help you deliver an exceptional client experience."
  }
];

// Generic Accordion Item Component for Sections
type SectionAccordionItemProps = {
  title: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
};

const SectionAccordionItem: React.FC<SectionAccordionItemProps> = ({
  title,
  isOpen,
  onToggle,
  children,
}) => {
  const contentRef = React.useRef<HTMLDivElement>(null);
  const contentHeight = contentRef.current?.scrollHeight ?? 0;

  return (
    <div className="border-b border-novaNeutral-200 py-4 last:border-b-0">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between text-left text-novaNeutral-900 hover:text-novaPrimary-600 transition-colors"
        aria-expanded={isOpen}
      >
        <span className="text-lg sm:text-xl font-semibold max-w-[85%] pr-4">
          {title}
        </span>
        <i
          className={`fa-solid ${
            isOpen ? "fa-minus" : "fa-plus"
          } text-base text-novaNeutral-600 flex-shrink-0 transition-transform duration-300 ${
            isOpen ? "rotate-180" : ""
          }`}
          aria-hidden="true"
        />
      </button>
      <div
        ref={contentRef}
        className="overflow-hidden transition-all duration-300 ease-in-out"
        style={{
          maxHeight: isOpen ? `${contentHeight}px` : "0px",
          opacity: isOpen ? 1 : 0,
          marginTop: isOpen ? "12px" : "0px",
        }}
      >
        <div className="text-base text-novaNeutral-600 leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
};

const BecomeNovaLawyerPage: React.FC = () => {
  const [openSectionIndex, setOpenSectionIndex] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Utility function to normalize text to key format (spaces to underscores)
  const normalizeToKey = (text: string): string => {
    return text.replace(/\s+/g, '_');
  };

  // Check if a field should be shown based on showIf conditions
  const shouldShowField = (field: any): boolean => {
    if (!field.showIf) return true;
    
    const { field: parentFieldId, values, value, contains } = field.showIf;
    const parentValue = formData[parentFieldId];
    
    // Helper to normalize and compare values
    const matchesValue = (pv: any, checkValue: string): boolean => {
      const normalizedPv = normalizeToKey(String(pv || ""));
      const normalizedCheck = normalizeToKey(checkValue);
      return normalizedPv === normalizedCheck || String(pv || "") === checkValue;
    };
    
    if (values && Array.isArray(parentValue)) {
      return values.some((v: string) => parentValue.some((pv: any) => matchesValue(pv, v)));
    }
    if (values) {
      return values.some((v: string) => matchesValue(parentValue, v));
    }
    if (value !== undefined) {
      return matchesValue(parentValue, String(value));
    }
    if (contains) {
      if (Array.isArray(parentValue)) {
        return parentValue.some((pv: any) => matchesValue(pv, contains));
      }
      return matchesValue(parentValue, contains);
    }
    return true;
  };

  // Get visible sections (sections that have at least one visible field)
  const visibleSections = useMemo(() => {
    return formConfig.sections
      .map((section, index) => ({ section, originalIndex: index }))
      .filter(({ section }) => {
        // Check if section has at least one visible non-HTML field
        return section.fields.some(
          (field: any) => field.type !== "html" && shouldShowField(field)
        );
      });
  }, [formData]);

  const handleSectionToggle = (index: number) => {
    setOpenSectionIndex((prev) => (prev === index ? null : index));
  };

  const handleFieldChange = (fieldId: number | string, value: any) => {
    setFormData((prev) => ({ ...prev, [fieldId]: value }));
  };

  const handleNext = () => {
    if (currentSectionIndex < visibleSections.length - 1) {
      setCurrentSectionIndex((prev) => prev + 1);
    } else {
      // Handle form submission
      handleFormSubmit();
    }
  };

  const handlePrevious = () => {
    if (currentSectionIndex > 0) {
      setCurrentSectionIndex((prev) => prev - 1);
    }
  };

  // Scroll to top of form when section changes (same as KYC form)
  useEffect(() => {
    scrollContainerRef.current?.scrollTo({ top: 0, behavior: "instant" });
  }, [currentSectionIndex]);

  // Adjust currentSectionIndex if it's out of bounds after sections become hidden
  useEffect(() => {
    if (visibleSections.length > 0 && currentSectionIndex >= visibleSections.length) {
      setCurrentSectionIndex(Math.max(0, visibleSections.length - 1));
    }
  }, [visibleSections.length, currentSectionIndex]);

  const handleStartForm = () => {
    setShowForm(true);
    setCurrentSectionIndex(0);
    setFormData({});
    setIsSubmitted(false);
    setIsSubmitting(false);
  };

  const handleGetStartedClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    handleStartForm();
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setCurrentSectionIndex(0);
    setFormData({});
    setIsSubmitted(false);
    setIsSubmitting(false);
  };

  // Function to normalize answer values (lowercase, spaces to underscores)
  const normalizeAnswer = (value: any): any => {
    if (value === null || value === undefined || value === "") {
      return value;
    }
    
    // Handle File objects
    if (value instanceof File) {
      return value.name; // Return filename as string
    }
    
    // Handle arrays
    if (Array.isArray(value)) {
      return value.map(item => {
        if (typeof item === "string") {
          return item.toLowerCase().replace(/\s+/g, '_');
        }
        return item;
      });
    }
    
    // Handle objects (like name, address)
    if (typeof value === "object" && !(value instanceof File)) {
      const normalized: Record<string, any> = {};
      Object.keys(value).forEach(key => {
        normalized[key] = normalizeAnswer(value[key]);
      });
      return normalized;
    }
    
    // Handle strings
    if (typeof value === "string") {
      return value.toLowerCase().replace(/\s+/g, '_');
    }
    
    // Handle numbers and other types
    return value;
  };

  // Transform form data to API format matching the schema
  const transformFormDataToApiFormat = () => {
    const get = (fieldId: number) => formData[fieldId];
    const hasValue = (value: any) => value !== null && value !== undefined && value !== "";
    
    // Helper to match client type (handles normalized values)
    const matchesClientType = (value: string, target: string) => {
      return value === target || 
             value.toLowerCase().replace(/\s+/g, '_') === target.toLowerCase().replace(/\s+/g, '_');
    };

    const name = get(1);
    const address = get(34);
    const professionalStatus = get(23);
    const otherProfessionalStatus = get(3);
    const clientTypes = get(27);
    const marriedCouplesAreas = get(9);
    const cohabiteesAreas = get(29);

    return {
      // Required string fields
      first_name: name?.firstName || "",
      last_name: name?.lastName || "",
      email: get(20) || "",
      phone: get(21) || "",
      work_status: get(39) || "",
      city: address?.city || "",
      post_code: address?.postcode || "",
      
      // Optional string fields (nullable)
      firm_name: get(38) || null,
      gender: get(31) || null,
      photo_url: get(33) instanceof File ? null : (get(33) || null), // File upload handled separately
      ncdr_description: get(11) || null,
      compelling_quote: get(14) || null,
      remote_consultation: get(37) || null,
      
      // Optional number field (nullable)
      experience: hasValue(get(4)) ? Number(get(4)) : null,
      
      // Object fields (nullable)
      professional_status: (() => {
        if (!professionalStatus?.length) return null;
        
        // Keep all values as-is (they should already be in the correct format like "SOLICITOR", "OTHER", etc.)
        // But handle case where "Other" label might be stored instead of "OTHER" value
        const mappedValues = professionalStatus.map((v: string) => 
          v === "Other" ? "OTHER" : v
        );
        
        // Get the other professional status value (field 3)
        const otherValue = otherProfessionalStatus || "";
        
        // Return format with values array (including "OTHER") and "Other" field
        return {
          values: mappedValues,
          Other: otherValue
        };
      })(),
      
      regulator: (() => {
        const regulatorValue = get(40);
        const regulatorOther = get(46);
        
        if (!regulatorValue) return null;
        
        // If "Other" is selected and there's a custom value, include "OTHER" in values and "other" field
        if (regulatorValue === "OTHER" && regulatorOther) {
          return { 
            values: ["OTHER"],
            other: regulatorOther 
          };
        }
        
        // If "Other" is selected but no custom value, don't save
        if (regulatorValue === "OTHER" && !regulatorOther) {
          return null; // Don't save "OTHER" if no custom value provided
        }
        
        // For regular regulator values
        return { values: [regulatorValue] };
      })(),
      
      ncdr_magic: get(18)?.length > 0 ? { values: get(18) } : null,
      
      accredited_specialist: get(19)?.length > 0 ? { values: get(19) } : null,
      // Field 47: "Other? Please provide your accredited specialism" – send as list of one string
      accredited_specialism_other: (() => {
        const value = get(47);
        const str = typeof value === "string" ? value.trim() : "";
        return str ? [str] : null;
      })(),
      
      consultation_offers: get(36)?.length > 0 ? { values: get(36) } : null,
      
      service_details: (() => {
        // Get client types (offers) - field 27
        const offers = Array.isArray(clientTypes) ? clientTypes : [];
        
        // Initialize the new format
        const details: {
          offers: string[];
          cohabitees?: { expertises: string[]; other: string[] };
          married_civil_partners?: { expertises: string[]; other: string[] };
        } = {
          offers: offers,
        };
        
        // Process Married Couples practice areas (field 9)
        // Check if MARRIED_CIVIL_PARTNERS is selected in client types
        const hasMarriedCouples = clientTypes?.some((v: string) => 
          v === "MARRIED_CIVIL_PARTNERS" || matchesClientType(v, "Married and civil partners")
        );
        
        if (hasMarriedCouples) {
          const marriedAreas = marriedCouplesAreas || [];
          // Access "9_other" directly from formData (stored as string key)
          const marriedOtherValues = formData["9_other"] || [];
          
          // Filter out "Other" option value
          const marriedOtherOptionValue = "OTHER_MARRIED_CIVIL_PARTNERS";
          const selectedExpertises = Array.isArray(marriedAreas) 
            ? marriedAreas.filter((v: string) => v !== marriedOtherOptionValue)
            : [];
          const otherValues = Array.isArray(marriedOtherValues) ? marriedOtherValues : [];
          
          // Only add if there are expertises or other values
          if (selectedExpertises.length > 0 || otherValues.length > 0) {
            details.married_civil_partners = {
              expertises: selectedExpertises,
              other: otherValues,
            };
          }
        }
        
        // Process Cohabitees practice areas (field 29)
        // Check if COHABITEES is selected in client types
        const hasCohabitees = clientTypes?.some((v: string) => 
          v === "COHABITEES" || matchesClientType(v, "Cohabitees")
        );
        
        if (hasCohabitees) {
          const cohabiteesAreasArray = cohabiteesAreas || [];
          // Access "29_other" directly from formData (stored as string key)
          const cohabiteesOtherValues = formData["29_other"] || [];
          
          // Filter out "Other" option value
          const cohabiteesOtherOptionValue = "OTHER_COHABITEES";
          const selectedExpertises = Array.isArray(cohabiteesAreasArray) 
            ? cohabiteesAreasArray.filter((v: string) => v !== cohabiteesOtherOptionValue)
            : [];
          const otherValues = Array.isArray(cohabiteesOtherValues) ? cohabiteesOtherValues : [];
          
          // Only add if there are expertises or other values
          if (selectedExpertises.length > 0 || otherValues.length > 0) {
            details.cohabitees = {
              expertises: selectedExpertises,
              other: otherValues,
            };
          }
        }
        
        // Return null if no service details (only offers with no expertises)
        const hasExpertises = details.married_civil_partners || details.cohabitees;
        return hasExpertises ? details : null;
      })()
    };
  };

  const handleFormSubmit = async () => {
    setIsSubmitting(true);
    
    // Transform form data to API format
    const apiFormattedData = transformFormDataToApiFormat();
    
    // Define response type
    interface LawyerOnboardingResponse {
      success: boolean;
      message: Array<{
        success: boolean;
        message: string;
      }>;
    }
    
    // Send the data to backend
    try {
      const response = await api.post<LawyerOnboardingResponse>('/v1/B2C-experts', apiFormattedData);
      // Extract message from nested response structure
      // const successMessage = response?.message?.[0]?.message || "Form submitted successfully";
      // toastManager.addToast(createSuccessToast("Success", successMessage));
      
      // Only show confirmation and close form after successful submission
      setShowForm(false);
      setIsSubmitted(true);
    } catch (error) {
      // console.error("Error submitting form:", error);
      // toastManager.addToast(createErrorToast("Error", "Form submitted failed: " + error));
      // Keep form open on error so user can retry
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <div className="min-h-screen bg-novaNeutral-50 flex flex-col">
        <LandingHeader hidenavs={false} onGetStartedClick={handleGetStartedClick}/>
        <main id="main-content">
          <Section1 onSignUpClick={handleStartForm} />
          <Section2 />
          <Section3 />
          <Section4 onSignUpClick={handleStartForm} />
          <Section5 />
          <Section6 onSignUpClick={handleStartForm} />
        </main>
        {/* <div className="flex-1 bg-white py-12">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl sm:text-4xl font-bold text-novaNeutral-900 mb-12 text-center font-nineties tracking-wide">
              Nova for Lawyers - Sign up page
            </h1>

            <div className="prose prose-lg max-w-none">
              <div className="mb-8 space-y-4">
                <p className="text-base text-novaNeutral-600 leading-relaxed">
                  A better way to work with family law clients.
                </p>
                <p className="text-base text-novaNeutral-600 leading-relaxed">
                  Nova connects you with people who want clarity, fairness, and progress – and prepares them so your first meeting is focused and productive.
                </p>
              </div>

              <SectionAccordionItem
                title="Why join Nova"
                isOpen={openSectionIndex === 0}
                onToggle={() => handleSectionToggle(0)}
              >
                <div className="space-y-4">
                  {whyJoinNovaList.map((item, index) => (
                    <div key={index} className="text-base text-novaNeutral-600 leading-relaxed">
                      {item}
                    </div>
                  ))}
                </div>
              </SectionAccordionItem>

              <SectionAccordionItem
                title="Benefits list for lawyers"
                isOpen={openSectionIndex === 1}
                onToggle={() => handleSectionToggle(1)}
              >
                <ul className="space-y-4">
                  {benefitsList.map((benefit, index) => (
                    <li key={index} className="flex items-start">
                      <i className="fas fa-check-circle text-novaPrimary-600 mr-3 mt-1 flex-shrink-0"></i>
                      <span>{benefit}</span>
                    </li>
                  ))}
                </ul>
              </SectionAccordionItem>

              <SectionAccordionItem
                title="FAQ for sceptical lawyers"
                isOpen={openSectionIndex === 2}
                onToggle={() => handleSectionToggle(2)}
              >
                <div className="mt-6 space-y-6">
                  {scepticalLawyerFaqs.map((faq, index) => (
                    <div key={faq.question}>
                      <h3 className="text-lg font-semibold text-novaNeutral-900 mb-3">
                        {faq.question}
                      </h3>
                      <div className="text-base text-novaNeutral-600 leading-relaxed">
                        {renderHtmlContent(faq.answer)}
                      </div>
                    </div>
                  ))}
                </div>
              </SectionAccordionItem>

              <div className="mt-8 space-y-4">
                <div className="text-base text-novaNeutral-600 leading-relaxed">
                  Join the next generation of family lawyer & help reimagine the experience of family law.
                </div>
                <div className="text-base text-novaNeutral-600 leading-relaxed">
                  We combine AI, expert guidance, and early-stage triage to send you clients who are ready for solutions, not an escalation of conflict.
                </div>
                <div className="text-base text-novaNeutral-600 leading-relaxed">
                  If you want to be part of a forward-thinking family law ecosystem and grow your practice with ethical purpose, register your interest below.
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-center mt-8">
            <button className="landing-primary-button" onClick={handleStartForm}>
              Register your interest
            </button>
          </div>
        </div> */}
        <LandingFooter />
      </div>

      {/* Form Modal Popup */}
      <GlobalModalWrapper
        isOpen={showForm && !isSubmitted}
        onClose={handleCloseForm}
        className="w-full max-w-4xl max-h-[90vh] flex flex-col border-[18px] border-[#ffc9a9] rounded-[30px] relative shadow-xl"
        backdropClassName="bg-black/60"
        backdropStyle={{
          backgroundImage: `url(${accountSetupBackground})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
        }}
        disableBackdropClose
      >
        {/* Close Button */}
        <button
          onClick={handleCloseForm}
          className="absolute top-4 right-4 z-10 flex items-center justify-center w-4 h-4 rounded-full hover:bg-novaNeutral-200 text-novaNeutral-600 hover:text-novaNeutral-900 transition-colors"
          aria-label="Close modal"
        >
          <i className="fas fa-times text-lg"></i>
        </button>

        <div ref={scrollContainerRef} className="bg-white rounded-[12px] flex-1 overflow-y-auto min-h-0 sm:p-8 p-5">
          {/* Form Card */}
          {visibleSections.length > 0 && currentSectionIndex < visibleSections.length && (
            <LawyerSignupQuestionCard
              section={{
                ...visibleSections[currentSectionIndex].section,
                fields: visibleSections[currentSectionIndex].section.fields.filter(
                  (field: any) => field.type !== "html"
                )
              }}
              sectionIndex={currentSectionIndex}
              totalSections={visibleSections.length}
              formData={formData}
              onFieldChange={handleFieldChange}
              onNext={handleNext}
              onPrevious={handlePrevious}
              entityType="b2c_expert_profile"
              formConfig={formConfig}
              isSubmitting={isSubmitting}
              introContent={currentSectionIndex === 0 ? (
                <div className="bg-novaNeutral-50 border border-novaNeutral-200 rounded-lg p-6 mb-8">                
                  <div className="text-sm text-novaNeutral-700">
                    <p className="mb-3">Tell us a bit about yourself.</p>
                    <ul className="list-disc list-outside space-y-1 ml-2">
                      <li>By completing the application to become a Nova Professional - you are doing so as a qualified, regulated or accredited professional within the family dispute resolution community.</li>
                    </ul>
                  </div>
                  <div className="text-sm text-novaNeutral-700 mt-4">
                    Let us help you find the people who need and want your specialist skills. Join us.
                  </div>
                </div>
              ) : undefined}
            />
          )}
        </div>
      </GlobalModalWrapper>

      {/* Confirmation Modal */}
      <GlobalModalWrapper
        isOpen={isSubmitted}
        onClose={() => setIsSubmitted(false)}
        className="w-full max-w-lg bg-white sm:border-[18px] border-[10px] rounded-[27px] p-8 relative border-[#ffc9a9]"
        backdropClassName="bg-black/60"
        disableBackdropClose={false}
      >
        <div className="text-center">
          <div className="mb-6">
            <i className="fas fa-check-circle text-novaPrimary-600 text-6xl mb-4"></i>
          </div>
          <h2 className="text-3xl font-bold text-novaNeutral-900 mb-4 font-nineties">
            {formConfig.confirmationMessage || "Thank you for your submission!"}
          </h2>
          {formConfig.privacyNote && (
            <div className="text-base text-novaNeutral-600 mb-6">
              {formConfig.privacyNote}
            </div>
          )}
          <button
            onClick={() => setIsSubmitted(false)}
            className="landing-primary-button"
          >
            Close
          </button>
        </div>
      </GlobalModalWrapper>
    </>
  );
};

export default BecomeNovaLawyerPage;

