import React, { useState } from "react";
import { Button } from "../../../../ui/button";
import { formatTimestamp } from "../../../../../utils";
import { formatCurrency } from "@/lib/utils";
import { api } from "@/lib/api";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface PaymentReceiptProps {
  timelineData?: any;
  isLatest?: boolean;
}

const PaymentReceipt: React.FC<PaymentReceiptProps> = ({ timelineData, isLatest }) => {
  const [isProcessing, setIsProcessing] = useState(false);

  // Extract data from timelineData
  const receiptData = timelineData?.meta_data;

  const popupRef = React.useRef<Window | null>(null);

  // Cleanup: Close popup when component unmounts or parent closes
  React.useEffect(() => {
    return () => {
      if (popupRef.current && !popupRef.current.closed) {
        popupRef.current.close();
      }
    };
  }, []);

  // Also handle page unload (when parent window closes)
  React.useEffect(() => {
    const handleBeforeUnload = () => {
      if (popupRef.current && !popupRef.current.closed) {
        popupRef.current.close();
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);

    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Check if timelineData exists and has meta_data
  if (!receiptData) {
    return (
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            <span className="text-sm font-medium text-novaNeutral-900">
              No payment data available
            </span>
            <p className="text-sm text-novaNeutral-700 mt-1">
              Unable to load payment information at this time.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleRetryPayment = async () => {
    setIsProcessing(true);
    try {
      const response = await api.get<{
        success: boolean;
        message: string;
        data: {
          checkout_session_url: string;
        };
      }>(
        `/v1/payment/checkout?amount=${receiptData.amount_paid}&invoice_id=${receiptData.invoice_id}&event_id=${timelineData.id}`
      );

      if (response.success && response.data.checkout_session_url) {
        const checkoutUrl = response.data.checkout_session_url;
        window.location.href = checkoutUrl;
      }
    } catch (error) {
      console.error("Error fetching checkout URL:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  const lawyerName = receiptData.lawyer_name || "your lawyer";

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        {/* Header */}
        <div className="flex gap-2">
          <i className="fas fa-check-circle text-[#1A1425] text-xl"></i>
          <span className="sm:text-[28px] text-xl font-semibold text-[#1A1425]">
            Initial payment received
          </span>
          {receiptData.payment_status && (
            <span
              className={`text-xs px-3 py-1 rounded-full h-fit mt-1 sm:mt-0
                ${
                  receiptData.payment_status.toLowerCase() === "completed"
                    ? "bg-novaDarkOrange text-white"
                    : receiptData.payment_status.toLowerCase() === "processing"
                    ? "bg-novaWarning-100 text-novaWarning-700"
                    : receiptData.payment_status.toLowerCase() === "failed"
                    ? "bg-novaCaution-100 text-novaCaution-700"
                    : "bg-novaNeutral-100 text-novaNeutral-700"
                }
              `}
            >
              {receiptData.payment_status[0].toUpperCase() + receiptData.payment_status.slice(1).toLowerCase()}
            </span>
          )}
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />

        {/* Description */}
        <p className="text-md leading-6 text-novaNeutral-700 mb-6 w-full lg:w-[60%]">
          {receiptData.payment_status?.toLowerCase() === "completed" ? (
            <>
              We’re pleased to confirm that your deposit has been successfully received into the client account of Family Law Partners and {" "}
              <strong className="text-[#1A1425] break-words">{lawyerName}</strong> will contact you shortly to arrange your first consultation.
            </>
          ) : receiptData.payment_status?.toLowerCase() === "processing" ? (
            <>
              Your payment is being processed. <strong className="text-[#1A1425]">{lawyerName}</strong> will contact you once the payment is confirmed.
            </>
          ) : receiptData.payment_status?.toLowerCase() === "failed" ? (
            <>
              Unfortunately, your payment failed. Please retry your payment to proceed with{" "}
              <strong className="text-[#1A1425]">{lawyerName}</strong>.
            </>
          ) : (
            <>
              Payment for legal services with <strong className="text-[#1A1425]">{lawyerName}</strong>.
            </>
          )}
        </p>

        {/* Payment Details Card */}
        <div className="bg-white rounded-lg sm:p-6 p-4 mb-2">
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="sm:text-sm text-xs items-center text-novaNeutral-600">Transaction ID:</span>
              <span className="sm:text-sm text-xs font-medium text-[#1A1425] text-right break-all max-w-[60%]">
                {receiptData.transaction_id || "-"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="sm:text-sm text-xs text-novaNeutral-600">Payment Date:</span>
              <span className="sm:text-sm text-xs font-medium text-[#1A1425]">
                {receiptData.payment_date || "-"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="sm:text-sm text-xs text-novaNeutral-600">Payment Method:</span>
              <span className="sm:text-sm text-xs font-medium text-[#1A1425]">
                {receiptData.payment_method || "-"}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="sm:text-sm text-xs text-novaNeutral-600">Legal Representative:</span>
              <span title={receiptData.lawyer_name || "-"} className="sm:text-sm text-xs font-medium text-[#1A1425] line-clamp-1">
                {receiptData.lawyer_name || "-"}
              </span>
            </div>
            <hr className="border-t border-novaDarkAmber my-2" />
            <div className="flex justify-between items-center">
              <span className="sm:text-md text-sm text-novaNeutral-700">Total Paid:</span>
              <span className="sm:text-lg text-md font-semibold text-[#1A1425]">
                {receiptData.amount_paid != null
                  ? formatCurrency("pound", receiptData.amount_paid)
                  : "-"}
              </span>
            </div>
          </div>
        </div>

        {/* Footer Note */}
        <p className="text-xs text-novaNeutral-500 mb-3">
          Funds will be held securely by Family Law Partners until your consultation.
        </p>

        {/* Timestamp */}
        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(receiptData.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {DEFAULT_ACTION_BY}</span>
        </p>
      </div>
    </div>
  );
};

export default PaymentReceipt;
