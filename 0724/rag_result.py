import json
import time
import openai
from pathlib import Path

# --- 설정 ---
DATA_PATH = Path("LLMVulGen_3127.json")
OUT_PATH = Path("results_with_cost.json")

openai.api_key = "your-openai-api-key"  # ✅ API 키 입력

# --- 데이터 로드 ---
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- GPT 호출 함수 ---
def call_gpt(prompt):
    start_time = time.time()
    response = openai.ChatCompletion.create(
        model="gpt-4",  # 또는 "gpt-4o"
        messages=[
            {"role": "system", "content": "You are a secure code generator."},
            {"role": "user", "content": f"Please provide a secure version of the following vulnerable code:\n\n{prompt}"}
        ],
        temperature=0.2,
    )
    end_time = time.time()
    
    secure_code = response.choices[0].message.content
    total_tokens = response.usage.total_tokens
    cost = (total_tokens / 1000) * 0.01  # gpt-4 기준, 적절히 수정
    
    return secure_code, end_time - start_time, cost

# --- 실행 및 측정 ---
results = []
total_time = 0
total_cost = 0

for i, item in enumerate(data):
    try:
        prompt = item["vulnerable_code"]
        secure_code, duration, cost = call_gpt(prompt)
        
        results.append({
            "prompt": item["prompt"],
            "vulnerable_code": item["vulnerable_code"],
            "secure_code": secure_code,
            "time_taken": duration,
            "cost": cost
        })
        
        total_time += duration
        total_cost += cost

        if i % 5 == 0:
            print(f"[{i}] secure_code snippet:\n{secure_code[:300]}\n---")
    
    except Exception as e:
        print(f"[{i}] Error: {e}")
        continue

# --- 저장 ---
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

# --- 통계 출력 ---
avg_time = total_time / len(results)
avg_cost = total_cost / len(results)

print(f"\n✅ 총 테스트 수: {len(results)}")
print(f"⏱️ 총 시간: {total_time:.2f}초")
print(f"⏱️ 평균 시간: {avg_time:.2f}초")
print(f"💰 총 비용: ${total_cost:.4f}")
print(f"💰 평균 비용: ${avg_cost:.4f}")
