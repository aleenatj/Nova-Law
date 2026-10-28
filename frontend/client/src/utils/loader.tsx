import React from "react";

export interface LoaderProps {
  message?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Loader({
  message = "Loading...",
  size = "md",
  className = "",
}: LoaderProps) {
  const sizeClasses = {
    sm: "h-6 w-6",
    md: "h-12 w-12",
    lg: "h-16 w-16",
  };

  const textSizeClasses = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg",
  };

  return (
    <div className={`text-center py-8 ${className}`}>
      <div
        className={`animate-spin rounded-full border-b-2 border-novaPrimary-500 mx-auto ${sizeClasses[size]}`}
      ></div>
      <p className={`mt-4 text-novaNeutral-600 ${textSizeClasses[size]}`}>
        {message}
      </p>
    </div>
  );
}

// Pre-configured loaders for common use cases
export function PageLoader({ message = "Loading..." }: { message?: string }) {
  return <Loader message={message} size="md" />;
}

export function CardLoader({ message = "Loading..." }: { message?: string }) {
  return <Loader message={message} size="sm" />;
}

export function FullPageLoader({
  message = "Loading...",
}: {
  message?: string;
}) {
  return (
    <Loader
      message={message}
      size="lg"
      className="min-h-screen flex items-center justify-center"
    />
  );
}
