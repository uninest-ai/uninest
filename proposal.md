# UniNest V2『一晚升级包』执行文档（混合检索 + 指标 + 小评测）

> 目标：在 **4–6 小时内** 完成“最小可行”的升级，让 UniNest 具备 **混合检索（BM25+向量+RRF）**、**延迟/QPS 指标**、**小评测集对比** 三个招聘方最关注的能力，并产出可展示的 README 与 90s 演示。

---

## 0. 范围与成果（一次就位）

**不改架构**（FastAPI + PostgreSQL + React/Next.js 保持不变），新增：

1. **BM25（Postgres FTS）** + **向量相似度（应用层余弦）** + **RRF 融合**
2. **/metrics** 端点：P50/P95/P99、QPS（近 1 分钟）
3. **微型评测集（10–20 条查询）**：Recall@10 / NDCG@10 对比
4. **README 顶部“一页图 + 两个数字”** + **90s 录屏**

**交付清单**

* 代码：`/server`（FastAPI）与 `/db`（SQL 脚本），`/eval`（评测脚本）
* 文档：README 顶部结果图与数值；/docs/ 下放对比图
* 演示：`demo.mp4`（60–90s）

---

## 1. 预备条件（15–20 min）

* `properties` 表中已有字段：`id`, `title`, `description`, `price`, `amenities`, `lat`, `lng`…（按你现状）
* Python 依赖：`fastapi`, `uvicorn`, `numpy`, `scikit-learn`（可选）, `psycopg2` or `asyncpg`
* **注意**：无 pgvector 依赖；向量相似度在应用层做。

---

## 2. 步骤 A：BM25（Postgres FTS）索引（30–45 min）

**2.1 建 tsvector 列与索引**

```sql
ALTER TABLE properties ADD COLUMN IF NOT EXISTS tsv tsvector;
UPDATE properties
  SET tsv = to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,''));
CREATE INDEX IF NOT EXISTS idx_properties_tsv ON properties USING GIN(tsv);
```

如用到中文，改为相应的文本配置，或先英文版落地（速度优先）。

**2.2 查询样例**

```sql
-- 取 BM25 排名（Postgres 中 ts_rank 近似 BM25）
SELECT id, ts_rank(tsv, plainto_tsquery('english', $1)) AS bm25_score
FROM properties
WHERE tsv @@ plainto_tsquery('english', $1)
ORDER BY bm25_score DESC
LIMIT $2;
```

---

## 3. 步骤 B：向量预计算 + 应用层相似度（60–90 min）

**3.1 生成并落库嵌入（一次性脚本）**

```python
# scripts/precompute_embeddings.py
import json, numpy as np, psycopg2
from sentence_transformers import SentenceTransformer

conn = psycopg2.connect("dbname=... user=... password=... host=...")
cur = conn.cursor()
cur.execute("SELECT id, coalesce(title,'') || ' ' || coalesce(description,'') FROM properties")
rows = cur.fetchall()

model = SentenceTransformer('all-MiniLM-L6-v2')  # 轻量优先

for pid, text in rows:
    emb = model.encode(text, normalize_embeddings=True).astype(np.float32)
    cur.execute(
        """
        INSERT INTO property_embeddings(id, embedding)
        VALUES (%s, %s)
        ON CONFLICT (id) DO UPDATE SET embedding = EXCLUDED.embedding
        """,
        (pid, json.dumps(emb.tolist()))
    )

conn.commit(); cur.close(); conn.close()
```

**建表**（若无）：

```sql
CREATE TABLE IF NOT EXISTS property_embeddings (
  id BIGINT PRIMARY KEY,
  embedding JSONB NOT NULL
);
```

**3.2 应用层相似度（FastAPI 内部）**

* 先从 BM25 拿前 `K_bm25`（如 200）作为候选，再对候选计算余弦；
* 再补充“全局向量 TopK”（如 50）用于召回长尾。

```python
# server/hybrid_search.py
import json, numpy as np
from numpy.linalg import norm

# 余弦相似度
def cos(a, b):
    na, nb = norm(a), norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b)/(na*nb))

# RRF 融合
def rrf_score(ranks, k=60):
    s = {}
    for order in ranks:  # order: list of ids 按各自排序
        for idx, _id in enumerate(order):
            s[_id] = s.get(_id, 0.0) + 1.0/(k + idx)
    return sorted(s.items(), key=lambda x: x[1], reverse=True)
```

---

## 4. 步骤 C：混合检索 API（RRF 融合）（30–40 min）

**查询流程**

1. 计算 query 的向量 `q_emb`（同一模型）
2. **BM25 候选**：SQL 取前 `K_bm25` id
3. **向量候选**：从 `property_embeddings` 拉一批（可以全量在内存中缓存一次，或先取 TopN 简化）
4. 对两个候选序列分别排序得到 id 列表，喂给 `rrf_score` 合并
5. 返回 TopK。

**FastAPI 端点**（示例）

```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/search")
def search(q: str, k: int = 20):
    # 1) q_emb = ...
    # 2) ids_bm25 = query_bm25_ids(q, K_bm25=200)
    # 3) ids_vec = topn_ids_by_vector(q_emb, N=50)  # 简版：暴力余弦或小索引
    # 4) rrf 合并
    merged = rrf_score([ids_bm25, ids_vec])
    # 5) 取 TopK 并拉取属性信息
    top_ids = [i for i, _ in merged[:k]]
    return fetch_properties(top_ids)
```

