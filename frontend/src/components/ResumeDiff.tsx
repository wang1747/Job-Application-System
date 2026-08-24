import { type FC } from "react";

interface ResumeDiffProps {
  original?: string;
  optimized?: string;
  changes?: string[];
}

const ResumeDiff: FC<ResumeDiffProps> = ({ original, optimized, changes }) => {
  if (!original && !optimized) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-400">
        暂无对比数据
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {changes && changes.length > 0 && (
        <div className="rounded-xl bg-brand-50 p-4">
          <h4 className="mb-2 text-sm font-semibold text-brand-700">AI 改动项</h4>
          <ul className="space-y-1">
            {changes.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-brand-400" />
                {c}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="grid gap-4 md:grid-cols-2">
        {original && (
          <div>
            <h4 className="mb-2 text-sm font-semibold text-rose-600">优化前</h4>
            <pre className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-xl bg-rose-50 p-4 text-xs leading-relaxed text-slate-700">
              {original}
            </pre>
          </div>
        )}
        {optimized && (
          <div>
            <h4 className="mb-2 text-sm font-semibold text-emerald-600">优化后</h4>
            <pre className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-xl bg-emerald-50 p-4 text-xs leading-relaxed text-slate-700">
              {optimized}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResumeDiff;
