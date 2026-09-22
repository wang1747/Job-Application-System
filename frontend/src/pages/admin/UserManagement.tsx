import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import type { AdminUser } from "../../types";
import { Card, EmptyState, Loading } from "../../components/ui";

export default function UserManagement() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.admin.listUsers();
      if (res.success && res.data) setUsers(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadUsers();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadUsers]);

  const handleRole = async (user: AdminUser, role: "admin" | "user") => {
    setError("");
    setMessage("");
    try {
      const res = await api.admin.updateRole(user.id, role);
      if (res.success) {
        setMessage(`${user.name} 角色已更新为 ${role}`);
        await loadUsers();
      } else {
        setError(res.error || "更新失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  };

  const handleActive = async (user: AdminUser, is_active: boolean) => {
    setError("");
    setMessage("");
    try {
      const res = await api.admin.updateActive(user.id, is_active);
      if (res.success) {
        setMessage(`${user.name} 已${is_active ? "激活" : "禁用"}`);
        await loadUsers();
      } else {
        setError(res.error || "更新失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新失败");
    }
  };

  return (
    <div>
      {/* 统计卡片 */}
      <div className="mb-4 grid grid-cols-3 gap-3">
        <div className="of-card p-4 text-center">
          <p className="text-xs font-medium text-slate-500">总用户</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{users.length}</p>
        </div>
        <div className="of-card p-4 text-center">
          <p className="text-xs font-medium text-slate-500">管理员</p>
          <p className="mt-1 text-2xl font-bold text-brand-600">{users.filter((u) => u.role === "admin").length}</p>
        </div>
        <div className="of-card p-4 text-center">
          <p className="text-xs font-medium text-slate-500">已禁用</p>
          <p className="mt-1 text-2xl font-bold text-rose-500">{users.filter((u) => !u.is_active).length}</p>
        </div>
      </div>

      {error && (
        <div className="of-alert-error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 flex-shrink-0">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4M12 16h.01" />
          </svg>
          {error}
        </div>
      )}
      {message && (
        <div className="of-alert-success">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mt-0.5 flex-shrink-0">
            <path d="M20 6L9 17l-5-5" />
          </svg>
          {message}
        </div>
      )}

      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm text-slate-500">共 {users.length} 个账号</span>
        <button onClick={loadUsers} className="of-btn-ghost" disabled={loading}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <path d="M23 4v6h-6" />
            <path d="M1 20v-6h6" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          刷新
        </button>
      </div>

      <Card className="overflow-hidden p-0">
        {loading ? (
          <Loading text="加载用户列表..." />
        ) : users.length === 0 ? (
          <div className="p-6">
            <EmptyState title="暂无用户" description="还没有用户注册" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/80 text-slate-500">
                  <th className="px-5 py-3 font-medium">用户</th>
                  <th className="px-5 py-3 font-medium">角色</th>
                  <th className="px-5 py-3 font-medium">状态</th>
                  <th className="px-5 py-3 font-medium">注册时间</th>
                  <th className="px-5 py-3 text-right font-medium">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {users.map((user) => (
                  <tr key={user.id} className="transition hover:bg-slate-50/50">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-3">
                        <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${
                          user.role === "admin"
                            ? "bg-brand-100 text-brand-700"
                            : "bg-slate-100 text-slate-500"
                        }`}>
                          {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <span className="block font-medium text-slate-900">{user.name}</span>
                          {user.email && (
                            <span className="block truncate text-xs text-slate-400">
                              {user.email}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      <select
                        value={user.role}
                        onChange={(e) => handleRole(user, e.target.value as "admin" | "user")}
                        className="cursor-pointer rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 outline-none transition hover:border-brand-400 focus:border-brand-500"
                      >
                        <option value="user">user</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td className="px-5 py-3.5">
                      <button
                        onClick={() => handleActive(user, !user.is_active)}
                        className={`of-badge cursor-pointer transition ${
                          user.is_active
                            ? "bg-emerald-50 text-emerald-600 hover:bg-emerald-100"
                            : "bg-rose-50 text-rose-600 hover:bg-rose-100"
                        }`}
                      >
                        <span className={`h-1.5 w-1.5 rounded-full ${user.is_active ? "bg-emerald-500" : "bg-rose-500"}`} />
                        {user.is_active ? "正常" : "禁用"}
                      </button>
                    </td>
                    <td className="px-5 py-3.5 text-slate-500">
                      {new Date(user.created_at).toLocaleDateString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit" })}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <span className="text-xs text-slate-300">修改即保存</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
