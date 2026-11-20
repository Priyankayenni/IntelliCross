/**
 * IntelliCross - Header Component
 * ===============================
 * Strict typographic hierarchy: "IntelliCross" remains the largest
 * text element on screen. Glassmorphic styling.
 */

export default function Header() {
  return (
    <header className="p-2 sm:p-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight text-white">
            IntelliCross
          </h1>
          <p className="text-base sm:text-lg text-slate-400 mt-1.5 max-w-xl">
            Metropolitan-Scale Intelligent Traffic Orchestration for Unconstrained Indian Roads
          </p>
        </div>
        
        <div className="flex items-center gap-4 text-right sm:text-left">
          <div className="hidden sm:block text-sm">
            <p className="text-slate-500">System Status</p>
            <p className="font-mono text-sky-400 text-lg">OPERATIONAL</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900/60 border border-slate-700/50 rounded-full">
            <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
            <span className="text-xs font-medium text-slate-300 font-mono">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
}