import { type FC, useEffect, useState } from "react";
import { api } from "../api/client";
import KanbanBoard from "../components/KanbanBoard";
import type { Application } from "../types";

const ApplicationTracker: FC = () => {
  const [items, setItems] = useState<Application[]>([]);

  useEffect(() => {
    api.applications.list().then((res) => {
      if (res.success && res.data) setItems(res.data);
    });
  }, []);

  return (
    <div>
      <h1 style={{ fontSize: 24, fontWeight: 600, margin: "0 0 24px" }}>投递追踪</h1>
      <div style={{
        background: "#fff",
        borderRadius: 8,
        padding: 20,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}>
        <KanbanBoard items={items} />
      </div>
    </div>
  );
};

export default ApplicationTracker;
