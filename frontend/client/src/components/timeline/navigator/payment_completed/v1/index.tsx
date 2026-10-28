import React from "react";
import { formatTimestamp } from "../../../../../utils";
import { formatCurrency } from "@/lib/utils";
import { DEFAULT_ACTION_BY } from "@/lib/constants";

interface PaymentCompletedProps {
  timelineData?: any;
  isLatest?: boolean;
}

const PaymentCompleted: React.FC<PaymentCompletedProps> = ({
  timelineData,
  isLatest,
}) => {
  const paymentData = timelineData?.meta_data;
  const isNavigator =
    timelineData?.action_user_role?.toLowerCase() === "navigator";
  const actionBy = timelineData?.action_user_name
    ? `${timelineData.action_user_name}${isNavigator ? " (Nova Navigator)" : ""}`
    : timelineData?.action_user_role || DEFAULT_ACTION_BY;

  if (!paymentData) {
    return (
      <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
        <div className="flex flex-col">
          <div className="flex gap-2">
            <i className="fas fa-exclamation-triangle text-xl mt-1"></i>
            <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
              No payment data available
            </span>
          </div>
          <hr className="block border-t border-novaDarkAmber my-3" />
          <p className="text-md leading-6 text-novaNeutral-700">
            Unable to load payment information at this time.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`${isLatest === true ? 'bg-novaActive' : 'bg-novaInactive'} sm:p-6 p-4 rounded-lg`}>
      <div className="flex flex-col">
        <div className="flex gap-2">
          <i className="fas fa-check-circle text-xl mt-1"></i>
          <span className="sm:text-[28px] text-2xl font-semibold text-[#1A1425]">
            Payment completed
          </span>
        </div>
        <hr className="block border-t border-novaDarkAmber my-3" />
        <p className="text-md leading-6 text-novaNeutral-700 mb-4">
          <strong className="text-[#1A1425]">{paymentData.customer_name}</strong> has successfully completed the initial payment of{" "}
          <strong className="text-[#1A1425]">{formatCurrency("pound", paymentData.amount_paid)}</strong> for case{" "}
          <strong className="text-[#1A1425]">{paymentData.case_number}</strong>. The case is now fully funded and ready to proceed.
        </p>
        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-center gap-2 mb-3">
            <i className="fas fa-receipt text-novaNeutral-700 text-sm"></i>
            <span className="text-sm font-semibold text-novaNeutral-900">Payment Details:</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm leading-5 text-novaNeutral-700">
            <div>
              <span className="text-novaNeutral-500">Client:</span>
              <div className="font-medium text-novaNeutral-900">{paymentData.customer_name}</div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Assigned Expert:</span>
              <div className="font-medium text-novaNeutral-900">{paymentData.lawyer_name}</div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Amount:</span>
              <div className="font-medium text-novaDarkOrange">
                {formatCurrency("pound", paymentData.amount_paid)}
              </div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Transaction ID:</span>
              <div className="font-medium font-mono max-w-full text-left sm:max-w-xs break-words whitespace-normal"
                title={paymentData.transaction_id || "-"}
              >
                {paymentData.transaction_id ? paymentData.transaction_id : "-"}
              </div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Case Type:</span>
              <div className="font-medium text-novaNeutral-900">{paymentData.case_type}</div>
            </div>
            <div>
              <span className="text-novaNeutral-500">Status:</span>
              <div className="font-medium mt-1">
                <span className="px-2 py-1 rounded-full text-xs font-normal bg-novaDarkOrange text-white">
                  {paymentData.status.charAt(0).toUpperCase() + paymentData.status.slice(1).toLowerCase()}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white sm:p-6 p-4 rounded-lg mb-4">
          <div className="flex items-start gap-2">
            <i className="fas fa-info-circle text-novaNeutral-700 text-sm mt-0.5"></i>
            <span className="text-sm text-novaNeutral-700">
              Case is now active and ready for legal proceedings
            </span>
          </div>
        </div>
        <p className="text-xs flex items-center">
          <i className="fas fa-clock text-xs mr-1"></i>
          <span>{formatTimestamp(paymentData.timestamp)}</span>
          <span className="text-xs text-novaNeutral-400 ml-2">• {actionBy}</span>
        </p>
      </div>
    </div>
  );
};

export default PaymentCompleted;
