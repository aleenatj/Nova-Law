import React from "react";
import backgroundGradient from "@/assets/landingpage/resultquotegradient.webp";
import backgroundGradientMobile from "@/assets/landingpage/resultquotegradientmobile.webp";
import landingSmallBgSection3 from "@/assets/landingpage/LandingSmallbgSection3.webp";
import landingBgSection3 from "@/assets/landingpage/LandingbgSection3.webp";

const stats = [
  {
    headline: "94%",
    subHeadline: "of clients",
    description:
      "preferred briefing their family professional online through Nova rather than in a traditional face-to-face meeting",
  },
  {
    headline: "20k+",
    subHeadline: "people",
    description:
      "just like you have used Nova to make sense of life's difficult moments",
  },
  {
    headline: "9/10",
    subHeadline: "Nova clients",
    description:
      "said they would recommend us to family and friends",
  },
];

const Section3: React.FC = () => {
  return (
    <section id="our-results" className="relative overflow-hidden">

      <div className="relative flex flex-col bg-[#DB219A]">
        <div
          className="section3-stats-bg px-6 py-20 text-white sm:px-10 lg:px-24"
          style={{
            backgroundImage: `url(${landingBgSection3})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
          }}
        >
          <div className="mx-auto max-w-5xl text-center">
            <h2 className="text-[40px] font-nineties text-white w-[80%] mx-auto sm:w-[50%] w-[90%] leading-[1.2]">
              Choose Nova for proven results, trusted by thousands
            </h2>

            <div className="mt-12 grid gap-12 md:grid-cols-3 max-w-[85%] md:max-w-full mx-auto">
              {stats.map((stat) => (
                <div key={stat.headline} className="">
                  <div className="flex font-nineties w-[76%] mx-auto text-left">
                    <p className="text-[72px] sm:text-[56px] leading-[1.2]">
                      {stat.headline}
                    </p>
                    <p className="text-[30px] sm:text-[23px] ml-2 max-w-[10%] leading-[1] flex items-end pb-2">
                      {stat.subHeadline}
                    </p>
                  </div>
                  <p className="font-roman text-[18px] w-[76%] mx-auto text-novaBlack leading-[1.2] text-left mt-2 md:mt-4">
                    {stat.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <style dangerouslySetInnerHTML={{ __html: `
          .landing-section3-quote-bg { background-image: url(${backgroundGradient}); }
          @media (max-width: 640px) {
            .section3-stats-bg {
              background-image: url(${landingSmallBgSection3}) !important;
              background-size: cover;
              background-position: center;
              background-repeat: no-repeat;
            }
          }
        `}} />
        <div className="relative overflow-hidden px-4 py-10 md:px4 md:py-12 bg-[#512187]">
          <div
            className="landing-section3-quote-bg absolute inset-0 bg-cover bg-center bg-no-repeat"
          />
          <div className="relative mx-auto max-w-[90%] md:max-w-[32%] text-left">
            <div className="flex flex-row items-start">
              <span className="text-[64px] text-white" aria-hidden>
                &ldquo;
              </span>
              <p className="text-[32px] font-nineties text-white mt-4 leading-[1.2] px-5">
                Clear and easy to follow. I understood why that approach was recommended.&rdquo;
              </p>
            </div>
            <div className="text-[16px] font-roman text-white ml-6 mt-6">
              <p>Brian B</p>
              <p>UK</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Section3;