import { useState } from "react";
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameMonth,
  isSameDay,
  isToday,
} from "date-fns";

interface CalendarEvent {
  id: string;
  date: Date;
  title: string;
  type: "case" | "consultation" | "deadline" | "meeting";
  time?: string;
}

// Mock user events - in real app this would come from API
const userEvents: CalendarEvent[] = [
  {
    id: "1",
    date: new Date(2025, 0, 10), // January 10, 2025
    title: "Case Review Meeting",
    type: "meeting",
    time: "2:00 PM",
  },
  {
    id: "2",
    date: new Date(2025, 0, 15), // January 15, 2025
    title: "Document Submission",
    type: "deadline",
    time: "5:00 PM",
  },
  {
    id: "3",
    date: new Date(2025, 0, 18), // January 18, 2025
    title: "Client Consultation",
    type: "consultation",
    time: "10:00 AM",
  },
  {
    id: "4",
    date: new Date(2025, 0, 22), // January 22, 2025
    title: "Case Status Update",
    type: "case",
    time: "3:30 PM",
  },
  {
    id: "5",
    date: new Date(2025, 0, 28), // January 28, 2025
    title: "Final Review",
    type: "meeting",
    time: "1:00 PM",
  },
];

const getEventTypeColor = (type: CalendarEvent["type"]) => {
  switch (type) {
    case "case":
      return "bg-novaPrimary-500";
    case "consultation":
      return "bg-novaSuccess-500";
    case "deadline":
      return "bg-novaCaution-500";
    case "meeting":
      return "bg-novaAccent-500";
    default:
      return "bg-novaNeutral-500";
  }
};

const getEventTypeIcon = (type: CalendarEvent["type"]) => {
  switch (type) {
    case "case":
      return "fas fa-folder";
    case "consultation":
      return "fas fa-user-md";
    case "deadline":
      return "fas fa-clock";
    case "meeting":
      return "fas fa-calendar";
    default:
      return "fas fa-circle";
  }
};

export function CalendarWidget() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const monthStart = startOfMonth(currentDate);
  const monthEnd = endOfMonth(currentDate);
  const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const getEventsForDate = (date: Date) => {
    return userEvents.filter((event) => isSameDay(event.date, date));
  };

  const hasEventsOnDate = (date: Date) => {
    return getEventsForDate(date).length > 0;
  };

  const selectedDateEvents = selectedDate ? getEventsForDate(selectedDate) : [];

  const previousMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() - 1)
    );
    setSelectedDate(null);
  };

  const nextMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() + 1)
    );
    setSelectedDate(null);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="space-y-4">
        {/* Calendar Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-novaNeutral-900">
            My Calendar
          </h3>
          <div className="flex items-center gap-1">
            <button
              onClick={previousMonth}
              className="p-1 hover:bg-novaNeutral-100 rounded text-novaNeutral-600"
            >
              <i className="fas fa-chevron-left text-xs"></i>
            </button>
            <button
              onClick={nextMonth}
              className="p-1 hover:bg-novaNeutral-100 rounded text-novaNeutral-600"
            >
              <i className="fas fa-chevron-right text-xs"></i>
            </button>
          </div>
        </div>

        {/* Month/Year Display */}
        <div className="text-center">
          <h4 className="text-lg font-semibold text-novaNeutral-900">
            {format(currentDate, "MMMM yyyy")}
          </h4>
        </div>

        {/* Calendar Grid */}
        <div className="grid grid-cols-7 gap-1 text-xs">
          {/* Day headers */}
          {["S", "M", "T", "W", "T", "F", "S"].map((day, index) => (
            <div
              key={index}
              className="text-center text-novaNeutral-500 font-medium py-2"
            >
              {day}
            </div>
          ))}

          {/* Calendar days */}
          {daysInMonth.map((day) => {
            const dayEvents = getEventsForDate(day);
            const hasEvents = dayEvents.length > 0;
            const isSelected = selectedDate && isSameDay(day, selectedDate);
            const isDayToday = isToday(day);

            return (
              <button
                key={day.toString()}
                onClick={() => setSelectedDate(isSelected ? null : day)}
                className={`
                  relative aspect-square p-1 text-xs rounded transition-colors
                  ${
                    isSameMonth(day, currentDate)
                      ? "text-novaNeutral-900"
                      : "text-novaNeutral-400"
                  }
                  ${isDayToday ? "bg-legal-blue text-white font-semibold" : ""}
                  ${
                    isSelected && !isDayToday
                      ? "bg-novaPrimary-100 border border-legal-blue"
                      : ""
                  }
                  ${
                    !isSelected && !isDayToday ? "hover:bg-novaNeutral-100" : ""
                  }
                `}
              >
                <span className="block">{format(day, "d")}</span>
                {hasEvents && (
                  <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 flex gap-px">
                    {dayEvents.slice(0, 3).map((event, index) => (
                      <div
                        key={event.id}
                        className={`w-1 h-1 rounded-full ${getEventTypeColor(
                          event.type
                        )}`}
                      />
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="w-1 h-1 rounded-full bg-novaNeutral-400" />
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Selected Date Events */}
        {selectedDate && selectedDateEvents.length > 0 && (
          <div className="mt-4 p-3 bg-novaNeutral-50 rounded-lg">
            <h5 className="text-sm font-medium text-novaNeutral-900 mb-2">
              {format(selectedDate, "MMMM d, yyyy")}
            </h5>
            <div className="space-y-2">
              {selectedDateEvents.map((event) => (
                <div key={event.id} className="flex items-center gap-2 text-xs">
                  <div
                    className={`w-2 h-2 rounded-full ${getEventTypeColor(
                      event.type
                    )}`}
                  />
                  <div className="flex-1">
                    <div className="font-medium text-novaNeutral-900">
                      {event.title}
                    </div>
                    {event.time && (
                      <div className="text-novaNeutral-500">{event.time}</div>
                    )}
                  </div>
                  <i
                    className={`${getEventTypeIcon(
                      event.type
                    )} text-novaNeutral-400`}
                  ></i>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="mt-6 p-3 bg-novaNeutral-50 rounded-lg">
          <h5 className="text-xs font-medium text-novaNeutral-900 mb-2">
            Event Types
          </h5>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-novaPrimary-500" />
              <span className="text-novaNeutral-600">Cases</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-novaSuccess-500" />
              <span className="text-novaNeutral-600">Consultations</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-novaCaution-500" />
              <span className="text-novaNeutral-600">Deadlines</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-novaAccent-500" />
              <span className="text-novaNeutral-600">Meetings</span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-4 space-y-2">
          <h5 className="text-xs font-medium text-novaNeutral-900">
            Quick Actions
          </h5>
          <button className="w-full text-left p-2 rounded-lg border border-novaNeutral-200 hover:border-legal-blue hover:bg-novaPrimary-50 transition-colors text-xs">
            <div className="flex items-center gap-2">
              <i className="fas fa-plus text-legal-blue"></i>
              <span className="text-novaNeutral-900">
                Schedule Consultation
              </span>
            </div>
          </button>
          <button className="w-full text-left p-2 rounded-lg border border-novaNeutral-200 hover:border-legal-blue hover:bg-novaPrimary-50 transition-colors text-xs">
            <div className="flex items-center gap-2">
              <i className="fas fa-calendar-check text-legal-blue"></i>
              <span className="text-novaNeutral-900">View All Events</span>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}
