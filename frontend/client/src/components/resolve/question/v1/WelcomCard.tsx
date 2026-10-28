import React from "react";
import { FormButton } from "@/utils/formComponents";
import AlenProfile from "@/assets/resolve-images/AlenProfile.png";
import ArrowIcon from "@/assets/resolve-images/arrow.svg";

interface WelcomeCardProps {
  totalQuestions: number;
  onNext: () => void;
}

export const WelcomeCard: React.FC<WelcomeCardProps> = ({
  totalQuestions,
  onNext,
}) => {
  return (
    <div className="flex justify-center w-full overflow-y-auto">
      <div className="w-full max-w-[864px]">
        <div
          className="relative bg-transparent sm:border-[18px] border-[10px] rounded-[30px] sm:rounded-[38px]"
          style={{ borderColor: 'rgba(252, 215, 176, 0.72)' }}
        >
          <div className="bg-white rounded-[18px] sm:rounded-[16px] px-6 py-8 sm:pl-12 sm:pr-10 sm:py-12 3xl:pl-16 3xl:pr-12 3xl:py-10 flex flex-col">
            {/* Progress indicator */}
            <p className="text-[24px] leading-[1.4] sm:flex hidden text-novaBlack font-nineties tracking-wide text-left">
              1/{totalQuestions + 1} Steps
            </p>
            <div className="gradient-incomplete-border">
              {/* Main heading */}
              <h1 className="text-[34px] w-full 3xl:w-[85%] sm:text-[48px] 3xl:text-[56px] leading-[1] font-normal font-nineties text-left mb-6 mt-2 md:mt-[30px]">
                Your personalised recommendation is minutes away
                {/* Your personalised Nova recommendation is minutes away */}
              </h1>
              {/* Testimonial */}
              <div className="items-center flex sm:hidden gap-2 mb-6 lg:w-[60%] w-full">
                <div className="flex-shrink-0">
                  <div className="w-16 h-16 rounded-full bg-novaNeutral-200 flex items-center justify-center overflow-hidden">
                  <img src={AlenProfile} alt="" className="w-full h-full object-cover" />
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <p className="font-roman text-novaNeutral-900 text-[16px] sm:text-[18px] leading-relaxed">
                    "We’ll help you understand the different ways your situation could be resolved – including options most people aren’t aware of."
                  </p>
                </div>
              </div>

              <div className="flex justify-start mb-6 sm:hidden">
                <FormButton
                  type="button"
                  variant="tertiary"
                  onClick={onNext}
                  className="inline-flex items-center justify-center gap-2 px-5 py-2.5 text-[20px] sm:text-[24px]"
                >
                  Continue
                  <img src={ArrowIcon} alt="arrow" className="w-4 h-4" />
                </FormButton>
              </div>

              {/* Description paragraphs */}
              <div className="3xl:space-y-6 space-y-4 mb-4">
                <p className="font-roman text-novaNeutral-600 text-[16px] 3xl:text-[18px] leading-relaxed text-left md:w-[75%] 3xl:w-[80%] w-full">
                  Answer a few quick questions and we’ll help you understand your options and find the best way forward for your situation.
                </p>
                <p className="font-roman text-novaNeutral-600 text-[16px] 3xl:text-[18px] leading-relaxed text-left md:w-[75%] w-full">
                  This takes around <strong>5 minutes</strong> and is completely <strong>secure and confidential</strong>. 
                </p>
              </div>

              {/* Testimonial */}
              <div className="items-center hidden sm:flex gap-4 3xl:mb-16 mb-14 3xl:w-[70%] md:w-[65%] w-[90%]">
                <div className="flex-shrink-0">
                  <div className="w-20 h-20 rounded-full bg-novaNeutral-200 flex items-center justify-center overflow-hidden">
                  <img src={AlenProfile} alt="" className="w-full h-full object-cover" />
                  </div>
                </div>
                <div className="flex-1">
                  <p className="font-roman text-novaNeutral-900 text-[16px] 3xl:text-[18px] leading-relaxed">
                    "We’ll help you understand the different ways your situation could be resolved – including options most people aren’t aware of."
                  </p>
                </div>
              </div>
            </div>
              {/* Next button */}
            <div className="justify-start hidden sm:flex" style={{ marginTop: '-22px' }}>
              <FormButton
                type="button"
                variant="tertiary"
                onClick={onNext}
                className="z-10 inline-flex items-center justify-center gap-2 px-5 py-2.5 text-[20px] sm:text-[22px] focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
              >
                Continue
                <img src={ArrowIcon} alt="arrow" className="w-6 h-4" />
              </FormButton>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
};

