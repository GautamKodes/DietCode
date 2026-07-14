# Contributing to DietCode 🤝

Thank you for your interest in contributing to DietCode! We welcome contributions from developers of all skill levels to help make this local code cartographer better.

---

## 🛠️ Development Setup

1.  **Fork the repository** on GitHub.
2.  **Clone your fork** locally:
    ```bash
    git clone https://github.com/your-username/DietCode.git
    cd DietCode
    ```
3.  **Install in editable developer mode** inside a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

---

## 📜 Coding Conventions & Guidelines

To maintain code cleanliness and alignment with our codebase requirements:

*   **No Comments:** Please do **not** write or leave comments inside Python source files (`# comments`). We prefer clean, readable, self-documenting code.
*   **Aesthetics:** All console output must utilize the `Rich` package commands to maintain unified panels, trees, and colorized tables.
*   **Offline-First:** Do not add third-party libraries or network calls that break the 100% offline local-only requirement of the tool.

---

## 📥 Submission Process

1.  **Create a new branch** for your feature or bugfix:
2.  **Commit your changes** with descriptive commit messages.
3.  **Push to your fork** and submit a **Pull Request (PR)** against our `master` branch.
4.  Write a clear description of what your PR changes and why.
