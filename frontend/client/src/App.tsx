import { lazy, Suspense, useEffect } from "react";
import { Switch, Route, useLocation } from "wouter";
import { useAuth } from "@/contexts/AuthContext";
import LoadingFallback from "@/components/LoadingFallback";
import { clearRedirectIfOnTargetPage } from "@/utils/redirectAfterLogin";
import { getTitleForPath } from "@/utils/pageTitle";

// Utility function to retry dynamic imports with exponential backoff
function lazyWithRetry(componentImport: () => Promise<any>) {
  return lazy(() => {
    return new Promise((resolve, reject) => {
      // Maximum number of retry attempts
      const maxRetries = 3;
      let retries = 0;

      const attemptImport = () => {
        componentImport()
          .then(resolve)
          .catch((error) => {
            // Check if it's a chunk load error
            const isChunkError = 
              error?.message?.includes('Failed to fetch dynamically imported module') ||
              error?.message?.includes('Failed to fetch') ||
              error?.name === 'TypeError';

            if (isChunkError && retries < maxRetries) {
              retries++;
              console.log(`Chunk load failed. Retrying... (${retries}/${maxRetries})`);
              
              // Exponential backoff: wait before retrying
              setTimeout(() => {
                attemptImport();
              }, 1000 * retries);
            } else if (isChunkError && retries >= maxRetries) {
              // After max retries, reload the page to get fresh chunks
              console.log('Max retries reached. Reloading page...');
              window.location.reload();
              reject(error);
            } else {
              // Not a chunk error, reject immediately
              reject(error);
            }
          });
      };

      attemptImport();
    });
  });
}

// Lazy load all page components for code-splitting with retry logic
const CaseDashboard = lazyWithRetry(() => import("@/pages/case-dashboard"));
const ResolveDashboard = lazyWithRetry(() => import("@/pages/resolve-dashboard"));
// const Home = lazyWithRetry(() => import("@/pages/home"));
const LandingPage = lazyWithRetry(() => import("@/pages/landing-page"));
const ConversionLandingPage = lazyWithRetry(() => import("@/pages/conversion-landing-page"));
const LandingPage2 = lazyWithRetry(() => import("@/pages/landing-page2"));
const CaseDetail = lazyWithRetry(() => import("@/pages/case/[:id]"));
const ResolveDetail = lazyWithRetry(() => import("@/pages/resolve/[:id]"));
const ResetPasswordPage = lazyWithRetry(() => import("@/pages/reset-password"));
const LawFirmsPage = lazyWithRetry(() => import("@/pages/lawfirms"));
const LawyersPage = lazyWithRetry(() => import("@/pages/lawyers"));
const NavigatorsPage = lazyWithRetry(() => import("@/pages/navigators"));
const ProfilePage = lazyWithRetry(() => import("@/pages/profile"));
const PageNotFound = lazyWithRetry(() => import("@/components/ui/page-not-found/PageNotFound"));
const SetInitialPasswordPage = lazyWithRetry(() => import("@/pages/set-intial-password"));
const TermsAndConditions = lazyWithRetry(() => import("@/pages/terms-and-conditions"));
const PrivacyPolicy = lazyWithRetry(() => import("@/pages/privacy-policy"));
const ContactUsPage = lazyWithRetry(() => import("@/pages/contact-us"));
const CookiePolicy = lazyWithRetry(() => import("@/pages/cookie-policy"));
const MissedCases = lazyWithRetry(() => import("@/pages/missed-cases"));
const MyMatches = lazyWithRetry(() => import("@/pages/my-matches"));
const DirectLoginPage = lazyWithRetry(() => import("@/pages/direct-login"));
const DirectEngageLoginPage = lazyWithRetry(() => import("@/pages/direct-engage-login"));
const NovaEngagePage = lazyWithRetry(() => import("@/pages/nova-engage"));
const BecomeNovaLawyerPage = lazyWithRetry(() => import("@/pages/become-a-nova-lawyer"));
const LegalExpertsPage = lazyWithRetry(() => import("@/pages/legal-experts"));
const SupportAndGuidancePage = lazyWithRetry(() => import("@/pages/support-and-guidance"));
const PaymentAndSecurityPage = lazyWithRetry(() => import("@/pages/payment-and-security"));
const LawyerMatchingPage = lazyWithRetry(() => import("@/pages/lawyer-matching"));
const SixtySecFeedbackPage = lazyWithRetry(() => import("@/pages/60-sec-feedback"));
const EngageFeedbackListPage = lazyWithRetry(() => import("@/pages/engage-feedback-list"));
const EngageFormPage = lazyWithRetry(() => import("@/pages/engage-form"));
const EngageFormPage2 = lazyWithRetry(() => import("@/pages/engage/[:id]"));
// Component to handle redirect cleanup globally for all routes
function RedirectCleanup() {
  const [location] = useLocation();
  const { isAuthenticated } = useAuth();

  // Clear redirect URL when user successfully lands on target page after login
  useEffect(() => {
    if (isAuthenticated) {
      clearRedirectIfOnTargetPage(location);
    }
  }, [location, isAuthenticated]);

  return null;
}

