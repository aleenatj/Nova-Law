import React from "react";
import "@/styles/landingpage.css";
import backgroundGradient from "@/assets/lawyerlandingpage/LawyerBgSection2.webp";
import backgroundGradientMobile from "@/assets/lawyerlandingpage/LawyerSmallBgSection2.webp";

const LawyerSection2: React.FC = () => {
  return (
    <>
    <style dangerouslySetInnerHTML={{ __html: `
      .lawyer-section2-bg { background-image: url(${backgroundGradient}); }
      @media (max-width: 768px) { .lawyer-section2-bg { background-image: url(${backgroundGradientMobile}); } }
    `}} />
    <section
      className="lawyer-section2-bg relative overflow-hidden bg-cover bg-center bg-no-repeat py-16 sm:py-24 lg:py-20 bg-[#FCF2FF]"
    >

      {/* Content */}
      <div className="relative z-10 mx-auto 3xl:max-w-[34%] lg:max-w-[46%] max-w-[80%] lg:px-10">
        <div className="text-center">
          {/* Heading */}
          <h2 className="text-[36px] sm:text-[38px] lg:text-[40px] font-nineties text-novaBlack tracking-wide leading-[1] mb-10 text-left max-w-[80%] sm:max-w-[98%]"
            style={{
              WebkitTextStroke: "0.6px",
            }}
          >
            How Nova works to support you
          </h2>

          {/* Paragraphs */}
          <div className="space-y-8 text-[16px] lg:text-[18px] text-novaBlack font-roman text-left">
            <p>
              Nova combines emotionally intelligent AI, specialist insight, and early-stage triage to connect you with clients who are ready for collaborative, solution-focused support, not unnecessary conflict.
            </p>
            <p>
              The Nova platform prepares clients step by step before they engage with you: gathering relevant information, clarifying goals, recommending appropriate pathways, and helping them understand what lies ahead.
            </p>
            <p>
              In turn, you receive clear, structured, and insightful case notes before your first meeting, allowing you to focus your expertise where it matters most from the very beginning.
            </p>
          </div>
        </div>
      </div>
    </section>
    </>
  );
};

export default LawyerSection2;
