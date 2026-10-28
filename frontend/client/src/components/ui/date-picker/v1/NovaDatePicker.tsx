import React, { useCallback, useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  getMonth,
  getYear,
  isAfter,
  isBefore,
  isSameDay,
  isSameMonth,
  isToday,
  parseISO,
  setMonth,
  setYear,
  startOfMonth,
  startOfWeek,
} from "date-fns";
import { enGB } from "date-fns/locale";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] as const;

type PickerStep = "day" | "year" | "month";

/** Where month panel returns when pressing Back */
type MonthBackTarget = "year" | "day";

/** Approximate popover height for viewport flipping (px). */
const POPOVER_EST_HEIGHT_COMPACT = 300;
const POPOVER_EST_HEIGHT = 360;

/** Max popover width: tighter on small viewports so it feels proportional on phones. */
function getPopoverWidth(vw: number): number {
  if (vw < 640) return Math.min(288, Math.max(240, vw - 20));
  return Math.min(340, vw - 16);
}

function isMonthOutsideRange(
  year: number,
  monthIndex: number,
  minD: Date | undefined,
  maxD: Date | undefined
): boolean {
  const start = startOfMonth(new Date(year, monthIndex, 1));
  const end = endOfMonth(start);
  if (minD && isBefore(end, minD)) return true;
  if (maxD && isAfter(start, maxD)) return true;
  return false;
}

function firstSelectableMonthInYear(
  year: number,
  minD: Date | undefined,
  maxD: Date | undefined
): number {
  for (let m = 0; m < 12; m++) {
    if (!isMonthOutsideRange(year, m, minD, maxD)) return m;
  }
  return 0;
}

function parseBoundary(iso: string | undefined): Date | undefined {
  if (!iso || typeof iso !== "string" || !iso.trim()) return undefined;
  const d = parseISO(iso);
  return Number.isNaN(d.getTime()) ? undefined : d;
}

