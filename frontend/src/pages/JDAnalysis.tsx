import { type FC, useState, type FormEvent } from "react";
import { api } from "../api/client";
import type { JDParseResult, JDItem } from "../types";

const JDAnalysis: FC = () => {
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<JDParseResult | null>(null);
  const [list, setList] = useState<JDItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!rawText.trim()) return;
    setLoading(true);
    setError(null);
    const res = await api.jd.parse(rawText);
    if (res.success && res.data) {
      setResult(res.data.parsed);
      loadList();
    } else {
      setError(res.error || "解析失败");
    }
    setLoading(false);
  };

  const loadList = async () => {
    const res = await api.jd.list();
    if (res.success && res.data) setList(res.data);
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 24px" }}>JD 解析</h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <textarea
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder="粘贴 JD 文本..."
          rows={6}
          style={{
            width: "100%",
            padding: 12,
            borderRadius: 8,
            border: "1px solid #d1d5db",
            fontSize: 14,
            resize: "vertical",
            boxSizing: "border-box",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: 12,
            padding: "10px 24px",
            background: "#3b82f6",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontSize: 14,
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "解析中..." : "解析"}
        </button>
      </form>

      {error && (
        <div style={{ color: "#dc2626", fontSize: 14, marginBottom: 16 }}>{error}</div>
      )}

      {result && (
        <div style={{ background: "#fff", borderRadius: 8, padding: 20, boxShadow: "0 1px 3px rgba(0,0,0,0.1)", marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, margin: "0 0 16px" }}>解析结果</h2>
          {result.company && <div style={{ marginBottom: 8 }}><strong>公司：</strong>{result.company}</div>}
          {result.position && <div style={{ marginBottom: 8 }}><strong>岗位：</strong>{result.position}</div>}
          {result.must_have.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <strong>硬性要求：</strong>
              <ul style={{ margin: "4px 0 0", paddingLeft: 20 }}>
                {result.must_have.map((item, i) => <li key={i} style={{ fontSize: 13 }}>{item}</li>)}
              </ul>
            </div>
          )}
          {result.tech_stack && Object.entries(result.tech_stack).filter(([, v]) => v.length > 0).length > 0 && (
            <div>
              <strong>技术栈：</strong>
              {Object.entries(result.tech_stack).map(([k, v]) =>
                v.length > 0 ? (
                  <div key={k} style={{ fontSize: 13, marginTop: 4 }}>
                    {k}: {v.join(", ")}
                  </div>
                ) : null
              )}
            </div>
          )}
        </div>
      )}

      <div>
        <h2 style={{ fontSize: 18, margin: "0 0 12px" }}>历史记录</h2>
        {list.length === 0 ? (
          <div style={{ color: "#999", fontSize: 14 }}>暂无记录</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {list.map((item) => (
              <div key={item.id} style={{
                background: "#fff",
                borderRadius: 8,
                padding: "12px 16px",
                boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}>
                <div>
                  <strong>{item.company || "未知公司"}</strong> - {item.position || "未知岗位"}
                </div>
                <button
                  onClick={() => api.jd.delete(item.id).then(loadList)}
                  style={{
                    padding: "4px 12px",
                    background: "#fee2e2",
                    color: "#dc2626",
                    border: "none",
                    borderRadius: 4,
                    cursor: "pointer",
                    fontSize: 12,
                  }}
                >
                  删除
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default JDAnalysis;
