import { Check, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export interface Step {
  id: number;
  label: string;
  status: "pending" | "active" | "completed";
}

interface ProcessStepperProps {
  steps: Step[];
}

const ProcessStepper = ({ steps }: ProcessStepperProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-md mx-auto py-6"
    >
      <div className="flex flex-col">
        {steps.map((step, index) => {
          const isLast = index === steps.length - 1;
          const segDone = step.status === "completed";

          return (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex gap-3 items-start"
            >
              <div className="flex w-7 shrink-0 flex-col items-center">
                <div
                  className={cn(
                    "relative z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-all duration-300",
                    step.status === "completed" &&
                      "border-success bg-success",
                    step.status === "active" &&
                      "border-primary bg-primary/10",
                    step.status === "pending" && "border-border bg-muted"
                  )}
                >
                  <AnimatePresence mode="wait">
                    {step.status === "completed" && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                        transition={{ type: "spring", stiffness: 400, damping: 15 }}
                      >
                        <Check className="h-3.5 w-3.5 text-success-foreground" />
                      </motion.div>
                    )}
                    {step.status === "active" && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        exit={{ scale: 0 }}
                      >
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
                {!isLast && (
                  <div
                    className={cn(
                      "mt-0.5 w-0.5 min-h-10 shrink-0 rounded-full transition-colors duration-300",
                      segDone ? "bg-success" : "bg-border"
                    )}
                    aria-hidden
                  />
                )}
              </div>

              <span
                className={cn(
                  "min-h-7 pt-1.5 text-sm font-medium transition-colors",
                  step.status === "completed" && "text-success",
                  step.status === "active" && "text-foreground",
                  step.status === "pending" && "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
};

export default ProcessStepper;
