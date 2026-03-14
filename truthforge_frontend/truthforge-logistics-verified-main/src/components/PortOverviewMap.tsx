import { motion } from "framer-motion";
import { Anchor, MapPin } from "lucide-react";

const ports = [
  { name: "Los Angeles", lat: 33.7, lng: -118.3, status: "active", shipments: 14 },
  { name: "Rotterdam", lat: 51.9, lng: 4.5, status: "active", shipments: 22 },
  { name: "Shanghai", lat: 31.2, lng: 121.5, status: "active", shipments: 31 },
  { name: "Singapore", lat: 1.3, lng: 103.8, status: "active", shipments: 18 },
  { name: "Dubai", lat: 25.3, lng: 55.3, status: "active", shipments: 9 },
  { name: "Felixstowe", lat: 51.9, lng: 1.3, status: "active", shipments: 7 },
  { name: "Tokyo", lat: 35.7, lng: 139.7, status: "active", shipments: 12 },
  { name: "Mumbai", lat: 19.1, lng: 72.9, status: "active", shipments: 10 },
];

// Convert lat/lng to rough SVG positions on a simplified world map
const toPos = (lat: number, lng: number) => ({
  x: ((lng + 180) / 360) * 100,
  y: ((90 - lat) / 180) * 100,
});

const PortOverviewMap = () => (
  <div className="rounded-xl border border-border bg-card shadow-card overflow-hidden hover:shadow-elevated transition-all duration-200">
    <div className="p-5 border-b border-border">
      <div className="flex items-center gap-2">
        <Anchor className="h-4 w-4 text-accent" />
        <h3 className="text-sm font-heading font-bold text-foreground">Global Port Overview</h3>
      </div>
      <p className="text-xs text-muted-foreground mt-1">Active ports with pre-arrival verification coverage.</p>
    </div>

    <div className="relative bg-[hsl(var(--navy-deep))] p-4" style={{ minHeight: 280 }}>
      {/* Grid lines */}
      <svg viewBox="0 0 100 50" className="w-full h-full absolute inset-0 opacity-10" preserveAspectRatio="none">
        {[10, 20, 30, 40].map(y => (
          <line key={`h${y}`} x1="0" y1={y} x2="100" y2={y} stroke="hsl(190 100% 50%)" strokeWidth="0.15" />
        ))}
        {[10, 20, 30, 40, 50, 60, 70, 80, 90].map(x => (
          <line key={`v${x}`} x1={x} y1="0" x2={x} y2="50" stroke="hsl(190 100% 50%)" strokeWidth="0.15" />
        ))}
      </svg>

      {/* Simplified continental outlines */}
      <svg viewBox="0 0 100 50" className="w-full h-full absolute inset-0" preserveAspectRatio="none">
        {/* North America */}
        <path d="M10,12 L25,10 L28,15 L30,20 L25,25 L18,28 L12,25 L8,18 Z" fill="hsl(213 40% 25%)" stroke="hsl(213 30% 35%)" strokeWidth="0.2" />
        {/* South America */}
        <path d="M22,28 L28,27 L30,32 L28,40 L24,44 L20,40 L19,34 Z" fill="hsl(213 40% 25%)" stroke="hsl(213 30% 35%)" strokeWidth="0.2" />
        {/* Europe */}
        <path d="M46,10 L54,9 L56,14 L52,18 L48,16 L45,13 Z" fill="hsl(213 40% 25%)" stroke="hsl(213 30% 35%)" strokeWidth="0.2" />
        {/* Africa */}
        <path d="M48,18 L56,17 L58,24 L56,34 L52,38 L48,35 L46,28 L47,22 Z" fill="hsl(213 40% 25%)" stroke="hsl(213 30% 35%)" strokeWidth="0.2" />
        {/* Asia */}
        <path d="M56,8 L80,6 L84,14 L82,22 L75,26 L68,24 L60,22 L56,16 Z" fill="hsl(213 40% 25%)" stroke="hsl(213 30% 35%)" strokeWidth="0.2" />
        {/* Australia */}
        <path d="M78,32 L86,30 L88,34 L86,38 L80,38 L78,36 Z" fill="hsl(213 40% 25%)" stroke="hsl(213 30% 35%)" strokeWidth="0.2" />
      </svg>

      {/* Port markers */}
      {ports.map((port, i) => {
        const pos = toPos(port.lat, port.lng);
        return (
          <motion.div
            key={port.name}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1, duration: 0.3 }}
            className="absolute group"
            style={{ left: `${pos.x}%`, top: `${pos.y}%`, transform: "translate(-50%, -50%)" }}
          >
            {/* Pulse ring */}
            <span className="absolute inset-0 rounded-full bg-accent/30 animate-ping" style={{ animationDuration: "3s" }} />
            <span className="relative flex h-3 w-3 items-center justify-center rounded-full bg-accent border border-accent/50 shadow-glow cursor-pointer" />

            {/* Tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-20">
              <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-elevated whitespace-nowrap">
                <div className="flex items-center gap-1.5">
                  <MapPin className="h-3 w-3 text-accent" />
                  <span className="text-xs font-heading font-bold text-foreground">{port.name}</span>
                </div>
                <div className="text-[10px] text-muted-foreground mt-0.5">{port.shipments} active shipments</div>
              </div>
            </div>
          </motion.div>
        );
      })}

      {/* Legend */}
      <div className="absolute bottom-3 right-3 flex items-center gap-3 bg-card/80 backdrop-blur-sm border border-border rounded-lg px-3 py-1.5">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-accent" />
          <span className="text-[10px] text-muted-foreground font-medium">Active Port</span>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground">{ports.length} ports</span>
      </div>
    </div>
  </div>
);

export default PortOverviewMap;
