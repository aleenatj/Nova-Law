import React from "react";
import { cn } from "../../../../lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  size?: "default" | "sm" | "lg" | "icon";
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  className,
  variant = "default",
  size = "default",
  children,
  ...props
}) => {
  const baseClasses =
    "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";

  const variantClasses = {
    default: "bg-novaPrimary-500 text-white hover:bg-novaPrimary-600",
    destructive: "bg-novaCaution text-white hover:bg-novaCaution/90",
    outline:
      "border border-novaNeutral-300 bg-white hover:bg-novaNeutral-50 hover:text-novaNeutral-900",
    secondary: "bg-novaNeutral text-white hover:bg-novaNeutral/80",
    ghost: "hover:bg-novaNeutral-50 hover:text-novaNeutral-900",
    link: "text-novaPrimary underline-offset-4 hover:underline",
  };

  const sizeClasses = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-11 rounded-md px-8",
    icon: "h-10 w-10",
  };

  return (
    <button
      className={cn(
        baseClasses,
        variantClasses[variant],
        sizeClasses[size],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
