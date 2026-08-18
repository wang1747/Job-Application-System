import { type ChangeEvent, type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type {
  GeneratedQuestion,
  InterviewArticle,
  InterviewQuestion,
  JDItem,
  ResumeItem,
} from "../types";

type Tab = "library" | "questions" | "simulate";

interface SimulateSummary {
  summary: string;
  total_questions: number;
  questions: string[];
  answers: string[];
  feedbacks: string[];
  status: string;
}

interface RoundHistory {
  question: string;
  answer: string;
  feedback: string;
}

const TABS: { key: Tab; label: string }[] = [
  { key: "library", label: "面经库" },
  { key: "questions", label: "题目生成" },
  { key: "simulate", label: "模拟面试" },
];

const InterviewPrep: FC = () => {
  const [tab, setTab] = useState<Tab>("library");

  const [articles, setArticles] = useState<InterviewArticle[]>([]);
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [resumes, setResumes] = useState<ResumeItem[]>([]);
  const [jds, setJds] = useState<JDItem[]>([]);

  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [ocrFile, setOcrFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);

  const [genResumeId, setGenResumeId] = useState("");
  const [genJdId, setGenJdId] = useState("");
  const [genArticleId, setGenArticleId] = useState("");
  const [generated, setGenerated] = useState<GeneratedQuestion[]>([]);
  const [generating, setGenerating] = useState(false);

  const [simResumeId, setSimResumeId] = useState("");
  const [simJdId, setSimJdId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [history, setHistory] = useState<RoundHistory[]>([]);
  const [summary, setSummary] = useState<SimulateSummary | null>(null);
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadAll = useCallback(async () => {
    try {
      const [articlesRes, questionsRes, resumesRes, jdsRes] = await Promise.all([
        api.interview.articles(),
        api.interview.questions(),
        api.resume.list(),
        api.jd.list(),
      ]);
      if (articlesRes.success && articlesRes.data) setArticles(articlesRes.data.items);
      if (questionsRes.success && questionsRes.data) setQuestions(questionsRes.data.items);
      if (resumesRes.success && resumesRes.data) setResumes(resumesRes.data);
      if (jdsRes.success && jdsRes.data) setJds(jdsRes.data);
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

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleImportText = async () => {
    setError("");
    setMessage("");
    if (!company.trim() || !content.trim()) {
      setError("请填写公司名称和面经内容");
      return;
    }
    setImporting(true);
    try {
      const res = await api.interview.importArticle(
        company.trim(),
        content.trim(),
        position.trim() || undefined,
      );
      if (!res.success) {
        setError(res.error || "导入失败");
        return;
      }
      setMessage(
        res.data?.duplicate
          ? "检测到重复面经，未重复入库"
          : `导入成功，提取 ${res.data?.question_count ?? 0} 道题目`,
      );
      setCompany("");
      setPosition("");
      setContent("");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "导入失败");
    } finally {
      setImporting(false);
    }
  };

  const handleImportFile = async () => {
    setError("");
    setMessage("");
    if (!company.trim() || !file) {
      setError("请填写公司名称并选择文件");
      return;
    }
    setImporting(true);
    try {
      const res = await api.interview.uploadArticle(company.trim(), file);
      if (!res.success) {
        setError(res.error || "导入失败");
        return;
      }
      setMessage(
        res.data?.duplicate
          ? "检测到重复面经，未重复入库"
          : `导入成功，提取 ${res.data?.question_count ?? 0} 道题目`,
      );
      setCompany("");
      setPosition("");
      setFile(null);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "导入失败");
    } finally {
      setImporting(false);
    }
  };

  const handleImportOcr = async () => {
    setError("");
    setMessage("");
    if (!company.trim() || !ocrFile) {
      setError("请填写公司名称并选择截图图片");
      return;
    }
    setImporting(true);
    try {
      const res = await api.interview.ocrArticle(
        company.trim(),
        ocrFile,
        position.trim() || undefined,
      );
      if (!res.success) {
        setError(res.error || "OCR 导入失败");
        return;
      }
      setMessage(
        res.data?.duplicate
          ? "检测到重复面经，未重复入库"
          : `OCR 导入成功，提取 ${res.data?.question_count ?? 0} 道题目`,
      );
      setCompany("");
      setPosition("");
      setOcrFile(null);
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "OCR 导入失败");
    } finally {
      setImporting(false);
    }
  };

  const handleDeleteArticle = async (article: InterviewArticle) => {
    if (!window.confirm(`确定删除 ${article.company} 的面经？`)) return;
    setError("");
    setMessage("");
    try {
      await api.interview.delete(article.id);
      setMessage("已删除");
      await loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  };

  const handleGenerate = async () => {
    setError("");
    setMessage("");
    if (!genResumeId || !genJdId) {
      setError("请选择简历和 JD");
      return;
    }
    setGenerating(true);
    setGenerated([]);
    try {
      const res = await api.interview.generate(genResumeId, genJdId, genArticleId || undefined);
      if (res.success && res.data) {
        setGenerated(res.data.questions);
        setMessage(`已生成 ${res.data.questions.length} 道题目`);
        await loadAll();
      } else {
        setError(res.error || "生成失败");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setGenerating(false);
    }
  };

  const handleStartSimulate = async () => {
    setError("");
    setMessage("");
    setHistory([]);
    setSummary(null);
    setSessionId("");
    setQuestion("");
    if (!simResumeId || !simJdId) {
      setError("请选择简历和 JD");
      return;
    }
    setStarting(true);
    try {
      const res = await api.interview.simulateStart(simResumeId, simJdId);
      if (res.success && res.data) {
        setSessionId(res.data.session_id);
        setQuestion(res.data.question);
        setAnswer("");
      } else {
        setError(res.error || "无法开始模拟面试");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "无法开始模拟面试");
    } finally {
      setStarting(false);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!sessionId || !answer.trim()) return;
    setError("");
    setSubmitting(true);
    try {
      const res = await api.interview.simulateAnswer(sessionId, answer.trim());
      if (!res.success || !res.data) {
        setError(res.error || "提交失败");
        return;
      }
      const data = res.data;
      setHistory((prev) => [...prev, { question, answer: answer.trim(), feedback: data.feedback }]);
      setAnswer("");
      if (data.is_finished) {
        setQuestion("");
        const summaryRes = await api.interview.simulateSummary(sessionId);
        if (summaryRes.success && summaryRes.data) setSummary(summaryRes.data);
      } else if (data.next_question) {
        setQuestion(data.next_question);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold mb-6">面试准备</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg border border-red-300">{error}</div>
      )}
      {message && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg border border-green-300">{message}</div>
      )}

      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {TABS.map((item) => (
          <button
            key={item.key}
            onClick={() => setTab(item.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition ${
              tab === item.key
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "library" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm h-fit">
            <h2 className="text-lg font-semibold mb-4">导入面经</h2>
            <div className="space-y-3">
              <input
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="公司名称"
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="公司名称"
              />
              <input
                value={position}
                onChange={(e) => setPosition(e.target.value)}
                placeholder="职位（可选）"
                className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="职位"
              />
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="粘贴面经内容..."
                className="w-full h-40 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="面经内容"
              />
              <input
                type="file"
                accept=".pdf,.md,.markdown,.html,.txt"
                onChange={handleFile}
                className="block w-full text-sm text-gray-600 file:mr-3 file:px-3 file:py-1.5 file:rounded file:border-0 file:bg-blue-600 file:text-white"
                aria-label="面经文件"
              />
              <input
                type="file"
                accept=".png,.jpg,.jpeg,.bmp,.webp"
                onChange={(e) => setOcrFile(e.target.files?.[0] || null)}
                className="block w-full text-sm text-gray-600 file:mr-3 file:px-3 file:py-1.5 file:rounded file:border-0 file:bg-cyan-600 file:text-white"
                aria-label="面经截图"
              />
              <div className="flex gap-3">
                <button
                  onClick={handleImportText}
                  disabled={importing}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
                >
                  导入文本
                </button>
                <button
                  onClick={handleImportFile}
                  disabled={importing}
                  className="px-4 py-2 border border-blue-600 text-blue-700 rounded-lg hover:bg-blue-50 disabled:border-gray-400 disabled:text-gray-400 transition"
                >
                  上传文件
                </button>
                <button
                  onClick={handleImportOcr}
                  disabled={importing || !ocrFile}
                  className="px-4 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700 disabled:bg-gray-400 transition"
                >
                  OCR 导入截图
                </button>
              </div>
            </div>
          </section>

          <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">面经列表 ({articles.length})</h2>
            {articles.length === 0 ? (
              <p className="text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg p-6 text-center">
                暂无面经
              </p>
            ) : (
              <div className="space-y-2">
                {articles.map((article) => (
                  <details key={article.id} className="group border border-gray-200 rounded-lg">
                    <summary className="flex items-center justify-between gap-3 p-3 cursor-pointer list-none">
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">
                          {article.company}
                          {article.position ? ` · ${article.position}` : ""}
                        </div>
                        <div className="text-xs text-gray-400 mt-0.5">
                          {article.difficulty || "未标定难度"}
                          {article.tags?.length ? ` · ${article.tags.join("、")}` : ""}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeleteArticle(article);
                        }}
                        className="text-xs text-red-500 hover:text-red-700 flex-shrink-0"
                        aria-label={`删除 ${article.company} 面经`}
                      >
                        删除
                      </button>
                    </summary>
                    <div className="px-3 pb-3 text-sm">
                      {article.questions?.length ? (
                        <ul className="list-disc list-inside space-y-1 mb-3">
                          {article.questions.map((q, idx) => (
                            <li key={idx}>{q}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-gray-400 mb-3">未提取到题目</p>
                      )}
                      <p className="text-gray-600 whitespace-pre-wrap line-clamp-4">{article.raw_content}</p>
                    </div>
                  </details>
                ))}
              </div>
            )}
          </section>
        </div>
      )}

      {tab === "questions" && (
        <div className="space-y-6">
          <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">基于简历 + JD 生成题目</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <select
                value={genResumeId}
                onChange={(e) => setGenResumeId(e.target.value)}
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
                value={genJdId}
                onChange={(e) => setGenJdId(e.target.value)}
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
              <select
                value={genArticleId}
                onChange={(e) => setGenArticleId(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg bg-white"
                aria-label="选择面经"
              >
                <option value="">结合面经（可选）</option>
                {articles.map((article) => (
                  <option key={article.id} value={article.id}>
                    {article.company}
                    {article.position ? ` · ${article.position}` : ""}
                  </option>
                ))}
              </select>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
              >
                {generating ? "生成中..." : "生成题目"}
              </button>
            </div>
          </section>

          {generated.length > 0 && (
            <section className="bg-white border border-green-200 rounded-lg p-5 shadow-sm">
              <h2 className="text-lg font-semibold mb-4 text-green-800">本次生成 ({generated.length})</h2>
              <ul className="space-y-3">
                {generated.map((item, idx) => (
                  <li key={idx} className="flex items-start justify-between gap-4 text-sm">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{item.question}</div>
                      <div className="text-xs text-gray-500 mt-1">
                        {item.category} · {item.difficulty}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
            <h2 className="text-lg font-semibold mb-4">面试题库 ({questions.length})</h2>
            {questions.length === 0 ? (
              <p className="text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg p-6 text-center">
                暂无题目
              </p>
            ) : (
              <ul className="space-y-2">
                {questions.map((item) => (
                  <li key={item.id} className="flex items-start justify-between gap-4 text-sm p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{item.question}</div>
                      {(item.category || item.difficulty) && (
                        <div className="text-xs text-gray-500 mt-1">
                          {[item.category, item.difficulty].filter(Boolean).join(" · ")}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}

      {tab === "simulate" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm h-fit">
            <h2 className="text-lg font-semibold mb-4">模拟面试</h2>
            <div className="space-y-3">
              <select
                value={simResumeId}
                onChange={(e) => setSimResumeId(e.target.value)}
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
                value={simJdId}
                onChange={(e) => setSimJdId(e.target.value)}
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
                onClick={handleStartSimulate}
                disabled={starting || !!sessionId}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
              >
                {starting ? "准备中..." : "开始面试"}
              </button>
            </div>
          </section>

          <section className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm lg:col-span-2">
            {!sessionId && !summary ? (
              <p className="text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg p-6 text-center">
                选择简历和 JD 后开始
              </p>
            ) : summary ? (
              <div>
                <h2 className="text-lg font-semibold mb-4 text-green-800">面试总结</h2>
                <p className="text-sm text-gray-700 whitespace-pre-wrap mb-4">{summary.summary}</p>
                <div className="text-sm text-gray-500">
                  共 {summary.total_questions} 轮
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="text-xs text-blue-600 mb-1">当前问题</div>
                  <div className="text-sm font-medium text-gray-800">{question}</div>
                </div>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="输入你的回答..."
                  className="w-full h-32 p-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  aria-label="回答"
                />
                <button
                  onClick={handleSubmitAnswer}
                  disabled={submitting || !answer.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
                >
                  {submitting ? "分析中..." : "提交回答"}
                </button>

                {history.length > 0 && (
                  <div className="space-y-3 pt-2">
                    {history.map((round, idx) => (
                      <div key={idx} className="p-3 bg-gray-50 border border-gray-200 rounded-lg text-sm">
                        <div className="font-medium mb-1">{round.question}</div>
                        <div className="text-gray-600 mb-1">回答：{round.answer}</div>
                        <div className="text-green-700">反馈：{round.feedback}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
};

export default InterviewPrep;
