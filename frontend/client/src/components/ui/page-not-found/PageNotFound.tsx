import React, { useEffect, useState } from "react";
import { Button } from "../button";
import { useLocation } from "wouter";

interface PageNotFoundProps {
  buttonText?: string;
  onButtonClick?: () => void;
  className?: string;
}

const PageNotFound: React.FC<PageNotFoundProps> = ({
  buttonText,
  onButtonClick,
  className,
}) => {
  const [, setLocation] = useLocation();
  const [secondsLeft, setSecondsLeft] = useState(3);

  useEffect(() => {
    if (secondsLeft <= 0) {
      setLocation("/");
      return;
    }
    const timer = setTimeout(() => {
      setSecondsLeft((sec) => sec - 1);
    }, 1000);
    return () => clearTimeout(timer);
  }, [secondsLeft, setLocation]);

  return (
    <div
      className={`flex flex-col items-center justify-center text-center w-full bg-novaNeutral-50 px-6 py-12 ${className}`}
    >
      <div className="">
        <h1
          id="notfound-title"
          className="text-5xl md:text-4xl font-extrabold text-novaNeutral-800"
        >
          Page not found.
        </h1>
        {/* Timer */}
        <div className="text-novaNeutral-600 mt-2 mb-2 text-sm">
          Redirecting to the home page in{" "}
          <span className="font-mono font-semibold text-novaPrimary-700">{secondsLeft}</span>
          s...
        </div>
        <div className="mx-auto my-4 w-40 border-t border-dotted border-novaNeutral-400" />
      </div>

      {/* Optional Button */}
      {buttonText && onButtonClick && (
        <span>
          Please{"  "}
          <Button
            variant="ghost"
            className="inline hover:text-novaPrimary-700 p-0 align-baseline text-novaPrimary-500"
            onClick={onButtonClick}
            style={{ display: "inline", background: "none", boxShadow: "none" }}
          >
            {buttonText}
          </Button>
        </span>
      )}
    </div>
  );
};

export default PageNotFound;
