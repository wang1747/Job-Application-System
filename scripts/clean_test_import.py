# -*- coding: utf-8 -*-
"""清理试导入阶段写入的测试语料（source=import 最近 N 条）。"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.dirname(_HERE), os.path.join(_HERE, "..", "backend")):
    if os.path.isdir(os.path.join(_p, "app")):
        sys.path.insert(0, _p)
        break

from app.core.database import init_db, SessionLocal
from app.models.corpus import CorpusItem
from app.modules.corpus.services import delete_corpus, count_corpus

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5

init_db()
db = SessionLocal()
before = count_corpus(db)
rows = (db.query(CorpusItem)
        .filter(CorpusItem.source == "import")
        .order_by(CorpusItem.created_at.desc())
        .limit(N).all())
ids = [r.id for r in rows]
for r in rows:
    delete_corpus(r.id, db)
after = count_corpus(db)
print("删除前:", before)
print(f"已删除最近 {len(ids)} 条测试语料")
print("删除后:", after)
db.close()
