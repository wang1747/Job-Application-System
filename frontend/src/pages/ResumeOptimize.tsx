import { type ChangeEvent, type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import ResumeDiff from "../components/ResumeDiff";
import type { JDItem, OptimizeResult, ResumeItem } from "../types";
import { Card, PageHeader, SectionTitle, Badge, Icons } from "../components/ui";

type UploadMode = "file" | "text";
type JdMode = "saved" | "paste";

const resumeLabel = (item: ResumeItem) => {
  const src = item.source_file;
  const validSrc = src && src !== "manual" && src !== "optimized" ? src : "";
  if (item.parsed_json?.kind === "optimized") {
    const jd = item.parsed_json?.target_jd;
    const hasJd = !!(jd?.company || jd?.position);
    const target = hasJd
      ? `针对 ${jd!.company || ""}${jd!.company && jd!.position ? " · " : ""}${jd!.position || ""}`
      : "未指定目标 JD";
    return { base: validSrc || "优化版本", target };
  }
  return { base: validSrc || "手动输入", target: "" };
};

/** 把后端返回结果归一化，兼容旧后端/缺失字段，避免渲染时访问 undefined 导致白屏。 */
const normalizeResult = (d: OptimizeResult | null): OptimizeResult | null => {
  if (!d) return null;
  return {
    ...d,
    optimized: d.optimized ?? "",
    changes: d.changes ?? [],
    added_keywords: d.added_keywords ?? [],
    removed_keywords: d.removed_keywords ?? [],
    removed: d.removed ?? [],
    length_warning: d.length_warning ?? "",
    gap: d.gap ?? { matched: [], missing: [], partial: [] },
    target_jd: d.target_jd ?? { id: null, company: "", position: "" },
    ats: d.ats ?? { score: 0, issues: [], suggestions: [] },
    ats_after: d.ats_after ?? { score: 0, issues: [], suggestions: [] },
    preservation: d.preservation ?? { score: 1, passed: true, fallback: false, missing_facts: [] },
    new_version: d.new_version ?? null,
  };
};

const ResumeOptimize: FC = () => {
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [jds, setJds] = useState<JDItem[]>([]);
  const [jdMode, setJdMode] = useState<JdMode>("saved");
  const [selectedJdId, setSelectedJdId] = useState("");
  const [uploadMode, setUploadMode] = useState<UploadMode>("file");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [uploading, setUploading] = useState(false);
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

  const loadJds = useCallback(async () => {
    try {
      const resp = await api.jd.list();
      if (resp.success && resp.data) {
        setJds(resp.data);
        // 自动选中第一个 JD，避免用户点「开始优化」时因未选 JD 被拦截而无响应
        setSelectedJdId((current) => {
          if (current && resp.data!.some((item) => item.id === current)) return current;
          return resp.data![0]?.id || "";
        });
      }
    } catch { setJds([]); }
  }, []);

  useEffect(() => { void loadResumes(); }, [loadResumes]);
  useEffect(() => { void loadJds(); }, [loadJds]);

  const selectedJd = jds.find((item) => item.id === selectedJdId);

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => { setFile(e.target.files?.[0] || null); };

  const handleJdSelect = (id: string) => {
    setSelectedJdId(id);
    setJdText("");
  };

  const handleUpload = async () => {
    setError(""); setMessage("");
    if (uploadMode === "file" && !file) { setError("请选择简历文件"); return; }
    if (uploadMode === "text" && !text.trim()) { setError("请粘贴简历文本"); return; }

    setUploading(true);
    try {
      if (uploadMode === "file") await api.resume.uploadFile(file!);
      else await api.resume.upload(text.trim(), "manual");
      setText(""); setFile(null);
      await loadResumes();
      setMessage("上传成功");
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally {
      setUploading(false);
    }
  };

  const handleOptimize = async () => {
    setError(""); setMessage("");
    if (!selectedId) { setError("请先选择一份简历"); return; }
    if (jdMode === "saved" && !selectedJdId) { setError("请选择一个目标 JD"); return; }
    if (jdMode === "paste" && !jdText.trim()) { setError("请输入目标 JD 文本"); return; }

    setOptimizing(true); setResult(null);
    try {
      const jdId = jdMode === "saved" ? selectedJdId : undefined;
      const jdInput = jdMode === "saved" ? "" : jdText.trim();
      const resp = await api.resume.optimize(selectedId, jdInput, jdId);
      if (resp.success && resp.data) {
        setResult(normalizeResult(resp.data));
        setMessage(
          resp.data.preservation?.fallback
            ? "AI 结果未通过内容保留校验，已保留原简历；请确认原简历被正确识别"
            : "优化完成，已保存为新版本",
        );
        await loadResumes();
      } else {
        setError(resp.error || "优化失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "优化失败");
    } finally {
      setOptimizing(false);
    }
  };

  const handleExport = async (format: "pdf" | "word", resumeId: string = selectedId) => {
    if (!resumeId) return;
    try {
      const blob = await api.resume.export(resumeId, format);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `resume-${resumeId}.${format === "pdf" ? "pdf" : "docx"}`;
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
        subtitle="针对目标 JD 做关键词对齐与措辞升级，导出可直接投递的简历"
        icon={Icons.resume}
      />

      {error && <div className="of-alert-error mb-4">{Icons.alert}<span>{error}</span></div>}
      {message && <div className="of-alert-success mb-4">{Icons.check}<span>{message}</span></div>}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* ===== 左：我的简历 ===== */}
        <Card className="p-5">
          <SectionTitle>我的简历</SectionTitle>

          <div className="mb-3 flex rounded-lg bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => setUploadMode("file")}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                uploadMode === "file" ? "bg-white text-emerald-700 shadow-sm" : "text-slate-500"
              }`}
            >
              上传文件
            </button>
            <button
              type="button"
              onClick={() => setUploadMode("text")}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                uploadMode === "text" ? "bg-white text-emerald-700 shadow-sm" : "text-slate-500"
              }`}
            >
              粘贴文本
            </button>
          </div>

          {uploadMode === "file" ? (
            <>
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 px-4 py-7 text-center transition hover:border-emerald-300 hover:bg-emerald-50/40">
                <div className="text-emerald-600">{Icons.upload}</div>
                <span className="mt-2 text-sm font-medium text-slate-700">
                  {file ? file.name : "选择 PDF / Word / Markdown / TXT"}
                </span>
                <span className="mt-1 text-xs text-slate-400">
                  {file ? "点击重新选择" : "支持 .pdf .docx .md .txt，最大 10MB"}
                </span>
                <input type="file" accept=".pdf,.md,.markdown,.docx,.txt" onChange={handleFile} className="hidden" />
              </label>
              {file && (
                <button onClick={handleUpload} disabled={uploading} className="of-btn-primary mt-3">
                  {uploading ? "上传中..." : "上传文件"}
                </button>
              )}
            </>
          ) : (
            <>
              <textarea
                className="of-textarea mt-3 h-40"
                placeholder="粘贴简历文本..."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <button onClick={handleUpload} disabled={uploading || !text.trim()} className="of-btn-primary mt-3">
                {uploading ? "上传中..." : "上传文本"}
              </button>
            </>
          )}

          <div className="mt-6 border-t border-slate-100 pt-5">
            <SectionTitle count={resumes.length}>选择简历</SectionTitle>
            {resumes.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-200 py-8 text-center text-sm text-slate-400">
                还没有简历，先上传一份吧
              </div>
            ) : (
              <div className="space-y-2">
                {resumes.map((item) => {
                  const label = resumeLabel(item);
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSelectedId(item.id)}
                      className={`w-full rounded-lg border p-3 text-left transition ${
                        item.id === selectedId
                          ? "border-emerald-400 bg-emerald-50/60 ring-1 ring-emerald-300"
                          : "border-slate-200 bg-white hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium text-slate-900">{label.base}</div>
                          {label.target && (
                            <div className="mt-0.5 truncate text-xs text-brand-600">
                              {label.target}
                            </div>
                          )}
                        </div>
                        <div className="flex flex-shrink-0 items-center gap-2">
                          {(item.version_count ?? 1) > 1 && (
                            <Badge color="indigo">共 {item.version_count} 版</Badge>
                          )}
                          {item.parsed_json?.kind === "optimized" ? (
                            <Badge color="green">优化版</Badge>
                          ) : (
                            <Badge color="gray">原简历</Badge>
                          )}
                          {item.id === selectedId && <span className="text-emerald-600">{Icons.check}</span>}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {selectedResume && (
            <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-xs font-medium text-slate-500">当前选择的内容预览</span>
                <div className="flex gap-2">
                  <button onClick={() => handleExport("pdf")} className="of-btn-outline px-2.5 py-1 text-xs">
                    {Icons.download} PDF
                  </button>
                  <button onClick={() => handleExport("word")} className="of-btn-outline px-2.5 py-1 text-xs">
                    {Icons.download} Word
                  </button>
                </div>
              </div>
              {selectedResume.raw_text ? (
                <pre className="max-h-44 overflow-y-auto whitespace-pre-wrap text-xs text-slate-600">
                  {selectedResume.raw_text}
                </pre>
              ) : (
                <div className="text-xs text-rose-600">该版本未识别到内容，请重新上传可编辑文本的简历</div>
              )}
            </div>
          )}
        </Card>

        {/* ===== 右：目标 JD ===== */}
        <Card className="p-5">
          <SectionTitle>针对目标 JD 优化</SectionTitle>

          <div className="mb-3 flex rounded-lg bg-slate-100 p-1">
            <button
              type="button"
              onClick={() => setJdMode("saved")}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                jdMode === "saved" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"
              }`}
            >
              从已保存 JD 选择
            </button>
            <button
              type="button"
              onClick={() => setJdMode("paste")}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                jdMode === "paste" ? "bg-white text-brand-700 shadow-sm" : "text-slate-500"
              }`}
            >
              手动粘贴 JD
            </button>
          </div>

          {jdMode === "saved" ? (
            <>
              {jds.length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-200 py-8 text-center text-sm text-slate-400">
                  还没有保存过 JD，请先在「JD 解析」页导入，或切换到「手动粘贴」
                </div>
              ) : (
                <div className="max-h-56 space-y-2 overflow-y-auto pr-1">
                  {jds.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => handleJdSelect(item.id)}
                      className={`w-full rounded-lg border p-3 text-left transition ${
                        item.id === selectedJdId
                          ? "border-brand-400 bg-brand-50/60 ring-1 ring-brand-300"
                          : "border-slate-200 bg-white hover:border-slate-300"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium text-slate-900">
                            {item.position || "未知职位"}
                          </div>
                          <div className="truncate text-xs text-slate-500">{item.company || "未知公司"}</div>
                        </div>
                        {item.id === selectedJdId && <span className="text-brand-600">{Icons.check}</span>}
                      </div>
                      {item.id === selectedJdId && item.must_have?.length ? (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {item.must_have.map((s) => <Badge key={s} color="indigo">{s}</Badge>)}
                        </div>
                      ) : null}
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <textarea
              className="of-textarea h-40"
              placeholder="粘贴目标职位描述 (JD) 文本..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          )}

          {/* 当前目标 JD 提示 */}
          {(selectedJd || (jdMode === "paste" && jdText.trim())) && (
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-700">
              {Icons.check}
              <span>
                {jdMode === "saved"
                  ? `将针对「${selectedJd?.company || "未知公司"} · ${selectedJd?.position || "未知职位"}」优化`
                  : "将针对手动粘贴的 JD 优化"}
              </span>
            </div>
          )}

          <button onClick={handleOptimize} disabled={optimizing || !selectedId} className="of-btn-primary mt-4">
            {optimizing ? (
              <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />优化中...</>
            ) : <>{Icons.sparkle} 开始优化</>}
          </button>
        </Card>
      </div>

      {/* ===== 优化结果 ===== */}
      {result && (
        <Card className="mt-5 p-5">
          <div className="mb-4 flex items-center justify-between">
            <SectionTitle>优化结果</SectionTitle>
            {(result.target_jd?.company || result.target_jd?.position) && (
              <Badge color="indigo">
                目标：{result.target_jd.company || ""}{result.target_jd.company && result.target_jd.position ? " · " : ""}{result.target_jd.position || ""}
              </Badge>
            )}
          </div>

          {result.length_warning && (
            <div className="mb-4 flex items-center gap-2 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800">
              {Icons.alert}
              <span>{result.length_warning}</span>
            </div>
          )}

          {/* 关键词差距 + ATS */}
          <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-xl bg-orange-50 p-4">
              <div className="text-sm font-medium text-orange-800">优化前 ATS</div>
              <div className="mt-1 text-3xl font-bold text-orange-700">{result.ats.score}</div>
              {result.ats.issues.map((issue) => (
                <div key={issue} className="mt-1 text-xs text-orange-600">- {issue}</div>
              ))}
            </div>
            <div className="rounded-xl bg-emerald-50 p-4">
              <div className="text-sm font-medium text-emerald-800">优化后 ATS</div>
              <div className="mt-1 text-3xl font-bold text-emerald-700">{result.ats_after.score}</div>
              {result.ats_after.suggestions.map((item) => (
                <div key={item} className="mt-1 text-xs text-emerald-600">- {item}</div>
              ))}
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <div className="text-sm font-medium text-slate-800">关键词命中</div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {result.gap.matched.map((s) => <Badge key={s} color="green">{s}</Badge>)}
                {result.gap.partial.map((s) => <Badge key={s} color="amber">{s}</Badge>)}
                {result.gap.missing.map((s) => <Badge key={s} color="red">{s}</Badge>)}
              </div>
              <div className="mt-2 text-xs text-slate-400">
                绿=已命中 · 黄=措辞不同已对齐 · 红=原文缺失
              </div>
            </div>
          </div>

          {/* 新增/移除内容 */}
          {(result.added_keywords.length > 0 || result.removed.length > 0) && (
            <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-xl bg-emerald-50/60 p-4">
                <div className="mb-2 text-sm font-medium text-emerald-800">本次对齐的关键词</div>
                <div className="flex flex-wrap gap-1.5">
                  {result.added_keywords.length
                    ? result.added_keywords.map((s) => <Badge key={s} color="green">{s}</Badge>)
                    : <span className="text-xs text-slate-400">无</span>}
                </div>
              </div>
              <div className="rounded-xl bg-rose-50/60 p-4">
                <div className="mb-2 text-sm font-medium text-rose-700">本次精简/删除的内容</div>
                <div className="space-y-1">
                  {result.removed.length
                    ? result.removed.map((s) => (
                        <div key={s} className="text-xs text-rose-600">- {s}</div>
                      ))
                    : <span className="text-xs text-slate-400">无</span>}
                </div>
              </div>
            </div>
          )}

          {/* 内容保留 */}
          <div className="mb-4 flex items-center gap-3 rounded-xl bg-slate-50 p-3 text-sm">
            {result.preservation?.fallback ? (
              <span className="text-amber-700">{Icons.alert} 内容保留校验未通过，已回退原简历</span>
            ) : (
              <>
                <span className="text-emerald-700">{Icons.check} 关键事实已保留</span>
                <span className="text-xs text-slate-400">
                  保留率 {Math.round((result.preservation?.score ?? 1) * 100)}%
                  {typeof result.edits_applied === "number" && ` · ${result.edits_applied} 处改动`}
                </span>
              </>
            )}
          </div>

          <ResumeDiff original={selectedResume?.raw_text} optimized={result.optimized} changes={result.changes} />

          {result.new_version && (
            <div className="mt-4 flex items-center gap-2">
              <span className="text-sm text-slate-500">导出优化后简历：</span>
              <button onClick={() => handleExport("pdf", result.new_version!.id)} className="of-btn-outline">
                {Icons.download} PDF
              </button>
              <button onClick={() => handleExport("word", result.new_version!.id)} className="of-btn-outline">
                {Icons.download} Word
              </button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};

export default ResumeOptimize;
