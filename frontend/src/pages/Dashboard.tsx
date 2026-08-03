import { type FC, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { STATUS_LABELS } from "../constants/application";
import type { Application, ApplicationStats, MatchResult, Reminders, User } from "../types";

const formatDate = (iso?: string) => {
  if (!iso) return "-";
  const d = new Date(iso);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

const Dashboard: FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState("检查中...");
  const [apps, setApps] = useState<Application[]>([]);
  const [stats, setStats] = useState<ApplicationStats | null>(null);
  const [reminders, setReminders] = useState<Reminders | null>(null);
  const [rankings, setRankings] = useState<MatchResult[]>([]);

  const loadAll = useCallback(async () => {
    try {
      const [userRes, appsRes, statsRes, remindRes, rankRes] = await Promise.all([
        api.auth.me(),
        api.applications.list(),
        api.applications.stats(),
        api.applications.reminders(),
        api.match.rankings(),
      ]);
      if (userRes.success && userRes.data) setUser(userRes.data);
      if (appsRes.success && appsRes.data) setApps(appsRes.data);
      if (statsRes.success && statsRes.data) setStats(statsRes.data);
      if (remindRes.success && remindRes.data) setReminders(remindRes.data);
      if (rankRes.success && rankRes.data) setRankings(rankRes.data);
    } catch {
      // 后端未启动时总览仍可展示部分状态
    }
  }, []);

  const checkModelConfig = useCallback(async () => {
    try {
      const res = await api.modelConfig.get();
      if (res.success && res.data) {
        if (!res.data.has_config) {
          navigate("/settings");
        }
      }
    } catch (err) {
      console.error("检查模型配置失败:", err);
    }
  }, [navigate]);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const checkHealth = async () => {
      try {
        const res = await api.health();
        if (cancelled) return;
        setHealth(res.data?.status || "未连接");
        if (res.data?.status === "ok") {
          await loadAll();
          await checkModelConfig();
        } else {
          timer = setTimeout(checkHealth, 3000);
        }
      } catch {
        if (cancelled) return;
        setHealth("连接失败");
        timer = setTimeout(checkHealth, 3000);
      }
    };

    checkHealth();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [loadAll, checkModelConfig]);

  const offerCount =
    (stats?.status_counts.offered || 0) + (stats?.status_counts.accepted || 0);
  const reminderCount =
    (reminders?.overdue_count || 0) + (reminders?.upcoming_count || 0);
  const topScore = rankings[0]?.score ?? 0;

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">👋 欢迎回来{user ? `，${user.name}` : ""}！</h1>
          <p className="text-gray-500 text-sm mt-1">这是你的求职仪表盘，快速了解整体进展。</p>
        </div>
        <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
          health === "ok" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
        }`}>
          <span className={`w-2 h-2 rounded-full ${health === "ok" ? "bg-green-500" : "bg-red-500"}`} />
          {health === "ok" ? "运行中" : health}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: "投递总数", value: stats?.total ?? 0, color: "text-blue-700" },
          { label: "Offer 数", value: offerCount, color: "text-green-700" },
          {
            label: "投递→面试",
            value: stats ? `${stats.conversion_rate.applied_to_interview}%` : "-",
            color: "text-amber-700",
          },
          {
            label: "待跟进",
            value: reminderCount,
            color: reminderCount > 0 ? "text-red-700" : "text-gray-700",
          },
        ].map((item) => (
          <div key={item.label} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
            <div className="text-xs text-gray-500">{item.label}</div>
            <div className={`text-2xl font-bold mt-1 ${item.color}`}>{item.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">最近投递</h2>
          {apps.length === 0 ? (
            <p className="text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg p-6 text-center">
              暂无投递记录
            </p>
          ) : (
            <div className="space-y-2">
              {apps.slice(0, 6).map((app) => (
                <div key={app.id} className="flex items-center justify-between gap-3 p-3 bg-gray-50 rounded-lg text-sm">
                  <div className="min-w-0">
                    <div className="font-medium truncate">{app.company} · {app.position}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{formatDate(app.updated_at)}</div>
                  </div>
                  <span className="text-xs px-2 py-1 bg-white border border-gray-200 rounded flex-shrink-0">
                    {STATUS_LABELS[app.status] || app.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">提醒</h2>
          {reminders && reminders.has_reminders ? (
            <div className="space-y-4">
              <div>
                <div className="text-sm font-medium text-red-700 mb-2">
                  超期未跟进 ({reminders.overdue_count})
                </div>
                <ul className="space-y-1.5">
                  {reminders.overdue.slice(0, 4).map((item) => (
                    <li key={item.id} className="text-sm flex justify-between gap-3">
                      <span className="min-w-0 truncate">{item.company} · {item.position}</span>
                      <span className="text-red-500 flex-shrink-0">{item.days_since_update} 天</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="text-sm font-medium text-blue-700 mb-2">
                  即将到来 ({reminders.upcoming_count})
                </div>
                <ul className="space-y-1.5">
                  {reminders.upcoming.slice(0, 4).map((item) => (
                    <li key={item.id} className="text-sm flex justify-between gap-3">
                      <span className="min-w-0 truncate">{item.company} · {item.position}</span>
                      <span className="text-gray-500 flex-shrink-0">{item.next_action_date}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg p-6 text-center">
              暂无提醒
            </p>
          )}
        </section>
      </div>

      {rankings.length > 0 && (
        <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm mt-6">
          <h2 className="text-lg font-semibold mb-4">匹配速览</h2>
          <div className="space-y-2">
            {rankings.slice(0, 4).map((item) => (
              <div key={item.id || `${item.jd_id}-${item.resume_id}`} className="flex items-center justify-between gap-3 p-3 bg-gray-50 rounded-lg text-sm">
                <div className="min-w-0">
                  <div className="font-medium truncate">
                    {item.company || "未知公司"} · {item.position || "未知职位"}
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5">{item.suggestion}</div>
                </div>
                <span className={`text-sm font-bold flex-shrink-0 ${
                  item.score >= 80 ? "text-green-600" : item.score >= 60 ? "text-amber-600" : "text-red-600"
                }`}>
                  {item.score}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {topScore > 0 && (
        <p className="mt-4 text-xs text-gray-400">最高匹配分：{topScore}</p>
      )}
    </div>
  );
};

export default Dashboard;