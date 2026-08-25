"use client";

import { useUIStore } from "@/store/ui";
import { useWebSocket } from "@/hooks/useWebSocket";

export function ApprovalModal() {
  const approvalPending = useUIStore((s) => s.approvalPending);
  const setApprovalPending = useUIStore((s) => s.setApprovalPending);
  const { sendApproval } = useWebSocket();

  if (!approvalPending) return null;

  const handleApprove = () => {
    sendApproval(true);
    setApprovalPending(null);
  };

  const handleReject = () => {
    sendApproval(false);
    setApprovalPending(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-[420px] rounded-xl bg-[var(--surface)] border border-[var(--border)] shadow-2xl overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--border)]">
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">
            Approval Required
          </h3>
        </div>

        <div className="p-4 space-y-3">
          <div>
            <span className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">
              Tool
            </span>
            <p className="text-sm font-mono text-[var(--accent)] mt-0.5">
              {approvalPending.tool}
            </p>
          </div>

          <div>
            <span className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">
              Description
            </span>
            <p className="text-sm text-[var(--text-primary)] mt-0.5">
              {approvalPending.description || "No description"}
            </p>
          </div>

          <div>
            <span className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider">
              Arguments
            </span>
            <pre className="mt-0.5 p-2 rounded text-xs font-mono bg-[var(--surface-secondary)] text-[var(--text-primary)] overflow-x-auto max-h-32 overflow-y-auto">
              {JSON.stringify(approvalPending.args, null, 2)}
            </pre>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-[var(--border)] bg-[var(--surface-secondary)]">
          <button onClick={handleReject} className="btn">
            Reject
          </button>
          <button onClick={handleApprove} className="btn-primary">
            Approve
          </button>
        </div>
      </div>
    </div>
  );
}
