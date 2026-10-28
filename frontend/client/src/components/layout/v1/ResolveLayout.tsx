import { ReactNode, useState, useCallback, useEffect, useMemo } from "react";
import { Link, useLocation } from "wouter";
import useEmblaCarousel from "embla-carousel-react";
import Backgroundgradient from "@/assets/landingpage/Resolvelayoutgradient.png";
import BackgroundgradientMobile from "@/assets/landingpage/ResolvelayoutgradientMobile.webp";
import NovaLogo from "@/assets/ui/NovaLogo.png";
import { FormButton } from "@/utils/formComponents";
import BackgroundQuestiongradient from "@/assets/landingpage/ResolvelayoutQuestiongradient.webp";
import { ProgressBar } from "@/components/ProgressBar";
import ResolveSummaryAbout from "@/components/resolve/summary/ResolveSummaryAbout";
import LawyerProfileDetail from "@/components/resolve/summary/LawyerProfileDetail";
import SummaryAboutGradient from "@/assets/landingpage/summaryabout.webp";
import SummaryAboutGradientMobile from "@/assets/landingpage/summaryaboutMobile.webp";
import Diamond from "@/assets/landingpage/intersection.svg";
import DownArrowIcon from "@/assets/summary-about/DownArrow.png";
import GlobalModal from "@/components/modal/GlobalModal";
import ResolveEmailConfirmationModal from "@/components/resolve/summary/ResolveEmailConfirmationModal";
import { useAuth } from "@/contexts/AuthContext";
import { useRole } from "@/contexts/RoleContext";
import type { Lawyer, ResolveResult} from "@/lib/types";
import { api } from "@/lib/api";
import { renderHtmlContent } from "@/utils";

interface ResolveLayoutProps {
  children: ReactNode;
  onPrevious?: () => void;
  isPreviousDisabled?: boolean;
  totalQuestions?: number;
  currentQuestionIndex?: number;
  /** Original question step number (1-based) for progress; when set, bar reflects current step. */
  currentQuestionStepNumber?: number;
  answeredQuestionsCount?: number;
  isResolveComplete?: boolean;
  showLawyerShopWindow?: boolean;
  // lawyerProfiles?: LawyerProfile[];
  resolveId?: string;
  caseId?: string | null;
  lawyerProfiles?: Lawyer[];
  storedEmail?: string | null;
  resolveResult?: ResolveResult | null;
}

const SummaryAbout = [
  {
    title: "Communication",
    description:
      "This approach involves you and your partner sitting together to discuss your situation and explore solutions. However, you are not left to manage this alone. Each of you receives help and guidance from your own specially trained advisor throughout the conversation.",
  },
  {
    title: "Understanding",
    description:
      "You and your partner are supported to ensure that each person’s thoughts and feelings are clearly heard. Everyone is given the chance to express their perspective, which helps foster a shared understanding of what matters most in your situation.",
  },
  {
    title: "Complexity",
    description:
      "When challenges arise, these discussions help you break difficult issues down into manageable parts. Step-by-step guidance is provided so that you can work out solutions, no matter how complicated things may seem at first.",
  },
  {
    title: "Trust",
    description:
      "The process encourages everyone to be open and honest in their conversations. With a respectful and supportive environment, both sides can have confidence that their interests are being taken seriously and that trust can be built.",
  },
  {
    title: "Conflict",
    description:
      "Conversations are handled with care to keep disagreements calm and respectful. Everyone is supported to share their concerns or frustrations and find ways to move forward, even if there are differences or strong opinions.",
  },
  {
    title: "Finances",
    description:
      "Financial matters are addressed with fairness and transparency for both sides. Support is given to understand the full picture and agree on practical arrangements, helping to reduce stress about money in these situations.",
  },
];

type HighlightItem = {
  id: string;
  content: ReactNode;
};

