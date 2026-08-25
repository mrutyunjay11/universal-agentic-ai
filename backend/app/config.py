from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Local Coding Agent"
    debug: bool = False
    log_level: str = "INFO"

    ollama_host: str = "http://localhost:11434"
    primary_model: str = "qwen2.5-coder:32b"
    fast_model: str = "qwen2.5-coder:14b"
    embedding_model: str = "nomic-embed-text"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    primary_model_ctx: int = 32768
    fast_model_ctx: int = 16384
    embedding_dim: int = 768

    qdrant_path: str = "./qdrant_data"
    sqlite_path: str = "./session_data.db"

    max_tool_calls_per_session: int = 50
    max_autonomous_runtime_seconds: int = 600
    max_iterations_per_task: int = 20
    max_retries_per_tool: int = 3
    max_debug_cycles: int = 5

    token_budget_headroom: int = 4096
    system_prompt_max_tokens: int = 500
    rag_max_tokens: int = 1500
    sliding_window_turns: int = 20

    embedding_batch_size: int = 32
    embedding_cache_size: int = 200
    file_cache_max_mb: int = 100

    project_root: str = "./projects"
    protected_paths: list[str] = [
        "/", "/etc", "/usr", "/bin", "/sbin",
        "~/.ssh", "~/.aws", "~/.config",
    ]
    command_allowlist: list[str] = [
        "git", "python", "python3", "pip", "npm", "npx", "node",
        "cargo", "rustc", "go", "java", "javac",
        "ls", "cat", "head", "tail", "wc", "sort", "uniq",
        "grep", "find", "diff", "echo", "printf",
        "make", "cmake", "gcc", "g++", "clang",
        "black", "ruff", "pytest", "jest", "tsc", "eslint",
        "prettier", "docker", "docker-compose",
        "mkdir", "touch", "cp", "mv", "rm",
        "curl", "wget",
        "which", "file", "du", "df", "date", "sleep", "clear",
    ]
    command_denylist: list[str] = [
        "dd", "mkfs", "fdisk", "parted", "mkswap",
        "reboot", "shutdown", "halt", "poweroff",
        "iptables", "ufw", "passwd", "chsh", "chpasswd",
        "sudo", "su", "chmod 4777", "chmod 777",
    ]

    file_read_timeout: int = 5
    file_write_timeout: int = 5
    terminal_timeout: int = 30
    indexing_timeout: int = 300


settings = Settings()
