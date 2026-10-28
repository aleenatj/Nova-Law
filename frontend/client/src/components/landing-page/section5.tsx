import React, { useState } from "react";

import NovaLogo from "@/assets/landingpage/Logo.png";
import { renderHtmlContent } from "@/utils";

export const faqIntroText = "Your situation is unique, but we've gathered some of the questions we're asked most often by our community at this part of the journey and the answers that can help you find your next step.";

export const faqTitle = "Frequently Asked Questions";

export const faqs = [
  {
    question: "What is Nova?",
    answer: "Nova is your intelligent guide through separation and divorce. It combines expert human insight with advanced AI to help you understand your situation, explore your options and take your next step with confidence.<br><br><strong>Nova helps you understand your options and connect with the right expert – mediator, lawyer, or other support – based on your situation.</strong>"
  },
  {
    question: "Who is Nova for?",
    answer: "Nova is for anyone navigating the end of a relationship – whether you’re married, cohabiting or figuring out shared parenting. If you’re unsure where to start, Nova helps you find clarity, practical direction and the right kind of expert support."
  },
  {
    question: "How does Nova work?",
    answer: "You answer a few simple questions about your situation. Nova’s AI analyses your responses, outlines your best options and, if needed, recommends trusted family professionals. If you need help along the way, Nova Navigators are Nova’s client support team, helping people use the platform and connect with the right experts at the right time."
  },
  {
    question: "Is Nova a law firm?",
    answer: "No, it’s an independent platform created by family lawyers, technologists and therapists to make expert legal help easier to access. When legal advice is needed, Nova introduces you to experts from the fully regulated law firm, Family Law Partners.<br><br><strong>Nova may recommend:</strong><ul><li>mediation</li><li>DIY divorce routes</li><li>family consultants</li><li>legal advice</li></ul><strong>depending on what’s best for your situation.</strong>"
  },
  {
    question: "How much does Nova cost?",
    // answer: "Most of Nova’s technology is completely free to use. If you decide to work with a lawyer or mediator, their fees will apply – but using Nova usually saves you hundreds of pounds, if not more, by briefing them efficiently from the start."
    answer: "Most of Nova’s technology is completely free to use. If you decide to work with a lawyer or mediator, their fees will apply – but using Nova usually saves you hundreds of pounds by briefing them efficiently from the start.<br /><br /Many people begin with a <strong>Strategic Advice Consultation (SAC)</strong> with a specialist family lawyer. These <strong>typically cost £299 including VAT</strong> and usually last around <strong>1 hour</strong>, so you have time to explore your situation in depth.<br /><br /><strong>Within 2 working days after the consultation</strong>, you’ll also receive a <strong>Recommendations & Next Steps Letter of Advice</strong> – giving you clear guidance you can return to, reflect on, or share if needed."
  },
  {
    question: "What are Nova Navigators?",
    answer: "Nova Navigators are Nova’s client support team, helping people use the platform and connect with the right experts at the right time.<br><br>They can answer questions about how Nova works, help you move through the platform, and guide you to the most appropriate next step.<br><br>Nova Navigators do not provide legal or other expert advice themselves. Their role is to support you in using Nova and ensure you connect with the right expert for your situation."
  },
  {
    question: "What are Nova Navigator support hours?",
    answer: "Nova Navigators respond within <strong>one business day</strong>.Live support is available <strong>Monday–Friday, 9.00am–7.00pm (UK business days)</strong>.You can submit an enquiry at any time, and messages received outside these hours will be responded to the next business day."
  },
  {
    question: "Is this AI? What’s the difference between Nova and ChatGPT?",
    answer: "Yes, Nova uses AI, but it’s specialised AI, designed by family law experts over many years. Unlike general chatbots, Nova asks you the right questions at the right time and gives you reliable, tailored guidance instead of generalised answers."
  },
  {
    question: "What is the divorce process?",
    answer: "Every situation is different, but most divorces involve three stages: ending the legal marriage or civil partnership, agreeing finances, and resolving child arrangements. Nova explains each step clearly and helps you understand which approach – like mediation or collaborative law – might work best for you."
  },
  {
    question: "Can Nova represent me at court?",
    answer: "Nova itself can’t represent you in court, but it can connect you with lawyers who can. It also helps you prepare efficiently, so if you do need to go to court, your lawyer already understands your case in detail."
  },
  {
    question: "I’ve already started my divorce process – can Nova still help me?",
    answer: "Absolutely. Whether you’re early on or deep into proceedings, Nova can still help you check your options, clarify next steps, and make sure you’re getting the right kind of expert help."
  },
  {
    question: "My case is complicated – can Nova still help me?",
    answer: "Yes. Nova supports everything from amicable separations to complex disputes involving finances, property, or children. Its network includes professionals experienced in high-conflict or high-value cases,  so you’re in capable hands."
  },
  {
    question: "I’m a family professional or dispute resolution expert – how do I join Nova?",
    answer: "Nova partners with trusted, highly skilled professionals who share its vision for a smarter, more humane family law system. If that sounds like you, please  get in touch through the <a href='/become-a-nova-professional' style='color: #DB219A; text-decoration: none;'>Join us</a> link to start a conversation."
  },
  {
    question: "What problem were you trying to solve when you created Nova?",
    answer: `Alan Larkin (Founder): “Families going through divorce and separation encounter a system that feels designed to hinder rather than help them. There’s no easy way for ordinary people to navigate the legal process. It’s confusing, stressful and, all too often, traumatic. The lack of affordability of expert legal help is an effective bar to large parts of our community that are as deserving of this assistance as those with deeper pockets. We have a collective failure of policy, regulation and business models designed to limit professional risk rather than promote exceptional client care.</br></br>
Nova was created to change this unacceptable reality.</br></br>
We wanted to give people clarity, support and accessible tools designed to meet their unique needs rather than the tick boxes of a legal system. Technology allows us to deliver this change in a way that traditional services alone cannot match. At its heart, Nova exists because well-designed technology allied to expert human services is the best way to increase access to affordable legal expertise.`
  }
];