const lawyerHighlights: HighlightItem[] = [
  {
    id: "ncdr-training",
    content: (
      <>
        Our regulated family professionals are trained in{" "}
        <strong>Non-Court Dispute Resolution</strong>
      </>
    ),
  },
  {
    id: "no-pressure",
    content: (
      <>
        There’s <strong> no pressure or obligation</strong> on you to proceed
      </>
    ),
  },
  {
    id: "confidential",
    content: (
      <>
        All discussions are undertaken in <strong>complete confidence</strong>
      </>
    ),
  },
];


export function ResolveLayout({
  children,
  onPrevious,
  isPreviousDisabled,
  totalQuestions,
  currentQuestionIndex,
  currentQuestionStepNumber,
  answeredQuestionsCount,
  isResolveComplete,
  showLawyerShopWindow,
  lawyerProfiles,
  resolveId,
  caseId,
  storedEmail,
  resolveResult,
}: ResolveLayoutProps) {
  const [, setLocation] = useLocation();
  const [modalOpen, setModalOpen] = useState(false);
  const [isBookingConsultation, setIsBookingConsultation] = useState(false);
  const [isLoginLinkSent, setIsLoginLinkSent] = useState(false);
  const [showAffordability, setShowAffordability] = useState(false);
  
  // Convert recommendations object to array format, or use default SummaryAbout
  const summaryItems = useMemo(() => {
    if (resolveResult?.recommendations) {
      const recommendations = resolveResult.recommendations;
      // Define the order of items
      const order = ["Communication", "Understanding", "Complexity", "Trust", "Conflict", "Finances","Confidence"];
      return order
        .filter(key => recommendations[key as keyof typeof recommendations])
        .map(key => ({
          title: key,
          description: recommendations[key as keyof typeof recommendations] || "",
        }));
    }
    return SummaryAbout;
  }, [resolveResult]);

  const hasProgress =
    typeof totalQuestions === "number" &&
    totalQuestions > 0 &&
    (typeof currentQuestionStepNumber === "number" ||
      typeof (answeredQuestionsCount ?? totalQuestions) === "number");

  const safeTotal = typeof totalQuestions === "number" ? totalQuestions : 0;
  const safeAnswered = Math.min(
    typeof answeredQuestionsCount === "number" ? answeredQuestionsCount : 0,
    safeTotal
  );

  // Progress reflects current step (e.g. 22/22 when on last question), not just answered count
  const progressCurrent = isResolveComplete
    ? safeTotal
    : typeof currentQuestionStepNumber === "number"
      ? Math.min(Math.max(0, currentQuestionStepNumber), safeTotal)
      : safeAnswered;

  const gradientBarClass =
    "bg-gradient-to-r from-[#A644C7] via-[#DF2E88 ] to-[#FF6958]";
  // State for selected factor index
  const [selectedLegendIndex, setSelectedLegendIndex] = useState(0);
  
  // State to control lawyers section visibility
  const [showLawyersSection, setShowLawyersSection] = useState(false);
  
  // Mobile factor buttons carousel
  const [factorEmblaRef, factorEmblaApi] = useEmblaCarousel({
    dragFree: true,
    align: "center",
    containScroll: "keepSnaps",
    loop: true,
  });

  // Content carousel with smooth transitions and drag support
  const [contentEmblaRef, contentEmblaApi] = useEmblaCarousel({
    align: "center",
    containScroll: "trimSnaps",
    loop: true,
    skipSnaps: false,
    duration: 25, // Smooth transition duration
  });

  // Sync content carousel with selected index
  useEffect(() => {
    if (!contentEmblaApi) return;
    const onSelect = () => {
      setSelectedLegendIndex(contentEmblaApi.selectedScrollSnap());
      // Sync factor buttons carousel with content
      if (factorEmblaApi) factorEmblaApi.scrollTo(contentEmblaApi.selectedScrollSnap());
    };
    contentEmblaApi.on("select", onSelect);
    return () => {
      contentEmblaApi.off("select", onSelect);
    };
  }, [contentEmblaApi, factorEmblaApi]);

  // Scroll to slide when factor button is clicked
  const scrollToSlide = useCallback(
    (index: number) => {
      setSelectedLegendIndex(index);
      if (factorEmblaApi) factorEmblaApi.scrollTo(index);
      if (contentEmblaApi) contentEmblaApi.scrollTo(index);
    },
    [factorEmblaApi, contentEmblaApi]
  );

  // Navigation handlers for content
  const scrollPrev = useCallback(() => {
    if (contentEmblaApi) contentEmblaApi.scrollPrev();
  }, [contentEmblaApi]);

  const scrollNext = useCallback(() => {
    if (contentEmblaApi) contentEmblaApi.scrollNext();
  }, [contentEmblaApi]);

  // Lawyer profiles carousel
  const [lawyerEmblaRef, lawyerEmblaApi] = useEmblaCarousel({
    dragFree: true,
    align: "center",
    containScroll: "trimSnaps",
    loop: false,
  });
  const [selectedLawyerIndex, setSelectedLawyerIndex] = useState(0);

  // Sync lawyer carousel index
  useEffect(() => {
    if (!lawyerEmblaApi) return;
    const onSelect = () => {
      setSelectedLawyerIndex(lawyerEmblaApi.selectedScrollSnap());
    };
    lawyerEmblaApi.on("select", onSelect);
    onSelect();
    return () => {
      lawyerEmblaApi.off("select", onSelect);
    };
  }, [lawyerEmblaApi]);

  // Scroll to lawyer slide
  const scrollToLawyerSlide = useCallback(
    (index: number) => {
      if (lawyerEmblaApi) lawyerEmblaApi.scrollTo(index);
    },
    [lawyerEmblaApi]
  );

  // Navigation handlers for lawyer carousel
  const scrollLawyerPrev = useCallback(() => {
    if (lawyerEmblaApi) lawyerEmblaApi.scrollPrev();
  }, [lawyerEmblaApi]);

  const scrollLawyerNext = useCallback(() => {
    if (lawyerEmblaApi) lawyerEmblaApi.scrollNext();
  }, [lawyerEmblaApi]);

  const lawyerProfilesCount = lawyerProfiles?.length ?? 0;
  const hasLawyerProfiles = lawyerProfilesCount > 0;
  const getLawyerLocation = (lawyer: Lawyer) =>
    [lawyer.city, lawyer.county, lawyer.country].filter(Boolean).join(", ");
  const getExperienceLabel = (experience: Lawyer["experience"]) => {
    if (experience === undefined || experience === null) {
      return null;
    }
    const value =
      typeof experience === "string" ? parseFloat(experience) : experience;
    if (Number.isNaN(value) || !Number.isFinite(value)) {
      return experience;
    }
    const rounded = Math.max(0, Math.floor(value));
    return `${rounded}+ yrs experience`;
  };
  const getProfilePhoto = (lawyer: Lawyer) =>
    lawyer.photo_urls?.large || lawyer.photo_urls?.medium || lawyer.photo_urls?.thumbnail || NovaLogo;
  const { isAuthenticated } = useAuth();
  const { currentRole } = useRole();  

  const handleBookConsultation = async () => {
    setIsBookingConsultation(true);
    // Reset to default false when opening modal
    setIsLoginLinkSent(false);
    // If we have a stored email, call send-login-link endpoint
    if (storedEmail) {
      try {
        await api.post("/v1/auth/send-login-link", {
          user_name: storedEmail,
          resolve_id: resolveId,
        });
        setIsLoginLinkSent(true);
      } catch (error) {
        console.error("Failed to send login link:", error);
      }
    }
    setModalOpen(true);
    // Clear loading after modal has had time to open (covers open lag)
    requestAnimationFrame(() => {
      requestAnimationFrame(() => setIsBookingConsultation(false));
    });
  };

  // Scroll to section handlers
  const scrollToRecommendationSection = () => {
    const section = document.getElementById("recommendation-section");
    if (section) {
      section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  const scrollToLawyersSection = () => {
    const section = document.getElementById("lawyers-section");
    if (section) {
      section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Scroll to top when lawyers section becomes visible
  useEffect(() => {
    if (showLawyersSection) {
      window.scrollTo({ top: 80, behavior: "instant" });
    }
  }, [showLawyersSection]);

  return (
    <div className="">
      <header
        data-resolve-header
        className={`sm:h-[80px] ${showLawyerShopWindow ? 'h-[80px]' : 'h-[145px]'} bg-[#FFF5F2] bg-cover bg-center flex z-50`}
        style={{
          backgroundImage: `url(${
            window.innerWidth <= 600
              ? BackgroundgradientMobile
              : Backgroundgradient
          })`,
        }}
      >
        <div className={`max-w-[1300px] mx-auto w-full px-6 ${showLawyerShopWindow ? 'py-2' : 'py-7'} gap-4 flex flex-col sm:flex-row sm:items-center`}>
          <div className="flex items-center justify-between w-full sm:hidden">
            {!showLawyerShopWindow && onPrevious ? (
              <FormButton
                variant="outline"
                size="sm"
                onClick={onPrevious}
                disabled={isPreviousDisabled}
                className="py-1 text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white"
              >
                <i className="fas fa-arrow-left mr-2"></i>
                <span>Back</span>
              </FormButton>
            ) : !showLawyerShopWindow ? (
              <span className="inline-block w-[90px]" />
            ) : null}
            <a href="/" className="flex items-center">
              <img src={NovaLogo} alt="Nova Logo" className="w-[82px] h-[60px]" />
            </a>
            {!showLawyerShopWindow && (
              <FormButton
                type="button"
                variant="outline"
                size="sm"
                className="py-1 text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white"
                onClick={() => setLocation("/")}
              >
                Save & Exit
              </FormButton>
            )}
            {showLawyersSection && showLawyerShopWindow && (
                <FormButton
                variant="outline"
                size="sm"
                onClick={() => setShowLawyersSection(false)}
                className="py-1 px-2 text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white whitespace-nowrap"
              >
                <i className="fas fa-arrow-left mr-2"></i>
                <span>Back</span>
              </FormButton>
              )}
          </div>

          {hasProgress && !showLawyerShopWindow && (
            <div className="sm:hidden">
              <ProgressBar
                current={progressCurrent}
                total={safeTotal}
                showPercentage={false}
                showLabel={false}
                className="w-full mb-0"
                barClassName={gradientBarClass}
                height="lg"
              />
            </div>
          )}

          <div className="hidden sm:flex items-center w-full gap-6">
            <a href="/" className="flex items-center">
              <img
                  src={NovaLogo}
                  alt="Nova Logo"
                  className="w-[82px] h-[60px]"
              />
            </a>
            <div className="flex items-center gap-4 flex-1 justify-center max-w-[88%]">
              {!showLawyerShopWindow && onPrevious && (
                <FormButton
                  variant="outline"
                  size="sm"
                  onClick={onPrevious}
                  disabled={isPreviousDisabled}
                  className="py-1 text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white"
                >
                  <span>Back</span>
                </FormButton>
              )}
              {hasProgress && !showLawyerShopWindow ? (
                <div className="flex items-center max-w-[852px] w-full px-4">
                  <ProgressBar
                    current={progressCurrent}
                    total={safeTotal}
                    showPercentage={false}
                    showLabel={false}
                    className="flex-1 mb-0"
                    barClassName={gradientBarClass}
                    height="md"
                  />
                </div>
              ) : (
                <span className="flex-1" />
              )}
              {!showLawyerShopWindow && (
                <FormButton
                  type="button"
                  variant="outline"
                  size="sm"
                  className="py-1 px-4 text-novaNeutral-600 focus:ring-transparent focus:ring-offset-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white whitespace-nowrap"
                  onClick={() => setLocation("/")}
                >
                  Save and Exit
                </FormButton>
              )}
              {showLawyersSection && showLawyerShopWindow && (
                <FormButton
                variant="outline"
                size="sm"
                onClick={() => setShowLawyersSection(false)}
                className="py-1 px-4 text-novaNeutral-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white whitespace-nowrap"
              >
                <i className="fas fa-arrow-left mr-2"></i>
                <span>Back</span>
              </FormButton>
              )}
            </div>
          </div>
        </div>
      </header>
      <main  className={`${!showLawyerShopWindow ? "bg-cover bg-fixed sm:bg-center bg-right-top bg-[#e64170]" : ""}`}
        style={{ backgroundImage: !showLawyerShopWindow ? `url(${BackgroundQuestiongradient})` : "linear-gradient(to bottom, #FFF4E0 0%, #FFD9D9 100%)" }}
      >
        {!showLawyersSection && (
          <>
            {children}
          </>
        )}
      
      {showLawyerShopWindow && (
        <div className="pb-6">
          {!showLawyersSection && (
          <section id="recommendation-section" className="py-[4px] md:py-[10px] flex flex-col text-center justify-center items-center gap-2 sm:gap-4 md:gap-8 bg-cover bg-center bg-no-repeat">
            <h2
              className="text-[30px] sm:text-[40px] px-8 leading-[1.4] text-novaBlack font-nineties"
              style={{ WebkitTextStroke: "0.5px #07161E" }}
            >
              How your responses informed our recommendation 
            </h2>
            {/* Desktop: Show all factor buttons in a row */}
            <div className="hidden lg:flex justify-center gap-2 py-1">
              {summaryItems.map((item, index) => (
                <FormButton
                  key={item.title}
                  variant="custom"
                  onClick={() => scrollToSlide(index)}
                  className={`px-4 py-2 text-sm sm:text-base rounded-full border transition-colors duration-300 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 ${
                    selectedLegendIndex === index
                      ? "bg-[#1A1425] text-novaInactive border-[#1A1425] hover:bg-[#1A1425]/90"
                      : "text-[#1A1425] border-[#1A1425] hover:bg-[#1A1425] hover:text-white"
                  }`}
                >
                  {item.title}
                </FormButton>
              ))}
            </div>

            {/* Mobile/Tablet: Looping Embla carousel for factor buttons */}
            <div className="hidden sm:block lg:hidden w-full max-w-full overflow-hidden select-none px-2" ref={factorEmblaRef}>
              <div className="flex">
                {summaryItems.map((item, index) => (
                  <div
                    key={item.title}
                    className="flex-[0_0_auto] min-w-0"
                  >
                    <FormButton
                      variant="custom"
                      onClick={() => scrollToSlide(index)}
                      className={`px-4 py-2 mx-2 text-sm rounded-full border transition-colors duration-300 ease-in-out whitespace-nowrap focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 ${
                        selectedLegendIndex === index
                          ? "bg-[#1A1425] text-novaInactive border-[#1A1425] hover:bg-[#1A1425]/90"
                          : "text-[#1A1425] border-[#1A1425] hover:bg-[#1A1425] hover:text-white"
                      }`}
                    >
                      {item.title}
                    </FormButton>
                  </div>
                ))}
              </div>
            </div>

            {/* Draggable content carousel with smooth transitions */}
            <div className="w-full overflow-hidden cursor-grab active:cursor-grabbing" ref={contentEmblaRef}>
              <div className="flex">
                {summaryItems.map((item, index) => (
                  <div
                    key={item.title}
                    className="flex-[0_0_100%] min-w-0 p-6"
                  >
                    <ResolveSummaryAbout
                      title={item.title}
                      description={item.description}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="flex flex-col items-center gap-4">
              {/* Dot indicators - visible only on mobile (below sm) */}
              <div className="flex sm:hidden items-center justify-center gap-2 mb-2">
                {summaryItems.map((_, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => scrollToSlide(index)}
                    className={`w-2.5 h-2.5 rounded-full transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 ${
                      selectedLegendIndex === index
                        ? "bg-[#1A1425] scale-110"
                        : "bg-transparent border border-[#1A1425]"
                    }`}
                    aria-label={`Go to slide ${index + 1}`}
                  />
                ))}
              </div>
              <div className="flex items-center justify-center gap-4 mb-6">
                <FormButton
                  variant="tertiary"
                  size="sm"
                  onClick={scrollPrev}
                  className="py-3 px-5 !text-[18px] text-novaNeutral-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white"
                >
                  <i className="fas fa-arrow-left"></i>
                </FormButton>
                <FormButton
                  variant="tertiary"
                  size="sm"
                  onClick={scrollNext}
                  className="py-3 px-5 !text-[18px] text-novaNeutral-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 hover:bg-novaPrimary-700 hover:text-white"
                >
                  <i className="fas fa-arrow-right"></i>
                </FormButton>
              </div>
            </div>
          </section>
          )}
          
          {showLawyersSection && (
          <section
            id="lawyers-section"
            className="sm:pt-[40px] pt-[20px] px-[15px] md:px-[100px] lg:px-[120px] md:pb-[40px] items-center justify-center flex overflow-hidden"
            style={{
              background: "linear-gradient(to bottom, #FFF6E0 0%, #FFD9D9 100%)"
            }}
          >
            <div className="relative bg-transparent border-[10px] sm:border-0 rounded-[28px] sm:rounded-none" style={{ borderColor: "rgb(255 255 255 / 41%)" }}
            >
            <div className="bg-white max-w-[1200px] px-[15px] md:px-[60px] py-[60px] mx-auto rounded-[20px] items-center justify-center flex flex-col gap-8 overflow-hidden">
              <h2 className="sm:text-[32px] text-[26px] md:text-[40px] leading-[1.4] text-novaBlack font-nineties text-center " style={{ WebkitTextStroke: "0.5px #07161E" }}>
                A selection of our experts with skills matching your needs
              </h2>
              <p className="text-center sm:text-base text-sm text-novaNeutral-500 sm:max-w-[86%] max-w-full mx-auto -mt-4">
                The experts shown here are solicitors at Family Law Partners (FLP), a law firm regulated by the Solicitors Regulation Authority.<br />
                Nova and FLP share common ownership. We work closely together, but FLP remain an independent law firm responsible for all legal advice.
                You are free to instruct any solicitor you choose. If you prefer to use a different firm, you can still download your Nova Personal Recommendation and take it to them.
              </p>
              <div className="w-full overflow-hidden relative -mx-[30px] md:mx-0" ref={lawyerEmblaRef}>
                <div className="flex sm:flex-row flex-col gap-4 px-0 sm:px-4 items-stretch justify-center">
                  {lawyerProfiles?.map((lawyer, index) => (
                    <div key={index} className="flex-shrink-0 flex items-stretch">
                      <LawyerProfileDetail lawyer={lawyer} />
                    </div>
                  ))}
                </div>
              </div>
              {/* <FormButton
                  type="button"
                  variant="primary"
                  size="lg"
                  onClick={handleBookConsultation}
                  className="hover:bg-gradient-to-r hover:from-[#9A00D2] hover:to-[#F41471] my-6 md:my-0 text-[20px] md:text-[24px]"
              >
                Connect me with a lawyer
              </FormButton> */}
              <p className="text-[16px] sm:text-[20px] px-2 text-novaNeutral-600 font-neue text-left sm:max-w-[66%] w-full items-start">
                Your case will be reviewed by our Nova Navigator team – real people, with AI supporting the process behind the scenes. They will help connect you to a family professional who can guide you further.
              </p>
              <div className="relative space-y-8 border-l border-novaBlack sm:pl-8 pl-6 sm:ml-[20px] ml-[30px] pt-6 pb-6 sm:w-[64%] w-[80%]">
                {lawyerHighlights.map((item, i) => (
                  <div key={item.id}>
                    <div className="flex items-center">
                      <span
                        className="border-t border-novaBlack/10 absolute"
                        style={{
                          width: i % 2 === 0 ? 46 : 70,
                          left: i % 2 === 0 ? "-25px" : "-50px",
                        }}
                      ></span>
                      <img
                        src={Diamond}
                        alt="Diamond"
                        className="absolute left-[-15px] w-[30px] h-[30px] mt-[1px]"
                      />
                    </div>
                    <div className="relative pl-2">
                      <p className="mt-[-14px] font-roman sm:text-[20px] text-[16px]">
                        {item.content}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              </div>
              {/* {hasLawyerProfiles && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full border border-novaNeutral-200 rounded-2xl p-6">
                  {lawyerProfiles?.map((lawyer) => (
                    <div
                      key={`${lawyer.lawyer_name}-${getLawyerLocation(lawyer)}`}
                      className="flex gap-4 items-center bg-[#FFF8F3] rounded-2xl p-4"
                    >
                      <img
                        src={getProfilePhoto(lawyer)}
                        alt={lawyer.lawyer_name}
                        className="w-16 h-16 rounded-full object-cover border border-novaNeutral-200 flex-shrink-0"
                      />
                      <div className="flex flex-col">
                        <span className="font-semibold text-[18px] text-novaBlack">
                          {lawyer.lawyer_name}
                        </span>
                        {getLawyerLocation(lawyer) && (
                          <span className="text-[14px] text-novaNeutral-600">
                            {getLawyerLocation(lawyer)}
                          </span>
                        )}
                        {getExperienceLabel(lawyer.experience) && (
                          <span className="text-[14px] text-novaPrimary-600">
                            {getExperienceLabel(lawyer.experience)}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )} */}
              {/* <h2 className="text-[40px] leading-[1.4] text-novaBlack font-nineties" style={{ WebkitTextStroke: "0.5px #07161E" }}>
                Ready to book a consultation?
              </h2> */}
            </div>
          </section>
          )}
          {/* <LandingFooter /> */}
        </div>
      )}
      </main>
      
      {/* Sticky Footer */}
      {(showLawyerShopWindow || showLawyersSection) && (
        <footer className="sticky bottom-0 left-0 right-0 bg-white py-5 px-4 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] z-50">
          <div className="flex justify-center">
            <p className="text-[18px] md:text-[22px] py-2 mr-4 tracking font-semibold text-novaBlack font-nineties hidden sm:block">Your next step:</p>
            {showLawyerShopWindow && !showLawyersSection && (
              <FormButton
                type="button"
                variant="gradient"
                size="lg"
                onClick={() => setShowLawyersSection(true)}
                className="hover:bg-gradient-to-r hover:from-[#9A00D2] hover:to-[#F41471] text-[18px] md:text-[22px] px-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
              >
                View my matching experts
              </FormButton>
            )}
            {showLawyersSection && (
              <FormButton
                type="button"
                variant="gradient"
                size="lg"
                onClick={handleBookConsultation}
                loading={isBookingConsultation}
                loadingText="Opening..."
                disabled={isBookingConsultation}
                className="hover:bg-gradient-to-r hover:from-[#9A00D2] hover:to-[#F41471] text-[18px] md:text-[22px] px-8 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaPrimary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
              >
                Connect me with an expert
              </FormButton>
            )}
          </div>
        </footer>
      )}
      
      <ResolveEmailConfirmationModal
        isOpen={modalOpen}
        onClose={() => {
          setModalOpen(false);
          // Reset to default false when closing modal
          setIsLoginLinkSent(false);
        }}
        resolveId={resolveId}
        isLoginLinkSent={isLoginLinkSent}
        email={storedEmail}
      />
    </div>
  );
}