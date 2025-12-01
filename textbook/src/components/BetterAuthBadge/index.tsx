/**
 * Better Auth Badge Component
 * Displays a badge showing Better Auth is being used
 */

import React from "react";

export function BetterAuthBadge(): React.ReactElement {
  return (
    <div
      style={{
        position: "fixed",
        bottom: "20px",
        right: "20px",
        zIndex: 1000,
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        color: "white",
        padding: "8px 16px",
        borderRadius: "20px",
        fontSize: "12px",
        fontWeight: 600,
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        display: "flex",
        alignItems: "center",
        gap: "8px",
      }}
    >
      <span>🔐</span>
      <span>Powered by Better Auth</span>
    </div>
  );
}

export default BetterAuthBadge;
