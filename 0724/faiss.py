# ✅ [1단계] FAISS + Neo4j 기반 벡터/그래프 저장 (GitHub-safe)

# --- 🔧 라이브러리 임포트 ---
import json
import pickle
import os
import numpy as np
import faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from dotenv import load_dotenv


# --- 🌱 환경변수 로드 ---
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise RuntimeError("❌ Neo4j 환경변수가 설정되지 않았습니다.")


# --- 📁 경로 설정 및 JSON 로드 ---
json_path = "/mnt/data/LLMVulGen_3127.json"
faiss_dir = Path("/mnt/data/faiss_index")
faiss_dir.mkdir(parents=True, exist_ok=True)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)


# --- ✏️ 임베딩 생성 ---
prompts = [entry["prompt"] for entry in data]

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(prompts, show_progress_bar=True)
embeddings = np.array(embeddings, dtype="float32")


# --- 🔎 FAISS 저장 ---
faiss_index = faiss.IndexFlatL2(embeddings.shape[1])
faiss_index.add(embeddings)

faiss_index_path = faiss_dir / "prompt_index.faiss"
id_mapping_path = faiss_dir / "id_mapping.pkl"

faiss.write_index(faiss_index, str(faiss_index_path))

id_mapping = {i: i for i in range(len(prompts))}
with open(id_mapping_path, "wb") as f:
    pickle.dump(id_mapping, f)


# --- 🧠 Neo4j 핸들러 ---
class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clear_all(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def save_prompts(self, prompts):
        with self.driver.session() as session:
            for i, prompt in enumerate(prompts):
                session.run(
                    "CREATE (:Prompt {id: $id, prompt: $prompt})",
                    id=i,
                    prompt=prompt
                )


# --- 🔗 Neo4j 저장 ---
neo4j = Neo4jHandler(
    uri=NEO4J_URI,
    user=NEO4J_USER,
    password=NEO4J_PASSWORD
)

neo4j.clear_all()
neo4j.save_prompts(prompts)
neo4j.close()


# --- ✅ 요약 ---
print({
    "total_prompts": len(prompts),
    "faiss_index": faiss_index_path.name,
    "id_mapping": id_mapping_path.name,
    "neo4j_nodes_inserted": len(prompts)
})