> **可选 +10 分**：对 `q` 做 LRU 缓存 60s，进一步降低 P95。

---

## 5. 步骤 D：极简指标 /metrics（20 min）

```python
# server/metrics.py
import time
from collections import deque
from fastapi import FastAPI, Request

lat_hist = deque(maxlen=1000)
req_1m = deque()

def attach_metrics(app: FastAPI):
    @app.middleware("http")
    async def timing_mw(request: Request, call_next):
        t0 = time.perf_counter()
        resp = await call_next(request)
        dt = (time.perf_counter() - t0) * 1000
        lat_hist.append(dt)
        now = time.time(); req_1m.append(now)
        while req_1m and now - req_1m[0] > 60: req_1m.popleft()
        return resp

    @app.get("/metrics")
    def metrics():
        arr = sorted(lat_hist); n = len(arr)
        def perc(p):
            if n == 0: return None
            idx = min(int(p*(n-1)), n-1); return round(arr[idx], 1)
        return {
            "latency_ms": {"p50": perc(0.5), "p95": perc(0.95), "p99": perc(0.99)},
            "qps_1m": round(len(req_1m)/60, 2)
        }
```

* 在 `main.py` 里 `attach_metrics(app)`。
* 用 `ab`/`wrk`/简单脚本压 200–500 次请求，截图 `/metrics` 返回的 JSON。

---

## 6. 步骤 E：微型评测集（60 min）

**6.1 标注 10–20 条真实查询**（CSV：`query, ideal_ids`，`ideal_ids` 为 id 列表）
**6.2 评测脚本**（Recall@10/NDCG@10）

```python
# eval/offline_eval.py
import csv, math
from client import search_old, search_new  # 旧策略 vs 新策略

def dcg(rels):
    return sum((1.0/math.log2(i+2) if r else 0.0) for i, r in enumerate(rels))

def ndcg_at_k(pred, truth, k=10):
    rels = [1 if x in truth else 0 for x in pred[:k]]
    idcg = dcg(sorted(rels, reverse=True)) or 1.0
    return dcg(rels)/idcg

def recall_at_k(pred, truth, k=10):
    return len(set(pred[:k]) & set(truth)) / max(1, len(truth))

def main():
    rows = list(csv.DictReader(open('queries.csv')))
    r_old = []; r_new = []; n_old = []; n_new = []
    for row in rows:
        q = row['query']; truth = [int(x) for x in row['ideal_ids'].split()]
        p_old = [r['id'] for r in search_old(q, k=10)]
        p_new = [r['id'] for r in search_new(q, k=10)]
        r_old.append(recall_at_k(p_old, truth)); r_new.append(recall_at_k(p_new, truth))
        n_old.append(ndcg_at_k(p_old, truth));  n_new.append(ndcg_at_k(p_new, truth))
    print('Recall@10 old/new:', round(sum(r_old)/len(r_old),3), round(sum(r_new)/len(r_new),3))
    print('NDCG@10  old/new:', round(sum(n_old)/len(n_old),3), round(sum(n_new)/len(n_new),3))

if __name__ == '__main__':
    main()
```

**输出**粘到 README 顶部（占位）：

* `Recall@10: old 0.42 → new 0.61 (+0.19)`
* `NDCG@10: old 0.46 → new 0.62 (+0.16)`

---

## 7. 步骤 F：README 与 90s 演示（45 min）

**README 顶部“一页图”**：

* 流程示意：Query → BM25（K1） & Vector（K2） → RRF → TopK → /metrics 观测
* 两个数字：`Recall@10 +Δpp`、`P95 ↓Δms`（来自 /metrics + 压测）
* 项目要点：Hybrid Retrieval｜RRF｜P95/P99｜QPS｜Offline Eval

---

## 8. 时间建议（顺序与用时）

1. BM25 建索引与验证（45m）
2. 预计算嵌入 + 简易相似度（75m）
3. Hybrid API + RRF 融合（30–40m）
4. /metrics 指标端点（20m）
5. 微型评测（60m）
6. README + 录屏（45m）

---

## 9. 回滚与风险

* 任一步失败：回退到“BM25 单路 + /metrics”，也能交付“可度量”版本（仍有展示价值）。
* 嵌入模型拉取慢：临时改用更小模型或本地缓存；或只对候选做向量检索。
* 压测无工具：写 20 行 Python 循环请求即可（记录平均与 P95）。

---

## 10. 勾选清单（完成即打勾）

* [ ] BM25 建表/索引/查询
* [ ] 预计算嵌入入库
* [ ] Hybrid API（BM25+Vector+RRF）
* [ ] /metrics（P50/P95/P99、QPS-1m）
* [ ] 微型评测（Recall@10/NDCG@10 对比）
* [ ] README 顶部一页图 + 两个数字
* [ ] 90s 演示录屏

> 完成以上 7 项，你就能在简历与面试中，用最小改动讲清楚：**效果提升、延迟与吞吐、可观测与评测方法、工程权衡与可扩展位**。
