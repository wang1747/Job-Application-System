import { type FC } from "react";

interface ResumeDiffProps {
  original?: string;
  optimized?: string;
  changes?: string[];
}

const ResumeDiff: FC<ResumeDiffProps> = ({ original, optimized, changes }) => {
  if (!original && !optimized) {
    return <div style={{ color: "#999", padding: 16 }}>暂无对比数据</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {changes && changes.length > 0 && (
        <div>
          <h4 style={{ margin: "0 0 8px", color: "#333" }}>改动项</h4>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {changes.map((c, i) => (
              <li key={i} style={{ fontSize: 13, color: "#555", marginBottom: 4 }}>{c}</li>
            ))}
          </ul>
        </div>
      )}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {original && (
          <div>
            <h4 style={{ margin: "0 0 8px", color: "#ef4444" }}>优化前</h4>
            <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", background: "#fef2f2", padding: 12, borderRadius: 6, margin: 0 }}>{original}</pre>
          </div>
        )}
        {optimized && (
          <div>
            <h4 style={{ margin: "0 0 8px", color: "#22c55e" }}>优化后</h4>
            <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", background: "#f0fdf4", padding: 12, borderRadius: 6, margin: 0 }}>{optimized}</pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeDiff;
