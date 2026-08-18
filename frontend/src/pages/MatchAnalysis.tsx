import { type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import MatchCard from "../components/MatchCard";
import type { JDItem, MatchResult, ResumeItem } from "../types";

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
        api.jd.list(),
        api.resume.list(),
        api.match.rankings(),
      ]);
      if (jdRes.success && jdRes.data) setJds(jdRes.data);
      if (resumeRes.success && resumeRes.data) setResumes(resumeRes.data);
      if (rankRes.success && rankRes.data) setRankings(rankRes.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }, []);

  useEffect(() => {
    const initialLoad = async () => {
      await loadAll();
    };
    initialLoad();
  }, [loadAll]);

  const handleRun = async () => {
    setError("");
    setResult(null);
    if (!resumeId || !jdId) {
      setError("请选择简历和 JD");
      return;
    }
    setRunning(true);
    try {
      const res = await api.match.run(jdId, resumeId);
      if (res.success && res.data) {
        setResult(res.data);
        await loadAll();
      } else {
        setError(res.error || "匹配失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "匹配失败");
    } finally {
      setRunning(false);
    }
  };

  const handleBatch = async () => {
    setError("");
    setBatchResults([]);
    if (!resumeId) {
      setError("请先选择简历");
      return;
    }
    const texts = batchText
      .split(/\n\s*\n/)
      .map((item) => item.trim())
      .filter(Boolean);
    if (texts.length === 0) {
      setError("请输入至少一条 JD");
      return;
    }
    setBatchRunning(true);
    try {
      const res = await api.match.batch(resumeId, texts);
      if (res.success && res.data) {
        setBatchResults(res.data.results);
        await loadAll();
      } else {
        setError(res.error || "批量匹配失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "批量匹配失败");
    } finally {
      setBatchRunning(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold mb-6">匹配分析</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-300">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm h-fit">
          <h2 className="text-lg font-semibold mb-4">计算匹配度</h2>
          <div className="space-y-3">
            <select
              value={resumeId}
              onChange={(e) => setResumeId(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg bg-white"
              aria-label="选择简历"
            >
              <option value="">选择简历</option>
              {resumes.map((resume) => (
                <option key={resume.id} value={resume.id}>
                  {resume.source_file || "手动输入"}
                </option>
              ))}
            </select>
            <select
              value={jdId}
              onChange={(e) => setJdId(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-lg bg-white"
              aria-label="选择 JD"
            >
              <option value="">选择 JD</option>
              {jds.map((jd) => (
                <option key={jd.id} value={jd.id}>
                  {jd.company || "未知公司"} · {jd.position || "未知职位"}
                </option>
              ))}
            </select>
            <button
              onClick={handleRun}
              disabled={running}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
            >
              {running ? "匹配中..." : "开始匹配"}
            </button>
          </div>
        </section>

        <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">匹配结果</h2>
          {result ? (
            <div className="space-y-4">
              <MatchCard result={result} />
              {result.skill_match_detail && (
                <div className="grid sm:grid-cols-3 gap-3 text-sm">
                  <div>
                    <div className="text-xs text-green-700 mb-1">匹配技能 ({result.skill_match_detail.matched?.length || 0})</div>
                    <ul className="list-disc list-inside text-gray-600">
                      {(result.skill_match_detail.matched || []).map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                  <div>
                    <div className="text-xs text-red-700 mb-1">缺失技能 ({result.skill_match_detail.missing?.length || 0})</div>
                    <ul className="list-disc list-inside text-gray-600">
                      {(result.skill_match_detail.missing || []).map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                  <div>
                    <div className="text-xs text-amber-700 mb-1">部分匹配 ({result.skill_match_detail.partial?.length || 0})</div>
                    <ul className="list-disc list-inside text-gray-600">
                      {(result.skill_match_detail.partial || []).map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg p-6 text-center">
              选择简历和 JD 后查看结果
            </p>
          )}
        </section>
      </div>

      <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm mt-6">
        <h2 className="text-lg font-semibold mb-3">批量匹配 JD</h2>
        <textarea
          value={batchText}
          onChange={(e) => setBatchText(e.target.value)}
          className="w-full h-40 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="粘贴多条 JD，JD 之间用空行分隔..."
        />
        <button
          onClick={handleBatch}
          disabled={batchRunning || !resumeId}
          className="mt-3 px-5 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition"
        >
          {batchRunning ? "批量匹配中..." : "批量匹配"}
        </button>

        {batchResults.length > 0 && (
          <div className="mt-4 space-y-3">
            {batchResults.map((item) => (
              <div
                key={item.index}
                className={`p-3 rounded-lg border ${
                  item.success
                    ? "bg-green-50 border-green-200"
                    : "bg-red-50 border-red-200"
                }`}
              >
                <div className="text-sm font-medium text-gray-700 mb-1">
                  JD {item.index}
                </div>
                {item.success && item.match ? (
                  <MatchCard result={item.match} />
                ) : (
                  <div className="text-sm text-red-600">{item.error || "匹配失败"}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm mt-6">
        <h2 className="text-lg font-semibold mb-4">历史排名</h2>
        {rankings.length === 0 ? (
          <p className="text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg p-6 text-center">
            暂无匹配记录
          </p>
        ) : (
          <div className="space-y-3">
            {rankings.map((item) => (
              <MatchCard key={item.id || `${item.jd_id}-${item.resume_id}`} result={item} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default MatchAnalysis;
