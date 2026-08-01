import { type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import KanbanBoard from "../components/KanbanBoard";
import { STATUS_LABELS, STATUS_ORDER } from "../constants/application";
import type {
  Application,
  ApplicationStats,
  ApplicationStatus,
  JDItem,
  Reminders,
  ResumeItem,
} from "../types";

const EMPTY_STATS: ApplicationStats = {
  total: 0,
  status_counts: {},
  status_order: [],
  conversion_rate: {
    applied_to_interview: 0,
    interview_to_offer: 0,
  },
};

interface EditForm {
  status: string;
  applied_date: string;
  next_action: string;
  next_action_date: string;
  notes: string;
}

const ApplicationTracker: FC = () => {
  const [items, setItems] = useState<Application[]>([]);
  const [stats, setStats] = useState<ApplicationStats>(EMPTY_STATS);
  const [reminders, setReminders] = useState<Reminders | null>(null);
  const [jds, setJds] = useState<JDItem[]>([]);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);

  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [jdId, setJdId] = useState("");
  const [resumeId, setResumeId] = useState("");

  const [editing, setEditing] = useState<Application | null>(null);
  const [editForm, setEditForm] = useState<EditForm>({
    status: "saved",
    applied_date: "",
    next_action: "",
    next_action_date: "",
    notes: "",
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadAll = useCallback(async () => {
    try {
      const [appsRes, statsRes, remindRes, jdRes, resumeRes] = await Promise.all([
        api.applications.list(),
        api.applications.stats(),
        api.applications.reminders(),
        api.jd.list(),
        api.resume.list(),
      ]);
      if (appsRes.success && appsRes.data) setItems(appsRes.data);
      if (statsRes.success && statsRes.data) setStats(statsRes.data);
      if (remindRes.success && remindRes.data) setReminders(remindRes.data);
      if (jdRes.success && jdRes.data) setJds(jdRes.data);
      if (resumeRes.success && resumeRes.data) setResumes(resumeRes.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }, []);

  useEffect(() => {
    const initialLoad = async () => {
      await loadAll();
    };
    initialLoad();
  }, [loadAll]);

  const handleCreate = async () => {
    setError("");
    setMessage("");
    if (!company.trim() || !position.trim()) {
      setError("请填写公司和职位");
      return;
    }
    setSaving(true);
    try {
      const res = await api.applications.create(
        company.trim(),
        position.trim(),
        jdId || undefined,
        resumeId || undefined,
      );
      if (!res.success) {
        setError(res.error || "创建失败");
        return;
      }
      setCompany("");
      setPosition("");
      setJdId("");
      setResumeId("");
      setMessage("已添加投递记录");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (app: Application, status: ApplicationStatus) => {
    if (app.status === status) return;
    setError("");
    setMessage("");
    try {
      const res = await api.applications.updateStatus(app.id, status);
      if (res.success) {
        setMessage(`已更新为「${STATUS_LABELS[status]}」`);
        await loadAll();
      } else {
        setError(res.error || "更新失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  };

  const openEdit = (app: Application) => {
    setEditing(app);
    setEditForm({
      status: app.status,
      applied_date: app.applied_date || "",
      next_action: app.next_action || "",
      next_action_date: app.next_action_date || "",
      notes: app.notes || "",
    });
  };

  const handleSaveEdit = async () => {
    if (!editing) return;
    setError("");
    setMessage("");
    setSaving(true);
    try {
      const res = await api.applications.update(editing.id, {
        status: editForm.status,
        applied_date: editForm.applied_date || undefined,
        next_action: editForm.next_action || undefined,
        next_action_date: editForm.next_action_date || undefined,
        notes: editForm.notes || undefined,
      });
      if (res.success) {
        setEditing(null);
        setMessage("已保存");
        await loadAll();
      } else {
        setError(res.error || "保存失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (app: Application) => {
    if (!window.confirm(`确定删除 ${app.company} 的投递记录？`)) return;
    setError("");
    setMessage("");
    try {
      await api.applications.remove(app.id);
      setMessage("已删除");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  };

  const offerCount =
    (stats.status_counts.offered || 0) + (stats.status_counts.accepted || 0);
  const reminderCount =
    (reminders?.overdue_count || 0) + (reminders?.upcoming_count || 0);

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold mb-6">投递追踪</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-300">{error}</div>
      )}
      {message && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg border border-green-300">{message}</div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: "投递总数", value: stats.total, color: "text-blue-700" },
          { label: "Offer 数", value: offerCount, color: "text-green-700" },
          {
            label: "投递→面试",
            value: `${stats.conversion_rate.applied_to_interview}%`,
            color: "text-amber-700",
          },
          {
            label: "待跟进提醒",
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

      {reminders && reminders.has_reminders && (
        <div className="grid lg:grid-cols-2 gap-4 mb-6">
          <section className="bg-white border border-red-200 rounded-lg p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-red-700 mb-3">
              超期未跟进 ({reminders.overdue_count})
            </h2>
            {reminders.overdue.length === 0 ? (
              <p className="text-sm text-gray-400">暂无</p>
            ) : (
              <ul className="space-y-2">
                {reminders.overdue.map((item) => (
                  <li key={item.id} className="text-sm flex justify-between gap-3">
                    <span className="min-w-0 truncate">
                      {item.company} · {item.position}
                    </span>
                    <span className="text-red-500 flex-shrink-0">{item.days_since_update} 天</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="bg-white border border-blue-200 rounded-lg p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-blue-700 mb-3">
              即将到来的面试 ({reminders.upcoming_count})
            </h2>
            {reminders.upcoming.length === 0 ? (
              <p className="text-sm text-gray-400">暂无</p>
            ) : (
              <ul className="space-y-2">
                {reminders.upcoming.map((item) => (
                  <li key={item.id} className="text-sm flex justify-between gap-3">
                    <span className="min-w-0 truncate">
                      {item.company} · {item.position}
                      {item.next_action ? ` · ${item.next_action}` : ""}
                    </span>
                    <span className="text-gray-500 flex-shrink-0">{item.next_action_date}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}

      <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm mb-6">
        <h2 className="text-lg font-semibold mb-4">添加投递记录</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="公司名称"
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="公司名称"
          />
          <input
            value={position}
            onChange={(e) => setPosition(e.target.value)}
            placeholder="职位"
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="职位"
          />
          <select
            value={jdId}
            onChange={(e) => setJdId(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg bg-white"
            aria-label="关联 JD"
          >
            <option value="">关联 JD（可选）</option>
            {jds.map((jd) => (
              <option key={jd.id} value={jd.id}>
                {jd.company || "未知公司"} · {jd.position || "未知职位"}
              </option>
            ))}
          </select>
          <select
            value={resumeId}
            onChange={(e) => setResumeId(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg bg-white"
            aria-label="关联简历"
          >
            <option value="">关联简历（可选）</option>
            {resumes.map((resume) => (
              <option key={resume.id} value={resume.id}>
                {resume.source_file || "手动输入"}
              </option>
            ))}
          </select>
          <button
            onClick={handleCreate}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
          >
            添加
          </button>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">进度看板</h2>
        <KanbanBoard
          items={items}
          onStatusChange={handleStatusChange}
          onEdit={openEdit}
          onDelete={handleDelete}
        />
      </section>

      {editing && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-lg p-5 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">编辑投递记录</h2>
              <button
                onClick={() => setEditing(null)}
                className="text-gray-400 hover:text-gray-600"
                aria-label="关闭"
              >
                ✕
              </button>
            </div>
            <div className="mb-3 text-sm text-gray-600">
              {editing.company} · {editing.position}
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">状态</label>
                <select
                  value={editForm.status}
                  onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg bg-white"
                >
                  {STATUS_ORDER.map((status) => (
                    <option key={status} value={status}>{STATUS_LABELS[status]}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">投递日期</label>
                <input
                  type="date"
                  value={editForm.applied_date}
                  onChange={(e) => setEditForm({ ...editForm, applied_date: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">下一步行动</label>
                <input
                  value={editForm.next_action}
                  onChange={(e) => setEditForm({ ...editForm, next_action: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                  placeholder="例如：准备技术面"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">提醒日期</label>
                <input
                  type="date"
                  value={editForm.next_action_date}
                  onChange={(e) => setEditForm({ ...editForm, next_action_date: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">备注</label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  className="w-full h-24 p-2 border border-gray-300 rounded-lg resize-none"
                />
              </div>
            </div>
            <div className="mt-5 flex justify-end gap-3">
              <button
                onClick={() => setEditing(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50"
              >
                取消
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationTracker;
