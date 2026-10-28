import React from "react";
import { Link } from "wouter";
import { FormButton } from "../../../utils/formComponents";
import GlobalModalWrapper from "../../modal/GlobalModalWrapper";

interface CaseCreatedSuccessModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId?: string;
}

const CaseCreatedSuccessModal: React.FC<CaseCreatedSuccessModalProps> = ({
  isOpen,
  onClose,
  caseId,
}) => {
  return (
    <GlobalModalWrapper isOpen={isOpen} onClose={onClose}>
      <div className="bg-white rounded-full shadow-2xl max-w-md w-full p-10 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-novaNeutral-400 hover:text-novaNeutral-600 transition-colors"
        >
          <i className="fas fa-times text-xl"></i>
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-xl font-bold text-novaNeutral-900 mb-4">
            Case Created!
          </h2>
          
          {/* Success Icon */}
          <div className="w-16 h-16 bg-novaSuccess-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <i className="fas fa-check text-2xl text-novaSuccess-600"></i>
          </div>
        </div>

        {/* Main Message */}
        <div className="text-center mb-6">
          <h3 className="text-2xl font-bold text-novaNeutral-900 mb-3">
            New Case Created!
          </h3>
          <p className="text-novaNeutral-600 text-sm leading-relaxed">
            Your consultation request has been converted into a new case. We will find the best match lawyer for your case and get back to you within 24 hours.
          </p>
        </div>

        {/* What happens next section */}
        <div className="bg-novaSuccess-50 border border-novaSuccess-200 rounded-lg p-4 mb-10">
          <h4 className="text-sm font-bold text-novaSuccess-800 mb-3">
            What happens next?
          </h4>
          <div className="space-y-2">
            <div className="flex items-start space-x-2">
              <i className="fas fa-users text-novaSuccess-600 text-xs"></i>
              <p className="text-xs text-novaSuccess-700">
                We'll match you with qualified attorneys in your area
              </p>
            </div>
            <div className="flex items-start space-x-2">
              <i className="fas fa-envelope text-novaSuccess-600 text-xs"></i>
              <p className="text-xs text-novaSuccess-700">
                You'll receive an email with attorney recommendations
              </p>
            </div>
            <div className="flex items-start space-x-2">
              <i className="fas fa-calendar text-novaSuccess-600 text-xs"></i>
              <p className="text-xs text-novaSuccess-700">
                Schedule your initial consultation at your convenience
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3">
          {caseId && (
            <Link href={`/case/${caseId}`}>
              <FormButton
                type="button"
                variant="success"
                size="lg"
                className="w-full text-sm text-white"
              >
                <i className="fas fa-folder text-sm mr-2"></i>
                <span>View Case</span>
              </FormButton>
            </Link>
          )}
        </div>
      </div>
    </GlobalModalWrapper>
  );
};

export default CaseCreatedSuccessModal;
