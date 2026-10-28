
import { FormButton } from "@/utils";
import React, { useState } from "react";
import ResolveEmailConfirmationModal from "./ResolveEmailConfirmationModal";
import { api } from "@/lib/api";

interface ResolveBookingCardProps {
  resolveId?: string | null;
  summary?: string;
  title?: string;
  caseId?: string;
  storedEmail?: string | null;
  userName?: string;
  partnerName?: string;
  affordability?: string;
}

const ResolveBookingCard: React.FC<ResolveBookingCardProps> = ({
  resolveId,
  summary,
  title,
  caseId,
  storedEmail,
  userName,
  partnerName,
  affordability,
}) => {
  const RESOLVE_SESSION_KEY = "resolve_session_data";
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoginLinkSent, setIsLoginLinkSent] = useState(false);
  const [showAffordability, setShowAffordability] = useState(false);
  
  const handleScrollToLawyers = () => {
    const lawyersSection = document.getElementById("lawyers-section");
    if (lawyersSection) {
      lawyersSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };
  const handleCloseBookingModal = () => {
    setIsModalOpen(false);
    // Reset to default false when closing modal
    setIsLoginLinkSent(false);
  };

  return (
    <div className="flex flex-col items-center w-full sm:px-4 px-0 mb-2 md:mb-0 gap-8">

      {/* Recommendation Card */}
      <div className="w-full max-w-[904px]">
        <div
          className="relative bg-transparent sm:border-[18px] border-[10px] rounded-[30px]"
          style={{ borderColor: "rgb(255 255 255 / 41%)" }}
        >
          <div className="bg-white rounded-[18px] sm:rounded-[14px] px-6 py-8 sm:px-20 sm:py-12 flex flex-col justify-center items-center text-center gap-6">
            <p className="text-base sm:text-lg text-novaNeutral-700 leading-relaxed max-w-xl">
            Our recommended approach for you, {userName}.
            </p>
            <div className="flex flex-col gap-6 max-w-2xl mx-auto">
              <div className="text-4xl sm:text-5xl xl:text-[54px] font-nineties text-novaBlack leading-tight w-[90%] lg:w-[45%] mx-auto">
                <p>{title}</p>
              </div>
              <p className="text-base sm:text-lg text-novaNeutral-700 leading-relaxed text-left">
                <span
                  className="block"
                  dangerouslySetInnerHTML={{ __html: summary || "" }}
                />
              </p>
            </div>

            {/* Affordability Section */}
            <div className="w-full max-w-2xl mt-2">
              <button
                type="button"
                className="w-full flex gap-1 md:gap-3 items-center sm:px-4 px-0 py-3 justify-center whitespace-nowrap"
                onClick={() => setShowAffordability((prev) => !prev)}
                aria-expanded={showAffordability}
                aria-controls="affordability-panel"
              >
                <span className="text-[20px] sm:text-[22px] leading-tight font-nineties tracking-wider font-semibold">A word about affordability</span>
                <span className={`ml-2 transition-transform duration-500 ease-in-out ${showAffordability ? 'rotate-180' : 'rotate-0'}`}>
                  <i className="fas fa-chevron-down text-sm"></i>
                </span>
              </button>
              <div
                id="affordability-panel"
                className={`transition-all duration-500 ease-in-out overflow-hidden ${showAffordability ? 'opacity-100 max-h-[3000px] mt-4' : 'max-h-0 opacity-0 mt-0'}`}
                aria-hidden={!showAffordability}
              >
                <div className="text-base sm:text-[18px] py-2 text-left leading-relaxed">
                  <p className="mb-6">Divorce and separation pathways vary significantly in cost, ranging from direct negotiation as the most affordable option to court proceedings as the most expensive. Let's see where {title} falls on this cost spectrum.</p>
                  {affordability ? (
                    <div dangerouslySetInnerHTML={{ __html: affordability }} />
                  ) : (
                    <span>No affordability summary available for this pathway.</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <p className="text-base sm:text-lg text-novaNeutral-700 leading-relaxed text-center max-w-[56%] mx-auto italic">
        Nova provides AI-generated guidance to help you understand possible dispute resolution pathways. It does not provide regulated legal advice. A qualified legal professional will advise you on your specific legal rights and best options.
      </p>
      <ResolveEmailConfirmationModal
        isOpen={isModalOpen}
        onClose={handleCloseBookingModal}
        resolveId={resolveId}
        isLoginLinkSent={isLoginLinkSent}
        email={storedEmail}
      />
    </div>
  );
};

export default ResolveBookingCard;