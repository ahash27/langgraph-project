import { useState, useEffect } from "react";
import { Calendar, Clock } from "lucide-react";
import { motion } from "framer-motion";

interface DateTimePickerProps {
  value: string;
  onChange: (value: string) => void;
  minDate?: Date;
}

const DateTimePicker = ({ value, onChange, minDate }: DateTimePickerProps) => {
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");

  useEffect(() => {
    if (value) {
      const dt = new Date(value);
      setDate(dt.toISOString().split("T")[0]);
      setTime(dt.toTimeString().slice(0, 5));
    } else {
      // Default to next optimal slot (next weekday 9am)
      const next = getNextOptimalSlot();
      setDate(next.toISOString().split("T")[0]);
      setTime("09:00");
      onChange(next.toISOString());
    }
  }, []);

  const getNextOptimalSlot = () => {
    const now = new Date();
    let next = new Date(now);
    next.setHours(9, 0, 0, 0);

    // If past 9am, move to tomorrow
    if (now.getHours() >= 9) {
      next.setDate(next.getDate() + 1);
    }

    // Skip weekends
    while (next.getDay() === 0 || next.getDay() === 6) {
      next.setDate(next.getDate() + 1);
    }

    return next;
  };

  const handleDateChange = (newDate: string) => {
    setDate(newDate);
    if (newDate && time) {
      const dt = new Date(`${newDate}T${time}`);
      onChange(dt.toISOString());
    }
  };

  const handleTimeChange = (newTime: string) => {
    setTime(newTime);
    if (date && newTime) {
      const dt = new Date(`${date}T${newTime}`);
      onChange(dt.toISOString());
    }
  };

  const minDateStr = minDate
    ? minDate.toISOString().split("T")[0]
    : new Date().toISOString().split("T")[0];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      <div className="flex-1 relative">
        <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <input
          type="date"
          value={date}
          onChange={(e) => handleDateChange(e.target.value)}
          min={minDateStr}
          className="w-full pl-10 pr-3 py-2 rounded-xl border border-border bg-card text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
        />
      </div>
      <div className="flex-1 relative">
        <Clock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        <input
          type="time"
          value={time}
          onChange={(e) => handleTimeChange(e.target.value)}
          className="w-full pl-10 pr-3 py-2 rounded-xl border border-border bg-card text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
        />
      </div>
    </motion.div>
  );
};

export default DateTimePicker;
