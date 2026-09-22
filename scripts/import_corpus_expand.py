# -*- coding: utf-8 -*-
"""批量导入扩充语料到共享语料库（corpus_items + Chroma）。

数据来源：scripts/corpus_data/*.py（简历范文/写作指南/面试题库/JD + 本地开源模板）。
每条自动做方向分类 + 技能打标签 + 整篇 embedding（复用 add_corpus_item）。

用法（backend 容器内 /app，或本地 backend 可 import app 时）：
    python scripts/import_corpus_expand.py [--limit N] [--dry-run]
"""
import glob
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.dirname(_HERE), os.path.join(_HERE, "..", "backend")):
    if os.path.isdir(os.path.join(_p, "app")):
        sys.path.insert(0, _p)
        break

from app.core.database import init_db, SessionLocal          # noqa: E402
from app.modules.corpus.services import add_corpus_item, count_corpus  # noqa: E402

# 模块 -> (变量名, item_type)
KEY_MAP = [
    ("RESUME_SAMPLES", "resume"),
    ("GUIDE_SAMPLES", "resume"),
    ("INTERVIEW_SAMPLES", "interview"),
    ("JD_SAMPLES", "jd"),
]


def load_all() -> list:
    """加载 corpus_data 目录下所有语料模块，返回 [(item_type, raw_text, tags), ...]"""
    items = []
    d = os.path.join(_HERE, "corpus_data")
    for f in sorted(glob.glob(os.path.join(d, "*.py"))):
        if f.endswith("__init__.py"):
            continue
        name = os.path.splitext(os.path.basename(f))[0]
        spec = importlib.util.spec_from_file_location(name, f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        n = 0
        for key, item_type in KEY_MAP:
            for entry in getattr(mod, key, []):
                raw = (entry.get("raw_text") or "").strip()
                if len(raw) < 40:
                    continue
                items.append((item_type, raw, entry.get("tags") or []))
                n += 1
        print(f"  加载 {name:<26} {n:>3} 条")
    return items


def main() -> None:
    dry = "--dry-run" in sys.argv
    limit = None
    for i, a in enumerate(sys.argv):
        if a == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])
        elif a.startswith("--limit="):
            limit = int(a.split("=")[1])

    items = load_all()
    print(f"\n共 {len(items)} 条语料待导入")
    if limit:
        items = items[:limit]
        print(f"仅导入前 {limit} 条（--limit）")
    if dry:
        print("DRY-RUN 模式，不实际写入")
        from collections import Counter
        c = Counter(t for t, _, _ in items)
        print("类型分布:", dict(c))
        return

    init_db()
    db = SessionLocal()
    before = count_corpus(db)
    print("导入前语料库:", before)

    ok = fail = 0
    try:
        for i, (item_type, raw, tags) in enumerate(items, 1):
            try:
                add_corpus_item(
                    item_type=item_type,
                    raw_text=raw,
                    db=db,
                    tags=tags,
                    source="import",
                    auto_tag=True,
                )
                ok += 1
            except Exception as exc:  # noqa: BLE001
                fail += 1
                if fail <= 10:
                    print(f"  [跳过] 第{i}条 {type(exc).__name__}: {exc}")
            if i % 50 == 0:
                print(f"  进度 {i}/{len(items)}（成功 {ok} / 失败 {fail}）")
    finally:
        after = count_corpus(db)
        db.close()

    print(f"\n导入完成：成功 {ok} / 失败 {fail}")
    print("导入后语料库:", after)


if __name__ == "__main__":
    main()
