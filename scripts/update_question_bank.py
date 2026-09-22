# -*- coding: utf-8 -*-
"""更新面试题库：补充 OfferFlow 核心亮点（事实保真/简历生成/一页约束/变体选择/中文导出），修正过时 Q7。"""
from docx import Document

SRC = 'E:/Desktop/面试题库.docx'
DST = 'E:/Desktop/面试题库_更新版.docx'

doc = Document(SRC)
paras = [p.text for p in doc.paragraphs]

# 1. 修正 Q7（题目 + 紧跟的答案段）
for i, t in enumerate(paras):
    if t.strip().startswith('Q7. 24 项测试'):
        paras[i] = 'Q7. 测试怎么保障的？'
        # 答案紧跟在下一段，替换
        if i + 1 < len(paras):
            paras[i + 1] = ('后端 pytest 覆盖核心模块（鉴权、JD 解析、简历上传优化、生成、匹配、面试、投递、模型配置），'
                            '优化器有专门单测（事实保真、一页约束、字数约束、差距分析）；关键链路用端到端冒烟测试验证（生成→落库→优化→导出）。'
                            '保证业务闭环能跑通、回归不被破坏。')
        break

# 2. 新增题目（插在「三、AgentTrace」之前）
new_questions = [
    'Q9. 简历优化怎么保证 AI 不编造、不丢关键信息？',
    '核心是「事实保真校验」，分两层：硬事实（邮箱、电话、链接、四位年份）一个都不能丢、不能改；软事实（英文技术词、中文关键词、数字）保留度要 ≥60%。优化结果先过校验，不过就回退或精简重试。踩过的坑：URL 正则贪婪匹配，把链接后面紧跟的中文「个人信息」粘成一个整体，LLM 重排间距就被误判成「URL 丢失」；年份区间「2023-2027」被电话正则误判成电话号码。都靠收紧正则修掉了。这套校验是护城河——竞品普遍美化过度甚至编造数字，我这里保证不编造。',
    'Q10. 简历生成怎么做到结构可控、内容够量？',
    '两个关键。一是结构化输出：不让 LLM 吐纯文本，而是输出 JSON（姓名/联系方式/总结/教育/经历/技能/证书），经历拆成「类型+名称+角色+时间+多条要点」，这样后面才能做分段重生成、评分、导出；生成时按求职方向加载同方向真实范文做 few-shot，只参考写法、不照抄事实。二是字数约束：prompt 写死「全文 800 字左右、绝不低于 700」，代码层再兜底——生成后字数不足 700 就带硬性反馈自动重生成一次。',
    'Q11. 简历「一页」怎么保证？内容多时怎么办？',
    '用「三刀裁剪法」做内容取舍，而不是简单缩小字号：删废话（弱动词、空话套话）、并同类（同一能力合并到最有力的一处）、强重点（JD 相关经历前置强化、无关的删减）。内容取舍和格式排版协同：导出层用字号梯度自动压缩兜底，但主导是「取舍」不是「压缩」。',
    'Q12. 逐段重生成为什么给 3 个候选而不是直接覆盖？',
    '覆盖式重写，用户不知道会变成啥、体验差。改成一次生成 3 个变体（偏量化成果/偏技术细节/偏简洁），用户选一个才落库。既给用户控制感，又避免「界面看到的是候选 A、导出却是重新生成的 B」这种不一致。',
    'Q13. 导出 PDF 中文乱码怎么排查解决的？',
    '后端跑在 Docker（Linux）容器里，默认只有 DejaVu 字体、不含中文，中文必然乱码。第一次装 Noto CJK 还是乱码，查出来 reportlab 报「postscript outlines are not supported」——Noto CJK 是 CFF 轮廓，reportlab 只支持 TrueType 轮廓。换成文泉驿（wqy）TrueType 字体解决，容器内验证 PDF 提取文本含中文、无乱码字符。',
]

insert_idx = None
for i, t in enumerate(paras):
    if t.strip().startswith('三、AgentTrace'):
        insert_idx = i
        break

if insert_idx is None:
    raise SystemExit('未找到「三、AgentTrace」标题，终止')

paras[insert_idx:insert_idx] = new_questions

# 3. 重新生成 docx（纯文本段落，与原格式一致）
new_doc = Document()
for t in paras:
    new_doc.add_paragraph(t)
new_doc.save(DST)

print('已生成更新版:', DST)
print('新增题目数: 5（Q9-Q13），修正 Q7')
print('原段落数:', len(doc.paragraphs), '-> 新段落数:', len(paras))
