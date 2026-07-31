import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { JDItem } from "../types";

interface ParsedResult {
  company?: string;
  position?: string;
  must_have: string[];
  nice_to_have: string[];
  tech_stack: Record<string, string[]>;
  hidden_signals: string[];
}

// 时间格式化工具
const formatTime = (iso: string) => {
  const d = new Date(iso);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString()}`;
};

export default function JDAnalysis() {
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ParsedResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<JDItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const autoCloseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const resp = await api.jd.list();
      if (resp.success && resp.data) {
        setHistory(resp.data);
      }
    } catch (err) {
      console.error("加载历史列表失败:", err);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    const initialLoad = async () => {
      await loadHistory();
    };
    initialLoad();
  }, [loadHistory]);

  useEffect(() => {
    return () => {
      if (autoCloseTimer.current) clearTimeout(autoCloseTimer.current);
    };
  }, []);

  const showError = (msg: string) => {
    setError(msg);
    if (autoCloseTimer.current) clearTimeout(autoCloseTimer.current);
    const timer = setTimeout(() => setError(null), 5000);
    autoCloseTimer.current = timer;
  };

  const handleParse = async () => {
    const trimmed = rawText.trim();
    if (!trimmed) {
      showError("请输入 JD 文本");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await api.jd.parse(trimmed);
      if (response.success && response.data?.parsed) {
        const parsed = response.data.parsed;
        // 检查是否为空对象
        if (Object.keys(parsed).length === 0) {
          showError("解析结果为空，请检查 JD 文本内容");
          setResult(null);
        } else {
          setResult(parsed);
        }
        await loadHistory();
        setRawText("");
      } else {
        showError(response.error || "解析失败");
      }
    } catch (err) {
      console.error("解析失败:", err);
      showError("请求失败，请确保后端服务已启动");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除这条 JD 吗？")) return;
    try {
      await api.jd.delete(id);
      await loadHistory();
    } catch (err) {
      console.error("删除失败:", err);
      showError("删除失败，请重试");
    }
  };

  const handleSelectHistory = (item: JDItem) => {
    setRawText(item.raw_text || "");
    setResult(null);
    setError(null);
  };

  const closeResult = () => {
    setResult(null);
  };

  // 渲染技术栈
  const renderTechStack = (techStack: Record<string, string[]>) => {
    if (!techStack || Object.keys(techStack).length === 0) {
      return <span className="text-gray-400">无</span>;
    }
    return (
      <div className="flex flex-wrap gap-2">
        {Object.entries(techStack).map(([key, values]) => (
          values && values.length > 0 && (
            <span key={key} className="bg-gray-100 px-2 py-1 rounded text-xs">
              <span className="font-medium">{key}:</span> {values.join(", ")}
            </span>
          )
        ))}
      </div>
    );
  };

  const hasResultData = result && Object.keys(result).length > 0;

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold mb-6">JD 智能解析</h1>

      {/* 输入区 */}
      <div className="mb-4">
        <textarea
          className="w-full h-48 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          placeholder="粘贴职位描述 (JD) 文本..."
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          disabled={loading}
          aria-label="JD 文本输入"
        />
      </div>

      <button
        onClick={handleParse}
        disabled={loading || !rawText.trim()}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
        aria-label="开始解析 JD"
      >
        {loading ? "解析中..." : "开始解析"}
      </button>

      {/* 错误提示 */}
      {error && (
        <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-300 flex justify-between items-center">
          <span>⚠️ {error}</span>
          <button
            className="text-sm underline"
            onClick={() => setError(null)}
            aria-label="关闭错误提示"
          >
            关闭
          </button>
        </div>
      )}

      {/* 解析结果 */}
      {hasResultData && (
        <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-semibold text-green-800">✅ 解析结果</h2>
            <button
              onClick={closeResult}
              className="text-gray-400 hover:text-gray-600 text-sm"
              aria-label="关闭结果"
            >
              ✕ 关闭
            </button>
          </div>
          <div className="space-y-3 text-sm">
            <div><span className="font-medium">公司：</span>{result.company || "-"}</div>
            <div><span className="font-medium">职位：</span>{result.position || "-"}</div>
            <div>
              <span className="font-medium">硬性要求：</span>
              <ul className="list-disc list-inside ml-4">
                {result.must_have?.length ? result.must_have.map((item, idx) => <li key={idx}>{item}</li>) : <li>无</li>}
              </ul>
            </div>
            <div>
              <span className="font-medium">加分项：</span>
              <ul className="list-disc list-inside ml-4">
                {result.nice_to_have?.length ? result.nice_to_have.map((item, idx) => <li key={idx}>{item}</li>) : <li>无</li>}
              </ul>
            </div>
            <div>
              <span className="font-medium">技术栈：</span>
              {renderTechStack(result.tech_stack)}
            </div>
            {result.hidden_signals?.length > 0 && (
              <div>
                <span className="font-medium">隐藏信号：</span>
                <ul className="list-disc list-inside ml-4">
                  {result.hidden_signals.map((item, idx) => <li key={idx}>{item}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 历史列表 */}
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-3">📋 历史记录</h2>
        {historyLoading ? (
          <div className="text-gray-500 text-sm">加载中...</div>
        ) : history.length === 0 ? (
          <div className="text-gray-400 text-sm border border-dashed border-gray-300 rounded-lg p-6 text-center">
            暂无 JD 记录，快来解析第一条吧！
          </div>
        ) : (
          <div className="space-y-2">
            {history.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-blue-50 hover:border-blue-200 transition cursor-pointer border border-transparent"
                onClick={() => handleSelectHistory(item)}
              >
                <div className="flex-1 min-w-0">
                  <span className="font-medium">{item.company || "未知公司"}</span>
                  <span className="text-gray-500 mx-2">·</span>
                  <span>{item.position || "未知职位"}</span>
                  <span className="text-gray-400 text-xs ml-3 hidden sm:inline">
                    {formatTime(item.created_at || "")}
                  </span>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}
                  className="text-red-500 hover:text-red-700 text-sm px-2 flex-shrink-0"
                  aria-label={`删除 ${item.company || "未知"} 的 JD`}
                >
                  删除
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
