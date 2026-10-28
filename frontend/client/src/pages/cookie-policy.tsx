import React from "react";
import LandingHeader from "@/components/landing-page/landing-layout/landingHeader";
import LandingFooter from "@/components/landing-page/landing-layout/landingFooter";

const CookiePolicy: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <LandingHeader hidenavs={false}/>
      <main id="main-content" role="main" className="flex-1 bg-white py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-novaNeutral-900 mb-8 text-center font-nineties tracking-wide">
            Cookie Policy
          </h1>
          
            <div className="prose prose-lg max-w-none">
                <div className="text-novaNeutral-600 space-y-6">
                    <p className="mb-4">
                        This website uses cookies. We use cookies to personalise content and ads, to provide social media features and to analyse our traffic. We also share information about your use of our site with our social media, advertising and analytics partners who may combine it with other information that you’ve provided to them or that they’ve collected from your use of their services.
                    </p>

                    <p className="mb-4">
                        Cookies are small text files that can be used by websites to make a user’s experience more efficient.
                    </p>

                    <p className="mb-4">
                        The law states that we can store cookies on your device if they are strictly necessary for the operation of this site. For all other types of cookies we need your permission.
                    </p>

                    <p className="mb-4">
                        This site uses different types of cookies. Some cookies are placed by third party services that appear on our pages.
                    </p>
                </div>
            </div>
        </div>
      </main>
      <LandingFooter />
    </div>
  );
};

export default CookiePolicy;

