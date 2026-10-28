import React, { useEffect } from "react";

import LandingHeader from "../components/landing-page/landing-layout/landingHeader";
import LandingFooter from "../components/landing-page/landing-layout/landingFooter";
import Section1 from "@/components/landing-page/section1";
import Section2 from "@/components/landing-page/section2";
import Section3 from "@/components/landing-page/section3";
import Section4 from "@/components/landing-page/section4";
import Section5 from "@/components/landing-page/section5";

const LandingPage: React.FC = () => {
  useEffect(() => {
    const scrollToHash = (isInitialLoad = false) => {
      const hash = window.location.hash;
      if (hash) {
        // Remove the '#' from the hash
        const id = hash.substring(1);
        
        // Function to attempt scrolling with retry logic
        const attemptScroll = (retries = 5) => {
          const element = document.getElementById(id);
          
          if (element) {
            // Account for sticky header offset
            const headerOffset = 80;
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
              top: offsetPosition,
              behavior: 'smooth'
            });
          } else if (retries > 0) {
            // Retry after a short delay if element not found yet (mainly for initial load)
            setTimeout(() => attemptScroll(retries - 1), 100);
          }
        };

        // For initial load, wait a bit for DOM to be ready
        // For hash changes (same-page navigation), scroll immediately
        if (isInitialLoad) {
          setTimeout(() => attemptScroll(), 100);
        } else {
          // Small delay to ensure hash change is processed
          setTimeout(() => attemptScroll(2), 50);
        }
      }
    };

    // Handle hash changes (same-page navigation) - this ensures smooth scrolling with header offset
    const handleHashChange = () => scrollToHash(false);

    // Handle initial page load with hash (cross-page navigation)
    scrollToHash(true);

    // Add event listener for same-page navigation
    window.addEventListener('hashchange', handleHashChange);

    return () => {
      window.removeEventListener('hashchange', handleHashChange);
    };
  }, []);

  return (
    <div className="min-h-screen bg-novaNeutral-50 flex flex-col">
      <LandingHeader />
      <main className="flex-1">
        <Section1 />
        <Section2 />
        <Section3 />
        <Section4 />
        <Section5 />
      </main>
      <LandingFooter />
    </div>
  );
};

export default LandingPage;
