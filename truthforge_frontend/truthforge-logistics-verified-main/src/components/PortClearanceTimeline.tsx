import { CheckCircle, AlertTriangle, Clock, Radio, FileText, Bot, CreditCard, Anchor } from "lucide-react";

export interface PortClearanceStepData {
  shipment_announced?: boolean;
  documents_submitted?: boolean;
  agents_verified?: boolean;
  hbar_settled?: boolean;
  clearance_issued?: boolean;
  flagged?: boolean;
}

type StepState = "pending" | "in-progress" | "completed" | "flagged";

interface Step { key: keyof PortClearanceStepData; label: string; icon: typeof Radio }

const STEPS: Step[] = [
  { key: "shipment_announced",  label: "Shipment Announced",          icon: Radio },
  { key: "documents_submitted", label: "Carrier Docs Submitted",      icon: FileText },
  { key: "agents_verified",     label: "AI Agents Verified",          icon: Bot },
  { key: "hbar_settled",        label: "HBAR Fee Settled",            icon: CreditCard },
  { key: "clearance_issued",    label: "Port Pre-Clearance Issued",   icon: Anchor },
];

const stateStyles: Record<StepState, { circle: string; label: string; line: string }> = {
  completed:    { circle: "bg-success border-success text-white",                      label: "text-success",          line: "bg-success" },
  "in-progress":{ circle: "bg-primary/20 border-primary text-primary animate-pulse",  label: "text-primary",          line: "bg-border" },
  flagged:      { circle: "bg-destructive/20 border-destructive text-destructive",     label: "text-destructive",      line: "bg-border" },
  pending:      { circle: "bg-secondary border-border text-muted-foreground",          label: "text-muted-foreground", line: "bg-border" },
};

function resolveState(step: Step, data: PortClearanceStepData, idx: number): StepState {
  if (step.key === "clearance_issued" && data.flagged) return "flagged";
  if (data[step.key]) return "completed";
  const firstIncomplete = STEPS.findIndex(s => !data[s.key]);
  if (firstIncomplete === idx) return "in-progress";
  return "pending";
}

function StepIcon({ state, Icon, sm }: { state: StepState; Icon: typeof Radio; sm?: boolean }) {
  const cls = sm ? "h-3 w-3" : "h-3.5 w-3.5";
  if (state === "completed") return <CheckCircle className={cls} />;
  if (state === "flagged") return <AlertTriangle className={cls} />;
  if (state === "in-progress") return <Clock className={cls} />;
  return <Icon className={cls} />;
}

interface Props { data: PortClearanceStepData }

const PortClearanceTimeline = ({ data }: Props) => (
  <div className="mt-3 pt-3 border-t border-border/60">
    {/* Desktop: horizontal */}
    <div className="hidden sm:flex items-start gap-0">
      {STEPS.map((step, idx) => {
        const state = resolveState(step, data, idx);
        const s = stateStyles[state];
        const isLast = idx === STEPS.length - 1;
        return (
          <div key={step.key} className="flex items-start flex-1 min-w-0">
            <div className="flex flex-col items-center flex-1 min-w-0">
              <div className={`h-7 w-7 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${s.circle}`}>
                <StepIcon state={state} Icon={step.icon} />
              </div>
              <span className={`text-[9px] font-medium mt-1 text-center leading-tight px-0.5 ${s.label}`}>
                {step.label}
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
        return (
          <div key={step.key} className="flex items-start gap-2">
            <div className="flex flex-col items-center">
              <div className={`h-6 w-6 rounded-full border-2 flex items-center justify-center shrink-0 ${s.circle}`}>
                <StepIcon state={state} Icon={step.icon} sm />
              </div>
              {!isLast && <div className={`w-0.5 h-4 mt-0.5 ${s.line}`} />}
            </div>
            <span className={`text-[10px] font-medium mt-1 ${s.label}`}>{step.label}</span>
          </div>
        );
      })}
    </div>
  </div>
);

export default PortClearanceTimeline;
