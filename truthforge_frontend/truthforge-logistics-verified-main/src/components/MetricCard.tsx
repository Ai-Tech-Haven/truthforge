import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  change?: string;
  variant?: "default" | "accent" | "success" | "warning";
}

const variantStyles = {
  default: "bg-card border-border",
  accent: "bg-accent/5 border-accent/20",
  success: "bg-success/5 border-success/20",
  warning: "bg-warning/5 border-warning/20",
};

const iconVariantStyles = {
  default: "text-primary",
  accent: "text-accent",
  success: "text-success",
  warning: "text-warning",
};

const MetricCard = ({ icon: Icon, label, value, change, variant = "default" }: MetricCardProps) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    className={`rounded-xl border p-4 shadow-card ${variantStyles[variant]}`}
  >
    <div className="flex items-center justify-between mb-3">
      <Icon className={`h-5 w-5 ${iconVariantStyles[variant]}`} />
      {change && (
        <span className="text-xs font-medium text-success bg-success/10 px-2 py-0.5 rounded-full">{change}</span>
      )}
    </div>
    <div className="text-2xl font-heading font-bold text-foreground">{value}</div>
    <div className="text-sm text-muted-foreground mt-1">{label}</div>
  </motion.div>
);

export default MetricCard;
