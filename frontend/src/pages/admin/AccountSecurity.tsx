import { useState } from "react";
import { api } from "../../api/client";
import { Card } from "../../components/ui";

const inputCls =
  "w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500";
const btnPrimary =
  "rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-50";

export default function AccountSecurity() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    setError("");
    setMessage("");

    if (!oldPassword) {
      setError("请输入当前密码");
      return;
    }
    if (newPassword.length < 6) {
      setError("新密码至少 6 位");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("两次输入的新密码不一致");
      return;
    }

    setSaving(true);
    try {
      await api.auth.changePassword(oldPassword, newPassword);
      setMessage("密码已修改，下次登录请使用新密码");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="max-w-xl p-6">
      <h3 className="text-base font-semibold text-slate-900">修改登录密码</h3>
      <p className="mt-1 text-sm text-slate-500">
        密码经 bcrypt 加密存储，不会以明文保存。修改后当前会话仍有效，下次登录需使用新密码。
      </p>

      {error && (
        <div className="mt-4 flex items-center justify-between rounded-lg bg-rose-50 px-4 py-2 text-sm text-rose-600">
          <span>{error}</span>
          <button className="text-rose-400 hover:text-rose-600" onClick={() => setError("")}>×</button>
        </div>
      )}
      {message && (
        <div className="mt-4 flex items-center justify-between rounded-lg bg-emerald-50 px-4 py-2 text-sm text-emerald-600">
          <span>{message}</span>
          <button className="text-emerald-400 hover:text-emerald-600" onClick={() => setMessage("")}>×</button>
        </div>
      )}

      <div className="mt-5 space-y-4">
        <div>
          <label className="mb-1 block text-sm text-slate-600">当前密码</label>
          <input
            type="password"
            className={inputCls}
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            autoComplete="current-password"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-600">新密码（至少 6 位）</label>
          <input
            type="password"
            className={inputCls}
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            autoComplete="new-password"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm text-slate-600">确认新密码</label>
          <input
            type="password"
            className={inputCls}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
          />
        </div>
        <button className={btnPrimary} onClick={submit} disabled={saving}>
          {saving ? "保存中…" : "修改密码"}
        </button>
      </div>
    </Card>
  );
}
