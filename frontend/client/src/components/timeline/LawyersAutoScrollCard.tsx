import React, { useState, useEffect } from "react";
import { LawyerProfileDisplayType } from "../../lib/types";
import { createSuccessToast, createErrorToast, toastManager } from "@/utils/toasts";
import { formatCurrency, getFirstName } from "../../lib/utils";
import { useParams } from "wouter";
import { api } from "@/lib/api";
import PhoneVerificationPopup from "./PhoneVerificationPopup";
import FullScreenModal from "../modal/FullScreenModal";
import { useRole } from "@/contexts/RoleContext";
import { FormButton } from "@/utils";
import { TruncatedContent } from "@/components/ui";
import resolveSummaryLawyerBg from "@/assets/summary-about/resolveSummaryLawyerbg.webp";


interface LawyersDetailsProps {
  lawyerDetails: LawyerProfileDisplayType;
  onProfileModalToggle?: (isOpen: boolean) => void;
  onEngageWithExpert?: (lawyerId?: string) => void;
  isEngaging?: boolean;
  canEngage?: boolean;
  canTalkToLawyer?: boolean;
  caseId?: string;
  allLawyers?: LawyerProfileDisplayType[];
  initialIndex?: number;
}

interface MessageItem {
  success: boolean;
  message: string;
}

interface ApiResponse {
  success: boolean;
  message?: string | MessageItem[];
}

