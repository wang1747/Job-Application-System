"""导入简历语料库：提取技能关键词词频表 + 生成结构化样本，写入 SQLite。

数据来源：
1. 真实抓取：ResumeSample 各岗位 md 里的「参考技能关键字」词频表（从数百份 JD 统计）
2. 结构化生成：基于优秀简历结构规律（分节 + STAR + 量化 + 动词开头）程序化生成的范例样本
"""
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime

DB = "E:/vscode/ai/求职系统/offerflow.db"
CORPUS = "E:/vscode/ai/求职系统/resume_corpus/ResumeSample"

# 抓取仓库里的岗位 → 中文标签
CORPUS_DIRECTIONS = {
    "android": "Android开发",
    "architect": "架构师",
    "c": "C/C++开发",
    "ios": "iOS开发",
    "java": "Java开发",
    "node": "Node.js开发",
    "php": "PHP开发",
    "web": "Web前端",
}

# ============ 结构化样本生成的方向数据 ============
# 每个方向：岗位名、技能、项目/经历名、动词、教育专业
SAMPLE_DIRECTIONS = {
    "tech": {
        "label": "技术研发",
        "positions": ["后端开发工程师", "前端开发工程师", "算法工程师", "测试开发工程师", "大数据开发工程师", "运维开发工程师"],
        "skills": ["Python", "Java", "Go", "MySQL", "Redis", "Docker", "Kubernetes", "Linux", "Git", "FastAPI", "Spring Boot", "React", "Vue", "Nginx", "Elasticsearch", "Kafka"],
        "projects": ["电商交易系统", "内容推荐平台", "日志分析平台", "API网关服务", "实时监控平台", "数据中台", "微服务框架", "分布式爬虫系统"],
        "verbs": ["主导", "重构", "设计", "搭建", "优化", "开发", "落地"],
        "metrics": ["QPS 从 1000 提升到 5000", "响应时间从 800ms 降至 100ms", "支撑日均 10 万请求", "服务可用性提升到 99.9%", "成本降低 40%", "人力效率提升 50%"],
        "majors": ["计算机科学与技术", "软件工程", "数据科学与大数据技术", "人工智能"],
    },
    "product": {
        "label": "产品经理",
        "positions": ["产品经理", "产品助理", "数据产品经理", "AI产品经理"],
        "skills": ["需求分析", "PRD撰写", "Axure", "Figma", "SQL", "数据分析", "用户研究", "项目管理", "A/B测试"],
        "projects": ["用户增长体系", "会员体系搭建", "内容社区改版", "B端管理后台", "搜索推荐优化"],
        "verbs": ["负责", "主导", "推动", "策划", "搭建", "设计"],
        "metrics": ["DAU 提升 30%", "转化率提升 15%", "用户留存率提升 12%", "需求返工率降低 20%", "上线周期缩短 25%"],
        "majors": ["信息管理与信息系统", "市场营销", "计算机科学与技术", "心理学"],
    },
    "design": {
        "label": "设计",
        "positions": ["UI设计师", "交互设计师", "视觉设计师", "用户体验设计师"],
        "skills": ["Figma", "Sketch", "Photoshop", "Illustrator", "设计系统", "用户研究", "交互设计", "视觉设计", "After Effects"],
        "projects": ["App视觉改版", "组件库搭建", "品牌视觉升级", "官网改版", "营销活动设计"],
        "verbs": ["主导", "负责", "搭建", "设计", "优化", "输出"],
        "metrics": ["用户满意度提升 25%", "设计周期缩短 40%", "转化率提升 15%", "组件复用 60+", "品牌认知度提升"],
        "majors": ["视觉传达设计", "工业设计", "数字媒体艺术", "产品设计"],
    },
    "operation": {
        "label": "运营",
        "positions": ["内容运营", "用户运营", "活动运营", "新媒体运营", "电商运营"],
        "skills": ["数据分析", "Excel", "SQL", "内容运营", "用户运营", "活动策划", "社群运营", "公众号", "短视频"],
        "projects": ["公众号内容矩阵", "用户增长活动", "社群运营体系", "电商大促活动", "短视频账号孵化"],
        "verbs": ["负责", "策划", "搭建", "推动", "运营", "孵化"],
        "metrics": ["粉丝增长 3 万", "新增用户 2 万", "获客成本降低 35%", "次日留存率提升 12%", "GMV 提升 45%"],
        "majors": ["新闻传播学", "市场营销", "电子商务", "汉语言文学"],
    },
    "marketing": {
        "label": "市场/销售",
        "positions": ["市场专员", "销售代表", "渠道经理", "品牌专员", "商务拓展"],
        "skills": ["数据分析", "CRM", "渠道拓展", "商务谈判", "市场推广", "客户关系", "Excel", "PPT", "销售漏斗"],
        "projects": ["区域渠道拓展", "品牌推广方案", "大客户销售", "市场活动策划", "渠道体系搭建"],
        "verbs": ["负责", "拓展", "策划", "落地", "维护", "推动"],
        "metrics": ["业绩达成 120%", "线索量提升 45%", "签约客户 30 家", "续约率 90%", "复购金额增长 25%"],
        "majors": ["市场营销", "工商管理", "国际经济与贸易", "广告学"],
    },
    "finance": {
        "label": "金融/财会",
        "positions": ["财务分析师", "会计", "审计助理", "投资分析师", "风控专员"],
        "skills": ["财务分析", "Excel", "Wind", "估值建模", "CPA", "CFA", "税务", "审计", "SQL", "Python"],
        "projects": ["财务尽调项目", "经营分析模型", "预算管理体系", "税务合规优化", "投资价值分析"],
        "verbs": ["参与", "负责", "搭建", "梳理", "输出", "分析"],
        "metrics": ["识别 5 处财务风险", "节省成本 15%", "差错率降至 0", "分析覆盖 100+ 报表", "提升效率 30%"],
        "majors": ["会计学", "金融学", "财务管理", "经济学"],
    },
    "legal": {
        "label": "法律",
        "positions": ["法务专员", "律师助理", "合规专员", "合同管理员"],
        "skills": ["法律检索", "合同审查", "尽职调查", "法律意见书", "合规", "法考", "案例分析", "文书写作"],
        "projects": ["合同审查专项", "尽职调查项目", "合规体系搭建", "法律风险排查", "纠纷案件处理"],
        "verbs": ["协助", "参与", "负责", "梳理", "输出", "跟踪"],
        "metrics": ["审查合同 100+ 份", "规避 8 处法律风险", "出具意见书 20 份", "合规整改 15 项", "案件胜诉率 90%"],
        "majors": ["法学", "民商法学", "知识产权", "经济法学"],
    },
    "education": {
        "label": "教育/教师",
        "positions": ["学科教师", "教研员", "课程研发", "班主任"],
        "skills": ["教学设计", "课件制作", "教研", "班级管理", "教师资格证", "PPT", "普通话", "课程开发"],
        "projects": ["分层教学设计", "校本教材编写", "教研活动组织", "班级管理体系", "在线课程开发"],
        "verbs": ["负责", "设计", "组织", "编写", "推动", "打造"],
        "metrics": ["班级平均分提升 15 分", "课堂满意度 95%", "覆盖学生 200+", "获教学成果奖", "年级排名前 3"],
        "majors": ["教育学", "汉语言文学", "数学与应用数学", "英语"],
    },
    "general": {
        "label": "通用",
        "positions": ["行政专员", "人力资源专员", "项目助理", "管培生"],
        "skills": ["沟通协调", "团队协作", "项目管理", "Excel", "PPT", "时间管理", "问题解决", "学习能力"],
        "projects": ["跨部门协作项目", "流程优化专项", "活动组织策划", "数据整理分析", "文档体系搭建"],
        "verbs": ["负责", "协调", "推动", "整理", "搭建", "优化"],
        "metrics": ["效率提升 30%", "按时交付率 100%", "新人上手时间缩短 50%", "协调 5 个团队", "满意度提升"],
        "majors": ["工商管理", "人力资源管理", "行政管理", "公共事业管理"],
    },
}

