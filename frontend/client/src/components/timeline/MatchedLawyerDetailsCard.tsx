import { MatchConfirmedLawyerType } from "@/lib/types";
import React from "react";

interface MatchedLawyerDetailsCardProps {
  lawyer: MatchConfirmedLawyerType;
  isSelected?: boolean;
  onClick?: (lawyerId: string) => void;
}

const MatchedLawyerDetailsCard: React.FC<MatchedLawyerDetailsCardProps> = ({
  lawyer,
  isSelected = false,
  onClick,
}) => {
  const handleClick = () => {
    if (onClick) {
      onClick(lawyer.lawyer_id);
    }
  };

  return (
    <div
      className={`p-3 rounded-lg border transition-colors cursor-pointer ${
        isSelected
          ? "border-novaBlue-300 bg-novaBlue-50"
          : "border-novaGray-200 hover:border-novaGray-300"
      }`}
      onClick={handleClick}
    >
      <div className="flex items-center gap-3">
        <img
          src={lawyer.lawyer_photo_urls?.thumbnail}
          alt={lawyer.lawyer_name}
          className="w-10 h-10 rounded-full object-cover"
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="text-sm font-semibold text-novaGray-900">
                {lawyer.lawyer_name}
              </h4>
              <p className="text-xs text-novaTextGray">
                {lawyer.lawyer_expert_type}
              </p>
              <p className="text-xs text-novaBlue-600 font-medium">
                {lawyer.lawyer_specialization}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-novaTextGray">
                {lawyer.lawyer_location}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchedLawyerDetailsCard;
