import { type ChangeEvent, type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import ResumeDiff from "../components/ResumeDiff";
import type { OptimizeResult, ResumeItem } from "../types";

const ResumeOptimize: FC = () => {
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [versions, setVersions] = useState<ResumeItem[]>([]);
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [optimizing, setOptimizing] = useState(false);
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const loadResumes = useCallback(async () => {
    try {
      const resp = await api.resume.list();
      if (resp.success && resp.data) {
        setResumes(resp.data);
        setSelectedId((current) => {
          if (current && resp.data!.some((item) => item.id === current)) return current;
          return resp.data![0]?.id || "";
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载简历失败");
    }
  }, []);

  const loadVersions = useCallback(async (resumeId: string) => {
    if (!resumeId) return;
    try {
      const resp = await api.resume.versions(resumeId);
      if (resp.success && resp.data) setVersions(resp.data);
    } catch {
      setVersions([]);
    }
  }, []);

  useEffect(() => {
    const initialLoad = async () => {
      await loadResumes();
    };
    initialLoad();
  }, [loadResumes]);

  useEffect(() => {
    const load = async () => {
      if (selectedId) await loadVersions(selectedId);
    };
    load();
  }, [selectedId, loadVersions]);

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleUpload = async () => {
    setError("");
    setMessage("");
    if (!file && !text.trim()) {
      setError("请粘贴简历文本或选择文件");
      return;
    }
    try {
      if (file) {
        await api.resume.uploadFile(file);
      } else {
        await api.resume.upload(text.trim(), "manual");
      }
      setText("");
      setFile(null);
      await loadResumes();
      setMessage("上传成功");
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    }
  };

  const handleOptimize = async () => {
    setError("");
    setMessage("");
    if (!selectedId) {
      setError("请先上传并选择一份简历");
      return;
    }
    if (!jdText.trim()) {
      setError("请输入目标 JD 文本");
      return;
    }
    setOptimizing(true);
    setResult(null);
    try {
      const resp = await api.resume.optimize(selectedId, jdText.trim());
      if (resp.success && resp.data) {
        setResult(resp.data);
        setMessage("优化完成，已保存为新版本");
        await loadVersions(selectedId);
      } else {
        setError(resp.error || "优化失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "优化失败");
    } finally {
      setOptimizing(false);
    }
  };

  const handleExport = async (format: "pdf" | "word") => {
    if (!selectedId) return;
    try {
      const blob = await api.resume.export(selectedId, format);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `resume.${format === "pdf" ? "pdf" : "docx"}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "导出失败");
    }
  };

  const selectedResume = resumes.find((item) => item.id === selectedId);

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold mb-6">简历优化</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-300">{error}</div>
      )}
      {message && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg border border-green-300">{message}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-white rounded-lg p-5 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-3">上传简历</h2>
          <textarea
            className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="粘贴简历文本，或上传 PDF / Word / Markdown / TXT 文件..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <input
            type="file"
            accept=".pdf,.md,.markdown,.docx,.txt"
            onChange={handleFile}
            className="mt-3 block w-full text-sm text-gray-600 file:mr-3 file:px-3 file:py-1.5 file:rounded file:border-0 file:bg-green-600 file:text-white"
          />
          <button
            onClick={handleUpload}
            className="mt-3 px-5 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            上传
          </button>

          <h3 className="mt-6 text-sm font-semibold text-gray-600">简历版本</h3>
          <select
            className="mt-2 w-full p-2 border border-gray-300 rounded-lg"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {resumes.length === 0 && <option value="">暂无简历</option>}
            {resumes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.source_file || "手动输入"}
              </option>
            ))}
          </select>
          {versions.length > 0 && (
            <div className="mt-3 space-y-2">
              {versions.map((item) => (
                <div key={item.id} className="p-2 bg-gray-50 rounded border border-gray-200 text-sm">
                  <div className="flex justify-between text-gray-600">
                    <span>{item.source_file || "手动输入"}</span>
                  </div>
                  {item.parsed_json?.kind === "optimized" && (
                    <div className="mt-1 text-xs text-green-700">优化版本</div>
                  )}
                </div>
              ))}
            </div>
          )}
          {selectedId && (
            <div className="mt-4 flex gap-2">
              <button
                onClick={() => handleExport("pdf")}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                导出 PDF
              </button>
              <button
                onClick={() => handleExport("word")}
                className="px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-800 transition"
              >
                导出 Word
              </button>
            </div>
          )}
        </section>

        <section className="bg-white rounded-lg p-5 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-3">针对 JD 优化</h2>
          <textarea
            className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="粘贴目标职位描述 (JD) 文本..."
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
          />
          <button
            onClick={handleOptimize}
            disabled={optimizing || !selectedId}
            className="mt-3 px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
          >
            {optimizing ? "优化中..." : "开始优化"}
          </button>

          {selectedResume && (
            <div className="mt-4 text-sm text-gray-600">
              {selectedResume.parsed_json?.skills?.length ? (
                <span> · 技能：{selectedResume.parsed_json.skills.join("、")}</span>
              ) : null}
            </div>
          )}
        </section>
      </div>

      {result && (
        <div className="mt-6 space-y-4">
          <section className="bg-white rounded-lg p-5 shadow-sm border border-gray-200">
            <h2 className="text-lg font-semibold mb-3">优化结果</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="p-3 bg-orange-50 rounded-lg">
                <div className="text-sm font-medium text-orange-800">优化前 ATS 评分</div>
                <div className="text-2xl font-bold text-orange-700">{result.ats.score}</div>
                {result.ats.issues.map((issue) => (
                  <div key={issue} className="text-xs text-orange-700 mt-1">- {issue}</div>
                ))}
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="text-sm font-medium text-green-800">优化后 ATS 评分</div>
                <div className="text-2xl font-bold text-green-700">{result.ats_after.score}</div>
                {result.ats_after.suggestions.map((item) => (
                  <div key={item} className="text-xs text-green-700 mt-1">- {item}</div>
                ))}
              </div>
            </div>
            <ResumeDiff
              original={selectedResume?.raw_text}
              optimized={result.optimized}
              changes={result.changes}
            />
            {result.new_version && (
              <div className="mt-3 text-sm text-gray-600">
                已保存为新版本
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
};

export default ResumeOptimize;
