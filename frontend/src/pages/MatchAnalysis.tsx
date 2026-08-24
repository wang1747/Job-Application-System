import { type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import MatchCard from "../components/MatchCard";
import type { JDItem, MatchResult, ResumeItem } from "../types";
import { Card, PageHeader, SectionTitle, EmptyState, Badge, Icons } from "../components/ui";

const MatchAnalysis: FC = () => {
  const [jds, setJds] = useState<JDItem[]>([]);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [rankings, setRankings] = useState<MatchResult[]>([]);
  const [resumeId, setResumeId] = useState("");
  const [jdId, setJdId] = useState("");
  const [result, setResult] = useState<MatchResult | null>(null);
  const [running, setRunning] = useState(false);
  const [batchText, setBatchText] = useState("");
  const [batchResults, setBatchResults] = useState<
    Array<{ index: number; success: boolean; error?: string | null; match?: MatchResult | null }>
  >([]);
  const [batchRunning, setBatchRunning] = useState(false);
  const [error, setError] = useState("");

  const loadAll = useCallback(async () => {
    try {
      const [jdRes, resumeRes, rankRes] = await Promise.all([
        api.jd.list(), api.resume.list(), api.match.rankings(),
      ]);
      if (jdRes.success && jdRes.data) setJds(jdRes.data);
      if (resumeRes.success && resumeRes.data) setResumes(resumeRes.data);
      if (rankRes.success && rankRes.data) setRankings(rankRes.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }, []);

  useEffect(() => { void loadAll(); }, [loadAll]);

  const handleRun = async () => {
    setError(""); setResult(null);
    if (!resumeId || !jdId) { setError("请选择简历和 JD"); return; }
    setRunning(true);
    try {
      const res = await api.match.run(jdId, resumeId);
      if (res.success && res.data) { setResult(res.data); await loadAll(); }
      else setError(res.error || "匹配失败");
    } catch (err) {
      setError(err instanceof Error ? err.message : "匹配失败");
    } finally {
      setRunning(false);
    }
  };

  const handleBatch = async () => {
    setError(""); setBatchResults([]);
    if (!resumeId) { setError("请先选择简历"); return; }
    const texts = batchText.split(/\n\s*\n/).map((item) => item.trim()).filter(Boolean);
    if (texts.length === 0) { setError("请输入至少一条 JD"); return; }
    setBatchRunning(true);
    try {
      const res = await api.match.batch(resumeId, texts);
      if (res.success && res.data) { setBatchResults(res.data.results); await loadAll(); }
      else setError(res.error || "批量匹配失败");
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量匹配失败");
    } finally {
      setBatchRunning(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="匹配分析"
        subtitle="简历与 JD 的技能匹配度计算，支持批量匹配和历史排名"
        icon={Icons.match}
      />

      {error && <div className="of-alert-error mb-4">{Icons.alert}<span>{error}</span></div>}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <Card className="h-fit p-5">
          <SectionTitle>计算匹配度</SectionTitle>
          <div className="space-y-3">
            <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} className="of-select" aria-label="选择简历">
              <option value="">选择简历</option>
              {resumes.map((resume) => (
                <option key={resume.id} value={resume.id}>{resume.source_file || "手动输入"}</option>
              ))}
            </select>
            <select value={jdId} onChange={(e) => setJdId(e.target.value)} className="of-select" aria-label="选择 JD">
              <option value="">选择 JD</option>
              {jds.map((jd) => (
                <option key={jd.id} value={jd.id}>{jd.company || "未知公司"} · {jd.position || "未知职位"}</option>
              ))}
            </select>
            <button onClick={handleRun} disabled={running} className="of-btn-primary w-full">
              {running ? (
                <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />匹配中...</>
              ) : "开始匹配"}
            </button>
          </div>
        </Card>

        <Card className="p-5">
          <SectionTitle>匹配结果</SectionTitle>
          {result ? (
            <div className="space-y-4">
              <MatchCard result={result} />
              {result.skill_match_detail && (
                <div className="grid gap-3 sm:grid-cols-3 text-sm">
                  <div className="rounded-xl bg-emerald-50 p-3">
                    <div className="mb-1 text-xs font-medium text-emerald-700">
                      匹配技能 ({result.skill_match_detail.matched?.length || 0})
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {(result.skill_match_detail.matched || []).map((item) => (
                        <Badge key={item} color="green">{item}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-xl bg-rose-50 p-3">
                    <div className="mb-1 text-xs font-medium text-rose-700">
                      缺失技能 ({result.skill_match_detail.missing?.length || 0})
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {(result.skill_match_detail.missing || []).map((item) => (
                        <Badge key={item} color="red">{item}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-xl bg-amber-50 p-3">
                    <div className="mb-1 text-xs font-medium text-amber-700">
                      部分匹配 ({result.skill_match_detail.partial?.length || 0})
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {(result.skill_match_detail.partial || []).map((item) => (
                        <Badge key={item} color="amber">{item}</Badge>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <EmptyState title="选择简历和 JD 后查看结果" />
          )}
        </Card>
      </div>

      <Card className="mt-5 p-5">
        <SectionTitle>批量匹配 JD</SectionTitle>
        <textarea
          className="of-textarea h-40"
          placeholder="粘贴多条 JD，JD 之间用空行分隔..."
          value={batchText}
          onChange={(e) => setBatchText(e.target.value)}
        />
        <button onClick={handleBatch} disabled={batchRunning || !resumeId} className="of-btn-primary mt-3">
          {batchRunning ? (
            <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />批量匹配中...</>
          ) : "批量匹配"}
        </button>

        {batchResults.length > 0 && (
          <div className="mt-4 space-y-3">
            {batchResults.map((item) => (
              <div key={item.index} className={`rounded-xl border p-3 ${item.success ? "border-emerald-200 bg-emerald-50/50" : "border-rose-200 bg-rose-50/50"}`}>
                <div className="mb-2 text-sm font-medium text-slate-700">JD {item.index}</div>
                {item.success && item.match ? (
                  <MatchCard result={item.match} />
                ) : (
                  <div className="text-sm text-rose-600">{item.error || "匹配失败"}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card className="mt-5 p-5">
        <SectionTitle count={rankings.length}>历史排名</SectionTitle>
        {rankings.length === 0 ? (
          <EmptyState title="暂无匹配记录" />
        ) : (
          <div className="space-y-3">
            {rankings.map((item) => (
              <MatchCard key={item.id || `${item.jd_id}-${item.resume_id}`} result={item} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default MatchAnalysis;
