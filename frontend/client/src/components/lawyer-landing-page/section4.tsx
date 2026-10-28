import React from "react";
import "@/styles/landingpage.css";
import backgroundGradient from "@/assets/lawyerlandingpage/LawyersBgSection4.webp";
import backgroundGradientMobile from "@/assets/lawyerlandingpage/LawyerSmallBgSection4.webp";
import { FormButton } from "@/utils";
import Diamond from "@/assets/landingpage/intersection.svg";

const benefits = [
  {
    bold: "A consistent flow of high-quality cases",
    regular: "aligned to your dispute resolution expertise",
  },
  {
    bold: "Higher client engagement",
    regular: "through thoughtful preparation and briefing",
  },
  {
    bold: "Clients",
    regular: "who are open to meaningful, productive conversations and advice",
  },
  {
    bold: "Streamlined information gathering",
    regular: "through Nova’s bespoke AI tools",
  },
  {
    bold: "Transparent, ethical outcomes",
    regular: "guided by your professional judgment",
  },
];

interface LawyerSection4Props {
  onSignUpClick?: () => void;
}

const LawyerSection4: React.FC<LawyerSection4Props> = ({ onSignUpClick }) => {
  return (
    <>
    <style dangerouslySetInnerHTML={{ __html: `
      .lawyer-section4-bg { background-image: url(${backgroundGradient}); }
      @media (max-width: 768px) { .lawyer-section4-bg { background-image: url(${backgroundGradientMobile}); } }
    `}} />
    <section
      className="lawyer-section4-bg relative overflow-hidden bg-cover bg-center bg-no-repeat py-16 sm:py-24 lg:py-20 bg-[#FCF2FF]"
    >
      {/* Content */}
      <div className="relative z-10 mx-auto max-w-full md:max-w-[60%] lg:max-w-[50%] 3xl:max-w-[40%] px-6 lg:px-8">
        <div className="text-center">
          {/* Heading */}
          <h2 className="text-[36px] 3xl:text-[40px] font-nineties text-novaBlack tracking-wide leading-[1.2] mb-8 sm:mb-10 w-full sm:w-[60%] 3xl:w-[70%] text-left sm:ml-10 md:ml-24 "
            style={{
              WebkitTextStroke: "0.4px",
            }}
          >
            Nova delivers proven results all round
          </h2>

          {/* Benefits List */}
          <div className="relative gap-8 flex flex-col border-l border-novaBlack pl-8 ml-[40px] md:ml-14 mt-0 py-6 max-w-[90%] 2xl:max-w-[95%] mx-auto">
            {benefits.map((benefit, i) => (
              <div key={i}>
                <div className="flex items-center">
                  <span 
                    className="border-t border-novaBlack/10 absolute" 
                    style={{ width: i % 2 === 0 ? 46 : 70, left: i % 2 === 0 ? "-25px" : "-50px" }}
                  />
                  <img 
                    src={Diamond} 
                    alt="Diamond" 
                    className="absolute left-[-15px] w-[30px] h-[30px] mt-[1px]" 
                  />
                </div>
                <div className="relative pl-2">
                  <p className="mt-[-12px] text-left text-novaBlack leading-[1.5] text-[16px] sm:text-[18px] font-roman">
                    <span className="font-semibold">{benefit.bold}</span>{" "}
                    {benefit.regular}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* CTA Button */}
          <div className="mt-10 sm:mt-6 text-left ml-24 mb-8">
            <FormButton
              onClick={onSignUpClick}
              variant="custom"
              className="landing-primary-button"
            >
              Sign up now
            </FormButton>
          </div>
        </div>
      </div>
    </section>
    </>
  );
};

export default LawyerSection4;
