import { useState } from "react";
import { Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import PromptInput from "@/components/PromptInput";
import ProcessStepper, { Step } from "@/components/ProcessStepper";
import ResultCard from "@/components/ResultCard";
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

    setPublishingIndex(index);
    setResults((prev) =>
      prev.map((r, i) => (i === index ? { ...r, status: "approved" } : { ...r, status: null }))
    );
    try {
      const res = await fetch(`${API_BASE}/demo/publish`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          variant: selected.variant,
          generated_posts: generatedPosts,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || "Publish failed");
      }
      const urn = data?.linkedin?.id ? ` (${data.linkedin.id})` : "";
      setSteps([
        { id: 1, label: "trends: completed", status: "completed" },
        { id: 2, label: "generation: completed", status: "completed" },
        { id: 3, label: "approval: completed", status: "completed" },
        { id: 4, label: "publish: completed", status: "completed" },
      ]);
      toast.success(`Published to LinkedIn${urn}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Publish failed";
      toast.error(msg);
      setResults((prev) => prev.map((r, i) => (i === index ? { ...r, status: null } : r)));
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
              {publishingIndex !== null && (
                <p className="text-center text-sm text-muted-foreground mb-6">
                  Publishing selected variant...
                </p>
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
