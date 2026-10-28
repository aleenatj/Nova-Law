import React, { useState } from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";
import { faqs, FAQAccordionItem, faqIntroText, faqTitle } from "@/components/landing-page/section5";

const SupportAndGuidance: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const handleToggle = (index: number) => {
    setOpenIndex((prev) => (prev === index ? null : index));
  };

  return (
    <div className="min-h-screen flex flex-col">
      <LandingHeader hidenavs={false}/>
      <main id="main-content" role="main" className="flex-1 bg-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-8 text-center font-nineties tracking-wide">
            Support & Guidance
          </h1>

          {/* FAQs Section */}
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-novaNeutral-900 mb-4 font-nineties tracking-wide">
              {faqTitle}
            </h2>
            <p className="text-[16px] text-novaNeutral-600 leading-[1.6] mb-6">
              {faqIntroText}
            </p>
            <div>
              {faqs.map((faq, index) => (
                <FAQAccordionItem
                  key={faq.question}
                  faq={faq}
                  isOpen={openIndex === index}
                  onToggle={() => handleToggle(index)}
                />
              ))}
            </div>
          </div>
        </div>
      </main>
      <LandingFooter />
    </div>
  );
};

export default SupportAndGuidance;
