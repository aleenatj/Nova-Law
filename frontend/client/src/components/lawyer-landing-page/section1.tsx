import React from "react";
import "@/styles/landingpage.css";
import { FormButton } from "@/utils";
import LawyerBackground from "@/assets/lawyerlandingpage/LawyerBg.webp";
import LawyerBackgroundMobile from "@/assets/lawyerlandingpage/LawyerSmallBgSection1.webp";
import LawyerGirl from "@/assets/lawyerlandingpage/LawyerGirl.png";

interface LawyerSection1Props {
  onSignUpClick?: () => void;
}

const LawyerSection1: React.FC<LawyerSection1Props> = ({ onSignUpClick }) => {
  return (
    <section className="relative min-h-[800px] flex items-center justify-center overflow-hidden">
      {/* Background and Girl Image Container */}
      <div className="absolute inset-0 z-0">
        <picture>
          <source media="(max-width: 568px)" srcSet={LawyerBackgroundMobile} />
          <img
            src={LawyerBackground}
            alt="Lawyer Background"
            aria-hidden="true"
            loading="eager"
            className="h-full w-full object-cover"
          />
        </picture>
        {/* Girl image positioned on the right side */}
        <img
          src={LawyerGirl}
          alt="Lawyer"
          aria-hidden="true"
          loading="eager"
          className="absolute bottom-0 h-full sm:max-h-[89%] max-h-[80%] w-auto right-[-136px] sm:right-[-120px] md:right-[-90px] lg:right-[6%] 2xl:right-[20%]"
        />
      </div>

      {/* Main content container - positioned more to the left/center */}
      <div className="lg:max-w-[60%] 2xl:max-w-[50%] max-w-[80%] relative z-10 mr-0 md:mr-[70px]">
        <div className="text-center flex flex-col gap-8 mt-0 md:mt-[-70px]">
          {/* Main Heading */}
          <h1 className="xl:w-[530px] sm:w-[350px] md:w-[410px] lg:w-[470px] w-full mx-auto sm:text-[48px] text-[46px] lg:text-[56px] xl:text-[64px] font-nineties text-novaBlack leading-[60px] md:leading-[55px] xl:leading-[70px] px-0 md:px-8">
            Join the Nova family professional network
          </h1>

          {/* Body Text */}
          <p className="max-w-[78%] sm:max-w-[80%] xl:max-w-[56%] 3xl:max-w-[60%] mx-auto  sm:text-[20px] text-[18px] lg:text-[24px] 2xl:text-[26px] text-novaBlack  leading-[30px] md:leading-[32px] xl:leading-[35px]">
            Working with Nova, you’ll be introduced to clients who arrive well informed, 
            emotionally prepared, and seeking a constructive way 
            forward, creating better outcomes for everyone involved.
          </p>

          {/* CTA Section */}
          <div className="flex flex-col items-center gap-6 pt-2">
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
  );
};

export default LawyerSection1;
