import React from "react";
import "@/styles/landingpage.css";
import { FormButton } from "@/utils";
import backgroundGradient from "@/assets/lawyerlandingpage/LawyerBgSection6.webp";

interface LawyerSection6Props {
  onSignUpClick?: () => void;
}

const LawyerSection6: React.FC<LawyerSection6Props> = ({ onSignUpClick }) => {
  return (
    <>
    <style dangerouslySetInnerHTML={{ __html: `
      .lawyer-section6-bg { background: url(${backgroundGradient}) center/cover no-repeat #FFCC73; }
      @media (max-width: 1200px) { .lawyer-section6-bg { background: radial-gradient(circle at left top, #f8404042 11%, transparent 50%), rgb(255, 204, 115); } }
    `}} />
    <section
      className="lawyer-section6-bg relative overflow-hidden bg-cover bg-center bg-no-repeat py-16 sm:py-20 lg:py-24"
    >
      {/* Content */}
      <div className="relative z-10 mx-auto max-w-[100%] md:max-w-[60%] lg:max-w-[50%] 3xl:max-w-[40%] px-6 lg:px-8">
        <div className="text-center">
          {/* Heading */}
          <h2 className="text-[36px] sm:text-[38px] lg:text-[40px] font-nineties text-novaBlack tracking-wide leading-[1.2] mb-6" 
            style={{
              WebkitTextStroke: "0.5px",
            }}
          >
            Welcome to the next generation of dispute
            <br />
            resolution professionals
          </h2>

          {/* Subtitle */}
          <p className="text-[16px] sm:text-[18px] text-novaBlack font-roman leading-[1.6] max-w-full sm:max-w-[76%] mx-auto mb-8">
            We’re building a modern, ethical, and human-centred ecosystem
             for professionals supporting families through change. 
             If that sounds like something you’d like to be part of, 
             we’d love to work with you.
          </p>

          {/* CTA Button */}
          <div>
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

export default LawyerSection6;
