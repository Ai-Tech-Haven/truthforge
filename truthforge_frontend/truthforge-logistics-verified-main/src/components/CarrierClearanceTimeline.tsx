import { CheckCircle, AlertTriangle, Clock, FileText, ShieldCheck, CreditCard, Anchor } from "lucide-react";

export interface CarrierClearanceStepData {
  documents_uploaded?: boolean;
  verification_completed?: boolean;
  /** true = payment confirmed (green) */
  payment_completed?: boolean;
  /** true = payment step is actively awaiting user action (amber) */
  payment_pending?: boolean;
  clearance_issued?: boolean;
  flagged?: boolean;
}

type StepState = "pending" | "in-progress" | "completed" | "flagged" | "payment-pending";

interface Step {
  key: keyof CarrierClearanceStepData;
  label: string;
  sublabel?: (d: CarrierClearanceStepData) => string | undefined;
  icon: typeof FileText;
}

const STEPS: Step[] = [
  { key: "documents_uploaded",     label: "Documents Uploaded",    icon: FileText },
  { key: "verification_completed", label: "Verification Completed", icon: ShieldCheck },
  {
    key: "payment_completed",
    label: "HBAR Payment",
    sublabel: (d) =>
      d.payment_completed
        ? "Payment Completed (HBAR)"
        : d.payment_pending
        ? "Payment Pending"
        : undefined,
    icon: CreditCard,
  },
  { key: "clearance_issued", label: "Port Clearance Issued", icon: Anchor },
];

const stateStyles: Record<StepState, { circle: string; label: string; line: string }> = {
  completed:         { circle: "bg-success border-success text-white",                       label: "text-success",          line: "bg-success" },
  "in-progress":     { circle: "bg-primary/20 border-primary text-primary animate-pulse",    label: "text-primary",          line: "bg-border" },
  "payment-pending": { circle: "bg-warning/20 border-warning text-warning",                  label: "text-warning",          line: "bg-border" },
  flagged:           { circle: "bg-destructive/20 border-destructive text-destructive",      label: "text-destructive",      line: "bg-border" },
  pending:           { circle: "bg-secondary border-border text-muted-foreground",           label: "text-muted-foreground", line: "bg-border" },
};

function resolveState(step: Step, data: CarrierClearanceStepData, idx: number): StepState {
  if (step.key === "clearance_issued" && data.flagged) return "flagged";
  if (step.key === "payment_completed" && data.payment_pending && !data.payment_completed) return "payment-pending";
  if (data[step.key]) return "completed";
  const firstIncomplete = STEPS.findIndex(s => !data[s.key]);
  if (firstIncomplete === idx) return "in-progress";
  return "pending";
}

function StepIcon({ state, Icon, sm }: { state: StepState; Icon: typeof FileText; sm?: boolean }) {
  const cls = sm ? "h-3 w-3" : "h-3.5 w-3.5";
  if (state === "completed") return <CheckCircle className={cls} />;
  if (state === "flagged") return <AlertTriangle className={cls} />;
  if (state === "in-progress" || state === "payment-pending") return <Clock className={cls} />;
  return <Icon className={cls} />;
}

interface Props { data: CarrierClearanceStepData }

const CarrierClearanceTimeline = ({ data }: Props) => (
  <div className="mt-4 pt-4 border-t border-border">
    {/* Desktop: horizontal */}
    <div className="hidden sm:flex items-start gap-0">
      {STEPS.map((step, idx) => {
        const state = resolveState(step, data, idx);
        const s = stateStyles[state];
        const isLast = idx === STEPS.length - 1;
        const sub = step.sublabel?.(data);
        return (
          <div key={step.key} className="flex items-start flex-1 min-w-0">
            <div className="flex flex-col items-center flex-1 min-w-0">
              <div className={`h-7 w-7 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${s.circle}`}>
                <StepIcon state={state} Icon={step.icon} />
              </div>
              <span className={`text-[9px] font-medium mt-1 text-center leading-tight px-0.5 ${s.label}`}>
                {sub ?? step.label}
              </span>
            </div>
            {!isLast && <div className={`h-0.5 flex-1 mt-3.5 mx-1 rounded transition-colors ${s.line}`} />}
          </div>
        );
      })}
    </div>

    {/* Mobile: vertical */}
    <div className="flex sm:hidden flex-col gap-2">
      {STEPS.map((step, idx) => {
        const state = resolveState(step, data, idx);
        const s = stateStyles[state];
        const isLast = idx === STEPS.length - 1;
        const sub = step.sublabel?.(data);
        return (
          <div key={step.key} className="flex items-start gap-2">
            <div className="flex flex-col items-center">
              <div className={`h-6 w-6 rounded-full border-2 flex items-center justify-center shrink-0 ${s.circle}`}>
                <StepIcon state={state} Icon={step.icon} sm />
              </div>
              {!isLast && <div className={`w-0.5 h-4 mt-0.5 ${s.line}`} />}
            </div>
            <span className={`text-[10px] font-medium mt-1 ${s.label}`}>{sub ?? step.label}</span>
          </div>
        );
      })}
    </div>
  </div>
);

export default CarrierClearanceTimeline;
