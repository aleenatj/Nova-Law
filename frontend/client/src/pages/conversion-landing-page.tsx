import React, { useEffect, useState } from "react";

import "@/styles/landingpage.css";
import conversionLandingBackground from "@/assets/landingpage/conversionlanding.webp";
import circleTick from "@/assets/landingpage/circletick.svg";
import womenwithcircle from "@/assets/landingpage/womenwithcircle1.webp";
import nextStepImg1 from "@/assets/landingpage/nextstepimg1.webp";
import nextStepImg2 from "@/assets/landingpage/nextstepimg2.webp";
import nextStepImg3 from "@/assets/landingpage/nextstepimg3.webp";
import nextStepImg3mobile from "@/assets/landingpage/nextstepimg3mobile.webp";
import nextStepsArrow from "@/assets/landingpage/nextstepsarrow.webp";
import arrowRight from "@/assets/landingpage/arrow-right.webp";
import arrowRightWhite from "@/assets/landingpage/arrow-right-white.webp";
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

const socialProofStats = [
  {
    stat: "94%",
    label: "of clients",
    description:
      "prefer briefing their lawyer or expert with Nova rather than in a traditional face-to-face meeting.",
  },
  {
    stat: "20k+",
    label: "people",
    description: "have used Nova to navigate separation and divorce.",
  },
  {
    stat: "9/10",
    label: "Nova clients",
    description: "would recommend Nova to friends and family.",
  },
] as const;

const nextSteps = [
  {
    image: nextStepImg1,
    title: "1. Tell us about your situation",
    description:
      "A quick assessment helps us understand your circumstances and what matters most.",
  },
  {
    image: nextStepImg2,
    title: "2. Get your free personalised recommendation",
    description:
      "You’ll receive a clear recommendation on the best way to move forward based on your situation.",
  },
  {
    image: nextStepImg3,
    imageMobile: nextStepImg3mobile,
    title: "3. Meet your matched expert",
    description:
      "If needed, we’ll connect you with a trusted family lawyer or expert who’s fully briefed and ready to help.",
  },
] as const;

const conversionLandingBgVars: { [key: `--${string}`]: string } = {
  "--conversion-landing-bg": `url(${conversionLandingBackground})`,
};

