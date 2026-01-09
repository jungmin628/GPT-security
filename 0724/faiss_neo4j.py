import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# === 0. 환경변수 로드 ===
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    raise RuntimeError("❌ Neo4j 환경변수가 설정되지 않았습니다.")

# === 1. Neo4j 핸들러 정의 ===
class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def clear_db(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ Neo4j DB 초기화 완료")
    
    def create_vuln_node(self, idx, prompt, vuln_code, secure_code):
        with self.driver.session() as session:
            session.run(
                """
                CREATE (n:Vulnerability {
                    id: $id,
                    prompt: $prompt,
                    vulnerable_code: $vuln_code,
                    secure_code: $secure_code
                })
                """,
                id=idx,
                prompt=prompt,
                vuln_code=vuln_code,
                secure_code=secure_code
            )

# === 2. JSON 파일 로드 ===
json_path = Path("C:/WHS/0724/LLMVulGen_3127.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"📦 데이터 로드 완료: 총 {len(data)}개")

# === 3. Neo4j 접속 및 초기화 ===
neo4j_handler = Neo4jHandler(
    uri=NEO4J_URI,
    user=NEO4J_USER,
    password=NEO4J_PASSWORD
)

neo4j_handler.clear_db()

# === 4. 모든 항목 저장 ===
for idx, item in enumerate(data):
    prompt = item.get("prompt", "")
    vuln_code = item.get("vulnerable_code", "")
    secure_code = item.get("secure_code", "")
    neo4j_handler.create_vuln_node(idx, prompt, vuln_code, secure_code)

neo4j_handler.close()
print("🎉 모든 데이터가 Neo4j에 저장되었습니다.")
