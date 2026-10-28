import React, { useState } from "react";
import type { Lawyer } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
import { FormButton } from "@/utils";
import { TruncatedContent } from "@/components/ui";

interface LawyerProfileDetailProps {
  lawyer: Lawyer;
  onEngageWithExpert?: (lawyerId?: string) => void;
  isEngaging?: boolean;
  canEngage?: boolean;
  onRequestCall?: () => void;
}

const LawyerProfileDetail: React.FC<LawyerProfileDetailProps> = ({
  lawyer,
  onEngageWithExpert,
  isEngaging = false,
  canEngage = false,
  onRequestCall,
}) => {
  const [activeTab, setActiveTab] = useState<'specialisms' | 'testimonial' | 'about'>('specialisms');

  // Map Lawyer type to display properties
  const lawyerName = `${lawyer.first_name} ${lawyer.last_name}`;
  const lawyerPhotoUrl = lawyer.photo_urls?.large || lawyer.photo_urls?.medium || lawyer.photo_urls?.thumbnail;
  const lawyerExperience = lawyer.experience != null 
    ? lawyer.experience
    : 0;
  const lawyerRate = lawyer.hourly_rate;
  const lawyerAbout = lawyer.about;
  const lawyerTestimonial = lawyer.testimonial;
  const expertises: string[] = Array.isArray(lawyer.expertises_all) ? lawyer.expertises_all : (lawyer.expertises_all ?? []);
  const accreditedSpecialisms: string[] = Array.isArray(lawyer.accreditations) ? lawyer.accreditations : [];
  const lawyerExpertTypeDisplay = lawyer.expert_types_all && Array.isArray(lawyer.expert_types_all)
      ? lawyer.expert_types_all.flatMap((item) =>
          String(item).split(",").map((s) => s.trim()).filter(Boolean)
        )
      : [];

  return (
    <div className={`rounded-lg bg-white overflow-hidden flex flex-col w-full sm:w-[320px] md:w-[340px] h-full border border-novaNeutral-200`} style={{ userSelect: 'none' }}>
      {/* Photo Section with Name Overlay */}
      <div className="relative w-full h-80 overflow-hidden">
        {lawyerPhotoUrl ? (
          <img
            src={lawyerPhotoUrl}
            alt={`${lawyerName} profile`}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="w-full h-full bg-novaNeutral-200 flex items-center justify-center">
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
        <div className="absolute bottom-0 left-0 right-0 p-4 line-clamp-1">
          <h3 className="text-white text-[30px] font-nineties" title={lawyerName}>{lawyerName}</h3>
        </div>
      </div>

      {/* Lawyer Expert Type and Experience */}
      <div className="px-4 pt-3 pb-2 flex flex-wrap gap-6 text-sm text-novaNeutral-600 my-2">
        {/* <div className="flex flex-col gap-0.5 max-w-[50%]">
          {lawyerExpertTypeDisplay.length > 0
            ? lawyerExpertTypeDisplay.map((type) => (
                <span key={type} className="sm:text-sm text-xs text-novaDarkOrange font-bold">
                  {type}
                </span>
              ))
            : <span className="sm:text-sm text-xs text-novaDarkOrange font-bold">N/A</span>}
        </div> */}
        <div className="flex-col items-center gap-4">
          <div><i className="fas fa-medal text-novaDarkOrange" aria-hidden></i> <span className="text-novaDarkOrange font-bold sm:text-[14px] text-xs">Experience</span></div>
          <div className="mt-1 text-xs sm:text-sm">{lawyerExperience}</div>
        </div>
        {/* {lawyerRate && (
          <div className="flex-col items-center gap-4">
            <div><i className="fas fa-money-bill-wave text-novaDarkOrange"></i> <span className="text-novaDarkOrange font-bold sm:text-[14px] text-xs">Rate</span></div>
            <div className="mt-1 text-xs sm:text-sm">{formatCurrency("pound", lawyerRate)} / hour</div>
          </div>
        )} */}
      </div>

      {/* Tabs */}
      <div className="px-4 flex">
        <button
          onClick={() => setActiveTab('specialisms')}
          className={`px-3 py-2 text-xs transition-colors
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
          className={`px-3 py-2 text-xs transition-colors
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
          className={`px-3 py-2 text-xs transition-colors
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
            <div className="min-w-0 flex-1 overflow-y-auto lg:max-h-[170px] max-h-[190px] pr-2">
              <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1"><i className="fas fa-circle-check"></i> Expert Type</span>
              <TruncatedContent
                content={lawyerExpertTypeDisplay.length > 0 ? lawyerExpertTypeDisplay.join(", ") : "N/A"}
                maxHeightCollapsed="6.5rem"
              />
            </div>
            <div className="min-w-0 flex-1 overflow-y-auto lg:max-h-[170px] max-h-[190px] pr-2">
              <span className="sm:text-[13px] text-xs font-bold text-novaDarkOrange block mb-1 min-w-[100px]">
                <i className="fas fa-graduation-cap mr-1"></i>
                Expertise
              </span>
              <TruncatedContent
                content={expertises.length > 0 ? expertises.join(", ") : "N/A"}
                maxHeightCollapsed="6.5rem"
              />
            </div>
          </div>
        )}
        {activeTab === 'testimonial' && (
          <div className="border-l border-novaDarkOrange pl-4">
          <div className="text-sm text-novaNeutral-700 italic overflow-y-auto lg:max-h-[170px] max-h-[210px] scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100 pr-2">
          <TruncatedContent
            split={false}
            content={lawyerTestimonial || "No testimonial available."}
            maxHeightCollapsed="7rem"
            contentClassName="leading-6"
          />
          </div>
          </div>
        )}
        {activeTab === 'about' && (
          <div className=""> 
          <p className="text-sm leading-6 text-novaNeutral-700 overflow-y-auto lg:max-h-[170px] max-h-[210px] scrollbar-thin scrollbar-thumb-novaNeutral-200 scrollbar-track-novaNeutral-100 pr-2">
            <TruncatedContent
              split={false}
              content={lawyerAbout || "No information available."}
              maxHeightCollapsed="7rem"
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
              onEngageWithExpert?.(lawyer.id);
            }}
            disabled={isEngaging}
            className="w-full h-10 text-sm bg-novaNeutral-800 hover:bg-novaNeutral-900 text-white"
          >
            <i className="fas fa-user-check mr-2"></i>
            Choose {lawyerName} as my Nova Expert
          </FormButton>
          </div>
        )}
        {onRequestCall && (
          <div className="px-4 pb-4 space-y-2 mt-auto">
          <FormButton
            variant="outline"
            onClick={() => {
              onRequestCall();
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

export default LawyerProfileDetail;
