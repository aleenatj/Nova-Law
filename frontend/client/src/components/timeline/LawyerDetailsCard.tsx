import { Button } from "@/components";
import React from "react";
import { LawyerDetailsDisplayCardType } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
import { FormButton } from "@/utils/formComponents";
import { TruncatedContent } from "@/components/ui";

export type LawyerDetailsCardProps = {
  lawyer: LawyerDetailsDisplayCardType;
  buttonConfig: {
    text: string;
    type: "Remove" | "Add";
    onClick: () => void;
    icon?: string;
    disabled?: boolean;
  };
  // onRemove: () => void;
  variant: "search" | "selected";
};

const LawyerDetailsCard: React.FC<LawyerDetailsCardProps> = ({
  lawyer,
  buttonConfig,
  // onRemove,
  variant = "selected", // Default to selected (novaSuccess background)
}) => {
  // Dynamic background styling based on variant
  const backgroundClasses =
    variant === "search"
      ? "border rounded-lg p-4 bg-novaInactive border-novaDarkAmber"
      : "border rounded-lg p-4 bg-novaActive border-novaDarkAmber";

  // Dynamic profile image border color based on variant
  const profileImageBorderClass =
    variant === "search" ? "border-novaDarkAmber" : "border-novaDarkOrange";

  return (
    <div className={backgroundClasses}>
      <div className="flex items-start gap-3">
        {/* Profile Image */}
        {lawyer.photo_urls  ? (
          <img
            src={lawyer.photo_urls?.thumbnail}
            alt={lawyer.first_name}
            className={`w-12 h-12 rounded-full object-cover border-2 ${profileImageBorderClass}`}
          />
        ) : (
          <div className="flex w-12 h-12 rounded-full bg-novaGray-100 items-center justify-center">
            <i className="fa-solid fa-circle-user text-4xl text-novaGray-900"></i>
          </div>
        )}
        {/* Lawyer Details */}
        <div className="flex-1">
          {/* Name and Remove Button */}
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-black">
              {lawyer.first_name && lawyer.last_name
                ? `${lawyer.first_name} ${lawyer.last_name}`
                : lawyer.first_name || lawyer.last_name || "Lawyer Name"}
            </h4>
            {buttonConfig && (
              <FormButton
                variant="custom"
                onClick={buttonConfig?.onClick}
                disabled={buttonConfig?.disabled}
                className={`${
                  buttonConfig?.type === "Add"
                  ? "text-white text-xs sm:text-sm whitespace-nowrap bg-gradient-to-r from-[#FF6A42] to-[#FC3C3F] cursor-pointer hover:bg-gradient-to-r hover:from-novaBlack hover:to-novaBlack hover:text-white"
                  : "inline-flex items-center bg-novaInactive justify-center gap-2 whitespace-nowrap text-sm ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 border hover:text-white h-9 px-3 text-novaPrimary-600 border-novaPrimary-500 hover:bg-novaBlack hover:border-novaBlack"
                }`}
              >
                {buttonConfig?.icon && !buttonConfig?.disabled && (
                  buttonConfig?.type === "Add" ? (
                    <i className="fas fa-plus mr-1"></i>
                  ) : (
                    <i className="fas fa-times"></i>
                  )
                )}
                {buttonConfig?.text || "Remove"}
              </FormButton>
            )}
          </div>

          <div className="flex items-center gap-2 text-sm text-novaGray-600 mb-2">
            <span className="flex items-center"></span>
            <span>•</span>
            {lawyer.experience != null ? (
              // if experience is not specified then show "Experience not specified"
              lawyer.experience === "Not specified" ? (
                <span>Experience not specified</span>
              ) : (
                <span>{lawyer.experience}</span>
              )
            ) : (
              <span>Experience not available</span>
            )}
            {/* <span>•</span>
            {lawyer.hourly_rate != null ? (
              <span>{formatCurrency("pound", lawyer.hourly_rate)} per hour</span>
            ) : (
              <span>Rate not available</span>
            )} */}
          </div>

          {/* Specialisation and Location Grid */}
          <div className="grid sm:grid-cols-2  gap-4 text-sm mb-2">
            <div>
              <span className="text-novaMutedSlate">Expert Types:</span>
              <div className="font-medium">
                <TruncatedContent
                  content={
                    lawyer.expert_types_all && lawyer.expert_types_all.length > 0
                      ? lawyer.expert_types_all.join(", ")
                      : "Not specified"
                  }
                  maxHeightCollapsed="5rem"
                  disableSeeMore={false}
                />
              </div>
            </div>
            <div>
              <span className="text-novaMutedSlate">Location:</span>
              <div className="font-medium">
                {[lawyer.country, lawyer.county, lawyer.city]
                  .filter(Boolean)
                  .join(", ") || "Not specified"}
              </div>
            </div>
          </div>

          {/* Description */}
          <p className="text-sm text-novaMutedSlate">
            {lawyer.about || "No description available"}
          </p>
        </div>
      </div>
    </div>
  );
};

export default LawyerDetailsCard;
