import React, { useState } from "react";
import "@/styles/landingpage.css";
import { useRole } from "@/contexts/RoleContext";
import { getResolveUrl } from "@/lib/utils";
import { FormButton } from "@/utils";
// import DoorBackground from "@/assets/landingpage/doorbackground.jpg";
import DoorBackground from "@/assets/landingpage/pinkdoorbackground.webp";
import DoorBackgroundMobile from "@/assets/landingpage/pinkdoorbackgroundmobile.webp";
import DoorGirl from "@/assets/landingpage/doorgirl.webp";

const Section1: React.FC = () => {
  // useRole may not be available during SSR (no PageWrapper on server)
  let currentRole = "Guest";
  try {
    const roleResult = useRole();
    currentRole = roleResult?.currentRole || "Guest";
  } catch {
    // Provider not available during SSR - use default
    currentRole = "Guest";
  }
  
  const [isLoading, setIsLoading] = useState(false);
  
  const handleGetStartedClick = async () => {
    setIsLoading(true);
    if (typeof window !== "undefined") {
      if (currentRole !== "Guest") {
        window.location.href = "/case-dashboard";
        return;
      }
      const url = await getResolveUrl();
      window.location.href = url;
    }
    setIsLoading(false);
  };

  const handleGetStartedKeyDown = (e: React.KeyboardEvent<HTMLAnchorElement>) => {
    if (e.key === " ") {
      e.preventDefault();
      (e.currentTarget as HTMLAnchorElement).click();
    }
  };

  return (
    <section className="relative min-h-[800px] flex items-center justify-center overflow-hidden">
      <div className="absolute inset-0 z-0">
        <picture>
          <source media="(max-width: 640px)" srcSet={DoorBackgroundMobile} />
          <img
            src={DoorBackground}
            alt="Door Background"
            aria-hidden="true"
            loading="eager"
            className="h-full w-full object-cover"
          />
        </picture>
        <img
          src={DoorGirl}
          alt="Door Girl"
          aria-hidden="true"
          loading="eager"
          className="absolute bottom-0 h-full xl:max-h-[90%] sm:max-h-[85%] max-h-[80%] w-auto left-[-90px] sm:left-[-5%] md:left-[1%] lg:left-[10%] 2xl:left-[20%]"
        />
      </div>

      {/* Main content container */}
      <div className="lg:max-w-[45%] xl:max-w-[40%] 2xl:max-w-[35%] max-w-[80%] relative z-10 ml-0 md:ml-[70px]">
        <div className="text-center flex flex-col gap-8 mt-[30px] sm:mt-[-25px]">
          {/* Main Heading */}
          <h1 className="text-[48px] lg:[56px] xl:text-[64px] font-nineties text-novaBlack leading-[60px] md:leading-[55px] xl:leading-[70px] px-0">
            Find the best way forward for your separation or divorce
          </h1>
          
          {/* Body Text */}
          <p className="text-[20px] lg:text-[24px] 2xl:text-[26px] text-novaBlack max-w-[81%] md:max-w-[85%] mx-auto leading-[30px] md:leading-[32px] xl:leading-[35px]">
            Answer a few questions and Nova will help you understand your options and recommend the best approach for your situation with a{" "}
            <span className="font-medium">free personalised recommendation</span>.
          </p>

          {/* CTA Section */}
          <div className="flex flex-col items-center flex flex-col sm:gap-6 gap-4 pt-2">
            <FormButton
              onClick={handleGetStartedClick}
              variant="custom"
              className="landing-primary-button focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
              loading={isLoading}
              loadingText="Getting started"
              disabled={isLoading}
            >
              Get started now
            </FormButton>
            <p className="sm:text-[18px] text-[16px] text-novaBlack w-[46%] md:w-[100%] mx-auto">
              Takes 5 minutes. No obligations. Secure and private.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Section1;