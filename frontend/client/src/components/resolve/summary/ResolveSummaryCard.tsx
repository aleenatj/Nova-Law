import React, { useState, useEffect, useCallback } from "react";
import { Link } from "wouter";
import useEmblaCarousel from "embla-carousel-react";
import Autoplay from "embla-carousel-autoplay";
import { FormButton } from "../../../utils/formComponents";
import GlobalModal from "@/components/modal/GlobalModal";
import { useAuth } from "../../../contexts/AuthContext";
import { useRole } from "../../../contexts/RoleContext";
import { LawyerProfile } from "@/lib/types";

interface ResolveSummaryCardProps {
  summary: string;
  title?: string;
  resolveId?: string;
  caseId?: string;
  lawyer_profiles?: LawyerProfile[];
}

export const ResolveSummaryCard: React.FC<ResolveSummaryCardProps> = ({
  summary,
  title = "Ready for Professional Legal Guidance?",
  resolveId,
  caseId,
  lawyer_profiles,
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);
  const { user, isAuthenticated } = useAuth();
  const { currentRole } = useRole();
  
  // Calculate total slides
  const totalSlides = lawyer_profiles ? lawyer_profiles.length : 0;
  const hasMultipleLawyers = totalSlides > 1;

  // Embla Carousel setup with autoplay
  const [emblaRef, emblaApi] = useEmblaCarousel(
    { 
      loop: hasMultipleLawyers,
      align: 'center',
      skipSnaps: false,
      duration: 20,
    },
    hasMultipleLawyers ? [Autoplay({ delay: 5000, stopOnInteraction: false, stopOnMouseEnter: true, stopOnFocusIn: false })] : []
  );

  // Track current slide index
  useEffect(() => {
    if (!emblaApi) return;

    const onSelect = () => {
      setCurrentSlide(emblaApi.selectedScrollSnap());
    };

    emblaApi.on("select", onSelect);
    onSelect();

    return () => {
      emblaApi.off("select", onSelect);
    };
  }, [emblaApi]);

  // Navigation handlers
  const handlePrevSlide = useCallback(() => {
    if (emblaApi) emblaApi.scrollPrev();
  }, [emblaApi]);

  const handleNextSlide = useCallback(() => {
    if (emblaApi) emblaApi.scrollNext();
  }, [emblaApi]);

  const scrollTo = useCallback(
    (index: number) => {
      if (emblaApi) emblaApi.scrollTo(index);
    },
    [emblaApi]
  );
  const features = [
    {
      icon: "fas fa-clock",
      title: "30-min Consultation",
      description: "Initial discussion about your case",
    },
    {
      icon: "fas fa-shield-alt",
      title: "Confidential",
      description: "Protected by attorney-client privilege",
    },
    {
      icon: "fas fa-star",
      title: "Experienced",
      description: "Specialized family law attorneys",
    },
    {
      icon: "fas fa-handshake",
      title: "No Pressure",
      description: "Get advice with no obligation",
    },
  ];

  // Function to render HTML content safely
  const renderHTMLContent = (htmlString: string) => {
    // Split by <br> tags and render each part
    const parts = htmlString.split("<br>");
    return parts.map((part, index) => {
      // Check if this part contains bold tags
      if (part.includes("<b>") && part.includes("</b>")) {
        const boldMatch = part.match(/(.*)<b>(.*?)<\/b>(.*)/);
        if (boldMatch) {
          const [, before, boldText, after] = boldMatch;
          return (
            <p key={index} className="mb-1 last:mb-0 text-xs sm:text-sm">
              {before}
              <strong className="font-semibold text-novaNeutral-900">
                {boldText}
              </strong>
              {after}
            </p>
          );
        }
      }
      return (
        <p key={index} className="mb-1 last:mb-0 text-xs sm:text-sm">
          {part}
        </p>
      );
    });
  };

  const handleBookConsultation = () => {
    // If user is guest or not authenticated, show signup modal
    setModalOpen(true);
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Main Content Card */}
      <div className="bg-novaSuccess-50 border border-novaSuccess-200 rounded-lg p-6">
        {/* Top Section */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-novaSuccess-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <i className="fas fa-user-check text-xl text-novaSuccess-600"></i>
          </div>
          <h2 className="text-xl font-bold text-novaNeutral-900 mb-3">
            {title}
          </h2>
          <p className="text-novaNeutral-600 text-sm leading-relaxed max-w-xl mx-auto">
            Based on your assessment, connecting with a qualified family law
            attorney can help you understand your rights and options.
          </p>
        </div>

        {/* Summary Card */}
        <div className="bg-white border border-novaNeutral-200 rounded-lg p-4 shadow-sm mb-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-novaSuccess-100 rounded-full flex items-center justify-center">
                <i className="fas fa-file-alt text-novaSuccess-600 text-sm"></i>
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-xs lg:text-base font-semibold text-novaNeutral-900 mb-1 lg:mb-2">
                Your Assessment Summary
              </h3>
              <div className="text-novaNeutral-700 text-xs lg:text-sm leading-relaxed max-h-32 xl:max-h-48 overflow-y-auto pr-1 sm:pr-2 scrollbar-thin scrollbar-thumb-novaNeutral-300 scrollbar-track-novaNeutral-100">
                {renderHTMLContent(summary)}
              </div>
            </div>
          </div>
        </div>

        {/* Feature Cards Grid - More compact on mobile */}
        <div className="grid grid-cols-2 gap-2 md:gap-3 mb-3 sm:mb-4">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-lg p-3 shadow-sm border border-novaNeutral-100 hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex items-center space-x-1 sm:space-x-2">
                <i className={`${feature.icon} text-novaSuccess-600 text-xs sm:text-sm`}></i>
                <div className="min-w-0 flex-1">
                  <h3 className="text-xs lg:text-sm font-semibold text-novaNeutral-900 truncate">
                    {feature.title}
                  </h3>
                  <p className="text-novaNeutral-600 text-xs leading-tight hidden sm:block">
                    {feature.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
        {/* Matched Lawyers Section - Slider */}
        {lawyer_profiles && lawyer_profiles.length > 0 && currentRole === 'Guest' && (
          <div className="bg-gradient-to-br from-white via-novaViolet-50/30 to-white border border-novaViolet-100 rounded-xl p-3 sm:p-5 mb-4">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-novaViolet-100 rounded-full hidden sm:flex items-center justify-center">
                  <i className="fas fa-gavel text-novaViolet-600 text-sm"></i>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="mb-4">
                  <h3 className="text-sm lg:text-lg font-bold text-novaNeutral-900 mb-1">
                    Recommended For You
                  </h3>
                  <p className="text-xs lg:text-sm text-novaNeutral-600 font-medium">
                    Our Nova network of regulated experts
                  </p>
                </div>

                {/* Slider Container */}
                <div className="relative overflow-hidden group">
                  {/* Left Arrow - Projects out from section */}
                  {hasMultipleLawyers && (
                    <button
                      onClick={handlePrevSlide}
                      className="absolute left-0 top-1/2 -translate-y-1/2 z-10 sm:w-9 sm:h-9 w-6 h-6 flex items-center justify-center rounded-full shadow-md border-2 border-white transition-all duration-300 bg-gradient-to-br from-white to-novaViolet-100 hover:from-novaViolet-50 hover:to-novaViolet-100 hover:scale-110"
                      aria-label="Previous profiles"
                    >
                      <i className="fas fa-chevron-left text-sm text-novaViolet-600"></i>
                    </button>
                  )}

                  {/* Right Arrow - Projects out from section */}
                  {hasMultipleLawyers && (
                    <button
                      onClick={handleNextSlide}
                      className="absolute right-0 top-1/2 -translate-y-1/2 z-10 sm:w-9 sm:h-9 w-6 h-6 flex items-center justify-center rounded-full shadow-md border-2 border-white transition-all duration-300 bg-gradient-to-br from-white to-novaViolet-100 hover:from-novaViolet-50 hover:to-novaViolet-100 hover:scale-110"
                      aria-label="Next profiles"
                    >
                      <i className="fas fa-chevron-right text-sm text-novaViolet-600"></i>
                    </button>
                  )}
                  
                  {/* Embla Viewport */}
                  <div className="overflow-hidden" ref={emblaRef}>
                    <div className="flex">
                      {lawyer_profiles && lawyer_profiles.map((lawyer, slideIndex) => (
                        <div
                          key={slideIndex}
                          className={`min-w-0 transition-opacity duration-300 ${
                            totalSlides === 1 
                              ? 'flex-[0_0_100%]' 
                              : 'flex-[0_0_80%] sm:flex-[0_0_85%] px-2 sm:px-3'
                          }`}
                          style={{
                            opacity: totalSlides === 1 ? 1 : (slideIndex === currentSlide ? 1 : 0.5)
                          }}
                        >
                          <div className="grid grid-cols-1 gap-4">
                              <div
                                className="bg-white rounded-xl transition-all duration-300 border border-novaViolet-100 hover:border-novaViolet-200 overflow-hidden group"
                              >
                                {/* Header with gradient background */}
                                <div className="bg-gradient-to-r from-novaViolet-50 to-novaPrimary-50 p-4 border-b border-novaNeutral-100">
                                  <div className="flex items-start gap-4">
                                    {lawyer.photo_url || lawyer.lawyer_photo_url ? (
                                      <div className="relative">
                                        <img
                                          src={lawyer.photo_url || lawyer.lawyer_photo_url}
                                          alt={""}
                                          className="w-14 h-14 rounded-full object-cover flex-shrink-0 ring-4 ring-white shadow-lg"
                                        />
                                        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-novaSuccess-600 rounded-full border-2 border-white flex items-center justify-center">
                                          <i className="fas fa-check text-white text-[8px]"></i>
                                        </div>
                                      </div>
                                    ) : (
                                      <div className="relative">
                                        <span
                                          className="w-14 h-14 flex items-center justify-center rounded-full bg-gradient-to-br from-novaViolet-400 to-novaViolet-600 flex-shrink-0 ring-4 ring-white shadow-lg"
                                          title={lawyer.name || lawyer.lawyer_name || "Lawyer"}
                                        >
                                          <i className="fa-solid fa-user text-white text-2xl"></i>
                                        </span>
                                        <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-novaSuccess-600 rounded-full border-2 border-white flex items-center justify-center">
                                          <i className="fas fa-check text-white text-[8px]"></i>
                                        </div>
                                      </div>
                                    )}
                                    <div className="flex-1 min-w-0">
                                      <h6 className="text-base lg:text-md font-bold text-novaNeutral-900 mb-1 truncate">
                                        {lawyer.name || lawyer.lawyer_name}
                                      </h6>
                                      {lawyer.experience && (
                                        <div className="flex items-center gap-1.5 text-xs text-novaNeutral-700 mb-1">
                                          <i className="fas fa-briefcase text-novaViolet-600"></i>
                                          <span className="font-medium">
                                            {typeof lawyer.experience === 'number' 
                                              ? `${lawyer.experience} Years Experience` 
                                              : `${lawyer.experience} Years Experience`}
                                          </span>
                                        </div>
                                      )}
                                      {(lawyer.city || lawyer.county) && (
                                        <div className="flex items-center gap-1.5 text-xs text-novaNeutral-600">
                                          <i className="fas fa-map-marker-alt text-novaViolet-600"></i>
                                          <span className="truncate">
                                            {[lawyer.city, lawyer.county].filter(Boolean).join(', ')}
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                </div>

                                {/* Content Section */}
                                <div className="p-4 space-y-3">
                                  {/* Specialisations */}
                                  
                                    <div className="bg-novaPrimary-50 rounded-lg p-3 border border-novaViolet-100">
                                      <div className="flex items-start gap-2">
                                        <div className="w-6 h-6 bg-novaViolet-100 rounded-lg flex items-center justify-center flex-shrink-0">
                                          <i className="fas fa-award text-novaViolet-600 text-xs"></i>
                                        </div>
                                        <div className="flex-1 min-w-0">
                                          <p className="text-xs font-bold text-novaViolet-900 mb-1">Specialisations</p>
                                          <p className="text-xs text-novaNeutral-700 leading-relaxed line-clamp-2">
                                            {lawyer.accredited_specialisations
                                              ? lawyer.accredited_specialisations
                                              : "Specialisation not specified"}
                                          </p>
                                        </div>
                                      </div>
                                    </div>

                                  {/* About Section */}
                                  {(lawyer.about || lawyer.lawyer_about) && (
                                    <div className="pt-2 border-t border-novaNeutral-100">
                                      <div className="flex items-start gap-2">
                                        <i className="fas fa-user-circle text-novaViolet-400 text-sm mt-0.5"></i>
                                        <div className="flex-1">
                                          <p className="text-xs font-semibold text-novaNeutral-900 mb-1">About</p>
                                          <p className="text-xs text-novaNeutral-600 leading-relaxed line-clamp-3">
                                            {lawyer.about || lawyer.lawyer_about}
                                          </p>
                                        </div>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Dots Indicator */}
                {hasMultipleLawyers && (
                  <div className="flex justify-center gap-2 mt-4">
                    {Array.from({ length: totalSlides }).map((_, index) => (
                      <button
                        key={index}
                        onClick={() => scrollTo(index)}
                        className={`rounded-full transition-all duration-300 ${
                          index === currentSlide
                            ? "bg-gradient-to-r from-novaViolet-500 to-novaViolet-600 w-8 h-2 shadow-md"
                            : "bg-novaNeutral-300 hover:bg-novaViolet-300 w-2 h-2"
                        }`}
                        aria-label={`Go to slide ${index + 1}`}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Call-to-Action Button */}
        <div className="text-center">
          {(caseId && isAuthenticated) ? ( 
            <Link href={`/case/${caseId}`}>
              <FormButton
                type="button"
                variant="success"
                size="md"
                className="bg-novaSuccess-600 text-white hover:bg-novaSuccess-700 py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2 mx-auto shadow-lg hover:shadow-xl"
              >
                <span className="text-white">View Case</span>
                <i className="fas fa-arrow-right text-xs"></i>
              </FormButton>
            </Link>
          ) : (currentRole === 'Guest') && (
            <FormButton
              type="button"
              variant="success"
              size="md"
              onClick={handleBookConsultation}
              className="bg-novaSuccess-600 hover:bg-novaSuccess-700 text-white py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-2 mx-auto shadow-lg hover:shadow-xl"
            >
              <span>Book Consultation</span>
              <i className="fas fa-arrow-right text-xs"></i>
            </FormButton>
          )}
        </div>
      </div>
      
      <GlobalModal 
        isOpen={modalOpen} 
        onClose={() => setModalOpen(false)} 
        type="signup" 
        resolveId={resolveId}
        onSuccess={() => {
          setModalOpen(false);
        }} 
      />
    </div>
  );
};

export default ResolveSummaryCard;
