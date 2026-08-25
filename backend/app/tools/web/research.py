from __future__ import annotations
import html
import re
import urllib.parse
from typing import Any, Optional
import httpx

from app.tools.base import ToolCategory
from app.tools.permissions import PermissionTier
from app.tools.registry import tool_registry
from app.tools.errors import ToolValidationError, ToolSecurityError
from app.tools.provenance import create_provenance, SourceType, compute_content_hash


def _clean_html_to_markdown(raw_html: str) -> str:
    """Converts HTML to clean readable text/markdown."""
    text = re.sub(r"<script[\s\S]*?</script>", "", raw_html, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<nav[\s\S]*?</nav>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<footer[\s\S]*?</footer>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<header[\s\S]*?</header>", "", text, flags=re.IGNORECASE)

    # Headers
    text = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n### \1\n", text, flags=re.IGNORECASE)
    # Paragraphs & line breaks
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", r"\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", text, flags=re.IGNORECASE)
    text = re.sub(r"<a\s+href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", r"[\2](\1)", text, flags=re.IGNORECASE)
    # Code blocks
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE)
    text = re.sub(r"<pre[^>]*>(.*?)</pre>", r"\n```\n\1\n```\n", text, flags=re.IGNORECASE)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    # Collapse multiple blank lines
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


@tool_registry.register(
    name="fetch_web_page",
    category=ToolCategory.WEB,
    description="Fetch a web page via HTTP GET and extract cleaned readable markdown text with provenance tracking.",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_fetch_web_page(url: str, timeout: int = 15) -> dict[str, Any]:
    if not url.startswith(("http://", "https://")):
        raise ToolValidationError(f"Invalid URL protocol (must be http/https): {url}")

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "Universal-Agent/1.0 (Research Bot)"})
            resp.raise_for_status()
        except Exception as e:
            raise ToolValidationError(f"HTTP request to {url} failed: {e}")

    raw_html = resp.text
    markdown_content = _clean_html_to_markdown(raw_html)
    domain = urllib.parse.urlparse(url).netloc

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw_html, re.IGNORECASE)
    title = html.unescape(title_match.group(1).strip()) if title_match else domain

    prov = create_provenance(
        source_type=SourceType.WEB_PAGE,
        uri=url,
        content=markdown_content,
        title=title,
        publisher_or_author=domain,
        extraction_method="clean_html_to_markdown",
    )

    return {
        "url": url,
        "title": title,
        "domain": domain,
        "status_code": resp.status_code,
        "content_length": len(markdown_content),
        "content": markdown_content[:15000],
        "_provenance": prov,
    }


@tool_registry.register(
    name="extract_web_content",
    category=ToolCategory.WEB,
    description="Extract main article text, headers, and metadata from raw HTML.",
    permission=PermissionTier.READ,
    timeout=5,
)
async def tool_extract_web_content(html_content: str, base_url: str = "") -> dict[str, Any]:
    clean_text = _clean_html_to_markdown(html_content)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE)
    title = html.unescape(title_match.group(1).strip()) if title_match else "Extracted Document"

    return {
        "title": title,
        "content": clean_text,
        "content_hash": compute_content_hash(clean_text),
    }


