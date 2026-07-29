import { type FC, useEffect, useState } from "react";
import { api } from "../api/client";

const Dashboard: FC = () => {
  const [health, setHealth] = useState<string>("检查中...");

  useEffect(() => {
    api.health().then((res) => {
      setHealth(res.data?.status || "未连接");
    }).catch(() => setHealth("连接失败"));
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 24px" }}>总览</h1>
      <div style={{
        background: "#fff",
        borderRadius: 8,
        padding: 24,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}>
        <div style={{ fontSize: 14, color: "#666", marginBottom: 8 }}>服务状态</div>
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          padding: "4px 12px",
          borderRadius: 20,
          fontSize: 14,
          background: health === "ok" ? "#dcfce7" : "#fef2f2",
          color: health === "ok" ? "#16a34a" : "#dc2626",
        }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: health === "ok" ? "#22c55e" : "#ef4444", display: "inline-block" }} />
          {health === "ok" ? "运行中" : health}
        </div>
      </div>
      <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        {[
          { label: "JD 解析", desc: "粘贴 JD 文本，AI 自动解析结构化信息", color: "#3b82f6" },
          { label: "简历优化", desc: "针对目标 JD 优化简历内容", color: "#22c55e" },
          { label: "面试准备", desc: "基于面经生成面试题", color: "#eab308" },
          { label: "投递追踪", desc: "看板式管理求职进度", color: "#e94560" },
        ].map((card) => (
          <div key={card.label} style={{
            background: "#fff",
            borderRadius: 8,
            padding: 20,
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
          }}>
            <div style={{ width: 40, height: 40, borderRadius: 8, background: card.color, marginBottom: 12 }} />
            <h3 style={{ margin: "0 0 8px", fontSize: 16 }}>{card.label}</h3>
            <p style={{ margin: 0, fontSize: 13, color: "#666", lineHeight: 1.5 }}>{card.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;
