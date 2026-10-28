import React from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";
import "@/styles/landingpage.css";

const NovaEngagePage: React.FC = () => {
  const handleGetStartedClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    window.open("https://novaforprofessionals.novalaw.co.uk/", "_blank", "noopener,noreferrer");
  };

  return (
    <div className="min-h-screen bg-novaNeutral-50">
      <LandingHeader hidenavs={false} onGetStartedClick={handleGetStartedClick}/>
      <div className="flex-1 bg-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-8 text-center font-nineties tracking-wide">
            Are you a family lawyer looking for better ways to connect to the people who need you most?
          </h1>

          <div className="prose prose-lg max-w-none">
            <div className="text-novaNeutral-600 space-y-6">
              <p>
                Nova Engage is our AI-powered client onboarding application that prepares your prospective family law clients for their first, all-important consultation. It provides you with essential client information, ensuring an exceptional client experience from the very first meeting.
              </p>

              <p>
                Nova Engage addresses your clients' pain points, helping them articulate their complex situations during emotional times. Our rich contextual help ensures your clients feel well informed, creating the space to build trust in advance of your meeting. We help your clients understand the importance of instructing regulated, highly trained family law specialists like you.
              </p>

              <p>
                Nova Engage addresses sensitive issues such as domestic abuse with sensitivity and compassion. Whether it's Child Inclusive Mediation, or Schedule 1 claims. We ask the right questions every time.
              </p>

              <p>
                Nova Engage is the first family law client onboarding application of its kind and has helped over 16,000 clients instruct family lawyers like you. That's over 4 billion pounds of net assets. What's more, 93 per cent of our public users have said they would recommend Nova Engage to a friend. We passionately believe that affordable, transformative technology should be available to every family lawyer.
              </p>

              <p>
                Nova Engage offers real-world productivity gains. You can use the time we'll save you on more valuable endeavours such as chargeable client work or business development. Stop being a data collector and get back to being the lawyer your clients are looking for: providing advice, guidance and strategy from the very first minute.
              </p>

              <p>
                Nova Engage helps practices of every size focus on what matters the most: Your clients and the advice you give them. Let's make it easy for your clients to instruct you. Click on the button below for a deeper look at Nova Engage.
              </p>

              <h2 className="text-2xl font-bold text-novaNeutral-900 mt-12 mb-8 text-center">
                Sharpen your focus with Nova Engage: our AI-powered client onboarding application specially developed for regulated lawyers in England and Wales.
              </h2>

              <div className="flex justify-center mt-8">
                <a
                  href="https://novaforprofessionals.novalaw.co.uk/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="landing-primary-button inline-block text-center"
                >
                  Nova Engage
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
      <LandingFooter />
    </div>
  );
};

export default NovaEngagePage;

