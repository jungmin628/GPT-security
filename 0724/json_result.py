import json
from pathlib import Path
from langdetect import detect  # 간단한 언어 감지
import re

# === 설정 ===
INPUT_PATH = Path("/root/3/0720/LLMVulGen_3127.json")
OUTPUT_PATH = Path("/root/3/0720/rag_output_filtered.json")

def extract_code_language(code: str):
    # 단순한 언어 판별 예시 (더 정교한 분석 필요시 개선 가능)
    if re.search(r"#include <|std::", code):
        return "cpp"
    elif re.search(r"import java|public class", code):
        return "java"
    elif re.search(r"def | import ", code):
        return "python"
    elif re.search(r"<script>|document\.|console\.", code):
        return "javascript"
    elif re.search(r"SELECT | FROM | WHERE", code, re.IGNORECASE):
        return "sql"
    elif re.search(r"\{.*:.*\}", code) and re.search(r"const|let", code):
        return "javascript"
    elif re.search(r"<[a-z]+>", code) and re.search(r"style|css", code):
        return "html"
    else:
        return "unknown"

def run_rag_with_lang_filter():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    filtered_data = []

    for item in data:
        prompt = item.get("prompt", "")
        vuln_code = item.get("vulnerable_code", "")
        secure_code = item.get("secure_code", "")

        # 1. prompt에서 언어 추출
        prompt_text = prompt.lower()
        if "python" in prompt_text:
            prompt_lang = "python"
        elif "java" in prompt_text:
            prompt_lang = "java"
        elif "javascript" in prompt_text or "js" in prompt_text:
            prompt_lang = "javascript"
        elif "sql" in prompt_text:
            prompt_lang = "sql"
        elif "html" in prompt_text or "css" in prompt_text:
            prompt_lang = "html"
        elif "c++" in prompt_text or "cpp" in prompt_text:
            prompt_lang = "cpp"
        else:
            prompt_lang = "unknown"

        # 2. 실제 코드 언어 추출
        code_lang = extract_code_language(vuln_code if vuln_code else secure_code)

        # 3. 일치하면 포함
        if prompt_lang == code_lang and prompt_lang != "unknown":
            filtered_data.append(item)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Filtered RAG-ready data saved to {OUTPUT_PATH} ({len(filtered_data)} items)")

if __name__ == "__main__":
    run_rag_with_lang_filter()