function parseValue(iso: string): Date | null {
  if (!iso || typeof iso !== "string" || !iso.trim()) return null;
  const d = parseISO(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

export interface NovaDatePickerProps {
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  disabled?: boolean;
  className?: string;
  triggerClassName?: string;
  /** ISO date `yyyy-MM-dd` */
  min?: string;
  /** ISO date `yyyy-MM-dd` */
  max?: string;
  placeholder?: string;
  id?: string;
  "aria-invalid"?: boolean | "true" | "false";
  name?: string;
}

const NovaDatePicker: React.FC<NovaDatePickerProps> = ({
  value,
  onChange,
  onBlur,
  disabled = false,
  className,
  triggerClassName,
  min,
  max,
  placeholder = "Select date",
  id: idProp,
  "aria-invalid": ariaInvalid,
  name,
}) => {
  const reactId = useId();
  const buttonId = idProp ?? `nova-date-${reactId}`;
  const listboxId = `${buttonId}-calendar`;

  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<PickerStep>("day");
  const [monthBackTarget, setMonthBackTarget] = useState<MonthBackTarget>("day");

  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const selectedYearBtnRef = useRef<HTMLButtonElement>(null);

  const [popoverPos, setPopoverPos] = useState({ top: 0, left: 0 });
  const [popoverWidth, setPopoverWidth] = useState(340);
  const minD = useMemo(() => parseBoundary(min), [min]);
  const maxD = useMemo(() => parseBoundary(max), [max]);

  const selected = useMemo(() => parseValue(value), [value]);

  const initialMonth = selected ?? new Date();
  const [visibleMonth, setVisibleMonth] = useState<Date>(initialMonth);

  useEffect(() => {
    const d = parseValue(value);
    if (d) setVisibleMonth(d);
  }, [value]);

  useEffect(() => {
    if (!open) {
      setStep("day");
      setMonthBackTarget("day");
    }
  }, [open]);

  const calendarDays = useMemo(() => {
    const start = startOfWeek(startOfMonth(visibleMonth), { weekStartsOn: 1 });
    const end = endOfWeek(endOfMonth(visibleMonth), { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  }, [visibleMonth]);

  const isDisabledDay = useCallback(
    (day: Date) => {
      if (minD && isBefore(day, minD)) return true;
      if (maxD && isAfter(day, maxD)) return true;
      return false;
    },
    [minD, maxD]
  );

  const canGoPrev = useMemo(() => {
    const prev = addMonths(visibleMonth, -1);
    const lastOfPrev = endOfMonth(prev);
    if (minD && isBefore(lastOfPrev, minD)) return false;
    return true;
  }, [visibleMonth, minD]);

  const canGoNext = useMemo(() => {
    const next = addMonths(visibleMonth, 1);
    const firstOfNext = startOfMonth(next);
    if (maxD && isAfter(firstOfNext, maxD)) return false;
    return true;
  }, [visibleMonth, maxD]);

  const yearOptions = useMemo(() => {
    const now = new Date();
    const minY = minD ? getYear(minD) : getYear(now) - 120;
    const maxY = maxD ? getYear(maxD) : getYear(now) + 10;
    const years: number[] = [];
    for (let y = minY; y <= maxY; y++) years.push(y);
    return years;
  }, [minD, maxD]);

  const visibleYear = getYear(visibleMonth);
  const visibleMonthIndex = getMonth(visibleMonth);

  const goBackFromMonth = useCallback(() => {
    if (monthBackTarget === "year") setStep("year");
    else setStep("day");
  }, [monthBackTarget]);

  const goBackFromYear = useCallback(() => {
    setStep("day");
  }, []);

  const pickYear = useCallback(
    (y: number) => {
      setVisibleMonth((prev) => {
        const fm = firstSelectableMonthInYear(y, minD, maxD);
        return setMonth(setYear(startOfMonth(prev), y), fm);
      });
      setMonthBackTarget("year");
      setStep("month");
    },
    [minD, maxD]
  );

  const pickMonth = useCallback((monthIndex: number) => {
    if (isMonthOutsideRange(visibleYear, monthIndex, minD, maxD)) return;
    setVisibleMonth((prev) => setMonth(startOfMonth(prev), monthIndex));
    setStep("day");
  }, [visibleYear, minD, maxD]);

  const openYearStep = useCallback(() => {
    setStep("year");
  }, []);

  const openMonthStepFromDay = useCallback(() => {
    setMonthBackTarget("day");
    setStep("month");
  }, []);

  useEffect(() => {
    if (step !== "year" || !open) return;
    const id = window.requestAnimationFrame(() => {
      selectedYearBtnRef.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    });
    return () => window.cancelAnimationFrame(id);
  }, [step, open, visibleYear]);

  const updatePopoverPosition = useCallback(() => {
    if (!open || !buttonRef.current) return;
    const r = buttonRef.current.getBoundingClientRect();
    const gap = 6;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const w = getPopoverWidth(vw);
    setPopoverWidth(w);
    const estH = vw < 640 ? POPOVER_EST_HEIGHT_COMPACT : POPOVER_EST_HEIGHT;
    let top = r.bottom + gap;
    if (top + estH > vh - 8 && r.top - estH - gap >= 8) {
      top = r.top - estH - gap;
    }
    // Center under trigger on narrow screens; align to trigger edge on wider
    let left =
      vw < 640
        ? r.left + (r.width - w) / 2
        : r.left;
    left = Math.min(Math.max(8, left), vw - 8 - w);
    setPopoverPos({ top, left });
  }, [open]);

  useLayoutEffect(() => {
    if (!open) return;
    updatePopoverPosition();
    const onWin = () => updatePopoverPosition();
    window.addEventListener("resize", onWin);
    window.addEventListener("scroll", onWin, true);
    return () => {
      window.removeEventListener("resize", onWin);
      window.removeEventListener("scroll", onWin, true);
    };
  }, [open, updatePopoverPosition, visibleMonth, step]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      const t = e.target as Node;
      if (rootRef.current?.contains(t) || popoverRef.current?.contains(t)) return;
      setOpen(false);
      onBlur?.();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      e.preventDefault();
      if (step === "month") {
        goBackFromMonth();
      } else if (step === "year") {
        goBackFromYear();
      } else {
        setOpen(false);
        onBlur?.();
      }
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onBlur, step, goBackFromMonth, goBackFromYear]);

  const displayLabel = selected
    ? format(selected, "d MMM yyyy", { locale: enGB })
    : placeholder;

  const handleSelect = (day: Date) => {
    if (isDisabledDay(day)) return;
    onChange(format(day, "yyyy-MM-dd"));
    setOpen(false);
    onBlur?.();
  };

  const goToday = () => {
    const t = new Date();
    if (isDisabledDay(t)) return;
    onChange(format(t, "yyyy-MM-dd"));
    setOpen(false);
    onBlur?.();
  };

  const panelTitleClass =
    "text-center font-semibold text-novaNeutral-900 tabular-nums";

  const popover = open && (
    <div
      ref={popoverRef}
      id={listboxId}
      role="dialog"
      aria-label={
        step === "day"
          ? "Choose date"
          : step === "year"
            ? "Choose year"
            : "Choose month"
      }
      style={{
        position: "fixed",
        top: popoverPos.top,
        left: popoverPos.left,
        width: popoverWidth,
        maxWidth: "calc(100vw - 1rem)",
        zIndex: 9999,
      }}
      className="box-border rounded-xl border border-novaNeutral-200 bg-white p-2 shadow-lg ring-1 ring-black/5 sm:p-3 touch-manipulation"
    >
      {step === "day" && (
        <>
          <div className="mb-2 flex items-center gap-1 sm:mb-3 sm:gap-1.5">
            <button
              type="button"
              disabled={!canGoPrev}
              onClick={() => setVisibleMonth((m) => addMonths(m, -1))}
              className={cn(
                "inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-transparent text-novaNeutral-700 transition-colors sm:h-9 sm:w-9",
                "hover:bg-novaNeutral-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40",
                !canGoPrev && "pointer-events-none opacity-30"
              )}
              aria-label="Previous month"
            >
              <ChevronLeft className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </button>
            <div className="flex min-w-0 flex-1 items-center justify-center gap-0.5 sm:gap-1">
              <button
                type="button"
                onClick={openMonthStepFromDay}
                className={cn(
                  "min-w-0 truncate rounded-md px-1.5 py-0.5 text-xs font-semibold text-novaNeutral-900 transition-colors sm:px-2 sm:py-1 sm:text-sm",
                  "hover:bg-novaNeutral-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40"
                )}
              >
                {format(visibleMonth, "MMMM", { locale: enGB })}
              </button>
              <button
                type="button"
                onClick={openYearStep}
                className={cn(
                  "shrink-0 rounded-md px-1.5 py-0.5 text-xs font-semibold tabular-nums text-novaNeutral-900 transition-colors sm:px-2 sm:py-1 sm:text-sm",
                  "hover:bg-novaNeutral-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40"
                )}
              >
                {visibleYear}
              </button>
            </div>
            <button
              type="button"
              disabled={!canGoNext}
              onClick={() => setVisibleMonth((m) => addMonths(m, 1))}
              className={cn(
                "inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-transparent text-novaNeutral-700 transition-colors sm:h-9 sm:w-9",
                "hover:bg-novaNeutral-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40",
                !canGoNext && "pointer-events-none opacity-30"
              )}
              aria-label="Next month"
            >
              <ChevronRight className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </button>
          </div>

          <div className="mb-0.5 grid grid-cols-7 gap-px text-center text-[9px] font-medium uppercase tracking-wide text-novaNeutral-500 sm:mb-1 sm:gap-0.5 sm:text-[11px]">
            {WEEKDAYS.map((d) => (
              <div key={d} className="py-0.5 sm:py-1">
                {d}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-px sm:gap-0.5">
            {calendarDays.map((day) => {
              const outside = !isSameMonth(day, visibleMonth);
              const sel = selected && isSameDay(day, selected);
              const today = isToday(day);
              const dis = isDisabledDay(day);

              return (
                <button
                  key={day.toISOString()}
                  type="button"
                  disabled={dis}
                  onClick={() => handleSelect(day)}
                  className={cn(
                    "relative flex min-h-8 w-full items-center justify-center rounded-md text-xs transition-colors sm:min-h-9 sm:rounded-lg sm:text-sm",
                    outside && !dis && "text-novaNeutral-400",
                    !outside && !dis && "text-novaNeutral-900",
                    dis && "cursor-not-allowed text-novaNeutral-300",
                    !dis && !sel && "hover:bg-novaNeutral-100",
                    sel &&
                      "bg-novaDarkOrange font-semibold text-white shadow-sm hover:brightness-95",
                    today &&
                      !sel &&
                      !dis &&
                      "ring-1 ring-novaDarkOrange ring-offset-1"
                  )}
                >
                  {format(day, "d")}
                </button>
              );
            })}
          </div>

          <div className="mt-2 flex justify-center border-t border-novaNeutral-100 pt-2 sm:mt-3 sm:pt-3">
            <button
              type="button"
              onClick={goToday}
              disabled={isDisabledDay(new Date())}
              className={cn(
                "text-[11px] font-medium text-novaDarkOrange underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40 rounded px-2 py-1 sm:text-xs",
                isDisabledDay(new Date()) && "pointer-events-none opacity-40"
              )}
            >
              Today
            </button>
          </div>
        </>
      )}

      {step === "year" && (
        <>
          <div className="mb-1.5 flex items-center gap-1.5 sm:mb-2 sm:gap-2">
            <button
              type="button"
              onClick={goBackFromYear}
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-transparent text-novaNeutral-700 transition-colors hover:bg-novaNeutral-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40 sm:h-9 sm:w-9"
              aria-label="Back to calendar"
            >
              <ChevronLeft className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </button>
            <p className={cn("flex-1 text-xs sm:text-sm", panelTitleClass)}>Select year</p>
            <div className="w-8 shrink-0 sm:w-9" aria-hidden />
          </div>
          <div className="max-h-[min(40vh,200px)] overflow-y-auto overscroll-contain rounded-lg border border-novaNeutral-100 bg-novaNeutral-50/50 p-1 sm:max-h-[220px] sm:p-1.5">
            <div className="grid grid-cols-4 gap-0.5 sm:gap-1">
              {yearOptions.map((y) => {
                const isSel = y === visibleYear;
                return (
                  <button
                    key={y}
                    ref={isSel ? selectedYearBtnRef : undefined}
                    type="button"
                    onClick={() => pickYear(y)}
                    className={cn(
                      "rounded-md py-1.5 text-center text-xs tabular-nums transition-colors sm:rounded-lg sm:py-2 sm:text-sm",
                      "focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40",
                      isSel
                        ? "bg-novaDarkOrange font-semibold text-white shadow-sm"
                        : "bg-white text-novaNeutral-900 hover:bg-novaNeutral-100"
                    )}
                  >
                    {y}
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}

      {step === "month" && (
        <>
          <div className="mb-1.5 flex items-center gap-1.5 sm:mb-2 sm:gap-2">
            <button
              type="button"
              onClick={goBackFromMonth}
              className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-transparent text-novaNeutral-700 transition-colors hover:bg-novaNeutral-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40 sm:h-9 sm:w-9"
              aria-label={monthBackTarget === "year" ? "Back to years" : "Back to calendar"}
            >
              <ChevronLeft className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </button>
            <p className={cn("flex-1 text-xs sm:text-sm", panelTitleClass)}>{visibleYear}</p>
            <div className="w-8 shrink-0 sm:w-9" aria-hidden />
          </div>
          <div className="grid grid-cols-3 gap-1 sm:gap-1.5">
            {Array.from({ length: 12 }, (_, m) => {
              const disabled = isMonthOutsideRange(visibleYear, m, minD, maxD);
              const isSel = m === visibleMonthIndex;
              return (
                <button
                  key={m}
                  type="button"
                  disabled={disabled}
                  onClick={() => pickMonth(m)}
                  className={cn(
                    "rounded-md px-0.5 py-2 text-center text-xs font-medium transition-colors sm:rounded-lg sm:px-1 sm:py-2.5 sm:text-sm",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-novaDarkOrange/40",
                    disabled && "cursor-not-allowed text-novaNeutral-300",
                    !disabled && !isSel && "bg-novaNeutral-50 text-novaNeutral-900 hover:bg-novaNeutral-100",
                    isSel &&
                      !disabled &&
                      "bg-novaDarkOrange text-white shadow-sm hover:brightness-95"
                  )}
                >
                  {format(new Date(2000, m, 1), "MMM", { locale: enGB })}
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );

  return (
    <div ref={rootRef} className={cn("relative w-full max-w-full sm:max-w-xs", className)}>
      <input type="hidden" name={name} value={value} readOnly />
      <button
        ref={buttonRef}
        type="button"
        id={buttonId}
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-controls={listboxId}
        aria-invalid={ariaInvalid}
        onClick={() => !disabled && setOpen((o) => !o)}
        className={cn(
          "flex w-full items-center justify-between gap-2 rounded-lg border border-novaNeutral-300 bg-white px-2.5 py-1.5 text-left text-sm text-novaNeutral-900 shadow-sm transition-[border-color,box-shadow]",
          "hover:border-novaNeutral-400 focus:outline-none focus-visible:border-novaDarkOrange focus-visible:ring-2 focus-visible:ring-novaDarkOrange/25",
          disabled && "cursor-not-allowed opacity-50",
          !selected && "text-novaNeutral-500",
          triggerClassName
        )}
      >
        <span className="min-w-0 truncate">{displayLabel}</span>
        <CalendarIcon
          className="h-4 w-4 shrink-0 text-novaDarkOrange"
          aria-hidden
        />
      </button>
      {typeof document !== "undefined" && open
        ? createPortal(popover, document.body)
        : null}
    </div>
  );
};

export default NovaDatePicker;
