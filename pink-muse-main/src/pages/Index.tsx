import { useState } from "react";
import { Sparkles, Calendar } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import PromptInput from "@/components/PromptInput";
import ProcessStepper, { Step } from "@/components/ProcessStepper";
import ResultCard from "@/components/ResultCard";
import DateTimePicker from "@/components/DateTimePicker";
import { toast } from "sonner";

type AppPhase = "idle" | "processing" | "results";
type VariantName = "thought_leadership" | "question_hook" | "data_insight";

interface PostResult {
  platform: string;
  content: string;
  hashtags: string[];
  status: "approved" | "rejected" | null;
  variant: VariantName;
}

type GeneratedPosts = Record<
  VariantName,
  {
    body: string;
    hashtags: string[];
  }
>;

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://localhost:8000";

const VARIANT_LABELS: Record<VariantName, string> = {
  thought_leadership: "Thought Leadership",
  question_hook: "Question Hook",
  data_insight: "Data Insight",
};

function stepsFromBackend(steps?: Record<string, string>): Step[] {
  const order = ["trends", "generation", "approval", "publish"] as const;
  return order.map((k, idx) => {
    const v = steps?.[k] || "pending";
    const done = v === "completed" || v === "success" || v === "partial_success";
    const status: Step["status"] = done
      ? "completed"
      : v === "pending"
        ? "pending"
        : v === "failed"
          ? "pending"
          : "active";
    return { id: idx + 1, label: `${k}: ${v}`, status };
  });
}

function mapResults(posts: GeneratedPosts): PostResult[] {
  const keys: VariantName[] = ["thought_leadership", "question_hook", "data_insight"];
  return keys.map((k) => ({
    platform: VARIANT_LABELS[k],
    variant: k,
    content: posts[k]?.body || "",
    hashtags: posts[k]?.hashtags || [],
    status: null,
  }));
}

