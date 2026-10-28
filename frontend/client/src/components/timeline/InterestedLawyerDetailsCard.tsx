import React from "react";
import { InterestedLawyerType } from "@/lib/types";
import { TruncatedContent } from "@/components/ui";

interface InterestedLawyerDetailsCardProps {
  lawyer: InterestedLawyerType;
  isSelected: boolean;
  onSelect: (lawyerId: string) => void;
  isDisabled?: boolean;
}

const InterestedLawyerDetailsCard: React.FC<
  InterestedLawyerDetailsCardProps
> = ({ lawyer, isSelected, onSelect, isDisabled = false }) => {
  const handleClick = () => {
    if (!isDisabled) {
      onSelect(lawyer.id);
    }
  };

  return (
    <div
      className={`p-4 rounded-lg border transition-colors ${
        isDisabled
          ? "border-novaDarkAmber bg-novaInactive opacity-50 cursor-not-allowed"
          : isSelected
            ? "border-novaDarkOrange bg-novaActive cursor-pointer"
            : "bg-novaInactive border-novaDarkAmber hover:border-novaActive cursor-pointer"
      }`}
      onClick={handleClick}
      tabIndex={isDisabled ? -1 : 0}
      onKeyDown={e => {
        if (!isDisabled && (e.key === " " || e.key === "Enter")) {
          e.preventDefault();
          onSelect(lawyer.id);
        }
      }}
      role="checkbox"
      aria-checked={isSelected}
      aria-disabled={isDisabled}
      title={isDisabled ? "Maximum 3 lawyers can be selected" : undefined}
    >
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={e => {
            e.stopPropagation();
            if (!isDisabled) {
              onSelect(lawyer.id);
            }
          }}
          aria-checked={isSelected}
          disabled={isDisabled}
          className={`h-4 w-4 rounded-sm border-2 border-novaDarkOrange mt-1 accent-[var(--nova-red)] ${
            isDisabled ? "cursor-not-allowed" : "cursor-pointer"
          }`}
          id={`modal-lawyer-${lawyer.id}`}
          onClick={e => e.stopPropagation()}
        />

        <div className="flex-shrink-0">
         
          {lawyer.photo_urls?.thumbnail ? (
            <img
            src={lawyer.photo_urls?.thumbnail}
            alt=""
            className="w-16 h-16 rounded-full object-cover"
          />
          ) : (
            <span className="w-16 h-16 flex items-center justify-center rounded-full bg-novaGray-100 border border-novaNeutral-200">
              <i className="fas fa-user text-novaNeutral-500 text-3xl"></i>
            </span>
          )}
        </div>

        <div className="flex flex-col flex-1 min-w-0 min-h-full justify-between">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1">
              <h4 className="text-base font-semibold text-novaGray-900">
                {lawyer.first_name} {lawyer.last_name}
              </h4>
            </div>
            <div className="text-right"></div>
          </div>

          <div className="space-y-2 mb-3">
            <div className="flex items-start text-sm text-novaTextGray">
              <i className="fas fa-gavel mr-2 w-4 text-novaBlack mt-0.5 flex-shrink-0"></i>
              <span className="min-w-0 flex-1">
                <TruncatedContent
                  content={lawyer.expert_types && lawyer.expert_types.length > 0
                      ? lawyer.expert_types.join(", ")
                      : "Expert Types not specified"}
                  maxHeightCollapsed="5rem"
                  disableSeeMore={false}
                />
              </span>
            </div>
            <div className="flex items-center text-sm text-novaTextGray">
              <i className="fas fa-medal mr-2 w-4 text-novaSuccess-600 flex-shrink-0"></i>
              <span>{lawyer.experience_years == "Not specified" ? "Experience not specified" : lawyer.experience_years + " experience"} </span>
            </div>
            <div className="flex items-center text-sm text-novaTextGray">
              <i className="fas fa-map-marker-alt mr-2 w-4 text-novaCaution-500 flex-shrink-0"></i>
              <span>
                {(lawyer.city && lawyer.county)
                  ? `${lawyer.city}, ${lawyer.county}` 
                  : lawyer.city ? lawyer.city : lawyer.county ? lawyer.county : "Location not specified"}
              </span>
            </div>
          </div>
        </div>
      </div> 
      <div className="mb-3 p-3 bg-novaInactive rounded text-sm text-novaTextGray min-h-[60px]">
            <i className="fas fa-info-circle mr-2 text-novaNeutral-700"></i>
            {lawyer.about || "No additional information available."}
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-novaGray-200">
            <span className="text-xs text-novaSuccess-600">
              <i className="fas fa-heart mr-1"></i>Interested{" "}
              {lawyer.hours_to_interested} ago
            </span>
          </div>
    </div>
  );
};

export default InterestedLawyerDetailsCard;