// Set document title based on current route (client-side navigation and first paint)
function DocumentTitle() {
  const [location] = useLocation();

  useEffect(() => {
    // Use router location when available; fallback to window.location for first paint (e.g. SPA shell on staging/live)
    const pathname = location || window.location.pathname;
    document.title = getTitleForPath(pathname);
  }, [location]);

  return null;
}

function Router() {
  const [, setLocation] = useLocation();

  return (
    <>
      <RedirectCleanup />
      <DocumentTitle />
      <Suspense fallback={<LoadingFallback />}>
        <Switch>
        <Route path="/" component={LandingPage} />
        <Route path="/login" component={LandingPage} />
        {/* <Route path="/landing-page" component={Home} /> */}
        <Route path="/divorce-options" component={ConversionLandingPage} />
        <Route path="/separation-divorce-next-steps" component={LandingPage2} />
        <Route path="/reset-password" component={ResetPasswordPage} />
        <Route path="/resolve" component={ResolveDetail} />
        <Route path="/resolve/:id" component={ResolveDetail} />
        <Route path="/resolve-new" component={ResolveDetail} />
        <Route path="/resolve-dashboard" component={ResolveDashboard} />
        <Route path="/case-dashboard" component={CaseDashboard} />
        <Route path="/case/:id" component={CaseDetail} />
        <Route path="/organisations" component={LawFirmsPage} />
        <Route path="/experts" component={LawyersPage} />
        <Route path="/navigators" component={NavigatorsPage} />
        <Route path="/nova-experts" component={LegalExpertsPage} />
        <Route path="/profile" component={ProfilePage} />
        <Route path="/set-initial-password" component={SetInitialPasswordPage} />
        <Route path="/user-agreement" component={TermsAndConditions} />
        <Route path="/missed-cases" component={MissedCases} />
        <Route path="/my-matches" component={MyMatches} />
        <Route path="/privacy-policy" component={PrivacyPolicy} />
        <Route path="/contact-us" component={ContactUsPage} />
        <Route path="/cookie-policy" component={CookiePolicy} />
        <Route path="/directlogin" component={DirectLoginPage} />
        <Route path="/directengagelogin/:token" component={DirectEngageLoginPage} />
        <Route path="/directengagelogin" component={DirectEngageLoginPage} />
        <Route path="/nova-engage" component={NovaEngagePage} />
        <Route path="/become-a-nova-professional" component={BecomeNovaLawyerPage} />
        <Route path="/support-and-guidance" component={SupportAndGuidancePage} />
        <Route path="/payment-and-security" component={PaymentAndSecurityPage} />
        <Route path="/lawyer-matching" component={LawyerMatchingPage} />
        <Route path="/60-sec-feedback" component={SixtySecFeedbackPage} />
        <Route path="/feedback" component={EngageFeedbackListPage} />
        <Route path="/engage-form" component={EngageFormPage} />
        <Route path="/engage/:id" component={EngageFormPage2} />
        <Route>
          <PageNotFound
            className="h-screen"
            buttonText="Go Back to The Home Page"
            onButtonClick={() => setLocation("/")}
          />
        </Route>
      </Switch>
    </Suspense>
    </>
  );
}

function App() {
  return <Router />;
}

export default App;
