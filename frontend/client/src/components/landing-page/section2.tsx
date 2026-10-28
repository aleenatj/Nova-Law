import React from "react";
// import ResolveScreenshot from "@/assets/landingpage/resolvescreenshot.png";
import ResolveScreenshot from "@/assets/landingpage/resolvescreenshot.webp";
import backgroundGradient from "@/assets/landingpage/howworksgradient.webp";
import backgroundGradientMobile from "@/assets/landingpage/howworksgradientmobile.webp";
import "@/styles/landingpage.css";
import Diamond from "@/assets/landingpage/intersection.svg";
import { useRole } from "@/contexts/RoleContext";
import { getResolveUrl } from "@/lib/utils";

const benefits = [
  {
    description:
      "We’re here for you every step of the way, so you receive the best possible expert advice, at the best possible price – avoiding the pain and cost of going to court wherever possible.",
  },
  {
    description:
      "If and when appropriate, we’ll introduce you to a carefully matched, regulated family lawyer, dispute resolution expert or other family professional, fully briefed via our intelligent AI and ready to help you before you even meet them – saving you time, money and stress.",
  },
  {
    description:
      "We’ll give you clarity, precision and confidence in every decision by combining advanced AI, personalised to your exact situation, with expert support available whenever you need it.",
  },
];

const Section2: React.FC = () => {
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
      .landing-section2-bg { background-image: url(${backgroundGradient}); }
      @media (max-width: 640px) { .landing-section2-bg { background-image: url(${backgroundGradientMobile}); } }
    `}} />
    <section
      id="how-nova-works"
      className="landing-section2-bg relative overflow-hidden bg-cover bg-center bg-no-repeat py-12 sm:py-24 bg-[#FCF2FF]"
    >
      <div className="relative mx-auto gap-8 flex max-w-[1300px] flex-col items-center text-center lg:flex-row lg:items-stretch lg:text-left px-6 lg:px-0">
        <div className=" text-novaBlack lg:flex-1 lg:self-stretch">
          <div className="md:ml-[60px] ml-0 gap-5 flex flex-col">
            <h2
              className="text-[40px] font-nineties leading-[1.2] text-left text-novaBlack max-w-[90%]"
              style={{
                WebkitTextStroke: '0.5px #07161E',
              }}
            >
              Choose Nova for expert, regulated and personalised guidance
            </h2>
            <p className="text-[18px] text-novaBlack font-roman leading-[1.5] text-left max-w-[80%] my-5">
              Nova combines advanced AI with award-winning family law professionals to help you understand your options, guide you step by step, and connect you with the right expert at the right time — starting with a<strong> free personalised recommendation</strong>.
            </p>
          </div>

          <div className="relative gap-8 flex flex-col border-l border-novaBlack pl-8 ml-[40px] md:ml-[20px] mt-0 pt-6 max-w-[80%]">
            {benefits.map((benefit, i) => (
              <div key={i}>
                <div className="flex items-center">
                <span className="border-t border-novaBlack/10 absolute" style={{ width: i % 2 === 0 ? 46 : 70, left: i % 2 === 0 ? "-25px" : "-50px" }}></span>
                <img src={Diamond} alt="Diamond" className="absolute left-[-15px] w-[30px] h-[30px] mt-[1px]" />
              </div>
              <div key={benefit.description} className="relative pl-2">
                <p className="mt-[-10px] text-left text-novaBlack leading-[1.5]">
                  {benefit.description}
                </p>
              </div>
              </div>
            ))}
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
            className="landing-primary-button md:ml-[60px] ml-0 mt-10 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2"
          >
            Get started now
          </a>
        </div>

        <div className="flex w-full items-center justify-center lg:flex-1 lg:self-stretch">
          <img
            src={ResolveScreenshot}
            alt="Resolve Screenshot"
            className="h-full w-full max-w-2xl object-contain" // <- Enlarged image, from max-w-xl to max-w-2xl
          />
        </div>
      </div>
    </section>
    </>
  );
};

export default Section2;