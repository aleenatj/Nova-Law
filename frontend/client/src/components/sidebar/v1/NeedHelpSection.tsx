import { Button } from "@/components/ui/button";
import { FormButton } from "@/utils";

export function NeedHelpSection() {
  const handleNeedHelp = () => {
    // Find the call-us-selector element
    const callUsSelector = document.querySelector('call-us-selector');

    if (callUsSelector && callUsSelector.shadowRoot) {
      // Access the call-us element inside the shadow root
      const callUs = callUsSelector.shadowRoot.querySelector('call-us');

      if (callUs && callUs.shadowRoot) {
        // First, try to find the action_option div
        const actionOption = callUs.shadowRoot.querySelector('div.action_option');

        if (actionOption && typeof (actionOption as HTMLElement).click === 'function') {
          (actionOption as HTMLElement).click();
        } else {
          // Fallback: try to find the button instead
          const button = callUs.shadowRoot.querySelector('#wplc-chat-button');

          if (button && typeof (button as HTMLElement).click === 'function') {
            (button as HTMLElement).click();
          }
        }
      }
    } 
  };

  return (
    <div className="p-6">
      <div className="">
        <h3 className="text-[18px] font-semibold text-novaNeutral-900">
          <i className="fas fa-question-circle mr-2"></i>Need further help?
        </h3>
        <div className="border-t border-novaNeutral-100 my-2 mb-5"></div>
        <button
          type="button"
          onClick={handleNeedHelp}
          className="py-1.5 rounded-full px-4 flex border border-novaPrimary-500 hover:border-transparent items-center hover:bg-gradient-to-r hover:from-[#FF6A42] hover:to-[#FC3C3F] hover:text-white"
        >
          <i className="fas fa-comments mr-2 text-xs"></i>
          <span className="text-[14px]">Chat to Nova Navigator</span>
        </button>
      </div>

      <div className="mt-6">
        <a
          className="text-[14px] text-[#D1822C] underline block mb-1"
          href="/support-and-guidance"
          target="_blank"
        >
          Support & Guidance
        </a>
        {/* <a
          className="text-[14px] text-[#D1822C] underline block mb-1"
          href="/payment-and-security"
          target="_blank"
        >
          Payment & security
        </a>
        <a
          className="text-[14px] text-[#D1822C] underline block"
          href="/lawyer-matching"
          target="_blank"
        >
          Lawyer matching
        </a> */}
      </div>
    </div>
  );
}
