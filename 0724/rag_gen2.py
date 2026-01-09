import json
import os
import time
import faiss
import pickle
import argparse
from pathlib import Path
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from neo4j import GraphDatabase
from dotenv import load_dotenv
import re


# === 🌱 환경변수 로드 ===
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([OPENAI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise RuntimeError("❌ 필수 환경변수가 설정되지 않았습니다.")


# === 🔍 코드 언어 감지 (Semgrep 친화적) ===
def detect_code_language(code: str) -> str:
    if re.search(r"#include <|std::", code):
        return "cpp"
    elif re.search(r"public class|import java", code):
        return "java"
    elif re.search(r"\bdef\b|\bimport\b", code):
        return "python"
    elif re.search(r"<script>|document\.|console\.", code):
        return "javascript"
    elif re.search(r"\bSELECT\b|\bFROM\b", code, re.IGNORECASE):
        return "sql"
    elif re.search(r"<html>|<div>", code):
        return "html"
    return "unknown"


# === 🧠 Neo4j 핸들러 ===
class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def fetch_vulnerable_code(self, idx):
        with self.driver.session() as session:
            record = session.run(
                """
                MATCH (n:Vulnerability {id: $id})
                RETURN n.vulnerable_code AS code
                """,
                id=idx
            ).single()
            return record["code"] if record else None


# === 🚀 RAG 실행 ===
def run_rag_pipeline(data_path, faiss_dir, output_path, top_k):
    # --- 데이터 로드 ---
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # --- FAISS 로드 ---
    index = faiss.read_index(str(faiss_dir / "prompt_index.faiss"))
    with open(faiss_dir / "id_mapping.pkl", "rb") as f:
        id_map = pickle.load(f)

    # --- 모델 ---
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    client = OpenAI(api_key=OPENAI_API_KEY)
    neo4j = Neo4jHandler(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    results = []

    for idx, item in enumerate(data):
        try:
            prompt = item["prompt"]
            query_vec = embedder.encode([prompt]).astype("float32")
            _, I = index.search(query_vec, k=top_k)
            db_idx = id_map.get(I[0][0])

            vul_code = neo4j.fetch_vulnerable_code(db_idx)
            if not vul_code:
                continue

            full_prompt = f"{prompt}\n\n{vul_code}"
            lang = detect_code_language(vul_code)

            start = time.time()
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": f"다음 취약 코드를 안전한 코드로 수정하세요:\n{full_prompt}"
                }],
                temperature=0.2
            )
            elapsed = round(time.time() - start, 4)

            secure_code = response.choices[0].message.content.strip()

            results.append({
                "prompt": prompt,
                "vulnerable_code": vul_code,
                "secure_code": secure_code,
                "language": lang,
                "time_taken": elapsed
            })

            if idx % 5 == 0:
                print(f"[{idx}] ✅ {elapsed}s")

        except Exception as e:
            print(f"[{idx}] ❌ Error: {e}")

    neo4j.close()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"🎉 RAG 결과 {len(results)}건 저장 완료 → {output_path}")


# === 🏁 CLI ===
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Secure Code Generation RAG Pipeline")
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--faiss_dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("rag_secure_output.json"))
    parser.add_argument("--top_k", type=int, default=1)

    args = parser.parse_args()

    run_rag_pipeline(
        data_path=args.data,
        faiss_dir=args.faiss_dir,
        output_path=args.output,
        top_k=args.top_k
    )
