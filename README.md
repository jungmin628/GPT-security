# 🔐 ChatGPT-security
### Security-Focused Code Generation with RAG

A research project combining **FAISS vector search** and **Neo4j graph retrieval** to reduce security vulnerabilities in LLM-generated code.

📄 **Publication:** KSC2025 · **First Author**  
*LLM 코드 생성의 보안 강화와 실행 비용 최적화를 위한 통합 접근 방법 연구*

## Overview

The pipeline retrieves CWE-related context and secure code examples to guide LLMs toward safer code generation. Generated code is evaluated using **Semgrep**.

## System Architecture

<img width="531" alt="System architecture" src="https://github.com/user-attachments/assets/5cdba75a-c0b8-42d0-a6e4-57e31ff95f06" />

## Method

- **Dataset:** 3,127 code samples with prompts and vulnerable/secure code pairs (`LLMVulGen_3127.json`)
- **Retrieval:** FAISS search results mapped to Neo4j nodes
- **Generation:** RAG prompts incorporating CWE information and secure coding patterns
- **Language consistency:** Align generated code with the requested language for static analysis

## Tech Stack

Python · OpenAI GPT · FAISS · Neo4j · Semgrep · Jupyter Notebook  
**Experimental:** SafeCoder fine-tuning

## Evaluation

- Measure code generation time per prompt.
- Detect CWE-related vulnerabilities using Semgrep.
- Compare security findings with and without RAG.
