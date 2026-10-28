import React, { useState, useCallback, useEffect, useRef } from "react";
import { TimelineItemType } from "../../../../../lib/types";
import { createErrorToast, formatTimestamp, FormButton, renderHtmlContent, toastManager } from "../../../../../utils";
import { api } from "../../../../../lib/api";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { useParams } from "wouter";
import { useTimeline } from "@/contexts/TimelineContext";
import useEmblaCarousel from "embla-carousel-react";
import ResolveDetailsModal from "../../../ResolveDetailsModal";
import KycForm from "../../../KycForm";
import KycFormNew from "../../../KycFormNew";
import helloIcon from "@/assets/ui/Hello.svg";
import pathwayIcon from "@/assets/ui/Pathway.svg";
import nextStepIcon from "@/assets/ui/NextStep.svg";
import communicationIcon from "@/assets/summary-about/communication.svg";
import understandingIcon from "@/assets/summary-about/understand.svg";
import complexityIcon from "@/assets/summary-about/complexity.svg";
import trustIcon from "@/assets/summary-about/trust.svg";
import conflictIcon from "@/assets/summary-about/conflict.svg";
import financesIcon from "@/assets/summary-about/finances.svg";
import confidenceIcon from "@/assets/summary-about/confidence.svg";


// Recommendations by factor
interface PathwayRecommendations {
  Communication?: string;
  Understanding?: string;
  Complexity?: string;
  Trust?: string;
  Conflict?: string;
  Finances?: string;
  Confidence?: string;
  [key: string]: string | undefined;
}

// Metadata structure for Case Pathway Overview
interface CasePathwayOverviewMetaData {
  action_by: string;
  first_name: string;
  title: string;
  summary: string;
  recommendations: PathwayRecommendations;
  resolve_id: string;
  kyc_id: string | null;
  timestamp: string;
  action_buttons: {
    view_resolve: boolean;
    view_kyc: boolean;
  };
}

interface CasePathwayOverviewProps {
  timelineData?: TimelineItemType & { meta_data?: CasePathwayOverviewMetaData };
  isLatest?: boolean;
}

// Factor tabs for the pathway recommendation
const PATHWAY_FACTORS = [
  "Communication",
  "Understanding",
  "Complexity",
  "Trust",
  "Conflict",
  "Finances",
  "Confidence",
];

// Mapping of factor names to their icons
const FACTOR_ICONS: Record<string, string> = {
  Communication: communicationIcon,
  Understanding: understandingIcon,
  Complexity: complexityIcon,
  Trust: trustIcon,
  Conflict: conflictIcon,
  Finances: financesIcon,
  Confidence: confidenceIcon,
};

