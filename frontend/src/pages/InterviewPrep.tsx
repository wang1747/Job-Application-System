import { type FC } from "react";

const InterviewPrep: FC = () => {
  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 24px" }}>面试准备</h1>
      <div style={{
        background: "#fff",
        borderRadius: 8,
        padding: 40,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        textAlign: "center",
        color: "#999",
      }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
        <p style={{ fontSize: 16, margin: 0 }}>面试准备功能即将上线</p>
        <p style={{ fontSize: 13, margin: "8px 0 0", color: "#bbb" }}>导入面经，基于简历和 JD 生成面试题，模拟面试练习</p>
      </div>
    </div>
  );
};

export default InterviewPrep;
