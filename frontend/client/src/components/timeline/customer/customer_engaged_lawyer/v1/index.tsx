import React, { useState } from "react";
import { CustomerEngagedLawyerTimelineProps } from "@/lib/types";
import { formatTimestamp } from "@/utils/formatedDate";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import { TruncatedContent } from "@/components/ui";

type TabType = "about" | "testimonial" | "specialisms";

const CustomerEngagedLawyer: React.FC<CustomerEngagedLawyerTimelineProps & { isLatest?: boolean }> = ({
  timelineData,
  isLatest,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>("specialisms");
  const { meta_data } = timelineData;

  const expertisesArr = Array.isArray((meta_data.lawyer_profile as any).lawyer_expertises)
    ? ((meta_data.lawyer_profile as any).lawyer_expertises as string[])
    : (meta_data.lawyer_profile as any).lawyer_expertises ? [String((meta_data.lawyer_profile as any).lawyer_expertises)] : [];
  const accreditationsArr = Array.isArray((meta_data.lawyer_profile as any).lawyer_accreditations)
    ? ((meta_data.lawyer_profile as any).lawyer_accreditations as string[])
    : (meta_data.lawyer_profile as any).lawyer_accreditations ? [String((meta_data.lawyer_profile as any).lawyer_accreditations)] : [];

  const lawyerExpertTypesArr = meta_data.lawyer_profile.lawyer_expert_types && Array.isArray(meta_data.lawyer_profile.lawyer_expert_types)
    ? meta_data.lawyer_profile.lawyer_expert_types.flatMap((item) =>
        String(item).split(",").map((s) => s.trim()).filter(Boolean)
      )
    : [];

  const actionBy =
    timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;

  const lawyerName = meta_data.lawyer_profile.lawyer_name;
  const customerName = (meta_data as any).first_name || "there";

  const renderTabContent = () => {
    switch (activeTab) {
      case "about":
        return (
          <div>
            <TruncatedContent
              split={false}
              content={meta_data.lawyer_profile.lawyer_about || "No information available."}
              maxHeightCollapsed="10rem"
            />
          </div>
        );
      case "testimonial":
        return (
          <TruncatedContent
            split={false}
            content={(meta_data.lawyer_profile as any).lawyer_testimonial || "No testimonial available."}
            maxHeightCollapsed="10rem"
          />
        );
      case "specialisms":
        return (
          <div className="flex xl:flex-row md:flex-col flex-row gap-4">
            <div className="min-w-0 flex-1 overflow-y-auto lg:max-h-[170px] max-h-[210px]">
              <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1">
                <i className="fas fa-circle-check"></i> Expert Type
              </span>
              <TruncatedContent
                content={lawyerExpertTypesArr.length > 0 ? lawyerExpertTypesArr.join(", ") : "N/A"}
                maxHeightCollapsed="8.5rem"
              />
            </div>
            <div className="min-w-0 flex-1 overflow-y-auto lg:max-h-[170px] max-h-[210px]">
              <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1 min-w-[100px]">
                <i className="fas fa-graduation-cap"></i> Expertise
              </span>
              <TruncatedContent
                content={expertisesArr.length > 0 ? expertisesArr.join(", ") : "N/A"}
                maxHeightCollapsed="8.5rem"
              />
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        {/* Header */}
        <div className="flex gap-2">
          <i className="fas fa-check-circle text-[#1A1425] text-xl"></i>
          <span className="sm:text-[28px] text-xl font-semibold items-center text-[#1A1425]">
          You’ve chosen {lawyerName} to be your Nova Expert
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />

        {/* Description paragraphs */}
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          Your next step is a Strategic Advice Consultation with {lawyerName} – a focused, one-hour session designed to give you clear, personalised options and a recommended next step, without pressure or obligation to take things further.        </p>
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          After your consultation, you’ll also receive a Recommendations & Next Steps Letter of Advice within 48 hours – giving you something tangible to return to, reflect on, or share if needed.
        </p>
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          There’s no rush to book. When you feel ready, you can secure your consultation with a small deposit.
        </p>
        <p className="text-md leading-6 text-novaNeutral-700 mb-6">
          We’ll then be in touch to confirm available dates and times for your session with {lawyerName}.
        </p>

        {/* Lawyer Profile Card */}
        <div className="flex flex-col md:flex-row gap-0 bg-white rounded-lg overflow-hidden border border-novaNeutral-200">
          {/* Left side - Photo with name overlay */}
          <div className="relative md:w-[350px] w-full h-[350px] md:h-[350px] flex-shrink-0 overflow-hidden">
            {meta_data.lawyer_profile.lawyer_photo_url ? (
              <img
                src={meta_data.lawyer_profile.lawyer_photo_url}
                alt={lawyerName}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-novaNeutral-200 flex items-center justify-center">
                <i className="fas fa-user text-novaNeutral-400 text-6xl"></i>
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
              <h3 className="text-3xl font-nineties text-white drop-shadow-lg line-clamp-1" title={lawyerName}>
                {lawyerName}
              </h3>
            </div>
          </div>

          {/* Right side - Details */}
          <div className="flex-1 p-4 md:p-5">
            {/* Lawyer Expert Type and Experience */}
            <div className="flex flex-wrap gap-6">
              {/* <div className="flex flex-col gap-0.5">
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
                  {meta_data.lawyer_profile.lawyer_experience || "N/A"}
                </span>
              </div>
              {/* <div className="items-center gap-2">
                <div className="flex items-center gap-2">
                <i className="fa-solid fa-money-bill-wave text-novaDarkOrange text-sm"></i>
                  <span className="sm:text-sm text-xs text-novaDarkOrange font-medium">Rate</span>
                </div>
                <span className="text-xs sm:text-sm text-novaNeutral-700">
                  {formatCurrency("pound", meta_data.lawyer_profile.lawyer_rate)} / hour
                </span>
              </div> */}
            </div>
            <div className="flex items-center gap-6 mb-4">
              
              
            </div>

            {/* Tabs */}
            <div className="relative mb-6">
              <div className="flex">
                <button
                  onClick={() => setActiveTab("specialisms")}
                  className={`px-3 py-1.5 sm:text-sm text-xs transition-colors relative font-medium ${
                    activeTab === "specialisms"
                      ? "text-[#1A1425] bg-white border-t border-l border-r border-novaNeutral-200 rounded-t-sm z-10"
                      : "text-novaNeutral-400 hover:text-novaNeutral-600 border-b border-novaNeutral-200"
                  }`}
                >
                  Specialisms
                </button>
                <button
                  onClick={() => setActiveTab("testimonial")}
                  className={`px-3 py-1.5 sm:text-sm text-xs transition-colors relative font-medium ${
                    activeTab === "testimonial"
                      ? "text-[#1A1425] bg-white border-t border-l border-r border-novaNeutral-200 rounded-t-sm z-10"
                      : "text-novaNeutral-400 hover:text-novaNeutral-600 border-b border-novaNeutral-200"
                  }`}
                >
                  Testimonial
                </button>
                <button
                  onClick={() => setActiveTab("about")}
                  className={`px-3 py-1.5 sm:text-sm text-xs transition-colors relative font-medium ${
                    activeTab === "about"
                      ? "text-[#1A1425] bg-white border-t border-l border-r border-novaNeutral-200 rounded-t-sm z-10"
                      : "text-novaNeutral-400 hover:text-novaNeutral-600 border-b border-novaNeutral-200"
                  }`}
                >
                  About
                </button>
                {/* Fill remaining space with bottom border */}
                <div className="flex-1 border-b border-novaNeutral-200"></div>
              </div>
            </div>

            {/* Tab Content */}
            <div className={`${activeTab === "testimonial" ? "border-l border-novaDarkOrange pl-4 pr-2" : ""} text-sm leading-6 text-novaNeutral-700 overflow-y-auto lg:max-h-[170px] max-h-[210px] scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100`}>
              {renderTabContent()}
            </div>
          </div>
        </div>

        {/* Timestamp */}
        <p className="text-xs mt-4 flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(meta_data.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default CustomerEngagedLawyer;