SURNAMES = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
GIVEN = ["晓明", "伟", "芳", "娜", "静", "强", "磊", "洋", "欣", "晨", "宇", "雪", "杰", "倩", "鹏"]


def _now():
    return datetime.now().isoformat(timespec="seconds")


def create_tables(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS resume_samples (
            id TEXT PRIMARY KEY,
            direction TEXT NOT NULL,
            label TEXT NOT NULL,
            title TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            structure TEXT,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS resume_skill_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direction TEXT NOT NULL,
            keyword TEXT NOT NULL,
            frequency INTEGER NOT NULL,
            source TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()


def extract_keywords():
    """从抓取仓库提取各岗位技能关键词词频表。"""
    rows = []
    for key, label in CORPUS_DIRECTIONS.items():
        path = os.path.join(CORPUS, key + ".md")
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        idx = text.find("## 参考技能关键字")
        if idx < 0:
            continue
        section = text[idx:]
        for kw, freq in re.findall(r"-\s*([a-zA-Z0-9+#./]+)\s*\((\d+)\)", section):
            rows.append((label, kw.lower(), int(freq)))
    return rows


def generate_samples(total=100):
    """按优秀简历结构规律程序化生成范例样本。"""
    dirs = list(SAMPLE_DIRECTIONS.keys())
    samples = []
    per = total // len(dirs)
    remainder = total % len(dirs)

    name_pool = []
    for s in SURNAMES:
        for g in GIVEN:
            name_pool.append(s + g)

    idx = 0
    for di, dkey in enumerate(dirs):
        d = SAMPLE_DIRECTIONS[dkey]
        count = per + (1 if di < remainder else 0)
        for c in range(count):
            name = name_pool[idx % len(name_pool)]
            idx += 1
            position = d["positions"][(idx + c) % len(d["positions"])]
            major = d["majors"][(idx + c) % len(d["majors"])]
            skills = d["skills"]
            project = d["projects"][(idx + c) % len(d["projects"])]
            project2 = d["projects"][(idx + c + 3) % len(d["projects"])]
            verb = d["verbs"][(idx + c) % len(d["verbs"])]
            verb2 = d["verbs"][(idx + c + 2) % len(d["verbs"])]
            m1 = d["metrics"][(idx + c) % len(d["metrics"])]
            m2 = d["metrics"][(idx + c + 2) % len(d["metrics"])]

            top_skills = skills[:6]
            raw = (
                f"{name}\n"
                f"1380000{(idx * 7) % 10000:04d} | {name.lower()}@example.com\n\n"
                f"求职意向\n{position}\n\n"
                f"教育经历\n"
                f"某大学 {major} 本科 2020-2024\n"
                f"主修课程：专业核心课程\n\n"
                f"项目经历\n"
                f"{project}（核心成员）\n"
                f"- {verb}{project}，{m1}\n"
                f"- {verb2}关键模块，{m2}\n\n"
                f"{project2}（核心成员）\n"
                f"- {verb}方案设计与落地，{m1}\n"
                f"- 跨团队协作推进，按时高质量交付\n\n"
                f"技能\n"
                f"{'、'.join(top_skills)}\n\n"
                f"证书\n"
                f"CET-4/CET-6"
            )
            structure = {
                "sections": ["求职意向", "教育经历", "项目经历", "技能", "证书"],
                "experience_count": 2,
                "bullet_per_experience": 2,
                "quantified_bullets": 2,
                "verb_first": True,
            }
            samples.append(
                {
                    "id": str(uuid.uuid4()),
                    "direction": dkey,
                    "label": d["label"],
                    "title": f"{d['label']} · {position}",
                    "raw_text": raw,
                    "structure": json.dumps(structure, ensure_ascii=False),
                    "source": "generated",
                }
            )
    return samples


def main():
    conn = sqlite3.connect(DB)
    create_tables(conn)

    # 1. 入库真实抓取的词频表
    kw_rows = extract_keywords()
    for label, kw, freq in kw_rows:
        conn.execute(
            "INSERT INTO resume_skill_keywords (direction, keyword, frequency, source, created_at) VALUES (?,?,?,?,?)",
            (label, kw, freq, "github_resumesample", _now()),
        )

    # 2. 入库结构化生成的样本
    samples = generate_samples(100)
    for s in samples:
        conn.execute(
            "INSERT INTO resume_samples (id, direction, label, title, raw_text, structure, source, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (s["id"], s["direction"], s["label"], s["title"], s["raw_text"], s["structure"], s["source"], _now()),
        )

    conn.commit()

    # 3. 统计
    kw_total = conn.execute("SELECT COUNT(*) FROM resume_skill_keywords").fetchone()[0]
    kw_dirs = conn.execute("SELECT COUNT(DISTINCT direction) FROM resume_skill_keywords").fetchone()[0]
    sample_total = conn.execute("SELECT COUNT(*) FROM resume_samples").fetchone()[0]
    sample_dirs = conn.execute("SELECT COUNT(DISTINCT direction) FROM resume_samples").fetchone()[0]
    print(f"技能关键词词频表：{kw_total} 条，覆盖 {kw_dirs} 个岗位方向")
    print(f"简历样本：{sample_total} 篇，覆盖 {sample_dirs} 个方向")
    print("样本各方向分布：")
    for row in conn.execute("SELECT label, COUNT(*) FROM resume_samples GROUP BY label ORDER BY COUNT(*) DESC"):
        print(f"  {row[0]}：{row[1]} 篇")
    conn.close()


if __name__ == "__main__":
    main()
