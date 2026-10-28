import React from "react";
import { useLocation } from "wouter";
import { ProfileDropdown } from "@/components/layout/v1/ProfileDropdown";
import { useAuth } from "@/contexts/AuthContext";
import { useModal } from "@/contexts/ModalContext";
import novaLogo from "@/assets/ui/nova_logo.png";
import { useRole } from "@/contexts/RoleContext";
const Home: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { openModal } = useModal();
  const [, setLocation] = useLocation();
  const { currentRole } = useRole();
  // Handle navigation to resolve page
  const handleGetStarted = () => {
    setLocation(isAuthenticated && currentRole !== "Customer" && currentRole !== "Guest"
      ? "/case-dashboard"
      : "/resolve");
  };

  return (
    <div className="min-h-screen bg-novaNeutral-50">
      {/* Header with Sign In */}
      <header className="bg-white shadow-sm border-b border-novaNeutral-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-2 sm:py-4">
            <div className="flex items-center space-x-3">
              <div className="w-18 h-18 rounded-lg flex items-center justify-center">
                <img src={novaLogo} alt="NovaAI" className="w-12 h-12 sm:w-16 sm:h-16" />
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-semibold text-novaNeutral-900">
                  NovaAI
                </h1>
                <p className="text-xs sm:text-sm text-novaNeutral-500">Legal Assistant</p>
              </div>
            </div>
            {(() => {
              return !isAuthenticated ? (
                <button
                  onClick={() => openModal("signin")}
                  className="py-1 px-2 text-sm sm:text-base sm:px-4 sm:py-2 text-novaPrimary-500 border border-novaPrimary-500 hover:bg-novaPrimary-500 hover:text-white transition-colors rounded"
                >
                  <i className="fas fa-sign-in-alt mr-2"></i>
                  Sign In
                </button>
              ) : (
                <ProfileDropdown />
              );
            })()}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8 sm:space-y-12">
          {/* Hero Section */}
          <div className="text-center">
            <div className="bg-gradient-to-r from-novaPrimary-600 to-novaPrimary-800 rounded-2xl py-10 sm:py-12 px-6 sm:px-12 text-white">
              <h1 className="text-2xl sm:text-4xl md:text-5xl font-bold mb-2 sm:mb-6">
                AI-Powered Legal Solutions
              </h1>
              <p className="text-sm sm:text-xl md:text-2xl mb-4 sm:mb-8 max-w-3xl mx-auto">
                Get expert legal guidance with our intelligent platform. Connect
                with qualified lawyers and resolve your legal matters
                efficiently.
              </p>
              <div className="flex flex-col px-4 sm:px-0 sm:flex-row gap-4 justify-center">
                <button
                  className="bg-white text-novaPrimary-600 hover:bg-novaNeutral-100 text-lg px-8 py-2 rounded-lg font-semibold transition-colors"
                  onClick={handleGetStarted}
                >
                  <i className="fas fa-rocket mr-2"></i>
                  Get Started
                </button>
                <button className="border-white text-white hover:bg-white hover:text-novaPrimary-600 text-lg px-8 py-2 rounded-lg font-semibold bg-transparent border transition-colors">
                  <i className="fas fa-play mr-2"></i>
                  Watch Demo
                </button>
                {isAuthenticated && (
                  <button
                    className="bg-white text-novaPrimary-600 hover:bg-novaNeutral-100 text-lg px-8 py-2 rounded-lg font-semibold transition-colors"
                    onClick={() => setLocation("/case-dashboard")}
                  >
                    <i className="fas fa-briefcase mr-2"></i>
                    Go to Cases
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* How It Works */}
          <div className="mt-0 sm:mt-4 space-y-4 sm:space-y-8">
            <div className="text-center">
              <h2 className="text-2xl sm:text-2xl font-bold text-novaNeutral-900 mb-0">
                How It Works
              </h2>
              <p className="text-sm sm:text-md text-novaNeutral-600 max-w-2xl mx-auto">
                Our streamlined process makes getting legal help simple and
                efficient
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white border-0 shadow-lg rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 sm:w-12 h-8 sm:h-12 bg-novaPrimary-100 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-4 sm:w-6 h-4 sm:h-6 text-novaPrimary-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg sm:text-xl font-semibold text-novaNeutral-900">
                    1. Tell Us About Your Case
                  </h3>
                </div>
                <div className="space-y-3 text-novaNeutral-600">
                  <p className="text-sm sm:text-md">
                    Begin by telling us about your legal situation in your own
                    words. Our platform will guide you through a few simple
                    questions to ensure our AI-powered Case Assessment can
                    provide you with the most relevant support and guidance.
                  </p>

                  <div className="space-y-3">
                    <div>
                      <h4 className="font-medium text-novaNeutral-900 mb-2">
                        What Happens in This Step?
                      </h4>
                      <div className="space-y-2">
                        <p className="text-sm sm:text-md">
                          <strong>Personalized Intake:</strong> Share a brief
                          description of your legal issue, including what
                          happened and what you need help with.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Key Details Collection:</strong> Include
                          important dates, people involved, and any relevant
                          documents.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Initial Actions:</strong> Let us know if
                          you've already taken any steps or spoken to anyone
                          about your issue.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Confidentiality:</strong> Your information is
                          kept private and is only used to match you with the
                          most suitable legal resources.
                        </p>
                      </div>
                    </div>
                  </div>

                  <p className="text-sm sm:text-md text-novaNeutral-500 italic">
                    Your privacy is our priority. All information you share is
                    confidential and used solely to help you get the right legal
                    assistance.
                  </p>
                </div>
              </div>

              <div className="bg-white border-0 shadow-lg rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 sm:w-12 h-8 sm:h-12 bg-novaSuccess-100 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-4 sm:w-6 h-4 sm:h-6 text-novaSuccess-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg sm:text-xl font-semibold text-novaNeutral-900">
                    2. AI-Powered Legal Review
                  </h3>
                </div>
                <div className="space-y-3 text-novaNeutral-600">
                  <p className="text-sm sm:text-md">
                    Our AI system will now review the information you provided
                    to deliver a clear, actionable assessment of your legal
                    situation. This step uses advanced legal intelligence to
                    help you understand your options and next steps.
                  </p>

                  <div className="space-y-3">
                    <div>
                      <h4 className="font-medium text-novaNeutral-900 mb-2">
                        What Happens in This Step?
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p className="text-sm sm:text-md">
                          <strong>Automated Analysis:</strong> The AI reviews
                          your submitted details, identifies key facts, and
                          highlights important dates, parties, and documents.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Issue Spotting:</strong> It detects potential
                          legal issues, rights, and obligations based on your
                          description.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Risk & Opportunity Identification:</strong>{" "}
                          The system flags urgent matters, missing information,
                          and any red flags that may affect your case.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Tailored Insights:</strong> You receive a
                          summary of your situation, including possible legal
                          strategies or recommendations for further action.
                        </p>
                      </div>
                    </div>
                  </div>

                  <p className="text-sm sm:text-md text-novaNeutral-500 italic">
                    Note: This AI assessment is not a substitute for
                    professional legal advice, but it helps you prepare for a
                    more informed conversation with a qualified lawyer.
                  </p>
                </div>
              </div>

              <div className="bg-white border-0 shadow-lg rounded-lg p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 sm:w-12 h-8 sm:h-12 bg-novaAccent-100 rounded-lg flex items-center justify-center">
                    <svg
                      className="w-4 sm:w-6 h-4 sm:h-6 text-novaAccent-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg sm:text-xl font-semibold text-novaNeutral-900">
                    3. Connect with a Lawyer
                  </h3>
                </div>
                <div className="space-y-3 text-novaNeutral-600">
                  <p className="text-sm sm:text-md">
                    Now that your case has been assessed, it's time to take
                    action. In this step, you'll be matched with a qualified
                    lawyer who specializes in your legal issue. Through a secure
                    and confidential consultation, you'll receive professional
                    guidance tailored to your unique situation.
                  </p>

                  <div className="space-y-3">
                    <div>
                      <h4 className="font-medium text-novaNeutral-900 mb-2">
                        What Happens in This Step?
                      </h4>
                      <div className="space-y-2 text-sm">
                        <p className="text-sm sm:text-md">
                          <strong>Personalized Lawyer Matching:</strong> Based
                          on your case details, you are connected with a lawyer
                          who has the right expertise for your legal matter.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Flexible Consultation Options:</strong> Choose
                          from video calls, phone calls, or secure messaging to
                          consult with your lawyer at your convenience.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Share Relevant Documents:</strong> Easily
                          upload and share documents or evidence needed for your
                          consultation.
                        </p>
                        <p className="text-sm sm:text-md">
                          <strong>Professional Legal Advice:</strong> Receive
                          clear, actionable advice and discuss possible
                          solutions or next steps directly with your lawyer.
                        </p>
                      </div>
                    </div>
                  </div>

                  <p className="text-sm sm:text-md text-novaNeutral-500 italic">
                    Your privacy and satisfaction are our top priorities. All
                    consultations are strictly confidential, and you can always
                    reach out for follow-up questions or continued legal
                    assistance.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Call to Action */}
          <div className="text-center bg-white rounded-2xl shadow-lg p-6 sm:p-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-novaNeutral-900 mb-4">
              Ready to Get Started?
            </h2>
            <p className="text-sm sm:text-lg text-novaNeutral-600 mb-4 sm:mb-8 max-w-2xl mx-auto">
              Join thousands of users who have already resolved their legal
              matters with our AI-powered platform.
            </p>
            <button
              className="bg-novaPrimary-700 hover:bg-novaPrimary-600 text-white text-sm sm:text-lg px-8 sm:px-12 py-2 sm:py-4 rounded-lg font-semibold transition-colors"
              onClick={handleGetStarted}
            >
              <i className="fas fa-rocket mr-2"></i>
              Start Your Legal Journey
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Home;