const CasePathwayOverview: React.FC<CasePathwayOverviewProps> = ({
  timelineData,
  isLatest,
}) => {
  const { refreshTimeline } = useTimeline();
  const [showSummary, setShowSummary] = useState(false);
  const [selectedFactorIndex, setSelectedFactorIndex] = useState(0);
  const [resolveData, setResolveData] = useState<any>({});
  const [resolveLoading, setResolveLoading] = useState(false);
  const [isResolveDetailsOpen, setIsResolveDetailsOpen] = useState(false);
  const [kycData, setKycData] = useState<any>(null);
  const [showKycPopup, setShowKycPopup] = useState(false);
  const [kycSubmitted, setKycSubmitted] = useState(false);
  /** Why the popup was opened: 'fill' = KycFormNew (Continue to next step), 'view' = KycForm (View your responses). Stops KycForm from showing after submit when timeline updates. */
  const [kycPopupIntent, setKycPopupIntent] = useState<'fill' | 'view' | null>(null);
  const params = useParams();
  const caseId = params.id;

  // Embla Carousel for content slides
  const [emblaRef, emblaApi] = useEmblaCarousel({
    loop: true,
    align: "center",
    containScroll: false,
  });

  // Embla Carousel for factor buttons (mobile looping)
  const [factorEmblaRef, factorEmblaApi] = useEmblaCarousel({
    loop: true,
    align: "center",
    containScroll: false,
    dragFree: true,
  });

  // Sync content carousel selection with state
  useEffect(() => {
    if (!emblaApi) return;
    
    const onSelect = () => {
      const index = emblaApi.selectedScrollSnap();
      setSelectedFactorIndex(index);
      // Also sync factor carousel
      if (factorEmblaApi) factorEmblaApi.scrollTo(index);
    };
    
    emblaApi.on("select", onSelect);
    onSelect();
    
    return () => {
      emblaApi.off("select", onSelect);
    };
  }, [emblaApi, factorEmblaApi]);

  // Sync factor carousel selection with content carousel
  useEffect(() => {
    if (!factorEmblaApi) return;
    
    const onSelect = () => {
      const index = factorEmblaApi.selectedScrollSnap();
      setSelectedFactorIndex(index);
      // Also sync content carousel
      if (emblaApi) emblaApi.scrollTo(index);
    };
    
    factorEmblaApi.on("select", onSelect);
    
    return () => {
      factorEmblaApi.off("select", onSelect);
    };
  }, [factorEmblaApi, emblaApi]);

  // Scroll to slide when factor button is clicked
  const scrollToSlide = useCallback(
    (index: number) => {
      if (emblaApi) emblaApi.scrollTo(index);
      if (factorEmblaApi) factorEmblaApi.scrollTo(index);
    },
    [emblaApi, factorEmblaApi]
  );

  // Get the currently selected factor name
  const selectedFactor = PATHWAY_FACTORS[selectedFactorIndex];

  // Get data from timeline metadata
  const metaData = timelineData?.meta_data;
  const customerName = metaData?.first_name || "there";
  const actionBy = timelineData?.action_user_name || timelineData?.action_user_role || DEFAULT_ACTION_BY;

  // Handle viewing resolve details
  const handleResolveDetails = async () => {
    try {
      setResolveLoading(true);
      const response = await api.get(
        `/v1/resolve?resolve_id=${metaData?.resolve_id}`
      );
      setResolveData((response as any).data || {});
      setIsResolveDetailsOpen(true);
    } catch (error: any) {
      let errorMessage = "Failed to get Resolve details. Please try again.";

      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      const toast = createErrorToast("Error", errorMessage);
      toastManager.addToast(toast);
      setIsResolveDetailsOpen(false);
    } finally {
      setResolveLoading(false);
    }
  };

  // Helper function to remove kycForm parameter from URL
  const removeKycFormParam = useCallback(() => {
    const urlParams = new URLSearchParams(window.location.search);
    urlParams.delete("kycForm");
    const newUrl = urlParams.toString()
      ? `${window.location.pathname}?${urlParams.toString()}`
      : window.location.pathname;
    window.history.replaceState({}, "", newUrl);
  }, []);

  // Handle opening KYC form: forView=true when "View your responses", false when "Continue to next step"
  const handleKycFormClick = useCallback(async (fromUrlParam?: boolean, forView?: boolean) => {
    const isForView = forView === true;
    setKycPopupIntent(isForView ? 'view' : 'fill');
    try {
      const encodedCaseId = encodeURIComponent(caseId || '');
      const response = await api.get(`/v1/customer/kyc?case_id=${encodedCaseId}`);
      setKycData((response as any).data);
      setShowKycPopup(true);
      if (fromUrlParam) {
        removeKycFormParam();
      }
    } catch (error) {
      const toast = createErrorToast("Error", "Failed to load KYC form. Please try again.");
      toastManager.addToast(toast);
    }
  }, [caseId, removeKycFormParam]);

  // Check for kycForm query parameter in URL
  useEffect(() => {
    // Skip auto-opening if form was just submitted to prevent reopening in view mode
    if (kycSubmitted) return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const kycFormParam = urlParams.get("kycForm");
    
    if (kycFormParam === "true" && caseId) {
      handleKycFormClick(true, false); // from URL = open for fill (KycFormNew)
    }
  }, [caseId, handleKycFormClick, kycSubmitted]);

  // Check if timelineData exists
  if (!timelineData?.meta_data) {
    return (
        <div className="bg-novaInactive sm:p-6 p-4 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-start sm:items-center gap-2 flex-wrap">
              <i className="fas fa-exclamation-triangle text-novaCaution-600 text-sm"></i>
              <span className="text-sm font-medium text-novaNeutral-900">
                No pathway data available
              </span>
            </div>
            <div className="h-px bg-novaCaution-200 my-2"></div>
            <p className="text-sm leading-5 text-novaNeutral-700 px-4 sm:px-0">
              Unable to load case pathway information at this time.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Section 1: Welcome Message */}
      <div className="bg-novaInactive sm:p-6 p-4 rounded-lg">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <img src={helloIcon} alt="Hello" className="w-6 h-4 mr-1" />
              <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
                Hello, {customerName}
              </span>
            </div>
            <hr className="block border-t border-novaDarkAmber my-3" />
            <p className="text-md leading-6 text-novaNeutral-700 mb-3 sm:w-[70%] w-full">
              We understand that moving through a divorce or separation can feel
              overwhelming, with so much to consider and take in, which is why
              we're with you every step of the way.
            </p>
            <p className="text-md leading-6 text-novaNeutral-700 sm:w-[70%] w-full">
              We'll keep you updated right here with all the recommendations
              you've received from us and the next actions to consider. If you
              have any worries or concerns, please feel free to chat.
            </p>
          </div>
        </div>
      </div>

      {/* Section 2: Personalised Pathway Recommendation */}
      <div id="case-pathway-overview-section-2" className="bg-novaInactive sm:p-6 p-4 rounded-lg">
        <div className="flex flex-col">
          {/* Header */}
          <div className="flex gap-2">
            <img src={pathwayIcon} alt="" className="w-6 h-6 sm:mt-1 mr-2" />
            <span className="sm:text-[28px] items-center text-2xl font-medium text-[#1A1425] ">
              {/* Your Personalised Pathway Recommendation */}
              Your personalised recommendation
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />

          {/* Title */}
          <div className="text-center mb-6 mt-14">
            <h2 className="sm:text-[52px] text-3xl font-nineties text-[#1A1425]">
              {metaData?.title || "Your recommendation"}
            </h2>
          </div>

          {/* Show Summary Toggle */}
          <div className="text-center mb-8">
            <button
              onClick={() => setShowSummary(!showSummary)}
              className="text-lg text-novaNeutral-600 hover:text-novaNeutral-800 inline-flex items-center gap-1 transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 rounded"
            >
              <span className="sm:inline hidden">Show me a summary of this pathway </span><span className="sm:hidden inline">What's this?</span>
              <i className={`fas fa-chevron-down text-xs ml-1 transition-transform duration-300 ease-in-out ${showSummary ? 'rotate-180' : 'rotate-0'}`}></i>
            </button>
          </div>

          {/* Collapsible Summary with Animation */}
          <div
            className={`grid transition-all duration-300 ease-in-out ${
              showSummary ? 'grid-rows-[1fr] opacity-100 mb-8' : 'grid-rows-[0fr] opacity-0 mb-0'
            }`}
          >
            <div className="overflow-hidden">
              {metaData?.summary && (
                <div className="p-4 bg-white rounded-md border border-amber-200">
                  <div className="text-md text-novaNeutral-700 italic leading-relaxed">
                    {renderHtmlContent(metaData.summary)}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Factors Section */}
          <div className="mb-8">
            <p className="text-center text-xl font-semibold text-[#1A1425] mb-6">
              Your recommendation was guided by these seven factors:
            </p>
            
            {/* Desktop: Static horizontal scrollable list */}
            <div className="hidden xl:flex justify-center gap-2 py-1">
              {PATHWAY_FACTORS.map((factor, index) => (
                <FormButton
                  key={factor}
                  variant="custom"
                  onClick={() => scrollToSlide(index)}
                  className={`px-4 py-2 text-sm rounded-full border transition-colors duration-300 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 ${
                    selectedFactorIndex === index
                      ? "bg-[#1A1425] text-novaInactive font-semibold border-[#1A1425] hover:bg-[#1A1425]/90"
                      : "text-[#1A1425] border-[#1A1425] hover:bg-[#1A1425] hover:text-white"
                  }`}
                >
                  {factor}
                </FormButton>
              ))}
            </div>

            {/* Mobile/Tablet: Looping Embla carousel for factors */}
            <div className="xl:hidden overflow-hidden select-none" ref={factorEmblaRef}>
              <div className="flex">
                {PATHWAY_FACTORS.map((factor, index) => (
                  <div
                    key={factor}
                    className="flex-[0_0_auto] min-w-0 px-1"
                  >
                    <FormButton
                      variant="custom"
                      onClick={() => scrollToSlide(index)}
                      className={`px-4 py-2 text-sm rounded-full border transition-colors duration-300 ease-in-out whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 ${
                        selectedFactorIndex === index
                          ? "bg-[#1A1425] text-novaInactive font-semibold border-[#1A1425]"
                          : "text-[#1A1425] border-[#1A1425]"
                      }`}
                    >
                      {factor}
                    </FormButton>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recommendation Carousel using Embla */}
          {metaData?.recommendations && (
            <div className="select-none">
              <div className="overflow-hidden" ref={emblaRef}>
                <div className="flex">
                  {PATHWAY_FACTORS.map((factor) => (
                    <div
                      key={factor}
                      className="flex-[0_0_100%] min-w-0"
                    >
                      {metaData.recommendations[factor] && (
                        <div className="sm:flex items-start gap-8 mb-4 xl:w-[60%] md:w-[80%] w-full sm:mx-auto px-4">
                          <div className="flex-shrink-0">
                            <div className="flex items-center justify-center mb-6 sm:mb-0">
                              <img src={FACTOR_ICONS[factor]} alt={factor} className="w-18 h-16 sm:mt-4 pointer-events-none" />
                            </div>
                          </div>
                          <p className="text-lg leading-6 text-novaNeutral-700">
                            {metaData.recommendations[factor]}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* View Responses Button */}
          {metaData?.action_buttons?.view_resolve && (
            <div className="mb-4">
              <FormButton 
                variant="primary" 
                className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
                onClick={handleResolveDetails}
                disabled={resolveLoading}
              >
                {resolveLoading ? (
                  <>
                    <i className="fas fa-spinner fa-spin"></i>
                    Loading...
                  </>
                ) : (
                  <>
                    <i className="fas fa-eye"></i>
                    View your responses
                  </>
                )}
              </FormButton>
            </div>
          )}

          {/* Timestamp */}
          <p className="text-xs flex items-center">
            <i className="fas fa-clock text-xs mr-1"></i>
            <span>Submitted on {formatTimestamp(metaData?.timestamp || "")}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </p>
        </div>
      </div>

      {/* Section 3: Next Step */}
      <div id="case-pathway-overview-section-3" className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          {/* Header */}
          <div className="flex gap-2">
            <img src={nextStepIcon} alt="" className="w-8 h-6 mr-2 mt-2 sm:mt-1" />
            {isLatest === true ? (
              <span className="sm:text-[28px] items-center text-2xl font-semibold text-[#1A1425]">
                Next step: Your Nova Expert Alignment Check
              </span>
            ) : (
              <span className="sm:text-[28px] items-center text-2xl font-semibold text-[#1A1425]">
                Your Nova Expert Alignment Check
              </span>
            )}
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          
          {/* Description */}
          <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full">
            Now you have your personalised pathway recommendation of{" "}
            {metaData?.title || "your pathway"}, {customerName}, 
            let's match you with one of our family experts who has 
            the skills to meet your needs and is available to support you.
          </p>

          {/* What happens next card */}
          <div className="bg-white sm:p-6 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <i className="fas fa-info-circle text-novaNeutral-700 text-sm"></i>
              <span className="text-sm font-semibold text-novaNeutral-900">
                What happens next:
              </span>
            </div>
            <ul className="space-y-2 text-sm text-novaNeutral-700 ml-2">
              <li className="flex items-start gap-6">
                <span className="text-novaNeutral-800">•</span>
                <span>
                  Answer a few short questions to help us understand 
                  more about your situation and preferences.
                </span>
              </li>
              <li className="flex items-start gap-6">
                <span className="text-novaNeutral-800">•</span>
                <span>
                  We’ll share a small selection of carefully matched family 
                  experts.
                </span>
              </li>
              <li className="flex items-start gap-6">
                <span className="text-novaNeutral-800">•</span>
                <span>
                  Choose if and when you’d like to book a consultation.
                </span>
              </li>
            </ul>
          </div>

          {/* Continue Button */}
          {metaData?.action_buttons?.view_kyc && (
            <div className="mt-6 mb-4">
              <FormButton 
                variant="primary" 
                className="inline-flex items-center gap-2 px-4 py-2 text-white text-sm rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
                onClick={() => handleKycFormClick(undefined, isLatest !== true)}
              >
                {isLatest === true ? <i className="fas fa-play text-xs"></i> : <i className="fas fa-eye text-xs"></i>}
                {isLatest === true ? "Continue to next step" : "View your responses"}
              </FormButton>
            </div>
          )}
          {/* Timestamp */}
          <p className="text-xs flex items-center">
            <i className="fas fa-clock text-xs mr-1"></i>
            <span>Submitted on {formatTimestamp(metaData?.timestamp || "")}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </p>
        </div>
      </div>

      {/* Resolve Details Modal */}
      <ResolveDetailsModal
        data={resolveData}
        isOpen={isResolveDetailsOpen}
        onClose={() => setIsResolveDetailsOpen(false)}
        caseId={caseId}
        showViewCaseButton={false}
      />

      {/* KYC Form Popup - show KycFormNew only when opened for fill; KycForm (details) only when opened via "View your responses" */}
      {kycData && showKycPopup && kycPopupIntent === 'fill' && (
        <KycFormNew
          data={kycData}
          isOpen={showKycPopup}
          onClose={() => {
            setShowKycPopup(false);
            setKycPopupIntent(null);
            removeKycFormParam();
          }}
          onSubmit={() => {
            setKycSubmitted(true);
            setShowKycPopup(false);
            setKycPopupIntent(null);
            removeKycFormParam();
            setKycData(null);
            refreshTimeline();
          }}
          caseId={caseId}
          viewMode={false}
        />
      )}
      {kycData && showKycPopup && kycPopupIntent === 'view' && (
        <KycForm
          data={kycData}
          isOpen={showKycPopup}
          onClose={() => {
            setShowKycPopup(false);
            setKycPopupIntent(null);
            removeKycFormParam();
          }}
          caseId={caseId}
          viewMode={true}
        />
      )}
    </div>
  );
};

export default CasePathwayOverview;