const ConversionLandingPage: React.FC = () => {
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
      className="flex min-h-screen flex-col bg-[#FFFFEF] sm:[background-image:var(--conversion-landing-bg)] sm:[background-size:100%_auto] sm:[background-position:top_center] sm:bg-no-repeat"
      style={conversionLandingBgVars}
    >
      <ConversionHeader />
      <main className="mx-auto flex w-full max-w-[1920px] flex-1 flex-col items-center py-10 sm:py-14 lg:pt-16 lg:pb-0">

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

        {/* Social proof / trust stats */}
        <section
          className="w-full py-16 sm:py-20 md:py-32"
          aria-labelledby="conversion-social-proof-heading"
        >
          <div className="mx-auto max-w-5xl px-4 text-center sm:px-6 lg:max-w-screen-2xl">
            <h2
              id="conversion-social-proof-heading"
              className="font-nineties leading-tight text-novaBlack text-[2.5rem] md:text-[2.25rem] md:leading-snug lg:text-[3rem] xl:text-[4rem] px-5 sm:px-0"
            >
              Choose Nova for proven results, trusted by thousands.
            </h2>
            <div className="mt-12 grid grid-cols-1 gap-4 md:mt-32 md:grid-cols-3 md:gap-8 lg:gap-12">
              {socialProofStats.map((item) => (
                <div key={item.stat} className="flex flex-col items-center text-center">
                  <p className="font-neue text-[90px] tabular-nums text-[#FCB84C] sm:text-5xl md:text-[40px] lg:text-[64px] xl:text-[128px]">
                    {item.stat}
                  </p>
                  <p className="mt-[-20px] sm:mt-3 font-neue text-[32px] sm:text-lg text-novaBlack md:text-[40px]">
                    {item.label}
                  </p>
                  <p className="mt-5 sm:mt-10 max-w-[22rem] font-neue text-[20px] sm:text-xl leading-relaxed text-novaBlack sm:max-w-none px-3 sm:px-5 mb-6 sm:mb-0">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <div className="flex justify-center sm:hidden mt-[-20px]">
              <FormButton
                onClick={handleGetStartedClick}
                variant="custom"
                size="custom"
                  className="landing-primary-button landing-primary-button--mini-hero group max-w-full self-start font-neue text-[16px] !py-3 sm:text-lg"
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

        {/* Three next steps — cream panel, illustrations, serif titles, flow arrows */}
        <section
          className="w-full py-12 sm:py-20 md:py-32 xl:py-42"
          aria-labelledby="conversion-next-steps-heading"
        >
          <div className="mx-auto max-w-5xl px-4 text-center sm:px-6 lg:max-w-screen-2xl">
            <h2
              id="conversion-next-steps-heading"
              className="font-nineties leading-tight text-novaBlack text-[2.5rem] md:text-[2.25rem] md:leading-snug lg:text-[4rem]"
            >
              Take your three next steps with Nova
            </h2>
            <div className="mt-12 flex flex-col items-stretch gap-12 md:mt-16 lg:mt-[128px] md:flex-row md:items-start md:justify-center md:gap-0 lg:gap-1">
              {nextSteps.map((item, index) => (
                <React.Fragment key={item.title}>
                  {index > 0 ? (
                    <div
                      className="hidden shrink-0 md:flex md:h-[13rem] md:items-center md:justify-center md:px-2 pt-40 lg:h-[14rem] lg:px-4"
                      aria-hidden
                    >
                      <img
                        src={nextStepsArrow}
                        alt=""
                        // className="h-[22px] w-auto shrink-0 object-contain object-center md:h-6 md:w-auto lg:h-7 lg:w-auto"
                        decoding="async"
                      />
                    </div>
                  ) : null}
                  <div className="flex min-w-0 flex-1 flex-col items-center text-center md:max-w-[min(100%,20rem)] lg:max-w-[22rem]">
                    <div className="mb-6 flex h-[min(11rem,42vw)] w-full max-w-[16rem] items-center justify-center sm:h-44 sm:max-w-none md:mb-8 md:h-[13rem] lg:h-[14rem]">
                      {"imageMobile" in item ? (
                        <>
                          <img
                            src={item.imageMobile}
                            alt=""
                            className="max-h-full w-auto max-w-full object-contain object-center md:hidden"
                            loading="lazy"
                            decoding="async"
                          />
                          <img
                            src={item.image}
                            alt=""
                            className="hidden max-h-full w-auto max-w-full object-contain object-center md:block"
                            loading="lazy"
                            decoding="async"
                          />
                        </>
                      ) : (
                        <img
                          src={item.image}
                          alt=""
                          className="max-h-full w-auto max-w-full object-contain object-center"
                          loading="lazy"
                          decoding="async"
                        />
                      )}
                    </div>
                    {index === 2 && <>
                      <div className="inline-flex items-center justify-center bg-[#FCD8FC] px-2 py-2 rounded-full text-[14px] leading-none text-novaBlack sm:hidden">
                        Optional
                      </div>
                    </>}
                    <h3 className="sm:max-w-[18rem] font-nineties text-[28px] leading-snug text-novaBlack sm:text-xl md:max-w-none lg:text-[31px] lg:leading-snug my-4 sm:my-0">
                      {item.title}
                    </h3>
                    <p className={`mt-3 sm:max-w-[20rem] font-neue text-[20px] leading-relaxed text-novaBlack/90 sm:text-xl md:max-w-none mb-4 sm:mb-0 ${index === 2 ? "px-[18px]" : "px-2"}`}>
                      {item.description}
                    </p>
                  </div>
                </React.Fragment>
              ))}
            </div>
            <div className="mt-12 flex justify-center md:mt-[128px]">
              <FormButton
                onClick={handleGetStartedClick}
                variant="custom"
                size="custom"
                  className="landing-primary-button landing-primary-button--mini-hero group max-w-full self-start font-neue text-base !py-3 sm:text-lg"
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
          </div>
        </section>
      </main>
      <ConversionFooter />
    </div>
  );
};

export default ConversionLandingPage;
