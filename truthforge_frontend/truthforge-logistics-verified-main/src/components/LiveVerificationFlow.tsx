import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Store, Ship, Shield, Anchor, CheckCircle, FileText,
  Wallet, CreditCard, UserCheck, ScrollText, Play, Pause, RotateCcw,
  ChevronRight, Zap, Clock,
} from "lucide-react";

/* ── Types ── */
interface FlowNode {
  id: string;
  label: string;
  shortLabel: string;
  description: string;
  icon: React.ElementType;
  status: "pending" | "active" | "verified" | "cleared";
}

interface LogEntry {
  timestamp: string;
  message: string;
  nodeId: string;
  type: "info" | "success" | "warning";
}

/* ── Flow Definitions ── */
const fullFlowNodes: FlowNode[] = [
  { id: "merchant", label: "Merchant Portal",     shortLabel: "Merchant", description: "Shipment created and submitted for carrier assignment.",                    icon: Store,        status: "pending" },
  { id: "shipment", label: "Shipment Record",     shortLabel: "Shipment", description: "Structured shipment record with cargo manifest and routing.",               icon: FileText,     status: "pending" },
  { id: "carrier",  label: "Carrier Portal",      shortLabel: "Carrier",  description: "Carrier uploads proof — container, cargo, or airway bill.",                icon: Ship,         status: "pending" },
  { id: "agent",    label: "Verification Agent",  shortLabel: "Agent",    description: "Compliance check by HOL-registered verification agents.",                  icon: Shield,       status: "pending" },
  { id: "port",     label: "Port Authority",      shortLabel: "Port",     description: "Pre-clearance determination issued by port authority.",                    icon: Anchor,       status: "pending" },
  { id: "cleared",  label: "Cleared for Entry",   shortLabel: "Cleared",  description: "Shipment eligible for expedited port processing.",                         icon: CheckCircle,  status: "pending" },
];

const directFlowNodes: FlowNode[] = [
  { id: "carrier",  label: "Carrier Portal",      shortLabel: "Carrier",  description: "Direct carrier submission with proof of cargo.",                          icon: Ship,         status: "pending" },
  { id: "agent",    label: "Verification Agent",  shortLabel: "Agent",    description: "Compliance check by HOL-registered verification agents.",                  icon: Shield,       status: "pending" },
  { id: "port",     label: "Port Authority",      shortLabel: "Port",     description: "Pre-clearance determination issued by port authority.",                    icon: Anchor,       status: "pending" },
  { id: "cleared",  label: "Cleared for Entry",   shortLabel: "Cleared",  description: "Shipment eligible for expedited port processing.",                         icon: CheckCircle,  status: "pending" },
];

const logMessages: Record<string, { message: string; type: LogEntry["type"] }> = {
  merchant:       { message: "Merchant portal → shipment created",            type: "info"    },
  shipment:       { message: "Shipment record structured & assigned",          type: "info"    },
  carrier:        { message: "Carrier proof uploaded (container scan)",        type: "info"    },
  agent:          { message: "Agent verification — compliance pass ✓",         type: "success" },
  port:           { message: "Port authority pre-clearance issued",            type: "success" },
  cleared:        { message: "STATUS: Cleared for entry",                      type: "success" },
  auto_pay:       { message: "Auto wallet deduction processed",                type: "info"    },
  manual_pay:     { message: "Payment request sent → awaiting confirm",        type: "warning" },
  manual_confirm: { message: "User confirmed → wallet deducted",               type: "info"    },
  audit:          { message: "Immutable audit log anchored (HCS)",             type: "info"    },
};

