import { BarChart, Bar, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const defaultThroughput = [
  { day: "Mon", cleared: 48, pending: 5, flagged: 2 },
  { day: "Tue", cleared: 52, pending: 8, flagged: 1 },
  { day: "Wed", cleared: 61, pending: 4, flagged: 3 },
  { day: "Thu", cleared: 55, pending: 6, flagged: 2 },
  { day: "Fri", cleared: 67, pending: 3, flagged: 1 },
  { day: "Sat", cleared: 42, pending: 7, flagged: 0 },
  { day: "Sun", cleared: 38, pending: 2, flagged: 1 },
];

const defaultHcs = [
  { hour: "00:00", messages: 42 },
  { hour: "04:00", messages: 28 },
  { hour: "08:00", messages: 95 },
  { hour: "12:00", messages: 134 },
  { hour: "16:00", messages: 178 },
  { hour: "20:00", messages: 112 },
  { hour: "23:59", messages: 67 },
];

interface ThroughputPoint { day: string; cleared: number; pending: number; flagged: number }
interface HcsPoint { hour: string; messages: number }

interface OperationalChartsProps {
  throughputData?: ThroughputPoint[];
  hcsData?: HcsPoint[];
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { color: string; dataKey: string; value: number }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-elevated text-xs">
      <div className="font-heading font-bold text-foreground mb-1">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: p.color }} />
          <span className="text-muted-foreground capitalize">{p.dataKey}:</span>
          <span className="font-mono font-medium text-foreground">{p.value}</span>
        </div>
      ))}
    </div>
  );
};

const OperationalCharts = ({ throughputData, hcsData }: OperationalChartsProps) => {
  const tData = throughputData ?? defaultThroughput;
  const hData = hcsData ?? defaultHcs;
  const peakMessages = Math.max(...hData.map((d) => d.messages));

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="rounded-xl border border-border bg-card p-5 shadow-card hover:shadow-elevated transition-all duration-200">
        <h4 className="text-sm font-heading font-bold text-foreground mb-1">Clearance Throughput</h4>
        <p className="text-[10px] text-muted-foreground mb-4">Weekly shipment processing by outcome.</p>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={tData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(213 30% 22%)" vertical={false} />
              <XAxis dataKey="day" tick={{ fontSize: 10, fill: "hsl(215 14% 55%)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "hsl(215 14% 55%)" }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="cleared" fill="hsl(122 39% 49%)" radius={[3, 3, 0, 0]} />
              <Bar dataKey="pending" fill="hsl(36 100% 50%)" radius={[3, 3, 0, 0]} />
              <Bar dataKey="flagged" fill="hsl(4 90% 58%)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-border">
          {[{ label: "Cleared", color: "bg-success" }, { label: "Pending", color: "bg-warning" }, { label: "Flagged", color: "bg-destructive" }].map((l) => (
            <div key={l.label} className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${l.color}`} />
              <span className="text-[10px] text-muted-foreground">{l.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-5 shadow-card hover:shadow-elevated transition-all duration-200">
        <h4 className="text-sm font-heading font-bold text-foreground mb-1">HCS Consensus Volume</h4>
        <p className="text-[10px] text-muted-foreground mb-4">24-hour Hedera message activity.</p>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={hData}>
              <defs>
                <linearGradient id="hcsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(190 100% 50%)" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="hsl(190 100% 50%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(213 30% 22%)" vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: "hsl(215 14% 55%)" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: "hsl(215 14% 55%)" }} axisLine={false} tickLine={false} width={30} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="messages" stroke="hsl(190 100% 50%)" fill="url(#hcsGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border">
          <span className="h-2 w-2 rounded-full bg-accent" />
          <span className="text-[10px] text-muted-foreground">HCS Messages</span>
          <span className="text-[10px] font-mono text-accent ml-auto">Peak: {peakMessages} msgs/hr</span>
        </div>
      </div>
    </div>
  );
};

export default OperationalCharts;