const Section5: React.FC = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const handleToggle = (index: number) => {
    setOpenIndex((prev) => (prev === index ? null : index));
  };

  return (
    <section
      id="faq"
      className="flex overflow-hidden px-4 py-10 md:px-12 md:py-24 items-center justify-center"
      style={{
        background: "linear-gradient(to bottom, #EDE0FF, #FBD3E4)",
      }}
    >
      <div className="rounded-[24px] bg-white max-w-[1362px] flex-1 flex md:px-[120px]  sm:py-[60px] p-6">
        <div className="hidden sm:block w-2/24">
          <img src={NovaLogo} alt="Nova Logo" className="h-auto w-[130px]" />
        </div>
        <div className="w-full sm:w-22/24 px-0 md:px-10 lg:px-20">
          <h2
            className="text-[#26055C] sm:text-novaBlack font-nineties text-[36px] md:text-[40px]"
            style={{
              WebkitTextStroke: '0.5px #07161E',
            }}
          >
            {faqTitle}
          </h2>
          <p className="text-[16px] text-novaBlack leading-[1.6] my-4 max-w-[700px]">
            {faqIntroText}
          </p>
          <div className="mt-6">
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

export default Section5;

export type FAQ = {
  question: string;
  answer: string;
};

export type FAQAccordionItemProps = {
  faq: FAQ;
  isOpen: boolean;
  onToggle: () => void;
};

export const FAQAccordionItem: React.FC<FAQAccordionItemProps> = ({
  faq,
  isOpen,
  onToggle,
}) => {
  const contentRef = React.useRef<HTMLDivElement>(null);
  const contentHeight = contentRef.current?.scrollHeight ?? 0;

  return (
    <div className="py-4 last:border-b-0 max-w-[700px]">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between text-left text-[#26055C]"
        aria-expanded={isOpen}
      >
        <span className="text-[18px] sm:text-novaBlack text-[#26055C] max-w-[80%]">{faq.question}</span>
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
        <div className="text-[16px] text-novaBlack leading-[1.6] my-4 [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:my-2 [&_li]:my-0.5 [&_ul]:list-outside">
          {renderHtmlContent(faq.answer)}
        </div>
      </div>
    </div>
  );
};