import { type ChangeEvent, type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import ResumeDiff from "../components/ResumeDiff";
import type { OptimizeResult, ResumeItem } from "../types";
import { Card, PageHeader, SectionTitle, Badge, Icons } from "../components/ui";

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
    } catch { setVersions([]); }
  }, []);

  useEffect(() => { void loadResumes(); }, [loadResumes]);
  useEffect(() => { if (selectedId) void loadVersions(selectedId); }, [selectedId, loadVersions]);

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => { setFile(e.target.files?.[0] || null); };

  const handleUpload = async () => {
    setError(""); setMessage("");
    if (!file && !text.trim()) { setError("请粘贴简历文本或选择文件"); return; }
    try {
      if (file) await api.resume.uploadFile(file);
      else await api.resume.upload(text.trim(), "manual");
      setText(""); setFile(null);
      await loadResumes();
      setMessage("上传成功");
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    }
  };

  const handleOptimize = async () => {
    setError(""); setMessage("");
    if (!selectedId) { setError("请先上传并选择一份简历"); return; }
    if (!jdText.trim()) { setError("请输入目标 JD 文本"); return; }
    setOptimizing(true); setResult(null);
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
    <div>
      <PageHeader
        title="简历优化"
        subtitle="上传简历 + 目标 JD，AI 帮你优化排版和关键词命中"
        icon={Icons.resume}
      />

      {error && <div className="of-alert-error mb-4">{Icons.alert}<span>{error}</span></div>}
      {message && <div className="of-alert-success mb-4">{Icons.check}<span>{message}</span></div>}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card className="p-5">
          <SectionTitle>上传简历</SectionTitle>
          <textarea
            className="of-textarea h-40"
            placeholder="粘贴简历文本，或上传 PDF / Word / Markdown / TXT 文件..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <input
            type="file"
            accept=".pdf,.md,.markdown,.docx,.txt"
            onChange={handleFile}
            className="mt-3 block w-full text-sm text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-emerald-50 file:px-3 file:py-1.5 file:text-emerald-600"
          />
          <button onClick={handleUpload} className="of-btn mt-3 bg-emerald-600 text-white hover:bg-emerald-700">
            {Icons.upload}
            上传
          </button>

          <h3 className="mt-6 text-sm font-semibold text-slate-600">简历版本</h3>
          <select className="of-select mt-2" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            {resumes.length === 0 && <option value="">暂无简历</option>}
            {resumes.map((item) => (
              <option key={item.id} value={item.id}>{item.source_file || "手动输入"}</option>
            ))}
          </select>

          {versions.length > 0 && (
            <div className="mt-3 space-y-2">
              {versions.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                  <span className="text-slate-600">{item.source_file || "手动输入"}</span>
                  {item.parsed_json?.kind === "optimized" && <Badge color="green">优化版本</Badge>}
                </div>
              ))}
            </div>
          )}

          {selectedId && (
            <div className="mt-4 flex gap-2">
              <button onClick={() => handleExport("pdf")} className="of-btn-outline">
                {Icons.download} PDF
              </button>
              <button onClick={() => handleExport("word")} className="of-btn-outline">
                {Icons.download} Word
              </button>
            </div>
          )}
        </Card>

        <Card className="p-5">
          <SectionTitle>针对 JD 优化</SectionTitle>
          <textarea
            className="of-textarea h-40"
            placeholder="粘贴目标职位描述 (JD) 文本..."
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
          />
          <button onClick={handleOptimize} disabled={optimizing || !selectedId} className="of-btn-primary mt-3">
            {optimizing ? (
              <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />优化中...</>
            ) : <>{Icons.sparkle} 开始优化</>}
          </button>

          {selectedResume && (
            <div className="mt-4 text-sm text-slate-600">
              {selectedResume.parsed_json?.skills?.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {selectedResume.parsed_json.skills.map((s: string) => (
                    <Badge key={s} color="indigo">{s}</Badge>
                  ))}
                </div>
              ) : null}
            </div>
          )}
        </Card>
      </div>

      {result && (
        <Card className="mt-5 p-5">
          <SectionTitle>优化结果</SectionTitle>
          <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            <div className="rounded-xl bg-orange-50 p-4">
              <div className="text-sm font-medium text-orange-800">优化前 ATS 评分</div>
              <div className="mt-1 text-3xl font-bold text-orange-700">{result.ats.score}</div>
              {result.ats.issues.map((issue) => (
                <div key={issue} className="mt-1 text-xs text-orange-600">- {issue}</div>
              ))}
            </div>
            <div className="rounded-xl bg-emerald-50 p-4">
              <div className="text-sm font-medium text-emerald-800">优化后 ATS 评分</div>
              <div className="mt-1 text-3xl font-bold text-emerald-700">{result.ats_after.score}</div>
              {result.ats_after.suggestions.map((item) => (
                <div key={item} className="mt-1 text-xs text-emerald-600">- {item}</div>
              ))}
            </div>
          </div>
          <ResumeDiff original={selectedResume?.raw_text} optimized={result.optimized} changes={result.changes} />
        </Card>
      )}
    </div>
  );
};

export default ResumeOptimize;