const LawyersAutoScrollCard: React.FC<LawyersDetailsProps> = ({
  lawyerDetails,
  onProfileModalToggle,
  onEngageWithExpert,
  isEngaging = false,
  canEngage = false,
  canTalkToLawyer = false,
  caseId,
  allLawyers = [],
  initialIndex = 0,
}) => {
  const { id } = useParams<{ id: string }>();
  const [isVerificationPopupOpen, setIsVerificationPopupOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [modalLawyerIndex, setModalLawyerIndex] = useState(initialIndex);
  const hasMultipleLawyers = allLawyers.length > 1;
  const [activeTab, setActiveTab] = useState('specialisms');
  const userRole = useRole();

  // Reset modal index when modal opens or when initialIndex changes
  useEffect(() => {
    if (isProfileModalOpen) {
      setModalLawyerIndex(initialIndex);
    }
  }, [initialIndex, isProfileModalOpen]);

  // Get the lawyer to display in modal
  const modalLawyer = allLawyers.length > 0 ? allLawyers[modalLawyerIndex] : lawyerDetails;

  // Modal navigation handlers
  const handleModalPrev = () => {
    setModalLawyerIndex((prev) => 
      prev > 0 ? prev - 1 : allLawyers.length - 1
    );
  };

  const handleModalNext = () => {
    setModalLawyerIndex((prev) => 
      prev < allLawyers.length - 1 ? prev + 1 : 0
    );
  };

  useEffect(() => {
    // Only call onProfileModalToggle when modal state actually changes (not on initial mount)
    if (onProfileModalToggle) {
      onProfileModalToggle(isProfileModalOpen);
    }
  }, [isProfileModalOpen, onProfileModalToggle]);

  const FullProfileCard: React.FC<{ className?: string }> = ({ className = "" }) => {
    // Use modalLawyer when in modal, otherwise use lawyerDetails
    const displayLawyer = isProfileModalOpen ? modalLawyer : lawyerDetails;
    
    if (!displayLawyer) return null;
    
    const lawyerFirstName = displayLawyer.first_name ?? (getFirstName(displayLawyer.lawyer_name) || (displayLawyer.lawyer_name ?? ""));
    const lawyerExpertTypesArr = displayLawyer.lawyer_expert_types && Array.isArray(displayLawyer.lawyer_expert_types)
      ? displayLawyer.lawyer_expert_types.flatMap((item) =>
          String(item).split(",").map((s) => s.trim()).filter(Boolean)
        )
      : [];

    // Check if there's only one lawyer
    const isSingleLawyer = !hasMultipleLawyers;
    
    // Render single lawyer layout (horizontal on desktop, vertical on mobile)
    if (isSingleLawyer) {
      return (
        <div className={`w-full flex flex-col md:flex-row gap-0 bg-white rounded-lg overflow-hidden border border-novaNeutral-200 ${className}`} style={{ userSelect: 'none' }}>
          {/* Left side - Photo with name overlay */}
          <div className="relative md:w-[350px] w-full h-[350px] md:h-[350px] flex-shrink-0 overflow-hidden">
            {displayLawyer.lawyer_photo_url ? (
              <img
                src={displayLawyer.lawyer_photo_url}
                alt={`${displayLawyer.lawyer_name} profile`}
                className="h-full w-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                }}
              />
            ) : (
              <div className="w-full h-full bg-novaNeutral-200 flex items-center justify-center">
                <i className="fas fa-user text-novaNeutral-400 text-6xl" aria-label="No profile photo"></i>
              </div>
            )}
            {/* Gradient overlays */}
            <div 
              className="absolute bottom-0 left-0 w-full h-2/3 pointer-events-none"
              style={{
                background: 'radial-gradient(ellipse 150% 100% at bottom left, rgb(223, 120, 24), transparent 80%)'
              }}
            ></div>
            <div 
              className="absolute bottom-0 right-0 w-full h-full pointer-events-none"
              style={{
                background: 'radial-gradient(ellipse 150% 100% at bottom right, rgba(216, 36, 4, 0.61), transparent 30%)'
              }}
            ></div>
            {/* Name overlay at bottom */}
            <div className="absolute bottom-0 left-0 right-0 p-4 z-10">
              <h3 className="text-3xl font-nineties text-white drop-shadow-lg line-clamp-1" title={displayLawyer.lawyer_name}>
                {displayLawyer.lawyer_name}
              </h3>
            </div>
          </div>

          {/* Right side - Details */}
          <div className="flex-1 p-4 md:p-5 flex flex-col min-h-0">
            {/* Lawyer Expert Type and Experience */}
            <div className="flex flex-wrap gap-6 mb-3">
              {/* <div className="flex flex-col gap-0.5 max-w-[50%]">
                {lawyerExpertTypesArr.length > 0
                  ? lawyerExpertTypesArr.map((type) => (
                      <span key={type} className="sm:text-sm text-xs text-novaDarkOrange font-bold">
                        {type}
                      </span>
                    ))
                  : <span className="sm:text-sm text-xs text-novaDarkOrange font-bold">N/A</span>}
              </div> */}
              <div className="flex flex-col gap-0">
                <div className="flex items-center gap-2">
                  <i className="fas fa-medal text-novaDarkOrange text-sm" aria-hidden></i>
                  <span className="sm:text-sm text-xs text-novaDarkOrange font-medium">Experience</span>
                </div>
                <span className="text-xs sm:text-sm text-novaNeutral-700">
                  {displayLawyer.lawyer_experience || "N/A"}
                </span>
              </div>
              {/* {displayLawyer.lawyer_rate && (
                <div className="items-center gap-2">
                  <div className="flex items-center gap-2">
                    <i className="fa-solid fa-money-bill-wave text-novaDarkOrange text-sm"></i>
                    <span className="sm:text-sm text-xs text-novaDarkOrange font-medium">Rate</span>
                  </div>
                  <span className="text-xs sm:text-sm text-novaNeutral-700">
                    {formatCurrency("pound", displayLawyer.lawyer_rate)} / hour
                  </span>
                </div>
              )} */}
            </div>

            {/* Content area: grows to fill space so buttons stay at bottom */}
            <div className="flex-1 flex flex-col min-h-0">
            {/* Tabs */}
            <div className="relative mb-4">
              <div className="flex">
                <button
                  onClick={() => setActiveTab('specialisms')}
                  className={`px-3 py-1.5 sm:text-sm text-xs transition-colors relative font-medium ${
                    activeTab === 'specialisms'
                      ? 'text-[#1A1425] bg-white border-t border-l border-r border-novaNeutral-200 rounded-t-sm z-10'
                      : 'text-novaNeutral-400 hover:text-novaNeutral-600 border-b border-novaNeutral-200'
                  }`}
                >
                  Specialisms
                </button>
                <button
                  onClick={() => setActiveTab('testimonial')}
                  className={`px-3 py-1.5 sm:text-sm text-xs transition-colors relative font-medium ${
                    activeTab === 'testimonial'
                      ? 'text-[#1A1425] bg-white border-t border-l border-r border-novaNeutral-200 rounded-t-sm z-10'
                      : 'text-novaNeutral-400 hover:text-novaNeutral-600 border-b border-novaNeutral-200'
                  }`}
                >
                  Testimonial
                </button>
                <button
                  onClick={() => setActiveTab('about')}
                  className={`px-3 py-1.5 sm:text-sm text-xs transition-colors relative font-medium ${
                    activeTab === 'about'
                      ? 'text-[#1A1425] bg-white border-t border-l border-r border-novaNeutral-200 rounded-t-sm z-10'
                      : 'text-novaNeutral-400 hover:text-novaNeutral-600 border-b border-novaNeutral-200'
                  }`}
                >
                  About
                </button>
                {/* Fill remaining space with bottom border */}
                <div className="flex-1 border-b border-novaNeutral-200"></div>
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex flex-1 min-h-0">
              {activeTab === 'specialisms' && (
                <div className={`flex flex-1 gap-4 ${canEngage ? 'max-h-content xl:max-h-[145px]' : 'max-h-[185px] xl:max-h-[180px]'} pl-4`}>
                  <div className="flex-1">
                    <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1">
                      <i className="fas fa-circle-check mr-1"></i>
                      Expert Type
                    </span>
                    <p className={`text-sm text-novaNeutral-700 overflow-y-auto px-2 ${canEngage ? 'max-h-content max-h-[130px]' : 'max-h-content max-h-[180px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
                      <TruncatedContent
                        content={
                          Array.isArray(displayLawyer.lawyer_expert_types) && (displayLawyer.lawyer_expert_types as string[]).length > 0
                            ? (displayLawyer.lawyer_expert_types as string[]).join(", ")
                            : displayLawyer.lawyer_expert_types
                              ? String(displayLawyer.lawyer_expert_types)
                              : "N/A"
                        }
                        maxHeightCollapsed="6.5rem"
                      />
                    </p>
                  </div>
                  <div className="flex-1">
                    <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1 min-w-[100px]">
                      <i className="fas fa-graduation-cap mr-1"></i>
                      Expertise
                    </span>
                    <p className={`text-sm text-novaNeutral-700 overflow-y-auto px-2 ${canEngage ? 'max-h-content max-h-[130px]' : 'max-h-content max-h-[180px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
                      <TruncatedContent
                        content={
                          Array.isArray(displayLawyer.lawyer_expertises) && displayLawyer.lawyer_expertises.length > 0
                            ? displayLawyer.lawyer_expertises.join(", ")
                            : displayLawyer.lawyer_expertises
                              ? String(displayLawyer.lawyer_expertises)
                              : "N/A"
                        }
                        maxHeightCollapsed={canEngage ? "6.5rem" : "10rem"}
                      />
                    </p>
                  </div>
                </div>
              )}
              {activeTab === 'testimonial' && (
                <div className={`text-sm text-novaNeutral-700 overflow-y-auto px-2 italic ${canEngage ? 'max-h-content max-h-[130px]' : 'max-h-content max-h-[190px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
                  <TruncatedContent
                    split={false}
                    content={displayLawyer.lawyer_testimonial || "No testimonial available."}
                    maxHeightCollapsed={canEngage ? "7.5rem" : "10rem"}
                  />
                </div>
              )}
              {activeTab === 'about' && (
                <div className={`text-sm text-novaNeutral-700 overflow-y-auto px-2 ${canEngage ? 'max-h-content max-h-[130px]' : 'max-h-content max-h-[200px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
                  <TruncatedContent
                    split={false}
                    content={displayLawyer.lawyer_about || displayLawyer.about_lawyer || "No information available."}
                    maxHeightCollapsed={canEngage ? "7.5rem" : "10rem"}
                  />
                </div>
              )}
            </div>
            </div>

            {/* Action Buttons - always at bottom; when content is small, spacer above keeps them separate */}
            <div className="mt-auto pt-2 flex flex-col 3xl:flex-row gap-2">
              {onEngageWithExpert && canEngage && (
                <FormButton
                  variant="primary"
                  onClick={() => {
                    onEngageWithExpert?.(displayLawyer.lawyer_id);
                    if (isProfileModalOpen) setIsProfileModalOpen(false);
                  }}
                  disabled={isEngaging}
                  className="w-full h-10 text-sm bg-novaNeutral-800 hover:bg-novaNeutral-900 text-white whitespace-nowrap"
                >
                  <span className="hidden sm:block md:hidden xl:block"><i className="fas fa-user-check mr-2"></i>Choose {lawyerFirstName} as my Nova Expert</span>
                  <span className="block xl:hidden sm:hidden md:block"><i className="fas fa-user-check mr-2"></i>Choose {lawyerFirstName}</span>
                </FormButton>
              )}
              {canTalkToLawyer && (
                <FormButton
                  variant="outline"
                  onClick={() => {
                    setIsVerificationPopupOpen(true);
                  }}
                  className="w-full h-10 text-sm border-novaNeutral-300 text-novaNeutral-700 hover:bg-novaNeutral-50"
                >
                  <i className="fas fa-phone-flip mr-2"></i>
                  Request 15-min intro call
                </FormButton>
              )}
            </div>
          </div>
        </div>
      );
    }
    
    // Render multiple lawyers layout (original vertical layout)
    return (
    <div className={`rounded-xl bg-white overflow-hidden flex flex-col ${className}`} style={{ userSelect: 'none' }}>
      {/* Photo Section with Name Overlay */}
      <div className="relative w-full h-80 overflow-hidden">
        {displayLawyer.lawyer_photo_url ? (
          <img
            src={displayLawyer.lawyer_photo_url}
            alt={`${displayLawyer.lawyer_name} profile`}
            className="w-full max-w-full sm:max-w-[380px] h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-full max-w-[380px] h-full bg-novaNeutral-200 flex items-center justify-center">
            <i className="fas fa-user text-novaNeutral-400 text-6xl" aria-label="No profile photo"></i>
          </div>
        )}
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent"></div>
        {/* Radial Gradients at Bottom */}
        <div 
          className="absolute bottom-0 left-0 w-full h-2/3 pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse 150% 100% at bottom left,rgb(223, 120, 24), transparent 65%)'
          }}
        ></div>
        <div 
          className="absolute bottom-0 right-0 w-[200%] h-full pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse 150% 100% at bottom right,rgba(216, 36, 4, 0.43), transparent 30%)'
          }}
        ></div>
        {/* Name Overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <h3 className="text-white text-[30px] font-nineties line-clamp-1" title={displayLawyer.lawyer_name}>{displayLawyer.lawyer_name}</h3>
        </div>
      </div>

      {/* Lawyer Expert Type and Experience */}
      <div className="px-4 pt-3 pb-2 flex flex-wrap gap-6 text-sm text-novaNeutral-600 my-2">
        {/* <div className="flex flex-col gap-0.5 max-w-[50%]">
          {lawyerExpertTypesArr.length > 0
            ? lawyerExpertTypesArr.map((type) => (
                <span key={type} className="text-novaDarkOrange font-bold sm:text-[14px] text-xs">
                  {type}
                </span>
              ))
            : <span className="text-novaDarkOrange font-bold sm:text-[14px] text-xs">N/A</span>}
        </div> */}
        <div className="flex flex-col gap-0">
          <div className="flex items-center gap-2"><i className="fas fa-medal text-novaDarkOrange" aria-hidden></i> <span className="text-novaDarkOrange font-bold sm:text-[14px] text-xs">Experience</span></div>
          <div className="text-xs sm:text-sm mt-1">{displayLawyer.lawyer_experience || "N/A"}</div>
        </div>
        {/* {displayLawyer.lawyer_rate && (
          <div className="flex-col items-center gap-4">
            <div><i className="fas fa-money-bill-wave text-novaDarkOrange"></i> <span className="text-novaDarkOrange font-bold sm:text-[14px] text-xs">Rate</span></div>
            <div className="mt-1 text-xs sm:text-sm">{formatCurrency("pound", displayLawyer.lawyer_rate)} / hour</div>
          </div>
        )} */}
      </div>

      {/* Tabs */}
      <div className="px-4 flex">
        <button
          onClick={() => setActiveTab('specialisms')}
          className={`px-3 py-2 sm:text-sm text-xs transition-colors
            ${
              activeTab === 'specialisms'
                ? 'text-novaNeutral-900 font-medium border-t border-l border-r border-novaNeutral-200 rounded-t-md bg-white'
                : 'text-novaNeutral-400 font-medium hover:text-novaNeutral-900 border-b border-novaNeutral-200'
            }`}
          style={activeTab === 'specialisms'
            ? { borderBottom: 'none' }
            : { borderTop: "none", borderLeft: "none", borderRight: "none" }
          }
        >
          Specialisms
        </button>
        <button
          onClick={() => setActiveTab('testimonial')}
          className={`px-3 py-2 sm:text-sm text-xs transition-colors
            ${
              activeTab === 'testimonial'
                ? 'text-novaNeutral-900 font-medium border-t border-l border-r border-novaNeutral-200 rounded-t-md bg-white'
                : 'text-novaNeutral-400 font-medium hover:text-novaNeutral-900 border-b border-novaNeutral-200'
            }`}
          style={activeTab === 'testimonial'
            ? { borderBottom: 'none' }
            : { borderTop: "none", borderLeft: "none", borderRight: "none" }
          }
        >
          Testimonial
        </button>
        <button
          onClick={() => setActiveTab('about')}
          className={`px-3 py-2 sm:text-sm text-xs transition-colors
            ${
              activeTab === 'about'
                ? 'text-novaNeutral-900 font-medium border-t border-l border-r border-novaNeutral-200 rounded-t-md bg-white'
                : 'text-novaNeutral-400 font-medium hover:text-novaNeutral-900 border-b border-novaNeutral-200'
            }`}
          style={activeTab === 'about'
            ? { borderBottom: 'none' }
            : { borderTop: "none", borderLeft: "none", borderRight: "none" }
          }
        >
          About
        </button>
        <div className="flex-1 border-b border-novaNeutral-200"></div>
      </div>

      {/* Tab Content */}
      <div className="px-4 py-4 flex-1">
        {activeTab === 'specialisms' && (
          <div className="flex flex-row gap-4">
            <div className="min-w-0 flex-1 pl-2">
              <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1">
                <i className="fas fa-circle-check mr-1"></i>
                Expert Type 
              </span>
              <p className={`text-sm text-novaNeutral-700 overflow-y-auto px-1 ${canEngage ? 'max-h-content max-h-[130px]' : 'max-h-content max-h-[140px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
                <TruncatedContent
                  content={
                    Array.isArray(displayLawyer.lawyer_expert_types) && (displayLawyer.lawyer_expert_types as string[]).length > 0
                      ? (displayLawyer.lawyer_expert_types as string[]).join(", ")
                      : displayLawyer.lawyer_expert_types
                        ? String(displayLawyer.lawyer_expert_types)
                        : "N/A"
                  }
                  maxHeightCollapsed={canEngage ? "6.5rem" : "7.5rem"}
                />
              </p>
            </div>
            <div className="min-w-0 flex-1">
              <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1 min-w-[100px]">
                <i className="fas fa-graduation-cap mr-1"></i>
                Expertise
              </span>
              <p className={`text-sm text-novaNeutral-700 overflow-y-auto px-1 ${canEngage ? 'max-h-content max-h-[120px]' : 'max-h-content max-h-[140px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
                <TruncatedContent
                  content={
                    Array.isArray(displayLawyer.lawyer_expertises) && displayLawyer.lawyer_expertises.length > 0
                      ? displayLawyer.lawyer_expertises.join(", ")
                      : displayLawyer.lawyer_expertises
                        ? String(displayLawyer.lawyer_expertises)
                        : "N/A"
                  }
                  maxHeightCollapsed={canEngage ? "6rem" : "7.5rem"}
                />
                </p>
            </div>
          </div>
        )}
        {activeTab === 'testimonial' && (
          <div className="border-l border-novaDarkOrange pl-4">
          <div className="text-sm text-novaNeutral-700 italic">
          <p className={`text-sm text-novaNeutral-700 overflow-y-auto px-1 ${canEngage ? 'max-h-content max-h-[130px]' : 'max-h-content max-h-[140px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
            <TruncatedContent
              split={false}
              content={displayLawyer.lawyer_testimonial || "No testimonial available."}
              maxHeightCollapsed={canEngage ? "7.5rem" : "8.75rem"}
              contentClassName="leading-6"
            />
          </p>
          </div>
          </div>
        )}
        {activeTab === 'about' && (
          <div className=""> 
          <p className={`text-sm text-novaNeutral-700 overflow-y-auto px-1 ${canEngage ? 'max-h-content max-h-[130px]' : 'max-h-content max-h-[140px]'} scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
            <TruncatedContent
              split={false}
              content={displayLawyer.lawyer_about || displayLawyer.about_lawyer || "No information available."}
              maxHeightCollapsed={canEngage ? "7.5rem" : "8.75rem"}
              contentClassName="leading-6"
            />
          </p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
        {onEngageWithExpert && canEngage && (
          <div className="px-4 pb-4 space-y-2 mt-auto">
          <FormButton
            variant="primary"
            onClick={() => {
              onEngageWithExpert?.(displayLawyer.lawyer_id);
              if (isProfileModalOpen) setIsProfileModalOpen(false);
            }}
            disabled={isEngaging}
            className="w-full h-10 text-sm bg-novaNeutral-800 hover:bg-novaNeutral-900 text-white"
          >
            <span className="hidden sm:block"><i className="fas fa-user-check mr-2"></i>Choose {lawyerFirstName} as my Nova Expert</span>
            <span className="block sm:hidden"><i className="fas fa-user-check mr-2"></i>Choose {lawyerFirstName}</span>
          </FormButton>
          </div>
        )}
        {canTalkToLawyer && (
          <div className="px-4 pb-4 space-y-2 mt-auto">
          <FormButton
            variant="outline"
            onClick={() => {
              setIsVerificationPopupOpen(true);
            }}
            className="w-full h-10 text-sm border-novaNeutral-300 text-novaNeutral-700 hover:bg-novaNeutral-50"
          >
            <i className="fas fa-phone-flip mr-2"></i>
            Request 15-min intro call
          </FormButton>
          </div>
        )}
      </div>
    );
  };

  const handleTalkToLawyer = async (phoneNumber: string) => {
    try {
      const response = await api.post(`/v1/customer/talk_to_lawyer`, {
        lawyer_id: modalLawyer.lawyer_id,
        case_id: id,
        phone: phoneNumber,
      }) as ApiResponse;

      // Helper to show toasts with delay
      const showToastsWithDelay = async (
        messages: MessageItem[],
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

      if (response.success) {
        // Handle array of messages
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, true);
        } else {
          // Fallback for single message (backward compatibility)
          const toast = createSuccessToast(
            "Success",
            response.message || "Requested call with Lawyer"
          );
          toastManager.addToast(toast);
        }
      } else {
        // Handle error case
        if (Array.isArray(response.message)) {
          await showToastsWithDelay(response.message, false);
        } else {
          const toast = createErrorToast(
            "Error",
            response.message || "Failed to request call with Lawyer"
          );
          toastManager.addToast(toast);
        }
      }
    } catch (error: any) {
      let errorMessage = "Failed to request call with Lawyer. Please try again.";

      if (error?.message) {
        // Try to extract the message from the error string (which may be a JSON string)
        const match = error.message.match(/"message"\s*:\s*"([^"]*)"/);
        if (match && match[1]) {
          errorMessage = match[1];
        } else {
          errorMessage = error.message;
        }
      }
      // const toast = createErrorToast("Error", errorMessage);
      // toastManager.addToast(toast);
    }
  };

  return (
    <div className="w-full h-full {singleLawyer ? 'sm:max-h-[350px]' : 'max-h-full'} flex flex-col">
      <FullProfileCard className="flex-1 flex flex-col" />

      <FullScreenModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
      >
        <div className="bg-white h-full sm:h-auto sm:bg-transparent sm:rounded-lg overflow-hidden">
          <FullProfileCard className="shadow-2xl h-full sm:h-auto sm:max-h-[80vh] overflow-y-auto border-0 sm:border" />
        </div>
      </FullScreenModal>

      <PhoneVerificationPopup
        isOpen={isVerificationPopupOpen}
        onClose={() => setIsVerificationPopupOpen(false)}
        onVerify={handleTalkToLawyer}
        lawyerName={modalLawyer.lawyer_name}
        onAfterVerify={() => setIsProfileModalOpen(false)}
      />
    </div>
  );
};

export default LawyersAutoScrollCard;