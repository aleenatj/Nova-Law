import React from "react";
import "@/styles/landingpage.css";
import AboutGradient from "@/assets/landingpage/aboutgradient.png";
import AboutGradientMobile from "@/assets/landingpage/aboutgradientmobile.webp";
import AboutImage from "@/assets/landingpage/alan_quote.webp";
import AboutImageDesk from "@/assets/landingpage/alan_quote_desk.webp";
import Achievement1 from "@/assets/landingpage/achievement1.png";
import Achievement2 from "@/assets/landingpage/achievement2.jpg";
import Achievement5 from "@/assets/landingpage/achievement5.jpg";
import Achievement6 from "@/assets/landingpage/achievement9.png";
import Achievement7 from "@/assets/landingpage/achievement7.png";
import { useRole } from "@/contexts/RoleContext";
import { getResolveUrl } from "@/lib/utils";
const Section4: React.FC = () => {
  // useRole may not be available during SSR (no PageWrapper on server)
  let currentRole = "Guest";
  try {
    const roleResult = useRole();
    currentRole = roleResult?.currentRole || "Guest";
  } catch {
    currentRole = "Guest";
  }
  
  const handleGetStartedClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (typeof window !== "undefined") {
      if (currentRole !== "Guest") {
        window.location.href = "/case-dashboard";
        return;
      }
      const url = await getResolveUrl();
      window.location.href = url;
    }
  };

  return (
    <>
    <style dangerouslySetInnerHTML={{ __html: `
      .landing-section4-bg { background-image: url(${AboutGradient}); }
      @media (max-width: 640px) { .landing-section4-bg { background-image: url(${AboutGradientMobile}); } }
      .landing-section4-border { background: linear-gradient(130deg, #E657FF 10%, #FF42AD 50%, transparent 50%, transparent 100%); }
      @media (max-width: 640px) { .landing-section4-border { background: linear-gradient(150deg, #E657FF 0%, #FF42AD 70%, transparent 40%, transparent 100%); } }
    `}} />
    <section id="about-us" className="landing-section4-bg relative overflow-hidden bg-[#FCF2FF] bg-cover bg-center bg-no-repeat">
      <div className="flex flex-col items-center justify-center py-8 md:py-24 px-4 gap-12">
        <div className="w-[95%] md:w-[62%] mx-auto flex flex-col lg:flex-row items-center justify-center gap-8">
          {/* Left/Top Content */}
          <div className="flex-1 flex flex-col items-center lg:items-start gap-8">
            <div className="font-nineties text-[40px] pr-0 lg:pr-8 leading-[1.2] text-left max-w-[100%] sm:max-w-[95%]" style={{ WebkitTextStroke: '0.5px #07161E' }}>
              Choose Nova for insightful support when you need it most
            </div>
            <div className="text-[18px] leading-[1.4] text-novaBlack flex flex-col gap-8 mt-3">
              <p className="max-w-[100%] md:max-w-[92%]">
                Nova offers you access exclusively to experts from Family Law Partners - one of The Times Law Firms of the Year 2026 - meaning that you’ll have access to the best possible advice at the best possible prices.
              </p>
              <p className="max-w-[100%] md:max-w-[92%]">
                This leading team of family experts (lawyers, mediators and therapists) is known for its innovative and client-centred approach, with an emphasis on avoiding court wherever possible.
              </p>
              <p className="max-w-[100%] md:max-w-[92%]">
                Using properly regulated experts ensures you have all the best possible options available to you on your journey through divorce or separation.
              </p>
              <p className="max-w-[100%] md:max-w-[92%]">
                The impact of Nova’s unique and innovative algorithms has been recognised with an Innovate UK ‘Best of the Best’ Award.
              </p>
            </div>
            <a 
              href="#"
              onClick={handleGetStartedClick}
              onKeyDown={(e) => {
                if (e.key === " ") {
                  e.preventDefault();
                  (e.currentTarget as HTMLAnchorElement).click();
                }
              }}
              className="landing-primary-button focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
            >
              Get started now
            </a>
          </div>
          {/* Right/Bottom Image */}
          <div className="flex-1 flex justify-center items-center">
            <img src={AboutImageDesk} alt="About" className="hidden md:block max-w-[100%] h-auto md:h-[50%]" />
            <img src={AboutImage} alt="About" className="block md:hidden max-w-full h-auto md:h-[50%]" />
          </div>
        </div>
        <div
          className="relative w-full sm:max-w-[685px] mx-auto my-4 rounded-[15px] overflow-hidden flex justify-center items-center"
          style={{
            padding: "1.2rem",
          }}
        >
          <div
            className="landing-section4-border"
            style={{
              content: '""',
              position: "absolute",
              inset: 0,
              borderRadius: 15,
              padding: 2,
              WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
              WebkitMaskComposite: "xor",
              mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
              maskComposite: "exclude",
              pointerEvents: "none",
              zIndex: 1,
              display: "block",
            } as React.CSSProperties}
            aria-hidden="true"
          />
          <div className="flex flex-wrap gap-1 sm:gap-2 p-0 sm:p-2 pl-2 items-center bg-transparent w-full relative z-10">
            <img src={Achievement1} alt="Achievement 1" className="h-[68px] sm:h-[85px] object-contain" />
            <img src={Achievement2} alt="Achievement 2" className="h-[68px] sm:h-[85px] object-contain" />
            <img src={Achievement5} alt="Achievement 5" className="h-[68px] sm:h-[85px] object-contain" />
            <img src={Achievement6} alt="Achievement 6" className="h-[68px] sm:h-[85px] object-contain bg-white p-1" />
            <img src={Achievement7} alt="Achievement 7" className="h-[68px] sm:h-[85px] object-contain" />
          </div>
        </div>
        <p className="text-center text-md text-novaNeutral-500 max-w-[900px] mx-auto italic">
          We have an ownership relationship with Family Law Partners, a firm of solicitors regulated by the Solicitors Regulation Authority.  You are not required to use this firm and may instruct any solicitor of your choosing.
        </p>
      </div>
    </section>
    </>
  );
};

export default Section4;