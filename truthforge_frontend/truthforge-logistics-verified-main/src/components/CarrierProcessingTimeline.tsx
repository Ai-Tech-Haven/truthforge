import { CheckCircle, AlertTriangle, Clock, Package, FileText, Bot, Ship, Landmark } from "lucide-react";

export interface CarrierTimelineData {
  shipment_received?: boolean;
  documents_uploaded?: boolean;
  agents_verified?: boolean;
  submitted_for_clearance?: boolean;
  port_pre_cleared?: boolean;
  flagged?: boolean;
}

type StepState = "pending" | "in-progress" | "completed" | "flagged";

interface Step {
  key: keyof CarrierTimelineData;
  label: string;
  icon: typeof Package;
}

const STEPS: Step[] = [
  { key: "shipment_received",       label: "Shipment Received",       icon: Package },
  { key: "documents_uploaded",      label: "Documents Uploaded",      icon: FileText },
  { key: "agents_verified",         label: "Agents Verified",         icon: Bot },
  { key: "submitted_for_clearance", label: "Submitted for Clearance", icon: Ship },
  { key: "port_pre_cleared",        label: "Port Pre-Cleared",        icon: Landmark },
];

const stateStyles: Record<StepState, { circle: string; label: string; line: string }> = {
  completed:    { circle: "bg-success border-success text-white",                        label: "text-success",          line: "bg-success" },
  "in-progress":{ circle: "bg-primary/20 border-primary text-primary animate-pulse",    label: "text-primary",          line: "bg-border" },
  flagged:      { circle: "bg-destructive/20 border-destructive text-destructive",       label: "text-destructive",      line: "bg-border" },
  pending:      { circle: "bg-secondary border-border text-muted-foreground",            label: "text-muted-foreground", line: "bg-border" },
};

function resolveState(step: Step, data: CarrierTimelineData, idx: number): StepState {
  if (step.key === "agents_verified" && data.flagged) return "flagged";
  if (data[step.key]) return "completed";
  const firstIncomplete = STEPS.findIndex(s => !data[s.key]);
  if (firstIncomplete === idx) return "in-progress";
  return "pending";
}

interface Props {
  data: CarrierTimelineData;
  preCleared?: boolean; // synced from merchant portal
}

const CarrierProcessingTimeline = ({ data, preCleared }: Props) => {
  const resolved = preCleared
    ? {
        shipment_received: true,
        documents_uploaded: true,
        agents_verified: true,
        submitted_for_clearance: true,
        port_pre_cleared: true,
        flagged: false,
      }
    : data;

  return (
    <div className="mt-3 pt-3 border-t border-border/60">
      {preCleared && (
        <p className="text-[10px] text-success font-medium mb-2 flex items-center gap-1">
          <CheckCircle className="h-3 w-3" />
          Pre-cleared upstream by merchant
        </p>
      )}

      {/* Desktop: horizontal */}
      <div className="hidden sm:flex items-start gap-0">
        {STEPS.map((step, idx) => {
          const state = resolveState(step, resolved, idx);
          const s = stateStyles[state];
          const Icon = step.icon;
          const isLast = idx === STEPS.length - 1;
          return (
            <div key={step.key} className="flex items-start flex-1 min-w-0">
              <div className="flex flex-col items-center flex-1 min-w-0">
                <div className={`h-7 w-7 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${s.circle}`}>
                  {state === "completed" ? (
                    <CheckCircle className="h-3.5 w-3.5" />
                  ) : state === "flagged" ? (
                    <AlertTriangle className="h-3.5 w-3.5" />
                  ) : state === "in-progress" ? (
                    <Clock className="h-3.5 w-3.5" />
                  ) : (
                    <Icon className="h-3.5 w-3.5" />
                  )}
                </div>
                <span className={`text-[9px] font-medium mt-1 text-center leading-tight px-0.5 ${s.label}`}>
                  {step.label}
                </span>
              </div>
              {!isLast && (
                <div className={`h-0.5 flex-1 mt-3.5 mx-1 rounded transition-colors ${s.line}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* Mobile: vertical */}
      <div className="flex sm:hidden flex-col gap-2">
        {STEPS.map((step, idx) => {
          const state = resolveState(step, resolved, idx);
          const s = stateStyles[state];
          const Icon = step.icon;
          const isLast = idx === STEPS.length - 1;
          return (
            <div key={step.key} className="flex items-start gap-2">
              <div className="flex flex-col items-center">
                <div className={`h-6 w-6 rounded-full border-2 flex items-center justify-center shrink-0 ${s.circle}`}>
                  {state === "completed" ? (
                    <CheckCircle className="h-3 w-3" />
                  ) : state === "flagged" ? (
                    <AlertTriangle className="h-3 w-3" />
                  ) : state === "in-progress" ? (
                    <Clock className="h-3 w-3" />
                  ) : (
                    <Icon className="h-3 w-3" />
                  )}
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
};

export default CarrierProcessingTimeline;
