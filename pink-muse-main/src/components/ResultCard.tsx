import { Check, X, Instagram, Twitter, Facebook } from "lucide-react";
import { motion } from "framer-motion";

interface ResultCardProps {
  index: number;
  platform: string;
  content: string;
  hashtags: string[];
  onApprove: () => void;
  onReject: () => void;
  status?: "approved" | "rejected" | null;
}

const platformIcons: Record<string, React.ReactNode> = {
  Instagram: <Instagram className="h-4 w-4" />,
  Twitter: <Twitter className="h-4 w-4" />,
  Facebook: <Facebook className="h-4 w-4" />,
};

const ResultCard = ({ index, platform, content, hashtags, onApprove, onReject, status }: ResultCardProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.15, duration: 0.4 }}
      className={`relative rounded-2xl border bg-card p-5 shadow-card transition-all hover:shadow-elevated ${
        status === "approved"
          ? "border-success/50 ring-1 ring-success/20"
          : status === "rejected"
          ? "border-destructive/30 opacity-60"
          : "border-border"
      }`}
    >
      {/* Platform badge */}
      <div className="flex items-center gap-2 mb-3">
        <span className="flex items-center gap-1.5 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-foreground">
          {platformIcons[platform]}
          {platform}
        </span>
        {status === "approved" && (
          <span className="text-xs font-medium text-success">✓ Approved</span>
        )}
        {status === "rejected" && (
          <span className="text-xs font-medium text-destructive">✗ Rejected</span>
        )}
      </div>

      {/* Content */}
      <p className="text-sm leading-relaxed text-foreground mb-3">{content}</p>

      {/* Hashtags */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {hashtags.map((tag) => (
          <span key={tag} className="text-xs text-primary font-medium">
            #{tag}
          </span>
        ))}
      </div>

      {/* Actions */}
      {!status && (
        <div className="flex gap-2">
          <button
            onClick={onApprove}
            className="flex-1 flex items-center justify-center gap-1.5 rounded-xl gradient-pink py-2 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90 active:scale-[0.98]"
          >
            <Check className="h-3.5 w-3.5" />
            Approve
          </button>
          <button
            onClick={onReject}
            className="flex-1 flex items-center justify-center gap-1.5 rounded-xl border border-border py-2 text-sm font-medium text-muted-foreground transition-all hover:bg-muted active:scale-[0.98]"
          >
            <X className="h-3.5 w-3.5" />
            Reject
          </button>
        </div>
      )}
    </motion.div>
  );
};

export default ResultCard;
