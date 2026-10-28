import React, { useState, useEffect, useRef } from "react";
import "@/styles/landingpage.css";

import NovaLogo from "@/assets/landingpage/Logo.png";

const faqs = [
  {
    question: "Is Nova trying to replace professionals?",
    answer:
      "Absolutely not. Human expertise remains essential. Nova exists to support professionals by preparing clients, reducing administrative burden, and improving early understanding: allowing you to do your best work.",
  },
  {
    question: "Will I receive good-quality cases?",
    answer: "Yes. Nova identifies readiness, intent to proceed, and suitability, so the clients introduced to you are actively seeking constructive guidance and are prepared to engage with professional support."
  },
  {
    question: "How much admin does Nova remove?",
    answer: "A significant amount. Clients arrive with structured information, early clarity, and realistic expectations, saving time in initial consultations and throughout the process."
  },
  {
    question: "Do I lose control of the client relationship?",
    answer: "Not at all. Nova prepares clients before they reach you, so your relationship begins from a calmer, more informed, and more productive starting point."
  },
  {
    question: "What does partnering with Nova involve?",
    answer: "You work on your own terms and within your own professional framework. Nova introduces clients, supports the early journey, and provides tools that enhance the experience for both you and the people you support."
  }
];

const LawyerSection5: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const handleToggle = (index: number) => {
    setOpenIndex((prev) => (prev === index ? null : index));
  };

  return (
    <section
      id="lawyer-faq"
      className="flex overflow-hidden px-4 py-10 md:px-12 md:py-24 items-center justify-center"
      style={{
        background: "linear-gradient(to bottom, #EDE0FF, #FBD3E4)"
      }}
    >
      <div className="rounded-[24px] bg-white max-w-[1362px] flex-1 flex md:px-[120px] sm:py-[60px] p-6">
        <div className="hidden sm:block w-2/24">
          <img src={NovaLogo} alt="Nova Logo" className="h-auto w-[130px]" />
        </div>
        <div className="w-full sm:w-22/24 px-0 md:px-10 lg:px-16">
          <h2
            className="text-[#26055C] sm:text-novaBlack font-nineties text-[36px] md:text-[38px] 3xl:text-[40px]"
            style={{
              WebkitTextStroke: "0.5px #07161E",
            }}
          >
            Frequently Asked Questions
          </h2>
          <div className="mt-6 sm:max-w-[80%] w-full">
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
    </section>
  );
};

export default LawyerSection5;

type FAQ = {
  question: string;
  answer: string;
};

type FAQAccordionItemProps = {
  faq: FAQ;
  isOpen: boolean;
  onToggle: () => void;
};

const FAQAccordionItem: React.FC<FAQAccordionItemProps> = ({
  faq,
  isOpen,
  onToggle,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const [contentHeight, setContentHeight] = useState(0);

  useEffect(() => {
    if (contentRef.current) {
      setContentHeight(contentRef.current.scrollHeight);
    }
  }, [isOpen, faq.answer]);

  return (
    <div className="py-4 last:border-b-0 max-w-[800px]">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between text-left text-[#26055C]"
        aria-expanded={isOpen}
      >
        <span className="text-[16px] lg:text-[20px] sm:text-novaBlack text-[#26055C] sm:max-w-[80%] w-full">
          {faq.question}
        </span>
        <i
          className={`fa-solid ${
            isOpen ? "fa-minus rotate-180" : "fa-plus rotate-0"
          } ml-4 text-base text-[#26055C] transform transition-transform duration-300`}
          aria-hidden="true"
        />
      </button>
      <div
        ref={contentRef}
        className="overflow-hidden transition-all duration-300 ease-in-out"
        style={{
          maxHeight: isOpen ? `${contentHeight}px` : "0px",
          opacity: isOpen ? 1 : 0,
          marginTop: isOpen ? "12px" : "0px",
        }}
      >
        <div className="text-[16px] lg:text-[18px] text-novaBlack leading-[1.6] my-4 sm:pr-8 pr-2">
          {faq.answer}
        </div>
      </div>
    </div>
  );
};
