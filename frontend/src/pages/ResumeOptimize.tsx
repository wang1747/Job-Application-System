import { type FC } from "react";

const ResumeOptimize: FC = () => {
  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 24px" }}>简历优化</h1>
      <div style={{
        background: "#fff",
        borderRadius: 8,
        padding: 40,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        textAlign: "center",
        color: "#999",
      }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>📄</div>
        <p style={{ fontSize: 16, margin: 0 }}>简历优化功能即将上线</p>
        <p style={{ fontSize: 13, margin: "8px 0 0", color: "#bbb" }}>支持上传 PDF / Markdown 简历，针对目标 JD 生成优化建议</p>
      </div>
    </div>
  );
};

export default ResumeOptimize;
