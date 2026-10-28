import communication from "@/assets/summary-about/communication.svg";
import complexity from "@/assets/summary-about/complexity.svg";
import trust from "@/assets/summary-about/trust.svg";
import conflict from "@/assets/summary-about/conflict.svg";
import finances from "@/assets/summary-about/finances.svg";
import understand from "@/assets/summary-about/understand.svg";
import confidence from "@/assets/summary-about/confidence.svg";

const imageMap: Record<string, string> = {
  Communication: communication,
  Understanding: understand,
  Complexity: complexity,
  Trust: trust,
  Conflict: conflict,
  Finances: finances,
  Confidence: confidence,
};

const ResolveSummaryAbout = ({
  title,
  description,
}: {
  title: string;
  description: string;
}) => {
  const imageSrc = imageMap[title] || "";

  return (
    <div
      className="md:max-w-[90%] lg:w-[70%] xl:w-[58%] 3xl:w-[46%] md:min-h-[420px] sm:min-h-[400px] h-full w-full bg-[#ffffff] p-5 md:p-10 sm:text-center text-left justify-center items-center mx-auto rounded-2xl flex flex-col gap-4"
      // style={{
      //   userSelect: "none",
      //   boxShadow: "8px 8px 0 0 #EDE0FF",
      //   justifyContent: "flex-start",
      // }}
    >
      {imageSrc && <img src={imageSrc} alt={title} className="sm:w-[90px] sm:h-[90px] w-[80px] h-[80px]" />}
      <h3 className="sm:text-[32px] text-[28px] text-novaBlack font-nineties" style={{WebkitTextStroke: "0.3px #07161E"}}>{title}</h3>
      <p className="text-novaBlack sm:text-[18px] text-[16px] font-roman leading-[1.4] w-[90%] mt-2 max-h-[300px] lg:max-h-none overflow-y-auto sm:p-0 px-2">
        {description}
      </p>
    </div>
  );
};

export default ResolveSummaryAbout;