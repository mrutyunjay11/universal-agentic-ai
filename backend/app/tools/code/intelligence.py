from __future__ import annotations
import ast
import os
import re
import shutil
import subprocess
from typing import Any, Optional

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.utils.security import enforce_project_root


_LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".json": "json",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@tool_registry.register(
    name="detect_language",
    category=ToolCategory.CODE,
    description="Detect programming language of a file or code snippet.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_detect_language(file_path: str = "", code_snippet: str = "") -> dict[str, Any]:
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        lang = _LANGUAGE_EXTENSIONS.get(ext, "unknown")
        return {"file_path": file_path, "language": lang, "confidence": 0.95 if lang != "unknown" else 0.2}

    if code_snippet:
        snippet = code_snippet.strip()
        if snippet.startswith("def ") or "import " in snippet or "class " in snippet and ":" in snippet:
            return {"language": "python", "confidence": 0.85}
        if "function " in snippet or "const " in snippet or "let " in snippet or "=>" in snippet:
            return {"language": "typescript", "confidence": 0.85}
        if "fn " in snippet or "pub struct " in snippet or "impl " in snippet:
            return {"language": "rust", "confidence": 0.9}
        if "package " in snippet and "func " in snippet:
            return {"language": "go", "confidence": 0.9}
        if "public class " in snippet or "System.out.println" in snippet:
            return {"language": "java", "confidence": 0.9}
        if "SELECT " in snippet.upper() or "CREATE TABLE" in snippet.upper():
            return {"language": "sql", "confidence": 0.9}

    return {"language": "unknown", "confidence": 0.0}


@tool_registry.register(
    name="find_symbols",
    category=ToolCategory.CODE,
    description="Extract defined symbols (functions, classes, methods, variables) from a code file using AST.",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_find_symbols(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    symbols = []

    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if ext == ".py":
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    symbols.append({
                        "name": node.name,
                        "type": "function",
                        "line": node.lineno,
                        "args": [a.arg for a in node.args.args],
                        "docstring": ast.get_docstring(node),
                    })
                elif isinstance(node, ast.AsyncFunctionDef):
                    symbols.append({
                        "name": node.name,
                        "type": "async_function",
                        "line": node.lineno,
                        "args": [a.arg for a in node.args.args],
                        "docstring": ast.get_docstring(node),
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    symbols.append({
                        "name": node.name,
                        "type": "class",
                        "line": node.lineno,
                        "methods": methods,
                        "docstring": ast.get_docstring(node),
                    })
        except SyntaxError as e:
            symbols.append({"error": f"AST parse syntax error: {e}"})
    else:
        # Regex-based extraction for TS/JS, Rust, Go, Java
        func_patterns = [
            (r"(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(", "function"),
            (r"(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", "arrow_function"),
            (r"class\s+([a-zA-Z0-9_$]+)", "class"),
            (r"interface\s+([a-zA-Z0-9_$]+)", "interface"),
            (r"type\s+([a-zA-Z0-9_$]+)\s*=", "type"),
            (r"fn\s+([a-zA-Z0-9_]+)\s*\(", "rust_function"),
            (r"struct\s+([a-zA-Z0-9_]+)", "struct"),
            (r"func\s+(?:\([^)]+\)\s*)?([a-zA-Z0-9_]+)\s*\(", "go_function"),
        ]
        lines = content.split("\n")
        for line_num, line in enumerate(lines, 1):
            for pat, sym_type in func_patterns:
                m = re.search(pat, line)
                if m:
                    symbols.append({"name": m.group(1), "type": sym_type, "line": line_num})

    return {"file_path": file_path, "symbol_count": len(symbols), "symbols": symbols}


@tool_registry.register(
    name="find_references",
    category=ToolCategory.CODE,
    description="Find all usages and references of a symbol across the project.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_find_references(symbol_name: str, project_root: str = "./projects", file_extension: Optional[str] = None) -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        raise ToolSecurityError(f"Root path denied: {project_root}", "path_traversal")

    pattern = rf"\b{re.escape(symbol_name)}\b"
    regex = re.compile(pattern)
    references = []

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", ".agent-backups")]
        for file in files:
            if file_extension and not file.endswith(file_extension):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, 1):
                        if regex.search(line):
                            references.append({
                                "file_path": rel_path,
                                "line_number": line_idx,
                                "line_content": line.strip()[:150],
                            })
                            if len(references) >= 100:
                                break
            except Exception:
                continue
        if len(references) >= 100:
            break

    return {"symbol": symbol_name, "reference_count": len(references), "references": references}


@tool_registry.register(
    name="find_definition",
    category=ToolCategory.CODE,
    description="Locate the definition of a class, function, or variable in the workspace.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_find_definition(symbol_name: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        raise ToolSecurityError("Root path access denied", "path_traversal")

    def_patterns = [
        re.compile(rf"^\s*(?:def|class|async def)\s+{re.escape(symbol_name)}\b"),
        re.compile(rf"^\s*(?:export\s+)?(?:async\s+)?function\s+{re.escape(symbol_name)}\b"),
        re.compile(rf"^\s*(?:const|let|var)\s+{re.escape(symbol_name)}\s*="),
        re.compile(rf"^\s*(?:interface|type|class)\s+{re.escape(symbol_name)}\b"),
        re.compile(rf"^\s*fn\s+{re.escape(symbol_name)}\b"),
        re.compile(rf"^\s*func\s+(?:\([^)]+\)\s*)?{re.escape(symbol_name)}\b"),
    ]

    definitions = []
    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", ".agent-backups")]
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for pat in def_patterns:
                            if pat.search(line):
                                definitions.append({
                                    "file_path": rel_path,
                                    "line_number": line_num,
                                    "definition_line": line.strip(),
                                })
            except Exception:
                continue

    return {"symbol": symbol_name, "definitions_found": len(definitions), "definitions": definitions}


@tool_registry.register(
    name="find_imports",
    category=ToolCategory.CODE,
    description="Extract all module and package imports from a code file.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_find_imports(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    imports = []

    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    if ext == ".py":
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        imports.append({"module": n.name, "alias": n.asname, "type": "import"})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for n in node.names:
                        imports.append({"module": f"{module}.{n.name}" if module else n.name, "alias": n.asname, "type": "from_import"})
        except Exception:
            pass
    else:
        # Regex match for JS/TS/Go/Rust
        for line in content.split("\n"):
            m_ts = re.search(r"import\s+.*?from\s+['\"](.*?)['\"]", line)
            if m_ts:
                imports.append({"module": m_ts.group(1), "type": "es_import"})
            m_go = re.search(r"import\s+['\"](.*?)['\"]", line)
            if m_go:
                imports.append({"module": m_go.group(1), "type": "go_import"})
            m_rs = re.search(r"use\s+([a-zA-Z0-9_:]+);", line)
            if m_rs:
                imports.append({"module": m_rs.group(1), "type": "rust_use"})

    return {"file_path": file_path, "import_count": len(imports), "imports": imports}


@tool_registry.register(
    name="find_callers",
    category=ToolCategory.CODE,
    description="Find all functions or files that call a specific function or method.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_find_callers(function_name: str, project_root: str = "./projects") -> dict[str, Any]:
    call_pattern = re.compile(rf"\b{re.escape(function_name)}\s*\(")
    abs_root = enforce_project_root(".", project_root)
    callers = []

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", ".agent-backups")]
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if call_pattern.search(line):
                            # Exclude definition lines
                            if not re.search(rf"(?:def|function|fn|func)\s+{re.escape(function_name)}", line):
                                callers.append({
                                    "file_path": rel_path,
                                    "line_number": line_num,
                                    "call_snippet": line.strip(),
                                })
            except Exception:
                continue

    return {"function": function_name, "callers_count": len(callers), "callers": callers[:50]}


@tool_registry.register(
    name="find_implementations",
    category=ToolCategory.CODE,
    description="Find implementations of an interface, abstract class, or trait.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_find_implementations(interface_name: str, project_root: str = "./projects") -> dict[str, Any]:
    patterns = [
        re.compile(rf"class\s+([a-zA-Z0-9_]+)\s*\([^)]*{re.escape(interface_name)}[^)]*\)"),
        re.compile(rf"class\s+([a-zA-Z0-9_]+)\s+implements\s+[^{{]*{re.escape(interface_name)}"),
        re.compile(rf"impl\s+[^{{]*{re.escape(interface_name)}\s+for\s+([a-zA-Z0-9_]+)"),
    ]
    abs_root = enforce_project_root(".", project_root)
    implementations = []

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", ".agent-backups")]
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for pat in patterns:
                            m = pat.search(line)
                            if m:
                                implementations.append({
                                    "implementing_class": m.group(1),
                                    "file_path": rel_path,
                                    "line_number": line_num,
                                    "statement": line.strip(),
                                })
            except Exception:
                continue

    return {"interface": interface_name, "implementations": implementations}


@tool_registry.register(
    name="grep_search",
    category=ToolCategory.CODE,
    description="Search for regex or text patterns across project code files.",
    permission=PermissionTier.READ,
    timeout=15,
)
async def tool_grep_search(pattern: str, project_root: str = "./projects", file_pattern: Optional[str] = None, max_results: int = 50) -> dict[str, Any]:
    abs_root = enforce_project_root(".", project_root)
    if not abs_root:
        raise ToolSecurityError("Path denied", "path_traversal")

    results = []
    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise ToolValidationError(f"Invalid regular expression: {e}")

    for root, dirs, files in os.walk(abs_root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", ".git", ".agent-backups")]
        for file in files:
            if file_pattern and not file.endswith(file_pattern):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_root)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append({
                                "file_path": rel_path,
                                "line_number": line_num,
                                "line_content": line.strip()[:200],
                            })
                            if len(results) >= max_results:
                                break
            except Exception:
                continue
        if len(results) >= max_results:
            break

    return {"pattern": pattern, "match_count": len(results), "matches": results}


@tool_registry.register(
    name="analyze_code",
    category=ToolCategory.CODE,
    description="Perform structural code analysis (complexity, LOC, functions, imports, docstring coverage).",
    permission=PermissionTier.READ,
    timeout=10,
)
async def tool_analyze_code(file_path: str, project_root: str = "./projects") -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total_loc = len(lines)
    blank_lines = sum(1 for l in lines if not l.strip())
    comment_lines = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*")))
    code_lines = total_loc - blank_lines - comment_lines

    metrics = {
        "file_path": file_path,
        "total_lines": total_loc,
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "blank_lines": blank_lines,
        "comment_ratio": round(comment_lines / max(1, code_lines), 3),
    }

    if file_path.endswith(".py"):
        try:
            tree = ast.parse("".join(lines))
            funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            docstrings = sum(1 for f in funcs if ast.get_docstring(f))
            metrics["functions_count"] = len(funcs)
            metrics["classes_count"] = len(classes)
            metrics["docstring_coverage"] = round(docstrings / max(1, len(funcs)), 2)
        except Exception:
            pass

    return metrics


@tool_registry.register(
    name="run_linter",
    category=ToolCategory.CODE,
    description="Run static linter (ruff, flake8, eslint) on a target file or directory.",
    permission=PermissionTier.EXECUTE,
    timeout=30,
)
async def tool_run_linter(target_path: str = ".", project_root: str = "./projects", linter: Optional[str] = None) -> dict[str, Any]:
    abs_path = enforce_project_root(target_path, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Path access denied: {target_path}", "path_traversal")

    cmd = None
    if linter:
        cmd = [linter, abs_path]
    elif shutil.which("ruff"):
        cmd = ["ruff", "check", abs_path]
    elif shutil.which("flake8"):
        cmd = ["flake8", abs_path]
    elif shutil.which("npx") and (os.path.exists(os.path.join(project_root, "package.json"))):
        cmd = ["npx", "eslint", abs_path]
    else:
        # Fallback to python syntax check via compile
        if os.path.isfile(abs_path) and abs_path.endswith(".py"):
            try:
                with open(abs_path, "r", encoding="utf-8") as f:
                    compile(f.read(), abs_path, "exec")
                return {"linter": "python_compile", "status": "passed", "errors": []}
            except SyntaxError as e:
                return {
                    "linter": "python_compile",
                    "status": "failed",
                    "errors": [{"line": e.lineno, "message": e.msg, "text": e.text}],
                }
        return {"status": "no_linter_available", "message": "No configured linter CLI detected on system."}

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "linter": cmd[0],
            "return_code": proc.returncode,
            "status": "passed" if proc.returncode == 0 else "lint_issues_found",
            "stdout": proc.stdout[:2000],
            "stderr": proc.stderr[:1000],
        }
    except Exception as e:
        return {"linter": cmd[0] if cmd else "unknown", "error": str(e)}


@tool_registry.register(
    name="format_code",
    category=ToolCategory.CODE,
    description="Format code using black, ruff, prettier, or rustfmt.",
    permission=PermissionTier.READ_WRITE,
    timeout=20,
)
async def tool_format_code(file_path: str, project_root: str = "./projects", formatter: Optional[str] = None) -> dict[str, Any]:
    abs_path = enforce_project_root(file_path, project_root)
    if not abs_path or not os.path.isfile(abs_path):
        raise ToolValidationError(f"File not found: {file_path}")

    cmd = None
    if formatter:
        cmd = [formatter, abs_path]
    elif file_path.endswith(".py"):
        if shutil.which("ruff"):
            cmd = ["ruff", "format", abs_path]
        elif shutil.which("black"):
            cmd = ["black", abs_path]
    elif file_path.endswith((".js", ".ts", ".jsx", ".tsx", ".json", ".css", ".html")):
        if shutil.which("npx"):
            cmd = ["npx", "prettier", "--write", abs_path]
    elif file_path.endswith(".rs") and shutil.which("rustfmt"):
        cmd = ["rustfmt", abs_path]

    if not cmd:
        return {"file_path": file_path, "status": "skipped", "message": "No suitable code formatter found in PATH."}

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return {
            "file_path": file_path,
            "formatter": cmd[0],
            "status": "formatted" if proc.returncode == 0 else "failed",
            "output": proc.stdout or proc.stderr,
        }
    except Exception as e:
        return {"file_path": file_path, "status": "error", "error": str(e)}


@tool_registry.register(
    name="type_check",
    category=ToolCategory.CODE,
    description="Run static type checker (mypy, pyright, tsc) on codebase or file.",
    permission=PermissionTier.EXECUTE,
    timeout=45,
)
async def tool_type_check(target_path: str = ".", project_root: str = "./projects", checker: Optional[str] = None) -> dict[str, Any]:
    abs_path = enforce_project_root(target_path, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Path access denied: {target_path}", "path_traversal")

    cmd = None
    if checker:
        cmd = [checker, abs_path]
    elif shutil.which("mypy") and (target_path.endswith(".py") or os.path.isdir(abs_path)):
        cmd = ["mypy", abs_path]
    elif shutil.which("npx") and (target_path.endswith((".ts", ".tsx")) or os.path.exists(os.path.join(project_root, "tsconfig.json"))):
        cmd = ["npx", "tsc", "--noEmit"]

    if not cmd:
        return {"status": "no_type_checker_available", "message": "No type checker (mypy, tsc) detected."}

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45, cwd=project_root)
        return {
            "checker": cmd[0],
            "return_code": proc.returncode,
            "status": "passed" if proc.returncode == 0 else "type_errors_found",
            "output": (proc.stdout + "\n" + proc.stderr).strip()[:3000],
        }
    except Exception as e:
        return {"checker": cmd[0] if cmd else "unknown", "error": str(e)}


@tool_registry.register(
    name="compile_code",
    category=ToolCategory.CODE,
    description="Compile code files (gcc, g++, rustc, cargo, go build, javac) and return compiler diagnostic messages.",
    permission=PermissionTier.EXECUTE,
    timeout=60,
)
async def tool_compile_code(file_or_target: str, project_root: str = "./projects", compiler: Optional[str] = None) -> dict[str, Any]:
    abs_path = enforce_project_root(file_or_target, project_root)
    if not abs_path:
        raise ToolSecurityError(f"Target denied: {file_or_target}", "path_traversal")

    ext = os.path.splitext(file_or_target)[1].lower()
    cmd = None

    if compiler:
        cmd = [compiler, abs_path]
    elif ext in (".c", ".cpp"):
        comp = "g++" if ext == ".cpp" else "gcc"
        if shutil.which(comp):
            cmd = [comp, "-fsyntax-only", abs_path]
    elif ext == ".rs" and shutil.which("rustc"):
        cmd = ["rustc", "--emit=metadata", abs_path]
    elif ext == ".go" and shutil.which("go"):
        cmd = ["go", "build", "-o", os.devnull, abs_path]
    elif ext == ".java" and shutil.which("javac"):
        cmd = ["javac", "-d", "/tmp", abs_path]

    if not cmd:
        return {"target": file_or_target, "status": "no_compiler", "message": "No compatible compiler found."}

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=project_root)
        return {
            "compiler": cmd[0],
            "return_code": proc.returncode,
            "status": "success" if proc.returncode == 0 else "compilation_error",
            "output": (proc.stdout + "\n" + proc.stderr).strip()[:3000],
        }
    except Exception as e:
        return {"compiler": cmd[0] if cmd else "unknown", "error": str(e)}
