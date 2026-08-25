"use client";

import { useEffect, useState } from "react";

export function TokenMonitor() {
  const [tokenCount, setTokenCount] = useState(0);
  const [contextLimit] = useState(32768);

  useEffect(() => {
    const interval = setInterval(() => {
      const chars = document.body.innerText.length;
      setTokenCount(Math.floor(chars / 4));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const percentage = Math.min((tokenCount / contextLimit) * 100, 100);
  const color =
    percentage > 90
      ? "text-red-500"
      : percentage > 70
      ? "text-yellow-500"
      : "text-green-500";

  return (
    <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
      <div className="w-20 h-1.5 rounded-full bg-[var(--surface-tertiary)] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color.replace("text-", "bg-")}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={color}>
        {tokenCount.toLocaleString()} / {contextLimit.toLocaleString()}
      </span>
    </div>
  );
}
