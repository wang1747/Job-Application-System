import { type ReactNode, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

type GateState = "loading" | "missing" | "ready";

export default function ModelConfigGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<GateState>("loading");

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(async () => {
      try {
        const res = await api.modelConfig.get();
        if (!active) return;
        setState(res.success && res.data?.has_config ? "ready" : "missing");
      } catch {
        if (active) setState("missing");
      }
    }, 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, []);

  if (state === "loading") {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        检查模型配置中...
      </div>
    );
  }

  if (state === "missing") {
    return (
      <div className="max-w-2xl mx-auto p-8">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 text-center">
          <h2 className="text-lg font-semibold text-amber-800 mb-2">
            请先完成模型设置
          </h2>
          <p className="text-sm text-amber-700 mb-4">
            该功能依赖 LLM，需要先配置你自己的 API Key。
          </p>
          <Link
            to="/settings"
            className="inline-block px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700"
          >
            去模型设置
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
