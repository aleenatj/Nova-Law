import React from "react";
import { CustomerInitialPaymentRequestedTimelineProps } from "@/lib/types";
import { formatCurrency } from "@/lib/utils";
import { formatTimestamp } from "@/utils/formatedDate";
import { Button } from "@/components";
import { api } from "@/lib/api";
import { FormButton } from "@/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";
import shieldIcon from "@/assets/ui/Shield.svg";

const CustomerInitialPaymentRequested: React.FC<
  CustomerInitialPaymentRequestedTimelineProps & { isLatest?: boolean }
> = ({ timelineData, isLatest }) => {
  const { meta_data, id } = timelineData;
  const actionBy =
  timelineData.action_user_role?.toLowerCase() === "navigator"
      ? "Nova Navigator"
      : timelineData.meta_data.action_by ||
        timelineData.action_user_name ||
        timelineData.action_user_role ||
        DEFAULT_ACTION_BY;

  const [isLoading, setIsLoading] = React.useState(false);
  const [showFailedAttemptsModal, setShowFailedAttemptsModal] = React.useState(false);

  const handlePayment = async () => {
    setIsLoading(true);
    try {
      // Make API call to get checkout URL
      const response = await api.get<{
        success: boolean;
        message: string;
        data: {
          checkout_session_url: string;
        };
      }>(
        // `/v1/payment/checkout?amount=${meta_data.amount_requested}&invoice_id=${meta_data.invoice_id}&event_id=${id}`
        `/v1/payment/checkout?amount=${meta_data.amount_requested}&payment_id=${meta_data.payment_id}`
      );

      if (response.success && response.data.checkout_session_url) {
        const checkoutUrl = response.data.checkout_session_url;

        // Redirect to Stripe checkout page
        window.location.href = checkoutUrl;
      } else {
        setIsLoading(false);
      }
    } catch (error) {
      console.error("Error fetching checkout URL:", error);
      setIsLoading(false);
    }
  };

  const lawyerName = meta_data.lawyer_name || "your expert";
  const amount = meta_data.amount_requested || 50;
  const totalFee = 299;
  const balanceFee = totalFee - Number(amount);

  return (
    <>
      {/* Failed Attempts Modal */}
      {showFailedAttemptsModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowFailedAttemptsModal(false)}
        >
          <div
            className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden p-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-novaNeutral-200">
              <div className="flex items-center gap-2">
                <i className="fas fa-exclamation-triangle text-novaCaution-600"></i>
                <h2 className="text-lg font-semibold text-novaNeutral-900">
                  Failed Attempts
                </h2>
              </div>
              <button
                onClick={() => setShowFailedAttemptsModal(false)}
                className="text-novaNeutral-500 hover:text-novaNeutral-700"
                aria-label="Close"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-4 overflow-y-auto max-h-[65vh]">
              <p className="text-sm text-novaNeutral-600 mb-4">
                The following payment attempts were unsuccessful. You can retry the payment using the "Pay Securely" button.
              </p>
              
              <div className="space-y-3 mb-4">
                {meta_data.failed_attempts?.map((attempt, index) => (
                  <div
                    key={attempt.transaction_id || index}
                    className="bg-novaCaution-50 border border-novaCaution-200 rounded-lg p-4"
                  >
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        <i className="fas fa-times-circle text-novaCaution-600"></i>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-semibold text-novaCaution-700 bg-novaCaution-100 px-2 py-1 rounded">
                            Attempt {index + 1}
                          </span>
                          <span className="text-xs text-novaNeutral-500">
                            {formatTimestamp(attempt.created_at || "")}
                          </span>
                        </div>
                        <p className="text-sm text-novaNeutral-700 mb-2">
                          <strong>Reason:</strong> {attempt.reason}
                        </p>
                        {attempt.transaction_id && (
                          <p className="text-xs text-novaNeutral-500">
                            <strong>Transaction ID:</strong> {attempt.transaction_id}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          {/* Header */}
          <div className="flex gap-2">
            <i className="fas fa-credit-card text-[#1A1425] text-xl"></i>
            <span className="sm:text-[28px] text-xl font-semibold text-[#1A1425]">
              {isLatest === true ? 'Next step: Secure your Strategic Advice Consultation' : 'Secure your Strategic Advice Consultation'}
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />

          {/* Description */}
          <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full lg:w-[70%]">
            To secure your Strategic Advice Consultation with <strong className="text-[#1A1425] break-words">{lawyerName}</strong>, a {formatCurrency("pound", amount)} deposit is required.<br />This deposit will be processed by Nova then held in the client account of Family Law Partners. Nova does not deduct any fees from this payment.
          </p>
          <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full lg:w-[70%]">
            {/* The total fixed fee for the Strategic Advice Consultation is {formatCurrency("pound", totalFee)} (including VAT).<br />
            The remaining balance will be paid to Family Law Partners after your consultation has taken place. */}
              The total fixed fee for the Strategic Advice Consultation is {formatCurrency("pound", totalFee)} (including VAT).<br />
              The remaining balance of {formatCurrency("pound", balanceFee)} is to be paid by you to Family Law Partners after your consultation has taken place.            
          </p>  
          <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full lg:w-[75%]">
            During your Strategic Advice Consultation, you’ll receive clear personalised advice and actionable options.
            Within 2 working days of the consultation, you’ll also receive a Recommendations & Next Steps Letter of Advice from <strong className="text-[#1A1425] break-words">{lawyerName}</strong> – giving you something tangible to return to, reflect on, or share if needed.
            <br />
            As a guide, consultations usually last around 1 hour, so don't feel rushed.
          </p>
          <p className="text-md leading-6 text-novaNeutral-700 mb-4 w-full lg:w-[70%]">
            There’s no obligation to proceed beyond the consultation.<br />
          </p>
          {/* <p className="text-md leading-6 text-novaNeutral-700 mb-4">
            Your deposit is fully protected by Nova's money-back guarantee (see full terms{" "}
            <a href="#" className="underline text-novaNeutral-700 hover:text-[#1A1425]">here</a>).
          </p> */}

         

          {/* What happens next section - COMMENTED OUT */}
          {/* <div className="bg-white rounded-lg p-3 mb-4 border border-novaDarkAmber">
            <div className="flex items-start gap-2">
              <i className="fas fa-info-circle text-novaDarkOrange text-sm mt-0.5"></i>
              <div className="text-sm leading-5 text-novaNeutral-900">
                <p className="font-medium mb-1">What happens next:</p>
                <ul className="space-y-1 list-disc list-inside">
                  <li>Secure payment processing via Stripe</li>
                  <li>
                    {meta_data.lawyer_name} will be notified immediately
                  </li>
                  <li>Initial consultation scheduled within 24 hours</li>
                  <li>Case work begins upon payment confirmation</li>
                </ul>
              </div>
            </div>
          </div> */}

          {/* Initial Payment Request section - COMMENTED OUT */}
          {/* <div className="text-sm mb-5 mt-4 text-novaNeutral-700">
            <div className="bg-white flex flex-col w-full rounded-lg p-3 border border-novaDarkAmber">
              <div className="flex items-start sm:items-center gap-2 mb-1">
                <i className="fas fa-wallet text-novaDarkOrange text-sm"></i>
                <span className="text-sm font-medium text-novaNeutral-900">Initial Payment Request</span>
              </div>
              <div className="flex flex-col justify-between w-full px-2 py-1">
                <div className="flex flex-row border-t border-novaDarkAmber font-medium justify-between w-full">
                  <div className="flex pt-2 text-novaNeutral-700 text-center align-middle items-center text-sm">
                    Initial Deposit:
                  </div>
                  <div className="font-semibold pt-2 text-xl text-novaNeutral-900">
                    {formatCurrency("pound")} {meta_data.amount_requested}
                  </div>
                </div>
              </div>
            </div>
          </div> */}

          {/* Buttons */}
          <div className="flex flex-col sm:flex-row gap-2 sm:items-center items-start">
          {meta_data?.action_buttons?.make_payment && (
            <FormButton
              variant="primary"
              onClick={handlePayment}
              disabled={isLoading || !meta_data?.action_buttons?.make_payment}
              className="items-center justify-center gap-2 whitespace-nowrap ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&amp;_svg]:pointer-events-none [&amp;_svg]:size-4 [&amp;_svg]:shrink-0 text-sm px-2 py-1 transition-colors"
            >
              {isLoading ? (
                <>
                  <i className="fas fa-spinner fa-spin mr-2"></i>
                  Processing...
                </>
              ) : (
                <>
                  <i className="fas fa-lock mr-2"></i>Pay{" "}
                  {formatCurrency("pound", meta_data.amount_requested)}{" "}
                  Securely
                </>
              )}
            </FormButton>
          )}
            {meta_data?.failed_attempts && meta_data.failed_attempts.length > 0 && meta_data?.action_buttons?.view_failed_attempts && (
              <button
                onClick={() => setShowFailedAttemptsModal(true)}
                title="Click to view failed attempts"
                className="inline-flex items-center justify-center pr-1 gap-2 transition-colors bg-transparent text-novaCaution-600 hover:text-novaCaution-500"
              >
                <i className="fas fa-exclamation-triangle text-xl"></i>
                <span className="text-sm mt-1 italic hover:underline">View failed attempts</span>
              </button>
            )}
          </div>
      {/* Security Footer */}
          <div className="flex items-center gap-2 mt-2 text-xs text-novaNeutral-500">
            <img src={shieldIcon} alt="shield" className="w-4 h-4" />
            <span>
              Secure payment through Stripe • SSL encrypted • Funds held securely until work begins
            </span>
          </div>
          {/* Timestamp */}
          {/* <div className="text-xs text-novaNeutral-500 mt-4 flex items-center gap-1">
            <i className="fas fa-clock text-novaNeutral-500 text-xs"></i>
            <span>{formatTimestamp(meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
          </div> */}
        </div>
        <br />
        <p className="text-xs text-novaNeutral-500 flex items-center">
            <i className="fas fa-clock text-novaNeutral-500 text-xs mr-1"></i>
            <span>{formatTimestamp(meta_data.timestamp)}</span>
            <span className="text-xs text-novaNeutral-400 ml-2">• {DEFAULT_ACTION_BY}</span>
        </p>    
      </div>
    </>
  );
};

export default CustomerInitialPaymentRequested;
