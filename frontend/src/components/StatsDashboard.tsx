import { useCallback, useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { api } from "../api/client";

interface StatsData {
  total: number;
  status_counts: Record<string, number>;
  status_order: string[];
  conversion_rate: {
    applied_to_interview: number;
    interview_to_offer: number;
  };
}

const STATUS_LABELS: Record<string, string> = {
  saved: "收藏",
  applied: "已投递",
  online_test: "笔试",
  first_interview: "一面",
  second_interview: "二面",
  hr_round: "HR面",
  offered: "Offer",
  accepted: "已接受",
  rejected: "已拒绝",
};

const STATUS_COLORS: Record<string, string> = {
  saved: "#9ca3af",
  applied: "#3b82f6",
  online_test: "#8b5cf6",
  first_interview: "#06b6d4",
  second_interview: "#22c55e",
  hr_round: "#eab308",
  offered: "#f97316",
  accepted: "#22c55e",
  rejected: "#ef4444",
};

export default function StatsDashboard() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    try {
      const resp = await api.applications.stats();
      if (resp.success && resp.data) {
        setStats(resp.data);
      } else {
        setError(resp.error || "加载失败");
      }
    } catch (err) {
      console.error("加载统计失败:", err);
      setError("加载统计失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadStats();
    }, 0);
    return () => clearTimeout(timer);
  }, [loadStats]);

  if (loading) {
    return (
      <div className="p-6 text-center text-gray-400">
        <div className="animate-pulse">加载统计中...</div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-6 text-center text-red-500">
        ⚠️ {error || "暂无数据"}
      </div>
    );
  }

  // 准备状态分布数据
  const statusData = stats.status_order
    .filter((key) => stats.status_counts[key] > 0)
    .map((key) => ({
      name: STATUS_LABELS[key] || key,
      value: stats.status_counts[key],
      color: STATUS_COLORS[key] || "#9ca3af",
    }));

  // 准备漏斗数据（按流程顺序）
  const funnelSteps = ["saved", "applied", "online_test", "first_interview", "second_interview", "hr_round", "offered"];
  const funnelData = funnelSteps
    .filter((key) => stats.status_counts[key] > 0)
    .map((key) => ({
      name: STATUS_LABELS[key] || key,
      value: stats.status_counts[key],
      color: STATUS_COLORS[key] || "#9ca3af",
    }));

  return (
    <div className="p-4 space-y-6">
      <h2 className="text-xl font-bold">📊 投递统计看板</h2>

      {/* 概览卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">总投递</div>
          <div className="text-2xl font-bold">{stats.total}</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">面试转化率</div>
          <div className="text-2xl font-bold text-blue-600">
            {stats.conversion_rate.applied_to_interview}%
          </div>
          <div className="text-xs text-gray-400">投递 → 一面</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">Offer转化率</div>
          <div className="text-2xl font-bold text-green-600">
            {stats.conversion_rate.interview_to_offer}%
          </div>
          <div className="text-xs text-gray-400">一面 → Offer</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="text-sm text-gray-500">已接受</div>
          <div className="text-2xl font-bold text-green-600">
            {stats.status_counts.accepted || 0}
          </div>
        </div>
      </div>

      {/* 图表区 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 漏斗图 */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-sm font-semibold mb-4">📈 投递漏斗</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={funnelData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="name" width={60} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={4}>
                {funnelData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 饼图 */}
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <h3 className="text-sm font-semibold mb-4">📊 状态分布</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent = 0 }) =>
                  `${name} ${(percent * 100).toFixed(0)}%`
                }
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
