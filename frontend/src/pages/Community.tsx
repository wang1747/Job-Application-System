import { type FC, useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { CommunityPost, CommunityPostDetail, Feedback } from "../types";
import { Badge, Card, EmptyState, Modal, PageHeader, Tabs, Icons } from "../components/ui";

const POST_CATEGORIES = ["经验分享", "面经", "offer分享", "资源推荐", "其他"];
const FEEDBACK_CATEGORIES = ["功能建议", "问题反馈", "体验优化", "其他"];

const FEEDBACK_STATUS: Record<string, { label: string; color: "gray" | "blue" | "green" | "amber" | "red" }> = {
  pending: { label: "待处理", color: "amber" },
  accepted: { label: "已采纳", color: "green" },
  declined: { label: "已婉拒", color: "gray" },
  replied: { label: "已回复", color: "blue" },
};

const formatDate = (iso?: string) => {
  if (!iso) return "-";
  const d = new Date(iso);
  return `${d.toLocaleDateString()} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
};

const btnPrimary =
  "rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700 disabled:opacity-50";
const btnGhost =
  "rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50";
const inputCls =
  "w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500";

const Community: FC = () => {
  const [tab, setTab] = useState<"posts" | "feedback">("posts");

  // 分享墙
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [postCategory, setPostCategory] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [postForm, setPostForm] = useState({ title: "", content: "", category: "经验分享", tags: "" });
  const [detail, setDetail] = useState<CommunityPostDetail | null>(null);
  const [commentText, setCommentText] = useState("");

  // 建议
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [fbCategory, setFbCategory] = useState("");
  const [showFb, setShowFb] = useState(false);
  const [fbForm, setFbForm] = useState({ category: "功能建议", title: "", content: "" });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadPosts = useCallback(async (category = postCategory) => {
    try {
      const res = await api.community.listPosts(category || undefined, 1, 50);
      if (res.success && res.data) {
        setPosts(res.data.items);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }, [postCategory]);

  const loadFeedbacks = useCallback(async (category = fbCategory) => {
    try {
      const res = await api.feedback.list(category || undefined, 1, 50);
      if (res.success && res.data) {
        setFeedbacks(res.data.items);
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }, [fbCategory]);

  useEffect(() => {
    loadPosts();
    loadFeedbacks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const submitPost = async () => {
    if (!postForm.title.trim() || !postForm.content.trim()) return;
    setLoading(true);
    try {
      const tags = postForm.tags.split(/[,，\s]+/).filter(Boolean);
      await api.community.createPost({
        title: postForm.title, content: postForm.content,
        category: postForm.category, tags,
      });
      setShowCreate(false);
      setPostForm({ title: "", content: "", category: "经验分享", tags: "" });
      await loadPosts();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (id: string) => {
    try {
      const res = await api.community.postDetail(id);
      if (res.success && res.data) setDetail(res.data);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const submitComment = async () => {
    if (!detail || !commentText.trim()) return;
    try {
      await api.community.addComment(detail.id, commentText);
      setCommentText("");
      await openDetail(detail.id);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const likePost = async (id: string) => {
    try {
      await api.community.toggleLike(id);
      await loadPosts();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const submitFeedback = async () => {
    if (!fbForm.title.trim() || !fbForm.content.trim()) return;
    setLoading(true);
    try {
      await api.feedback.create(fbForm);
      setShowFb(false);
      setFbForm({ category: "功能建议", title: "", content: "" });
      await loadFeedbacks();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const likeFeedback = async (id: string) => {
    try {
      await api.feedback.toggleLike(id);
      await loadFeedbacks();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div>
      <PageHeader
        title="交流中心"
        subtitle="和同行分享求职经验，给产品提建议"
        icon={Icons.interview}
      />

      <Tabs
        tabs={[
          { key: "posts", label: "分享墙", icon: Icons.interview },
          { key: "feedback", label: "建议反馈", icon: Icons.alert },
        ]}
        active={tab}
        onChange={(k) => setTab(k as "posts" | "feedback")}
      />

      {error && (
        <div className="mb-4 flex items-center justify-between rounded-lg bg-rose-50 px-4 py-2 text-sm text-rose-600">
          <span>{error}</span>
          <button className="text-rose-400 hover:text-rose-600" onClick={() => setError("")}>×</button>
        </div>
      )}

      {tab === "posts" ? (
        <div>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              <button className={`${postCategory === "" ? btnPrimary : btnGhost}`} onClick={() => { setPostCategory(""); loadPosts(""); }}>
                全部
              </button>
              {POST_CATEGORIES.map((c) => (
                <button key={c} className={`${postCategory === c ? btnPrimary : btnGhost}`}
                  onClick={() => { setPostCategory(c); loadPosts(c); }}>
                  {c}
                </button>
              ))}
            </div>
            <button className={btnPrimary} onClick={() => setShowCreate(true)}>发布分享</button>
          </div>

          {posts.length === 0 ? (
            <EmptyState icon={Icons.interview} title="还没有分享" description="来发布第一条求职经验或面经吧" />
          ) : (
            <div className="space-y-3">
              {posts.map((p) => (
                <Card key={p.id} hover className="cursor-pointer p-5">
                  <div onClick={() => openDetail(p.id)}>
                    <div className="flex items-start justify-between gap-4">
                      <h3 className="text-base font-semibold leading-6 text-slate-900">{p.title}</h3>
                      <span className="shrink-0">
                        <Badge color="indigo">{p.category}</Badge>
                      </span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">{p.content}</p>
                    <div className="mt-4 flex items-center gap-5 border-t border-slate-100 pt-3 text-xs text-slate-400">
                      <span>{p.author}</span>
                      <span>{formatDate(p.created_at)}</span>
                      <button
                        className="flex items-center gap-1 rounded-md px-1.5 py-0.5 transition hover:bg-rose-50 hover:text-rose-500"
                        onClick={(e) => { e.stopPropagation(); likePost(p.id); }}
                      >
                        ♥ {p.like_count}
                      </button>
                      <span className="flex items-center gap-1">💬 {p.comment_count}</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              <button className={`${fbCategory === "" ? btnPrimary : btnGhost}`} onClick={() => { setFbCategory(""); loadFeedbacks(""); }}>
                全部
              </button>
              {FEEDBACK_CATEGORIES.map((c) => (
                <button key={c} className={`${fbCategory === c ? btnPrimary : btnGhost}`}
                  onClick={() => { setFbCategory(c); loadFeedbacks(c); }}>
                  {c}
                </button>
              ))}
            </div>
            <button className={btnPrimary} onClick={() => setShowFb(true)}>提建议</button>
          </div>

          {feedbacks.length === 0 ? (
            <EmptyState icon={Icons.alert} title="还没有建议" description="你的建议能帮助产品变得更好" />
          ) : (
            <div className="space-y-3">
              {feedbacks.map((f) => {
                const st = FEEDBACK_STATUS[f.status] || FEEDBACK_STATUS.pending;
                return (
                  <Card key={f.id} hover className="p-5">
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge color="indigo">{f.category}</Badge>
                          <Badge color={st.color}>{st.label}</Badge>
                        </div>
                        <h3 className="mt-2 text-base font-semibold leading-6 text-slate-900">{f.title}</h3>
                      </div>
                      <button className="flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-sm text-slate-400 transition hover:bg-rose-50 hover:text-rose-500"
                        onClick={() => likeFeedback(f.id)}>
                        ♥ {f.like_count}
                      </button>
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-500">{f.content}</p>
                    {f.admin_reply && (
                      <div className="mt-3 rounded-lg bg-brand-50 px-3 py-2 text-sm leading-6 text-slate-700">
                        <span className="font-medium text-brand-600">官方回复：</span>{f.admin_reply}
                      </div>
                    )}
                    <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-3 text-xs text-slate-400">
                      <span>{f.author}</span>
                      <span>{formatDate(f.created_at)}</span>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 发布分享 Modal */}
      <Modal
        open={showCreate}
        onClose={() => setShowCreate(false)}
        title="发布分享"
        footer={
          <>
            <button className={btnGhost} onClick={() => setShowCreate(false)}>取消</button>
            <button className={btnPrimary} onClick={submitPost} disabled={loading}>发布</button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm text-slate-600">分类</label>
            <select className={inputCls} value={postForm.category}
              onChange={(e) => setPostForm({ ...postForm, category: e.target.value })}>
              {POST_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">标题</label>
            <input className={inputCls} placeholder="一句话概括你的分享" value={postForm.title}
              onChange={(e) => setPostForm({ ...postForm, title: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">内容</label>
            <textarea className={`${inputCls} min-h-32`} placeholder="详细说说你的经验或经历…" value={postForm.content}
              onChange={(e) => setPostForm({ ...postForm, content: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">标签（可选，逗号分隔）</label>
            <input className={inputCls} placeholder="如：Java, 后端, 校招" value={postForm.tags}
              onChange={(e) => setPostForm({ ...postForm, tags: e.target.value })} />
          </div>
        </div>
      </Modal>

      {/* 帖子详情 Modal */}
      <Modal
        open={!!detail}
        onClose={() => setDetail(null)}
        title={detail?.title || ""}
        footer={<button className={btnGhost} onClick={() => setDetail(null)}>关闭</button>}
      >
        {detail && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <span>{detail.author}</span>
              <Badge color="indigo">{detail.category}</Badge>
              <span>{formatDate(detail.created_at)}</span>
            </div>
            <p className="whitespace-pre-wrap text-sm text-slate-700">{detail.content}</p>

            <div className="border-t border-slate-100 pt-4">
              <h4 className="mb-3 text-sm font-semibold text-slate-700">评论（{detail.comments.length}）</h4>
              <div className="space-y-3">
                {detail.comments.length === 0 && (
                  <p className="text-xs text-slate-400">还没有评论，来抢沙发</p>
                )}
                {detail.comments.map((c) => (
                  <div key={c.id} className="rounded-lg bg-slate-50 px-3 py-2">
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span className="font-medium text-slate-600">{c.author}</span>
                      <span>{formatDate(c.created_at)}</span>
                    </div>
                    <p className="mt-1 text-sm text-slate-700">{c.content}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 flex gap-2">
                <input className={inputCls} placeholder="写下你的评论…" value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") submitComment(); }} />
                <button className={btnPrimary} onClick={submitComment}>发送</button>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* 提建议 Modal */}
      <Modal
        open={showFb}
        onClose={() => setShowFb(false)}
        title="提出建议"
        footer={
          <>
            <button className={btnGhost} onClick={() => setShowFb(false)}>取消</button>
            <button className={btnPrimary} onClick={submitFeedback} disabled={loading}>提交</button>
          </>
        }
      >
        <div className="space-y-3">
          <div>
            <label className="mb-1 block text-sm text-slate-600">分类</label>
            <select className={inputCls} value={fbForm.category}
              onChange={(e) => setFbForm({ ...fbForm, category: e.target.value })}>
              {FEEDBACK_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">标题</label>
            <input className={inputCls} placeholder="一句话概括你的建议" value={fbForm.title}
              onChange={(e) => setFbForm({ ...fbForm, title: e.target.value })} />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">详细说明</label>
            <textarea className={`${inputCls} min-h-32`} placeholder="描述你希望改进的功能或遇到的问题…" value={fbForm.content}
              onChange={(e) => setFbForm({ ...fbForm, content: e.target.value })} />
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Community;
