import React from "react";
import "@/styles/landingpage.css";
import backgroundGradient from "@/assets/lawyerlandingpage/LawyreBgSection3.webp";
import backgroundGradientMobile from "@/assets/lawyerlandingpage/LawyerSmallBgSection3.webp";

const LawyerSection3: React.FC = () => {
  return (
    <>
    <style dangerouslySetInnerHTML={{ __html: `
      .lawyer-section3-bg { background-image: url(${backgroundGradient}); }
      @media (max-width: 768px) { .lawyer-section3-bg { background-image: url(${backgroundGradientMobile}); } }
    `}} />
    <section
      className="lawyer-section3-bg relative overflow-hidden bg-cover bg-center bg-no-repeat px-6 py-12 sm:py-16 lg:py-10 bg-[#2B2187]"
    >
      {/* Content */}
      <div className="relative z-10 mx-auto max-w-[92%] md:max-w-[50%] lg:max-w-[48%] 3xl:max-w-[36%] text-left">
        <div className="flex flex-row items-start">
          <span 
            className="text-[64px] sm:text-[80px] leading-none font-nineties text-white"
            aria-hidden
          >
            &ldquo;
          </span>
          <p className="text-[32px] font-nineties text-white mt-4 leading-[1.3] px-3 sm:px-5">
          Nova Engage makes onboarding smooth, structured, and stress-free for clients, wherever they are in the world. It’s smart, efficient, and exactly what modern family law needs.&rdquo;
          </p>
        </div>
        <div className="text-[14px] sm:text-[16px] font-roman ml-8 sm:ml-11 mt-4 text-white">
          <p>Melanie Bataillard-Samuel</p>
          <p>MBS Family Law. Chair of Resolution</p>
        </div>
      </div>
    </section>
    </>
  );
};

export default LawyerSection3;
