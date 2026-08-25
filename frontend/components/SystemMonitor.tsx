"use client";

import { useEffect, useState } from "react";

interface SystemStats {
  gpu_utilization?: number;
  gpu_memory_used?: number;
  gpu_memory_total?: number;
  ram_used: number;
  ram_total: number;
  cpu_percent: number;
}

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function SystemMonitor() {
  const [stats, setStats] = useState<SystemStats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${API}/api/system`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch {
        // ignore
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) {
    return (
      <div className="text-xs text-[var(--text-tertiary)]">System stats unavailable</div>
    );
  }

  const ramPercentage = stats.ram_total > 0 ? (stats.ram_used / stats.ram_total) * 100 : 0;

  return (
    <div className="flex items-center gap-3 text-xs text-[var(--text-tertiary)]">
      <span>CPU: {stats.cpu_percent?.toFixed(0) ?? "?"}%</span>
      <span>
        RAM: {ramPercentage.toFixed(0)}% (
        {(stats.ram_used / 1024 / 1024 / 1024).toFixed(1)}GB /{" "}
        {(stats.ram_total / 1024 / 1024 / 1024).toFixed(1)}GB)
      </span>
      {stats.gpu_utilization !== undefined && (
        <span>GPU: {stats.gpu_utilization.toFixed(0)}%</span>
      )}
      {stats.gpu_memory_used !== undefined && stats.gpu_memory_total !== undefined && (
        <span>
          VRAM: {stats.gpu_memory_used.toFixed(0)}MB /{" "}
          {stats.gpu_memory_total.toFixed(0)}MB
        </span>
      )}
    </div>
  );
}
