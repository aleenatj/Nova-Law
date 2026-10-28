import React from "react";

import NovaLogo from "@/assets/landingpage/Logo.png";
import HeaderGradient from "@/assets/landingpage/header-gradiant.png";

const LandingFooter: React.FC = () => {
  return (
    <footer
      className="bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: `url(${HeaderGradient})` }}
    >
      <div className="flex flex-col gap-8 md:flex-row md:items-center md:justify-between max-w-[1400px] mx-auto py-6 px-6 text-novaBlack">
        <div className="flex items-center gap-3">
          <img src={NovaLogo} alt="Nova" className="w-[120px]" />
        </div>
        <div className="flex flex-col gap-8 mt-0 md:mt-12">
          <nav className="flex gap-6 text-sm font-roman text-[16px] text-novaBlack">
            <a href="/user-agreement" className="hover:opacity-70">
              User Agreement
            </a>
            <a href="/privacy-policy" className="hover:opacity-70">
              Privacy Policy
            </a>
            <a href="/contact-us" className="hover:opacity-70">
              Contact Us
            </a>
          </nav>
          <p className="text-[14px] font-roman leading-[1.4] text-novaBlack w-[100%] md:w-[80%] lg:w-[62%]">
            © Nova Law Trading Limited, a limited company incorporated in England & Wales with number 14398388 and registered office at Preston Park House, South Road, Brighton, East Sussex, United Kingdom, BN1 6SB.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default LandingFooter;
