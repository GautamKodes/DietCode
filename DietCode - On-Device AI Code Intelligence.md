Vision
A terminal-first tool that understands a codebase locally. Instead of generating code, it
builds a semantic map of the repository to help developers navigate, assess impact,
and generate context for AI coding assistants.
Problem
Developers spend hours understanding unfamiliar repositories. Existing AI coding
assistants waste time exploring project structure and often lack repository context.
Solution
Index the repository, parse code using Tree-sitter, build a dependency graph, create
semantic embeddings, and answer developer questions entirely on-device.
Core Features
1. Index repository.
2. Semantic search.
3. Impact analysis.
4. Code journey visualization.
5. Duplicate logic detection.
6. Mission Brief generation for developers or AI coding agents.
Mission Brief
Given a task like 'Add GST support', generate a Markdown document containing
relevant files, dependency graph, risks, suggested tests, coding conventions, and
affected modules. Optionally rewrite it with a small local LLM.
Architecture
Repository -> Tree-sitter Parser -> SQLite + Knowledge Graph (NetworkX) ->
Embedding Model -> Vector Search -> Context Builder -> Optional Local LLM -> CLI
Output.
Tech Stack
Python, Typer, Tree-sitter, NetworkX, SQLite, ONNX Runtime, FAISS (or SQLite cosine
search), Rich. Optional: Qwen2.5-Coder 1.5B/3B or SmolLM2.
Hackathon Roadmap (Optimized 3-Day Plan)
Day 1: Setup CLI (Typer/Rich), Database Schema (SQLite), and Indexer/AST Parser (Python & JS/TS).
Day 2: Update parser and indexer to extract and save import statements to SQLite.
Day 3: Build Dependency Graph (NetworkX), Impact Analysis, Semantic Search, Mission Brief generator, Local LLM (Ollama), and terminal UI polish.
Day 4 (Post-Dev): README, demonstration video, and final bug triage.

Why It Fits
Runs locally, protects proprietary code, minimizes LLM usage, avoids runtime parsing issues by using pre-compiled parsers, and showcases practical on-device AI.

Theme:
Theme: On Device AI

Your project should focus on AI that runs locally.
You can build around:
Local AI models
Browser-based AI
Mobile on-device AI
Desktop AI tools
Edge or embedded AI
Offline-first AI apps
Privacy-focused AI utilities
Lightweight local inference
Cloud services are allowed for support features like hosting, authentication, storage, databases, or deployment.
The main AI feature, however, should run on-device, locally, in-browser, on edge, or on embedded hardware.