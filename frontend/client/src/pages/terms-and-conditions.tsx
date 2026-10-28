import React from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";

const TermsAndConditions: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <LandingHeader hidenavs={false}/>
      <main id="main-content" role="main" className="flex-1 bg-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-8 text-center font-nineties tracking-wide">
            Nova Platform User Agreement
          </h1>
          
          <div className="prose prose-lg max-w-none">
            <div className="text-novaNeutral-600 space-y-6">
              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">1. Welcome and Acceptance</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    Welcome to Nova. By creating an account and clicking "I agree", you enter into this User Agreement ("Agreement") with Nova Law Trading Limited ("Nova", "we", "us"). This Agreement governs your use of the Nova Platform (as defined below), including any free or paid features that help you understand your separation or divorce options and, if you choose, connect with a regulated lawyer.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">2. Contracting Parties</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    This Agreement is between: (i) you, the individual creating a Nova account ("you"); and (ii) Nova Law Trading Limited, a limited company registered in England and Wales (Company No. 14139589) with registered office at Preston Park House, South Road, Brighton, BN1 6SB ("Nova", "we", "us").
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">3. About Nova</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    Nova is a digital platform hosted at <a href="https://novalaw.co.uk" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">https://novalaw.co.uk</a> designed to guide individuals through separation and divorce (the "Nova Platform"). We help you understand your options, create a personalised pathway, and if you wish, introduce you to a regulated family lawyer. Neither the Nova Platform nor Nova Law Trading Limited is a law firm and does not itself provide legal advice. Legal advice is provided only by regulated lawyers, currently all of whom are from Family Law Partners, under their own Client Terms of Engagement with you.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">4. Licence to Use</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    Subject to your compliance with this Agreement, Nova grants you a limited, non-exclusive, non-transferable licence to use the Nova Platform on your devices for your personal separation or divorce journey. You may not reverse-engineer, copy, or modify Nova except as permitted by law.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">5. Fees and Deposit</h2>
                <div className="ml-6">
                  <p className="mb-4">
                  Fees and Deposit To secure your initial consultation with a regulated lawyer,
                  you will pay a deposit of £50 to Nova which will process the payment then transfer the monies into the client account of Family Law Partners where it will be held. This deposit is applied towards securing your first consultation and is non-refundable once your consultation is confirmed.
                  Any further fees for legal advice or representation are agreed directly between you and the regulated lawyer from Family Law Partners and paid directly to Family Law Partners. Nova does not receive any technology or referral fees from Family Law Partners.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">6. Lawyers and Legal Advice</h2>
                <div className="ml-6">
                  <p className="mb-4">
                  Nova works with lawyers from a regulated law firm, Family Law Partners, who provide legal advice under their own regulatory and professional indemnity obligations. Nova is not responsible for the content or outcome of any legal advice you receive. Your relationship with the lawyer is governed by their own Client Terms of Engagement with you, not by this Agreement.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">7. Data Protection and Privacy</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    Your use of the Nova Platform is governed by our <a href="/privacy-policy" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">Privacy Policy</a>, <a href="/cookie-policy" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">Cookie Policy</a>, and Data Sharing Agreement, which together set out how your data is processed, shared and retained. By using the Nova Platform, you consent to these policies.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">8. Your Responsibilities</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    You must not misuse the Nova Platform, introduce malware, interfere with its operation, or attempt to access data belonging to others. You agree to use the Nova Platform only for lawful personal purposes and not for any commercial use or automated access.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">9. Limitation of Liability</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    Nova provides the Nova Platform "as is" and you use it at your own risk. Nova does not warrant that the information or guidance generated is error-free or suitable for every individual. To the maximum extent permitted by law, Nova is not liable for any loss or damage arising from reliance on information generated by the Nova Platform or from actions taken by any lawyer. Nova's total liability to you is limited to the amount of the deposit you have paid, except in cases of death or personal injury caused by our negligence or fraud in which case it is unlimited.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">10. Termination</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    You may delete your Nova Platform account at any time. Nova may suspend or terminate your access to the Nova Platform if you breach this Agreement, fail to pay the deposit, or misuse the Nova Platform. Upon termination, all licences granted under this Agreement cease immediately.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">11. Changes to this Agreement</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    Nova may update this Agreement from time to time by publishing a new version on our website. Continued use of the Nova Platform after publication means you accept the updated terms.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">12. Governing Law and Jurisdiction</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    This Agreement is governed by and construed in accordance with the laws of England and Wales. The Parties agree to attempt to resolve any dispute or claim in connection with this Agreement in good faith using some form of Alternative Dispute Resolution ("ADR"). The method of ADR shall be chosen by mutual agreement of both parties. In the event that such ADR is unsuccessful, Any disputes will be subject to the exclusive jurisdiction of the courts of England and Wales.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">13. Contact and Complaints</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    By creating an account, you agree that we may contact you via email, messaging or phone with information directly related to your matter, including recommendations, next steps, and connections with relevant experts. These communications are part of the service and are not marketing communications.
                    <br/>If you have questions or complaints about Nova, please contact <a href="mailto:hello@novalaw.co.uk" className="text-blue-600 underline hover:text-blue-800">hello@novalaw.co.uk</a>. If your concern relates to legal advice provided by a regulated lawyer, you may contact Family Law Partners (UK) Limited or the Legal Ombudsman (<a href="https://www.legalombudsman.org.uk" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline hover:text-blue-800">www.legalombudsman.org.uk</a>).
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-novaNeutral-900 mb-4">14. Miscellaneous</h2>
                <div className="ml-6">
                  <p className="mb-4">
                    This Agreement constitutes the entire agreement between you and Nova. If any clause is found unenforceable, the rest remains valid. No third party has rights under this Agreement. Each party is independent, and nothing here creates employment, agency or partnership relations.
                  </p>
                </div>
              </section>
            </div>
          </div>
        </div>
      </main>
      <LandingFooter />
    </div>
  );
};

export default TermsAndConditions;
