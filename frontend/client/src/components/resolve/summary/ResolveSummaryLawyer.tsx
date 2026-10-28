import NovaLogo from "@/assets/ui/NovaLogo.png";
import resolveSummaryLawyerBg from "@/assets/summary-about/resolveSummaryLawyerbg.webp";
import type { Lawyer } from "@/lib/types";

const ResolveSummaryLawyer = ({ lawyer }: { lawyer: Lawyer }) => {
  const name = `${lawyer.first_name} ${lawyer.last_name}`;
  const location = [lawyer.city, lawyer.county, lawyer.country].filter(Boolean).join(", ");
  const photo = lawyer.photo_urls?.large || lawyer.photo_urls?.medium || lawyer.photo_urls?.thumbnail || NovaLogo;
  const experience =
    lawyer.experience != null
      ? (Number.isFinite(+lawyer.experience)
          ? `${Math.max(0, Math.floor(+lawyer.experience))} years experience`
          : lawyer.experience)
      : null;

  return (
    <div
      className="relative h-[400px] rounded-[18px] overflow-hidden flex flex-col justify-end select-none w-[260px] sm:w-[280px] md:w-[300px]"
      style={{
        backgroundImage: `url(${resolveSummaryLawyerBg}), url(${photo})`,
        backgroundColor: !lawyer.photo_urls?.large ? "#515151" : undefined,

        backgroundPosition: "bottom center, center",
        backgroundRepeat: "no-repeat, no-repeat",
      }}
    >
      {/* Nova logo at top left */}
      <img
        src={NovaLogo}
        alt="Nova Logo"
        className="absolute top-4 left-4 w-12 h-12 rounded-full object-contain z-10"
      />
      {/* Card footer with text */}
      <div className="relative z-20 flex flex-col items-start p-4">
        <span className="text-white text-[24px] font-nineties ">{name}</span>
        {location && <span className="text-white text-[14px]">{location}</span>}
        {experience && <span className="text-white text-[12px] mt-2">{experience}</span>}
      </div>
    </div>
  );
};

export default ResolveSummaryLawyer;
