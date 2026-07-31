import { type FC } from "react";
import type { MatchResult } from "../types";

interface MatchCardProps {
  result: MatchResult;
}

const MatchCard: FC<MatchCardProps> = ({ result }) => {
  const color = result.score >= 80 ? "#22c55e" : result.score >= 60 ? "#eab308" : "#ef4444";
  return (
    <div style={{
      background: "#fff",
      borderRadius: 8,
      padding: 16,
      boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      display: "flex",
      alignItems: "center",
      gap: 16,
    }}>
      <div style={{
        width: 56,
        height: 56,
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 18,
        fontWeight: "bold",
        color: "#fff",
        background: color,
      }}>
        {result.score}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: "#333", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {result.company || `JD ${result.jd_id.slice(0, 8)}`}
        </div>
        {result.position && (
          <div style={{ fontSize: 12, color: "#666", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {result.position}
          </div>
        )}
        {result.suggestion && (
          <div style={{ fontSize: 12, color: "#999", marginTop: 4, lineHeight: 1.4 }}>{result.suggestion}</div>
        )}
      </div>
    </div>
  );
};

export default MatchCard;
