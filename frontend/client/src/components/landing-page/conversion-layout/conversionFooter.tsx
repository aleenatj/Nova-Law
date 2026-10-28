import React from "react";

import NovaLogo from "@/assets/landingpage/Logo.png";
// import HeaderGradient from "@/assets/landingpage/header-gradiant.png";

const ConversionFooter: React.FC = () => {
  return (
    <footer
      className="border-t border-novaGray-400"
    >
      <div className="flex gap-8 flex-row md:items-center md:justify-between max-w-[1500px] mx-auto py-6 px-6 text-novaBlack">
        <div className="flex min-w-0 flex-1 basis-0 items-start gap-3 md:flex-none md:basis-auto md:items-center">
          <a href="/" className="flex items-start md:items-center">
            <img src={NovaLogo} alt="Nova" className="w-[80px] sm:w-[120px]" />
          </a>
        </div>
        <div className="flex min-w-0 flex-1 basis-0 flex-col gap-8 mt-0 md:mt-12 md:flex-none md:basis-auto">
          <nav className="flex flex-col md:flex-row md:gap-6 gap-2 text-sm font-roman text-[16px] text-novaBlack">
            <a href="/#about-us" className="hover:opacity-70">
              About us
            </a>
            <a href="/#our-results" className="hover:opacity-70">
              Our results
            </a>
            <a href="/#faq" className="hover:opacity-70">
              FAQs
            </a>
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
          <p className="text-[14px] font-roman leading-[1.4] text-novaBlack w-[100%] md:w-[80%] lg:w-[62%] sm:block hidden">
            © Nova Law Trading Limited, a limited company incorporated in England & Wales with number 14398388 and registered office at Preston Park House, South Road, Brighton, East Sussex, United Kingdom, BN1 6SB.
          </p>
        </div>
      </div>
      <div className="flex flex-col gap-8 mt-0 md:mt-12 sm:hidden p-6">
          <p className="text-[14px] font-roman leading-[1.4] text-novaBlack w-[100%] md:w-[80%] lg:w-[62%]">
            © Nova Law Trading Limited, a limited company incorporated in England & Wales with number 14398388 and registered office at Preston Park House, South Road, Brighton, East Sussex, United Kingdom, BN1 6SB.
          </p>
        </div>
    </footer>
  );
};

export default ConversionFooter;