const now = () => {
  const d = new Date();
  return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}:${d.getSeconds().toString().padStart(2, "0")}`;
};

/* ── Status Badge ── */
const StatusBadge = ({ status }: { status: FlowNode["status"] }) => {
  const cfg = {
    pending:  { label: "Pending",    cls: "text-[hsl(210,20%,55%)] bg-[hsl(213,40%,18%)] border-[hsl(213,30%,25%)]" },
    active:   { label: "Processing", cls: "text-[hsl(45,100%,60%)] bg-[hsl(45,80%,15%)] border-[hsl(45,80%,35%)]" },
    verified: { label: "Verified",   cls: "text-[hsl(122,39%,60%)] bg-[hsl(122,39%,15%)] border-[hsl(122,39%,35%)]" },
    cleared:  { label: "Cleared",    cls: "text-[hsl(190,100%,60%)] bg-[hsl(190,80%,15%)] border-[hsl(190,80%,35%)]" },
  }[status];
  return (
    <span className={`text-[9px] font-heading font-bold uppercase tracking-wider px-1.5 py-0.5 rounded border ${cfg.cls}`}>
      {cfg.label}
    </span>
  );
};

/* ── Main Component ── */
const LiveVerificationFlow = () => {
  const [path, setPath]               = useState<"full" | "direct">("full");
  const [paymentMode, setPaymentMode] = useState<"auto" | "manual">("auto");
  const [activeStep, setActiveStep]   = useState(-1);
  const [playing, setPlaying]         = useState(false);
  const [logs, setLogs]               = useState<LogEntry[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const logEndRef   = useRef<HTMLDivElement>(null);

  const baseNodes = path === "full" ? fullFlowNodes : directFlowNodes;
  const nodes = baseNodes.map((n, i) => ({
    ...n,
    status:
      i < activeStep  ? ("verified" as const) :
      i === activeStep ? ("active"  as const) :
                         ("pending" as const),
  }));

  const addLog = useCallback((nodeId: string) => {
    const msg = logMessages[nodeId];
    if (!msg) return;
    setLogs(prev => [...prev, { timestamp: now(), message: msg.message, nodeId, type: msg.type }]);
  }, []);

  const advance = useCallback(() => {
    setActiveStep(prev => {
      const max = (path === "full" ? fullFlowNodes : directFlowNodes).length;
      const next = prev + 1;
      if (next > max) { setPlaying(false); return prev; }
      return next;
    });
  }, [path]);

  /* Log on step change */
  useEffect(() => {
    if (activeStep < 0) return;
    const nodeList = path === "full" ? fullFlowNodes : directFlowNodes;
    if (activeStep < nodeList.length) {
      addLog(nodeList[activeStep].id);
      if (nodeList[activeStep].id === "agent") {
        setTimeout(() => {
          if (paymentMode === "auto") {
            addLog("auto_pay");
          } else {
            addLog("manual_pay");
            setTimeout(() => addLog("manual_confirm"), 600);
          }
        }, 400);
      }
      if (["merchant", "carrier", "agent", "port"].includes(nodeList[activeStep].id)) {
        setTimeout(() => addLog("audit"), 500);
      }
    }
    if (activeStep === nodeList.length) setPlaying(false);
  }, [activeStep, path, paymentMode, addLog]);

  /* Auto-scroll log */
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  /* Interval */
  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(advance, 1800);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [playing, advance]);

  const reset = () => {
    setPlaying(false);
    setActiveStep(-1);
    setLogs([]);
    setSelectedNode(null);
  };

  const togglePlay = () => {
    const max = (path === "full" ? fullFlowNodes : directFlowNodes).length;
    if (activeStep >= max) {
      reset();
      setTimeout(() => setPlaying(true), 100);
    } else {
      setPlaying(p => !p);
    }
  };

  return (
    <div className="rounded-xl border border-[hsl(213,30%,28%)] bg-[hsl(213,50%,15%)] shadow-card overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-[hsl(213,30%,22%)]">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-accent" />
              <h3 className="text-sm font-heading font-bold text-[hsl(210,20%,88%)]">
                How TruthForge Works — Live Verification Flow
              </h3>
            </div>
            <p className="text-xs text-[hsl(210,20%,55%)] mt-1">
              Interactive process flow with real-time step progression.
            </p>
          </div>
          {/* Path toggle */}
          <div className="flex rounded-lg overflow-hidden border border-[hsl(213,30%,25%)]">
            <button
              onClick={() => { reset(); setPath("full"); }}
              className={`px-2.5 py-1 text-[10px] font-heading font-bold uppercase tracking-wider transition-colors ${
                path === "full"
                  ? "bg-accent/20 text-accent"
                  : "bg-[hsl(213,50%,12%)] text-[hsl(210,20%,50%)] hover:text-[hsl(210,20%,70%)]"
              }`}
            >
              Full Flow
            </button>
            <button
              onClick={() => { reset(); setPath("direct"); }}
              className={`px-2.5 py-1 text-[10px] font-heading font-bold uppercase tracking-wider transition-colors ${
                path === "direct"
                  ? "bg-accent/20 text-accent"
                  : "bg-[hsl(213,50%,12%)] text-[hsl(210,20%,50%)] hover:text-[hsl(210,20%,70%)]"
              }`}
            >
              Direct Carrier
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-col lg:flex-row">
        {/* Flow Area */}
        <div className="flex-1 p-5">
          {/* Controls */}
          <div className="flex items-center gap-3 mb-5 flex-wrap">
            <button
              onClick={togglePlay}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-heading font-bold bg-accent/15 text-accent border border-accent/25 hover:bg-accent/25 transition-colors"
            >
              {playing ? <Pause className="h-3 w-3" /> : <Play className="h-3 w-3" />}
              {playing ? "Pause" : activeStep >= nodes.length ? "Replay" : "Start"}
            </button>
            <button
              onClick={reset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[hsl(210,20%,55%)] border border-[hsl(213,30%,25%)] hover:text-[hsl(210,20%,75%)] transition-colors"
            >
              <RotateCcw className="h-3 w-3" />Reset
            </button>
            {/* Payment mode */}
            <div className="ml-auto flex items-center gap-2">
              <span className="text-[10px] text-[hsl(210,20%,50%)] uppercase tracking-wider font-heading">Payment:</span>
              <button
                onClick={() => setPaymentMode(p => p === "auto" ? "manual" : "auto")}
                className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] font-heading font-bold uppercase tracking-wider transition-colors border ${
                  paymentMode === "auto"
                    ? "text-[hsl(122,39%,60%)] bg-[hsl(122,39%,15%)] border-[hsl(122,39%,35%)]"
                    : "text-[hsl(45,100%,60%)] bg-[hsl(45,80%,15%)] border-[hsl(45,80%,35%)]"
                }`}
              >
                {paymentMode === "auto"
                  ? <><Wallet className="h-3 w-3" /> Auto</>
                  : <><CreditCard className="h-3 w-3" /> Manual</>}
              </button>
            </div>
          </div>

          {/* Nodes Flow */}
          <div className="flex flex-wrap sm:flex-nowrap items-center gap-1 overflow-x-auto pb-2">
            {nodes.map((node, i) => {
              const Icon     = node.icon;
              const isActive = node.status === "active";
              const isDone   = node.status === "verified";
              const isSelected = selectedNode === node.id;

              return (
                <div key={node.id} className="flex items-center">
                  {i > 0 && (
                    <div className="flex items-center px-0.5">
                      <motion.div
                        className="flex items-center"
                        initial={{ opacity: 0.3 }}
                        animate={{ opacity: isDone || isActive ? 1 : 0.3 }}
                      >
                        <div className={`w-5 h-px ${isDone ? "bg-[hsl(122,39%,49%)]" : isActive ? "bg-[hsl(45,100%,50%)]" : "bg-[hsl(213,30%,25%)]"}`} />
                        <ChevronRight className={`h-3 w-3 -ml-1 ${isDone ? "text-[hsl(122,39%,49%)]" : isActive ? "text-[hsl(45,100%,50%)]" : "text-[hsl(213,30%,25%)]"}`} />
                      </motion.div>
                    </div>
                  )}
                  <motion.button
                    onClick={() => setSelectedNode(isSelected ? null : node.id)}
                    className={`relative flex flex-col items-center gap-1.5 px-3 py-3 rounded-lg border transition-all min-w-[68px] ${
                      isActive
                        ? "bg-[hsl(45,80%,15%)] border-[hsl(45,80%,40%)] shadow-[0_0_12px_hsl(45,80%,50%,0.15)]"
                        : isDone
                        ? "bg-[hsl(122,39%,12%)] border-[hsl(122,39%,30%)]"
                        : "bg-[hsl(213,50%,12%)] border-[hsl(213,30%,22%)] hover:border-[hsl(213,30%,35%)]"
                    }`}
                    animate={isActive ? { scale: [1, 1.03, 1] } : {}}
                    transition={isActive ? { duration: 1.5, repeat: Infinity } : {}}
                  >
                    {isDone && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-1.5 -right-1.5 h-4 w-4 rounded-full bg-[hsl(122,39%,49%)] flex items-center justify-center"
                      >
                        <CheckCircle className="h-2.5 w-2.5 text-white" />
                      </motion.div>
                    )}
                    <Icon className={`h-4 w-4 ${isActive ? "text-[hsl(45,100%,60%)]" : isDone ? "text-[hsl(122,39%,60%)]" : "text-[hsl(210,20%,50%)]"}`} />
                    <span className={`text-[10px] font-heading font-bold leading-tight text-center ${
                      isActive ? "text-[hsl(45,100%,70%)]" : isDone ? "text-[hsl(122,39%,70%)]" : "text-[hsl(210,20%,65%)]"
                    }`}>
                      {node.shortLabel}
                    </span>
                  </motion.button>
                </div>
              );
            })}
          </div>

          {/* Selected Node Detail */}
          <AnimatePresence>
            {selectedNode && (() => {
              const node = nodes.find(n => n.id === selectedNode);
              if (!node) return null;
              return (
                <motion.div
                  key={selectedNode}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="mt-4 p-3 rounded-lg bg-[hsl(213,50%,12%)] border border-[hsl(213,30%,22%)]"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-heading font-bold text-[hsl(210,20%,85%)]">{node.label}</span>
                    <StatusBadge status={node.status} />
                  </div>
                  <p className="text-[11px] text-[hsl(210,20%,55%)] leading-relaxed">{node.description}</p>
                </motion.div>
              );
            })()}
          </AnimatePresence>

          {/* Payment Branch Visual */}
          {activeStep >= 0 && (
            <div className="mt-4 flex items-center gap-2 flex-wrap">
              <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${
                paymentMode === "auto"
                  ? "text-[hsl(122,39%,60%)] bg-[hsl(122,39%,12%)] border-[hsl(122,39%,30%)]"
                  : "text-[hsl(210,20%,40%)] bg-[hsl(213,50%,12%)] border-[hsl(213,30%,20%)]"
              }`}>
                <Wallet className="h-3 w-3" /> Auto Deduction
              </div>
              <span className="text-[10px] text-[hsl(210,20%,40%)]">or</span>
              <div className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded border text-[10px] font-heading font-bold uppercase tracking-wider ${
                paymentMode === "manual"
                  ? "text-[hsl(45,100%,60%)] bg-[hsl(45,80%,12%)] border-[hsl(45,80%,30%)]"
                  : "text-[hsl(210,20%,40%)] bg-[hsl(213,50%,12%)] border-[hsl(213,30%,20%)]"
              }`}>
                <CreditCard className="h-3 w-3" /> Manual → Confirm
              </div>
            </div>
          )}

          {/* Audit Log Badge */}
          <div className="mt-4 flex items-center gap-2">
            <ScrollText className="h-3 w-3 text-[hsl(210,20%,45%)] shrink-0" />
            <span className="text-[10px] text-[hsl(210,20%,45%)] font-heading uppercase tracking-wider">
              All steps anchored to immutable audit log (HCS)
            </span>
          </div>
        </div>

        {/* Live Log Panel */}
        <div className="lg:w-64 border-t lg:border-t-0 lg:border-l border-[hsl(213,30%,22%)] bg-[hsl(213,50%,11%)]">
          <div className="p-3 border-b border-[hsl(213,30%,22%)] flex items-center gap-1.5">
            <div className="h-1.5 w-1.5 rounded-full bg-[hsl(122,39%,49%)] animate-pulse" />
            <span className="text-[10px] font-heading font-bold text-[hsl(210,20%,55%)] uppercase tracking-wider">Live Log</span>
          </div>
          <div className="h-48 lg:h-auto lg:min-h-[280px] overflow-y-auto p-3 space-y-1.5">
            {logs.length === 0 && (
              <div className="flex items-center gap-1.5 text-[10px] text-[hsl(210,20%,35%)]">
                <Clock className="h-3 w-3" />
                Waiting for flow to start…
              </div>
            )}
            {logs.map((log, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex gap-2 text-[10px] leading-relaxed"
              >
                <span className="font-mono text-[hsl(210,20%,40%)] shrink-0">{log.timestamp}</span>
                <span className={
                  log.type === "success" ? "text-[hsl(122,39%,60%)]" :
                  log.type === "warning" ? "text-[hsl(45,100%,60%)]" :
                  "text-[hsl(210,20%,65%)]"
                }>
                  {log.message}
                </span>
              </motion.div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveVerificationFlow;