const Index = () => {
  const [phase, setPhase] = useState<AppPhase>("idle");
  const [prompt, setPrompt] = useState("");
  const [steps, setSteps] = useState<Step[]>([]);
  const [results, setResults] = useState<PostResult[]>([]);
  const [generatedPosts, setGeneratedPosts] = useState<GeneratedPosts | null>(null);
  const [publishingIndex, setPublishingIndex] = useState<number | null>(null);
  const [showScheduler, setShowScheduler] = useState(false);
  const [scheduledTime, setScheduledTime] = useState("");

  const handleSubmit = async (text: string) => {
    setPrompt(text);
    setPhase("processing");
    setSteps([
      { id: 1, label: "trends: pending", status: "active" },
      { id: 2, label: "generation: pending", status: "pending" },
      { id: 3, label: "approval: pending", status: "pending" },
      { id: 4, label: "publish: pending", status: "pending" },
    ]);
    setResults([]);
    setGeneratedPosts(null);
    try {
      const res = await fetch(`${API_BASE}/demo/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: text, region: "united_states" }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || "Generation failed");
      }
      const posts = data.generated_posts as GeneratedPosts;
      setGeneratedPosts(posts);
      setResults(mapResults(posts));
      setSteps(stepsFromBackend(data.steps));
      setPhase("results");
      toast.success("3 variants generated. Pick one to publish.");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Generation failed";
      toast.error(msg);
      setPhase("idle");
      setSteps([]);
    }
  };

  const handleCardAction = async (index: number, action: "approved" | "rejected") => {
    if (action === "rejected") {
      setResults((prev) => prev.map((r, i) => (i === index ? { ...r, status: "rejected" } : r)));
      return;
    }
    if (!generatedPosts) {
      toast.error("Nothing to publish yet.");
      return;
    }
    const selected = results[index];
    if (!selected) return;

    // Show scheduler option
    setPublishingIndex(index);
    setShowScheduler(true);
    setResults((prev) =>
      prev.map((r, i) => (i === index ? { ...r, status: "approved" } : { ...r, status: null }))
    );
  };

  const handlePublish = async (immediate: boolean) => {
    if (publishingIndex === null || !generatedPosts) return;
    
    const selected = results[publishingIndex];
    if (!selected) return;

    try {
      const payload: any = {
        variant: selected.variant,
        generated_posts: generatedPosts,
      };

      if (!immediate && scheduledTime) {
        payload.scheduled_time = scheduledTime;
      }

      const res = await fetch(`${API_BASE}/demo/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || "Publish failed");
      }

      if (data.scheduled) {
        const schedTime = new Date(data.scheduled_time).toLocaleString();
        toast.success(`Post scheduled for ${schedTime}`);
        setSteps([
          { id: 1, label: "trends: completed", status: "completed" },
          { id: 2, label: "generation: completed", status: "completed" },
          { id: 3, label: "approval: completed", status: "completed" },
          { id: 4, label: `publish: scheduled for ${schedTime}`, status: "completed" },
        ]);
      } else {
        const urn = data?.linkedin?.id ? ` (${data.linkedin.id})` : "";
        setSteps([
          { id: 1, label: "trends: completed", status: "completed" },
          { id: 2, label: "generation: completed", status: "completed" },
          { id: 3, label: "approval: completed", status: "completed" },
          { id: 4, label: "publish: completed", status: "completed" },
        ]);
        toast.success(`Published to LinkedIn${urn}`);
      }
      
      setShowScheduler(false);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Publish failed";
      toast.error(msg);
      setResults((prev) => prev.map((r, i) => (i === publishingIndex ? { ...r, status: null } : r)));
    } finally {
      setPublishingIndex(null);
    }
  };

  const handleReset = () => {
    setPhase("idle");
    setPrompt("");
    setSteps([]);
    setResults([]);
    setGeneratedPosts(null);
    setPublishingIndex(null);
    setShowScheduler(false);
    setScheduledTime("");
  };

  return (
    <div className="relative min-h-screen gradient-surface overflow-hidden">
      {/* Glow effect */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{ background: "var(--gradient-glow)" }}
      />

      <div className="relative z-10 flex flex-col items-center min-h-screen px-4 py-12">
        {/* Header */}
        <AnimatePresence mode="wait">
          {phase === "idle" && (
            <motion.div
              key="header"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center mb-10 mt-20"
            >
              <div className="gradient-pink rounded-2xl p-3 mb-5 shadow-soft">
                <Sparkles className="h-7 w-7 text-primary-foreground" />
              </div>
              <h1 className="text-3xl sm:text-4xl font-bold text-foreground tracking-tight text-center">
                Trend2Post Studio
              </h1>
              <p className="mt-2 text-muted-foreground text-center max-w-md text-sm">
                Generate professional LinkedIn content with a guided approval flow.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Prompt display when processing/results */}
        <AnimatePresence>
          {phase !== "idle" && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="w-full max-w-2xl mx-auto mt-6 mb-4"
            >
              <div className="flex items-start gap-3 rounded-2xl bg-accent/50 border border-border px-5 py-4">
                <div className="gradient-pink rounded-lg p-1.5 mt-0.5">
                  <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
                </div>
                <p className="text-sm text-foreground leading-relaxed">{prompt}</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Stepper */}
        <AnimatePresence>
          {(phase === "processing" || phase === "results") && (
            <ProcessStepper steps={steps} />
          )}
        </AnimatePresence>

        {/* Results */}
        <AnimatePresence>
          {phase === "results" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="w-full max-w-3xl mx-auto"
            >
              <div className="grid gap-4 sm:grid-cols-3 mb-8">
                {results.map((result, i) => (
                  <ResultCard
                    key={result.variant}
                    index={i}
                    platform={result.platform}
                    content={result.content}
                    hashtags={result.hashtags}
                    status={result.status}
                    onApprove={() => {
                      if (publishingIndex === null) handleCardAction(i, "approved");
                    }}
                    onReject={() => handleCardAction(i, "rejected")}
                  />
                ))}
              </div>
              {publishingIndex !== null && showScheduler && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-6 p-5 rounded-2xl bg-accent/50 border border-border"
                >
                  <div className="flex items-center gap-2 mb-4">
                    <Calendar className="h-4 w-4 text-primary" />
                    <h3 className="text-sm font-semibold text-foreground">Schedule Post</h3>
                  </div>
                  <p className="text-xs text-muted-foreground mb-4">
                    Choose when to publish (defaults to next weekday 9am)
                  </p>
                  <DateTimePicker
                    value={scheduledTime}
                    onChange={setScheduledTime}
                    minDate={new Date()}
                  />
                  <div className="flex gap-3 mt-4">
                    <button
                      onClick={() => handlePublish(false)}
                      className="flex-1 rounded-xl gradient-pink py-2 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90"
                    >
                      Schedule Post
                    </button>
                    <button
                      onClick={() => handlePublish(true)}
                      className="flex-1 rounded-xl border border-border py-2 text-sm font-medium text-foreground transition-all hover:bg-muted"
                    >
                      Publish Now
                    </button>
                    <button
                      onClick={() => {
                        setShowScheduler(false);
                        setPublishingIndex(null);
                        setResults((prev) => prev.map((r) => ({ ...r, status: null })));
                      }}
                      className="px-4 rounded-xl border border-border py-2 text-sm font-medium text-muted-foreground transition-all hover:bg-muted"
                    >
                      Cancel
                    </button>
                  </div>
                </motion.div>
              )}

              {/* New prompt button */}
              <div className="flex justify-center">
                <button
                  onClick={handleReset}
                  className="text-sm font-medium text-primary hover:underline underline-offset-4 transition-colors"
                >
                  ← Start a new post
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Input area */}
        <div className={`w-full ${phase === "idle" ? "" : "mt-auto pt-8"}`}>
          <PromptInput
            onSubmit={handleSubmit}
            disabled={phase === "processing"}
          />
        </div>
      </div>
    </div>
  );
};

export default Index;
