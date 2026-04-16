import { useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

interface PromptInputProps {
  onSubmit: (prompt: string) => void;
  disabled?: boolean;
}

const PromptInput = ({ onSubmit, disabled }: PromptInputProps) => {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = () => {
    if (prompt.trim() && !disabled) {
      onSubmit(prompt.trim());
      setPrompt("");
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="w-full max-w-2xl mx-auto"
    >
      <div className="relative rounded-2xl border border-border bg-card shadow-card transition-shadow focus-within:shadow-elevated focus-within:border-primary/40">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="Describe your social media post..."
          disabled={disabled}
          rows={3}
          className="w-full resize-none bg-transparent px-5 py-4 pr-14 text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 text-[15px] leading-relaxed"
        />
        <button
          onClick={handleSubmit}
          disabled={!prompt.trim() || disabled}
          className="absolute right-3 bottom-3 rounded-xl gradient-pink p-2.5 text-primary-foreground transition-all hover:opacity-90 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </motion.div>
  );
};

export default PromptInput;
