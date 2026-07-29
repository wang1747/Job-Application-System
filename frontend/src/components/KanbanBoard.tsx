import { type FC } from "react";
import type { Application, ApplicationStatus } from "../types";

const STATUS_LABELS: Record<string, string> = {
  saved: "已收藏",
  applied: "已投递",
  online_test: "笔试",
  first_interview: "一面",
  second_interview: "二面",
  hr_round: "HR 面",
  offered: "Offer",
  accepted: "已接受",
  rejected: "已拒绝",
};

const STATUS_ORDER: ApplicationStatus[] = [
  "saved", "applied", "online_test", "first_interview",
  "second_interview", "hr_round", "offered", "accepted", "rejected",
];

interface KanbanBoardProps {
  items: Application[];
}

const KanbanBoard: FC<KanbanBoardProps> = ({ items }) => {
  const grouped = STATUS_ORDER.reduce((acc, status) => {
    acc[status] = items.filter((item) => item.status === status);
    return acc;
  }, {} as Record<string, Application[]>);

  return (
    <div style={{ display: "flex", gap: 12, overflow: "auto", minHeight: 400 }}>
      {STATUS_ORDER.map((status) => (
        <div key={status} style={{ minWidth: 180, flex: 1 }}>
          <h3 style={{
            fontSize: 13,
            color: "#555",
            margin: "0 0 8px",
            padding: "8px 12px",
            background: "#e5e7eb",
            borderRadius: 6,
            textAlign: "center",
          }}>
            {STATUS_LABELS[status]} ({grouped[status]?.length || 0})
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(grouped[status] || []).map((app) => (
              <div key={app.id} style={{
                background: "#fff",
                borderRadius: 6,
                padding: 12,
                boxShadow: "0 1px 2px rgba(0,0,0,0.08)",
              }}>
                <div style={{ fontWeight: 500, fontSize: 14 }}>{app.company}</div>
                <div style={{ fontSize: 12, color: "#666" }}>{app.position}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default KanbanBoard;
