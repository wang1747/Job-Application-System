import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { api } from "../api/client";

interface PresetProvider {
  key: string;
  base_url: string;
  model: string;
}

interface ModelConfig {
  provider: string;
  base_url: string;
  model: string;
  api_key_masked: string;
  has_config: boolean;
}

export default function ModelSettings() {
  const { token } = useAuthStore();
  const navigate = useNavigate();

  const [presets, setPresets] = useState<PresetProvider[]>([]);
  const [config, setConfig] = useState<ModelConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  const [selectedProvider, setSelectedProvider] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [apiKey, setApiKey] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [testResult, setTestResult] = useState<{ success: boolean; message?: string } | null>(null);

  const loadData = async () => {
    try {
      const [presetsRes, configRes] = await Promise.allSettled([
        api.modelConfig.presets(),
        api.modelConfig.get(),
      ]);
      if (presetsRes.status === "fulfilled" && presetsRes.value.success && presetsRes.value.data) {
        setPresets(presetsRes.value.data);
      }
      if (configRes.status === "fulfilled" && configRes.value.success && configRes.value.data) {
        setConfig(configRes.value.data);
        if (configRes.value.data.has_config) {
          setSelectedProvider(configRes.value.data.provider);
          setBaseUrl(configRes.value.data.base_url);
          setModel(configRes.value.data.model);
        }
      } else if (configRes.status === "rejected") {
        setError("加载当前模型配置失败");
      }
    } catch {
      setError("加载配置失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    const timer = window.setTimeout(() => {
      void loadData();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [navigate, token]);

  const handlePresetChange = (key: string) => {
    const preset = presets.find((p) => p.key === key);
    if (preset) {
      setSelectedProvider(key);
      setBaseUrl(preset.base_url);
      setModel(preset.model);
    }
  };

  const handleTest = async () => {
    if (!baseUrl || !model || !apiKey) {
      setTestResult({ success: false, message: "请填写完整配置" });
      return;
    }
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.modelConfig.test({
        base_url: baseUrl,
        model: model,
        api_key: apiKey,
      });
      if (res.success) {
        setTestResult({ success: true, message: "连接成功！" });
      } else {
        setTestResult({ success: false, message: res.error || "连接失败" });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: err instanceof Error ? err.message : "测试失败",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!selectedProvider || !baseUrl || !model || !apiKey) {
      setError("请填写完整配置");
      return;
    }
    if (apiKey.length < 8) {
      setError("API Key 长度至少8位");
      return;
    }
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const res = await api.modelConfig.save({
        provider: selectedProvider,
        base_url: baseUrl,
        model: model,
        api_key: apiKey,
      });
      if (res.success) {
        setSuccess("配置保存成功！");
        await loadData();
        setApiKey("");
        setTimeout(() => navigate("/"), 2000);
      } else {
        setError(res.error || "保存失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm("确定要清除模型配置吗？清除后 LLM 功能将不可用。")) return;
    try {
      const res = await api.modelConfig.clear();
      if (res.success) {
        setSuccess("配置已清除");
        setConfig(null);
        setSelectedProvider("");
        setBaseUrl("");
        setModel("");
        setApiKey("");
      } else {
        setError(res.error || "清除失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "清除失败");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-2">⚙️ 模型设置</h1>
      <p className="text-gray-500 mb-6">
        配置 LLM 模型和 API Key，用于 JD 解析、简历优化、面试题生成等功能
      </p>

      {config?.has_config && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-700">
            ✅ 当前已配置：{config.provider} · {config.model}
            <br />
            <span className="text-xs text-gray-500">API Key: {config.api_key_masked}</span>
          </p>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-300">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg border border-green-300">
          {success}
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            模型提供商
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => handlePresetChange(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">请选择</option>
            {presets.map((p) => (
              <option key={p.key} value={p.key}>
                {p.key.charAt(0).toUpperCase() + p.key.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Base URL
          </label>
          <input
            type="url"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://api.deepseek.com"
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            模型名
          </label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="deepseek-chat"
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            API Key
          </label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="请输入 API Key"
            className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {config?.has_config && (
            <p className="text-xs text-gray-400 mt-1">
              当前已配置掩码：{config.api_key_masked}
              <br />
              输入新 Key 将覆盖旧配置
            </p>
          )}
        </div>

        <div className="flex flex-wrap gap-3 pt-2">
          <button
            onClick={handleTest}
            disabled={testing || !baseUrl || !model || !apiKey}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 transition"
          >
            {testing ? "测试中..." : "🔗 测试连接"}
          </button>

          <button
            onClick={handleSave}
            disabled={saving || !selectedProvider || !baseUrl || !model || !apiKey}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition"
          >
            {saving ? "保存中..." : "💾 保存配置"}
          </button>

          {config?.has_config && (
            <button
              onClick={handleClear}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              🗑️ 清除配置
            </button>
          )}
        </div>

        {testResult && (
          <div
            className={`mt-3 p-3 rounded-lg border ${
              testResult.success
                ? "bg-green-50 border-green-200 text-green-700"
                : "bg-red-50 border-red-200 text-red-700"
            }`}
          >
            {testResult.success ? "✅ " : "❌ "}
            {testResult.message}
          </div>
        )}
      </div>
    </div>
  );
}
