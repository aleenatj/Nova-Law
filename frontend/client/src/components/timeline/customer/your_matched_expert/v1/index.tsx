import React, { useState, useEffect, useCallback } from "react";
import useEmblaCarousel from "embla-carousel-react";
import Autoplay from "embla-carousel-autoplay";
import { Button } from "../../../../ui/button";
import { MatchedExpertsTimelineProps } from "../../../../../lib/types";
import { createSuccessToast, formatTimestamp, FormButton } from "../../../../../utils";
import { createErrorToast, toastManager } from "../../../../../utils/toasts";
import { api } from "../../../../../lib/api";
import  LawyersAutoScrollCard  from "../../../../timeline/LawyersAutoScrollCard";
import PhoneVerificationPopup from "../../../../timeline/PhoneVerificationPopup";
import { useRole } from "@/contexts/RoleContext";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

const MatchedExperts: React.FC<MatchedExpertsTimelineProps> = ({
  timelineData,
  isLatest,
}) => {
  const [isEngaging, setIsEngaging] = useState(false);
  const [isTalkingToNN, setIsTalkingToNN] = useState(false);
  const [isNNVerificationPopupOpen, setIsNNVerificationPopupOpen] = useState(false);
  const [currentExpertIndex, setCurrentExpertIndex] = useState(0);
  const userRole = useRole();

  // Get lawyer profiles count early for carousel setup
  const lawyerProfilesCount = timelineData?.meta_data?.lawyer_profiles?.length || 0;
  const hasMultipleLawyers = lawyerProfilesCount > 3;
  const isSingleLawyer = lawyerProfilesCount === 1;

  // Embla Carousel setup with autoplay (enable loop and autoplay for 2+ lawyers)
  // containScroll: 'trimSnaps' so drag stops at last slide (no empty space after last lawyer)
  const [emblaRef, emblaApi] = useEmblaCarousel(
    { 
      loop: hasMultipleLawyers,
      skipSnaps: false,
      duration: 20,
      containScroll: "trimSnaps",
    },
    hasMultipleLawyers ? [Autoplay({ delay: 3000, stopOnInteraction: false, stopOnMouseEnter: true, stopOnFocusIn: false })] : []
  );

  if (!timelineData?.meta_data) {
    return (
      <div className="timeline-card-border bg-novaNeutral-50 border-novaNeutral-200 p-6">
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-start sm:items-center gap-2 flex-wrap">
              <i className="fas fa-users text-novaNeutral-600 text-sm"></i>
              <span className="text-sm font-medium text-novaNeutral-900">
                No matched experts available
              </span>
            </div>
            <div className="h-px bg-novaNeutral-200 my-2"></div>
            <p className="text-sm leading-5 text-novaNeutral-700 px-4 sm:px-0">
              We could not load matched expert information right now. Please try
              again shortly.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Track current slide index
  useEffect(() => {
    if (!emblaApi) return;

    const onSelect = () => {
      setCurrentExpertIndex(emblaApi.selectedScrollSnap());
    };

    emblaApi.on("select", onSelect);
    onSelect();

    return () => {
      emblaApi.off("select", onSelect);
    };
  }, [emblaApi]);

  const { lawyer_profiles = [], action_buttons, timestamp, action_by, first_name } = timelineData.meta_data;
  const currentExpert = lawyer_profiles[currentExpertIndex] || lawyer_profiles[0];
  const totalExperts = lawyer_profiles.length;
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;

  // Navigation handlers
  const scrollPrev = useCallback(() => {
    if (emblaApi) emblaApi.scrollPrev();
  }, [emblaApi]);

  const scrollNext = useCallback(() => {
    if (emblaApi) emblaApi.scrollNext();
  }, [emblaApi]);

  const scrollTo = useCallback(
    (index: number) => {
      if (emblaApi) emblaApi.scrollTo(index);
    },
    [emblaApi]
  );

  const handleEngageWithExpert = async (lawyerId?: string) => {
    if (!action_buttons.engage_with) return;
    
    // Use provided lawyerId or fall back to current expert
    const targetLawyerId = lawyerId || currentExpert?.lawyer_id;
    if (!targetLawyerId) return;
    
    setIsEngaging(true);

    // Utility function for showing all API messages as toast(s), with delay (from file_context_0)
    const showToastsWithDelay = async (
      messages: Array<{ message: string; success?: boolean }>,
      isSuccess: boolean
    ) => {
      const delay = 400; // ms
      for (let i = 0; i < messages.length; i++) {
        const messageItem = messages[i];
        await new Promise((resolve) =>
          setTimeout(resolve, i === 0 ? 0 : delay)
        );
        if (isSuccess) {
          if (messageItem.success) {
            const toast = createSuccessToast("Success", messageItem.message);
            toastManager.addToast(toast);
          } else {
            const toast = createErrorToast("Error", messageItem.message);
            toastManager.addToast(toast);
          }
        } else {
          const toast = createErrorToast("Error", messageItem.message);
          toastManager.addToast(toast);
        }
      }
    };

    try {
      const response = await api.post('/v1/timeline/accept-lawyer', {
        lawyer_id: targetLawyerId,
        case_id: timelineData.case_id,
      }) as any;

      if (Array.isArray(response?.message)) {
        await showToastsWithDelay(response.message, response.success === true);
      } else if (typeof response?.message === "string") {
        // Backward compatibility fallback
        if (response.success) {
          toastManager.addToast(createSuccessToast("Success", response.message));
        } else {
          toastManager.addToast(createErrorToast("Error", response.message));
        }
      } else {
        // Generic fallback
        toastManager.addToast(
          createSuccessToast("Success", "Engage Requested with Lawyer")
        );
      }
    } catch (error: any) {
      let errorMessage = "Failed to request engage with lawyer.";
      if (error?.message) {
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      // toastManager.addToast(createErrorToast("Error", errorMessage));
    } finally {
      setIsEngaging(false);
    }
  };

  const handleTalkToNN = async (phoneNumber: string) => {
    if (!action_buttons.talk_to_nn) return;
    
    setIsTalkingToNN(true);
    try {
      // API call to talk to Nova Navigator
      await api.post(`/v1/customer/talk_to_navigator`, {
        case_id: timelineData.case_id,
        phone: phoneNumber,
      });
      const toast = createSuccessToast("Success", "Requested call with Nova Navigator");
      toastManager.addToast(toast);
    } catch (error) {
      // const toast = createErrorToast("Error", "Failed to Request call with Navigator");
      // toastManager.addToast(toast);
      // Handle error
    } finally { 
      setIsTalkingToNN(false);
    }
  };

  // Handle modal opening/closing - stop autoplay when modal is open
  const handleProfileModalToggle = useCallback(
    (isOpen: boolean) => {
      if (!emblaApi || !hasMultipleLawyers) return;
      // Ensure carousel is ready before accessing plugins
      if (!emblaApi.slideNodes() || emblaApi.slideNodes().length === 0) return;
      try {
        const plugins = emblaApi.plugins();
        if (!plugins) return;
        const autoplay = plugins.autoplay;
        if (autoplay && typeof autoplay.stop === 'function' && typeof autoplay.play === 'function') {
          if (isOpen) {
            autoplay.stop();
          } else {
            autoplay.play();
          }
        }
      } catch (error) {
        // Silently handle autoplay plugin access errors
      }
    },
    [emblaApi, hasMultipleLawyers]
  );

  return (
    <div className="timeline-card-border bg-white border-novaBlue-200 sm:p-6 p-4 w-full max-w-full">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start sm:items-center gap-2 sm:flex-wrap">
            <i className="fas fa-users text-xl"></i>
            <span className="sm:text-[28px] text-2xl font-medium text-novaBlack">
              Your Matching Nova Experts
            </span>
            <span className="text-xs bg-novaDarkOrange text-white px-2 py-1 rounded-full hidden sm:inline">
              {totalExperts} Available
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-4" />

          {/* Description */}
          <p className="text-[16px] leading-6 text-novaNeutral-700 sm:px-0 mb-4 w-full lg:w-[70%]">
          Now we’ve got to know you and your circumstances much better {first_name || "User"} - and having carefully considered what typically leads to the best outcomes for people in your situation - our team of Nova Navigators has selected the Nova Experts below for you.</p>
          <p className="text-[16px] leading-6 text-novaNeutral-700 sm:px-0 mb-2 w-full lg:w-[70%]">
          When you feel ready, you can book a consultation with your preferred Nova Expert from right here. You can also request a 15 minute intro call if you would like to ask them any initial questions.          </p>

          {/* {hasMultipleLawyers && (
            <div className="hidden sm:flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-3">
              <div className="flex items-center gap-2 text-xs text-novaNeutral-500">
                <div className="w-2 h-2 bg-novaDarkOrange rounded-full animate-pulse"></div>
                <span>Auto-rotating</span>
              </div>
            </div>
          )} */}

          {/* Embla Carousel */}
          <div className="relative mb-4">
            {/* Navigation Buttons - Left */}
            {hasMultipleLawyers && (
              <button
                type="button"
                onClick={scrollPrev}
                className="absolute left-0 sm:left-[-15px] top-[100px] sm:top-[200px] w-8 h-8 flex items-center justify-center border border-novaNeutral-200 rounded-lg z-20 bg-white"
                aria-label="View previous expert"
              >
                <i className="fas fa-chevron-left text-sm"></i>
              </button>
            )}

            {/* Embla Viewport */}
            <div className="overflow-hidden my-6" ref={emblaRef}>
              <div className={`flex sm:gap-6 gap-4 items-stretch ${lawyer_profiles.length > 1 ? 'flex-col sm:flex-row' : ''} ${lawyer_profiles.length <= 2 ? 'lg:justify-center' : ''}`}>
                {lawyer_profiles.map((lawyer, index) => (
                  <div
                    key={index}
                    className={`flex-shrink-0 ${
                      isSingleLawyer 
                        ? 'flex-[0_0_100%] max-w-full' 
                        : 'w-full sm:w-auto max-w-full sm:max-w-[380px] flex-[0_0_100%] sm:flex-[0_0_33.333%] pr-0 sm:pr-1 min-w-0 sm:min-w-[360px]'
                    }`}
                  >
                    <LawyersAutoScrollCard
                      lawyerDetails={lawyer}
                      onProfileModalToggle={handleProfileModalToggle}
                      onEngageWithExpert={handleEngageWithExpert}
                      isEngaging={isEngaging}
                      canEngage={action_buttons.engage_with}
                      canTalkToLawyer={action_buttons.talk_to_lawyer}
                      caseId={timelineData.case_id}
                      allLawyers={lawyer_profiles}
                      initialIndex={index}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Navigation Buttons - Right */}
            {hasMultipleLawyers && (
              <button
                type="button"
                onClick={scrollNext}
                className="absolute right-0 sm:right-1 top-[100px] sm:top-[200px] w-8 h-8 flex items-center justify-center transition-all z-20 bg-white border border-novaNeutral-200 rounded-lg"
                aria-label="View next expert"
              >
                <i className="fas fa-chevron-right text-sm"></i>
              </button>
            )}
          </div>

          {/* Action Buttons */}
{/*           <div className="mt-4 hidden sm:flex flex-col gap-2 sm:flex-row sm:gap-2 w-full">
            <FormButton
              variant="primary"
              className="w-full sm:w-auto flex-1 text-sm"
              disabled={!action_buttons.engage_with || isEngaging || !currentExpert}
              onClick={() => handleEngageWithExpert()}
            >
              <i className="mr-2 fas fa-user-check"></i>
              {isEngaging
                ? "Engaging..."
                : currentExpert ? `Engage with ${currentExpert.lawyer_name}` : "Engage with Expert"}
            </FormButton>
            {lawyer_profiles.length > 1 && (
              <FormButton
                variant="outline"
                className="hidden hover:shadow-md sm:inline-flex sm:w-auto border-novaDarkAmber text-novaNeutral-700 hover:bg-novaNeutral-50 text-sm"
                onClick={scrollNext}
              >
                <i className="fas fa-arrow-right my-auto mr-2 justify-center"></i>
                Next
              </FormButton>
            )}
          </div> */}

          {/* Pagination Dots - Show on xs when >2, on sm+ when >3 */}
          {lawyer_profiles.length > 2 && (
            <>
              {/* Show on xs screens when length > 2 */}
              {lawyer_profiles.length <= 3 && (
                <div className="sm:flex hidden 3xl:hidden justify-center gap-1.5 mt-3 flex-wrap">
                  {lawyer_profiles.map((_, index) => (
                    <button
                      key={index}
                      className={`w-1.5 h-1.5 rounded-full transition-colors ${
                        index === currentExpertIndex
                          ? "bg-novaPrimary"
                          : "bg-novaNeutral-300"
                      }`}
                      onClick={() => scrollTo(index)}
                      aria-label={`Go to expert ${index + 1}`}
                      disabled={isSingleLawyer}
                      style={isSingleLawyer ? { cursor: 'default' } : {}}
                    />
                  ))}
                </div>
              )}
              {/* Show on sm+ screens when length > 3 */}
              {lawyer_profiles.length > 3 && (
                <div className="hidden sm:flex justify-center gap-2 mt-3 flex-wrap">
                  {lawyer_profiles.map((_, index) => (
                    <button
                      key={index}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        index === currentExpertIndex
                          ? "bg-novaPrimary"
                          : "bg-novaNeutral-300"
                      }`}
                      onClick={() => scrollTo(index)}
                      aria-label={`Go to expert ${index + 1}`}
                      disabled={isSingleLawyer}
                      style={isSingleLawyer ? { cursor: 'default' } : {}}
                    />
                  ))}
                </div>
              )}
            </>
          )}

          {/* Timestamp */}
          {/* <div className="text-xs text-novaNeutral-500 mt-3 flex items-center gap-1">
            <i className="fas fa-clock text-novaNeutral-500 text-xs"></i>
            <span>{formatTimestamp(timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </div> */}

          {/* Nova Navigator Help Section */}
          {/* <div className="mt-4 p-4 bg-white rounded-lg">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3 w-full sm:w-auto">
                <div className="hidden sm:flex w-10 h-10 bg-novaDarkOrange rounded-full items-center justify-center flex-shrink-0">
                  <i className="fas fa-headset text-white text-sm"></i>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-novaNeutral-900">Need Help?</h4>
                  <p className="text-sm leading-5 text-novaNeutral-700">
                    Request a guidance session to discuss your case and get
                    personalized advice from our legal expert.
                  </p>
                </div>
              </div>
              <div className="w-full sm:w-auto flex-shrink-0">
                <FormButton
                  variant="primary"
                  className="w-full sm:w-auto text-white text-sm px-4 py-2 mt-2 sm:mt-0"
                  disabled={
                    !action_buttons.talk_to_nn ||
                    isTalkingToNN
                  }
                  onClick={() => setIsNNVerificationPopupOpen(true)}
                >
                  <i className="fas fa-comments mr-2"></i>
                  {isTalkingToNN ? "Starting..." : "Talk to Nova Navigator"}
                </FormButton>
              </div>
            </div>
          </div> */}


          <p className="text-xs text-novaNeutral-500 flex items-center">
            <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
            <span>{formatTimestamp(timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </p>    
          {/* Phone Verification Popup for Nova Navigator */}
          <PhoneVerificationPopup
            isOpen={isNNVerificationPopupOpen}
            onClose={() => setIsNNVerificationPopupOpen(false)}
            onVerify={handleTalkToNN}
            lawyerName="Nova Navigator"
          />
        </div>
      </div>
    </div>
  );
};

export default MatchedExperts;
