import React, { useEffect, useState } from "react";
import "@/styles/landingpage.css";
import conversionLandingBackground from "@/assets/landingpage/conversionlanding.webp";
import circleTick from "@/assets/landingpage/circletick.svg";
import arrowRight from "@/assets/landingpage/arrow-right.webp";
import arrowRightWhite from "@/assets/landingpage/arrow-right-white.webp";
import womenwithcircle from "@/assets/landingpage/womenwithcircle1.webp";
import { useRole } from "@/contexts/RoleContext";
import { getResolveUrl } from "@/lib/utils";
import { FormButton } from "@/utils";
import ConversionHeader from "../components/landing-page/conversion-layout/conversionHeader";
import ConversionFooter from "../components/landing-page/conversion-layout/conversionFooter";

const checklistItems = [
  "Free",
  "Private & confidential",
  "Takes about 5 minutes",
] as const;

const conversionLandingBgVars: { [key: `--${string}`]: string } = {
  "--conversion-landing-bg": `url(${conversionLandingBackground})`,
};

const LandingPageMini: React.FC = () => {
  const { currentRole } = useRole();
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const html = document.documentElement;
    const body = document.body;
    const cls = "conversion-landing-hide-scrollbar";
    html.classList.add(cls);
    body.classList.add(cls);
    return () => {
      html.classList.remove(cls);
      body.classList.remove(cls);
    };
  }, []);

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

  return (
    <div
      className="flex min-h-screen flex-col bg-[#FDFCF0] sm:[background-image:var(--conversion-landing-bg)] sm:[background-size:100%_auto] sm:[background-position:top_center] sm:bg-no-repeat"
      style={conversionLandingBgVars}
    >
      <ConversionHeader />
      <main className="mx-auto flex w-full max-w-[1920px] flex-1 flex-col items-center py-10 sm:py-14 lg:py-16">

        {/* Hero section in new landing page */}
        <section className="w-full min-h-[min(100svh,520px)] overflow-visible md:min-h-[600px] ">
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-[1.35fr_1fr] lg:gap-14 lg:items-center">
            <div className="flex min-w-0 flex-col justify-center text-left md:pl-[250px] px-6 md:px-0">
              <h1 className="font-nineties mt-6 sm:mt-0 text-[2.5rem] text-novaBlack sm:text-[2.5rem] lg:text-[3rem] xl:text-[63px] leading-[1.15] max-w-full md:max-w-[80%]">
                Not sure what to do next in your separation or divorce?
              </h1>
              <p className="mt-8 font-neue text-xl leading-snug text-novaBlack md:mt-10 md:text-2xl max-w-full md:max-w-[85%]">
                Get a clear, personalised recommendation on the best way to move forward in your
                situation.
              </p>
              <ul className="mt-10 space-y-5 sm:space-y-3.5 font-neue text-base text-novaBlack md:mt-10 md:text-xl">
                {checklistItems.map((label) => (
                  <li key={label} className="flex items-center gap-3">
                    <img
                      src={circleTick}
                      alt=""
                      className="h-[22px] w-[22px] shrink-0"
                      aria-hidden
                    />
                    <span>{label}</span>
                  </li>
                ))}
              </ul>
              <FormButton
                onClick={handleGetStartedClick}
                variant="custom"
                size="custom"
                className="landing-primary-button landing-primary-button--mini-hero group mt-10 max-w-full self-start font-neue text-base !py-3 sm:text-lg md:mt-[68px]"
                loading={isLoading}
                loadingText="Get my personalised recommendation"
                disabled={isLoading}
              >
                <span className="inline-flex items-center gap-2 whitespace-nowrap">
                  Get my personalised recommendation
                  <span className="relative block h-6 w-6 shrink-0" aria-hidden>
                    <img
                      src={arrowRight}
                      alt=""
                      className="pointer-events-none absolute left-1/2 top-1/2 h-6 w-6 max-h-full max-w-full -translate-x-1/2 -translate-y-1/2 object-contain object-center transition-opacity duration-300 group-hover:opacity-0"
                    />
                    <img
                      src={arrowRightWhite}
                      alt=""
                      className="pointer-events-none absolute left-1/2 top-1/2 max-h-full max-w-full -translate-x-1/2 -translate-y-1/2 object-contain object-center opacity-0 transition-opacity duration-300 group-hover:opacity-100"
                    />
                  </span>
                </span>
              </FormButton>
            </div>
            <div className="flex min-w-0 justify-end lg:justify-end p-0">
              <img
                src={womenwithcircle}
                alt="Illustration of a women with a circle"
                className="h-auto max-w-none w-[min(100%,28rem)] sm:w-[min(100%,34rem)] lg:w-[26rem] xl:w-[42rem]"
                loading="eager"
                decoding="async"
              />
            </div>
          </div>
        </section>
      </main>
      <ConversionFooter />
    </div>
  );
};

export default LandingPageMini;