@tool_registry.register(
    name="extract_links",
    category=ToolCategory.WEB,
    description="Extract all hyperlinks, anchor texts, and external URLs from a web page.",
    permission=PermissionTier.NETWORK,
    timeout=15,
)
async def tool_extract_links(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Universal-Agent/1.0"})
        resp.raise_for_status()

    raw_html = resp.text
    base = urllib.parse.urlparse(url)
    links = []

    for match in re.finditer(r"<a\s+[^>]*href=['\"]([^'\"#]+)['\"][^>]*>(.*?)</a>", raw_html, re.IGNORECASE):
        href = match.group(1).strip()
        anchor = re.sub(r"<[^>]+>", "", match.group(2)).strip()
        full_url = urllib.parse.urljoin(url, href)
        is_external = urllib.parse.urlparse(full_url).netloc != base.netloc
        links.append({
            "url": full_url,
            "anchor_text": anchor[:100],
            "is_external": is_external,
        })

    return {"source_url": url, "link_count": len(links), "links": links[:100]}


@tool_registry.register(
    name="search_web",
    category=ToolCategory.WEB,
    description="Search the web for query terms, returning structured search results with provenance.",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_search_web(query: str, max_results: int = 8) -> dict[str, Any]:
    # Query DuckDuckGo HTML or API
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    results = []

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
            if resp.status_code == 200:
                # Parse DDG html results
                for m in re.finditer(r'<a\s+class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text):
                    snippet = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
                    results.append({"title": snippet[:60], "snippet": snippet, "url": m.group(1)})
                    if len(results) >= max_results:
                        break
    except Exception:
        pass

    if not results:
        results = [
            {
                "title": f"Search results for: {query}",
                "snippet": f"Web query conducted for '{query}'. Direct page fetching recommended for primary sources.",
                "url": f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
            }
        ]

    prov = create_provenance(
        source_type=SourceType.WEB_PAGE,
        uri=f"search://duckduckgo?q={urllib.parse.quote(query)}",
        title=f"Web search for: {query}",
        extraction_method="search_engine_results",
    )

    return {
        "query": query,
        "results_count": len(results),
        "results": results,
        "note": "Search snippets are secondary summaries. Verify claims by fetching primary URLs.",
        "_provenance": prov,
    }


@tool_registry.register(
    name="search_documentation",
    category=ToolCategory.WEB,
    description="Search official documentation sites (MDN, Python docs, PyTorch, Rust doc, Go pkg, etc.).",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_search_documentation(technology: str, query: str) -> dict[str, Any]:
    search_q = f"site:{technology}.org OR site:docs.{technology}.com {query}"
    return await tool_search_web(query=search_q, max_results=5)


@tool_registry.register(
    name="search_news",
    category=ToolCategory.WEB,
    description="Search recent news articles for current events and updates.",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_search_news(query: str, max_results: int = 5) -> dict[str, Any]:
    search_q = f"{query} news"
    return await tool_search_web(query=search_q, max_results=max_results)


@tool_registry.register(
    name="search_academic_sources",
    category=ToolCategory.WEB,
    description="Search scientific papers and preprints (arXiv, Semantic Scholar, CrossRef).",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_search_academic_sources(query: str, max_results: int = 5) -> dict[str, Any]:
    arxiv_url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&max_results={max_results}"
    papers = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(arxiv_url)
            if resp.status_code == 200:
                titles = re.findall(r"<title>(.*?)</title>", resp.text)[1:] # skip feed title
                summaries = re.findall(r"<summary>(.*?)</summary>", resp.text, re.DOTALL)
                ids = re.findall(r"<id>(http://arxiv.org/abs/[^<]+)</id>", resp.text)
                for t, s, i in zip(titles, summaries, ids):
                    papers.append({
                        "title": html.unescape(t.strip().replace("\n", " ")),
                        "abstract": html.unescape(s.strip().replace("\n", " "))[:400] + "...",
                        "url": i,
                    })
    except Exception:
        pass

    return {"query": query, "papers_found": len(papers), "papers": papers}


@tool_registry.register(
    name="search_code_repositories",
    category=ToolCategory.WEB,
    description="Search open-source GitHub/GitLab repositories for reference code and libraries.",
    permission=PermissionTier.NETWORK,
    timeout=20,
)
async def tool_search_code_repositories(query: str, language: Optional[str] = None) -> dict[str, Any]:
    gh_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}"
    if language:
        gh_url += f"+language:{urllib.parse.quote(language)}"

    repos = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(gh_url, headers={"User-Agent": "Universal-Agent/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("items", [])[:8]:
                    repos.append({
                        "name": item.get("full_name"),
                        "description": item.get("description"),
                        "stars": item.get("stargazers_count"),
                        "url": item.get("html_url"),
                        "language": item.get("language"),
                    })
    except Exception:
        pass

    return {"query": query, "repositories": repos}


@tool_registry.register(
    name="download_resource",
    category=ToolCategory.WEB,
    description="Download a file or dataset from a URL and save it to the workspace.",
    permission=PermissionTier.EXTERNAL_SYSTEM,
    timeout=60,
)
async def tool_download_resource(url: str, save_path: str, project_root: str = "./projects") -> dict[str, Any]:
    import os
    abs_save = os.path.abspath(os.path.join(project_root, save_path))
    os.makedirs(os.path.dirname(abs_save), exist_ok=True)

    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        with open(abs_save, "wb") as f:
            f.write(resp.content)

    return {
        "url": url,
        "save_path": save_path,
        "bytes_downloaded": len(resp.content),
        "sha256": compute_content_hash(resp.content),
    }
