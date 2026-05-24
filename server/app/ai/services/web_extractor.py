from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class WebPageExtract:
    url: str
    title: str | None
    description: str | None
    headings: list[str]
    text: str


async def _fetch_via_jina(url: str) -> str:
    """
    Fallback extractor for JS-heavy sites.

    `r.jina.ai/http(s)://...` returns a readable plaintext/markdown-ish view for many pages.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        raise RuntimeError("Invalid URL scheme")

    proxy_url = f"https://r.jina.ai/{url}"
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(proxy_url, headers={"User-Agent": "ContextOSBot/1.0"})
        resp.raise_for_status()
        text = (resp.text or "").strip()
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        raise RuntimeError("Unable to extract readable text from the webpage")
    return text[:200_000]


async def fetch_readable_text(url: str) -> str:
    # Prefer LangChain loader when available.
    try:
        from langchain_community.document_loaders import WebBaseLoader

        loader = WebBaseLoader(url)
        docs = loader.load()
        text = "\n\n".join(d.page_content for d in docs if getattr(d, "page_content", None))
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if text:
            return text[:200_000]
    except Exception:
        pass

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url, headers={"User-Agent": "ContextOSBot/1.0"})
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    if not text:
        return await _fetch_via_jina(url)
    return text[:200_000]


async def fetch_page_extract(url: str) -> WebPageExtract:
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url, headers={"User-Agent": "ContextOSBot/1.0"})
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else None
    desc = None
    meta_desc = soup.select_one('meta[name="description"]')
    if meta_desc and meta_desc.get("content"):
        desc = str(meta_desc.get("content")).strip() or None
    if not desc:
        og_desc = soup.select_one('meta[property="og:description"]')
        if og_desc and og_desc.get("content"):
            desc = str(og_desc.get("content")).strip() or None

    headings_raw: list[str] = []
    for sel in ("h1", "h2", "h3"):
        for h in soup.select(sel):
            t = h.get_text(" ", strip=True)
            if t:
                headings_raw.append(t)
    headings: list[str] = []
    seen = set()
    for h in headings_raw:
        key = h.lower()
        if key in seen:
            continue
        seen.add(key)
        headings.append(h)
        if len(headings) >= 10:
            break

    # Prefer the primary content area when present (many sites are SPAs with lots of boilerplate).
    root = soup.select_one("main") or soup.select_one("article") or soup.body or soup
    text = root.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        text = await _fetch_via_jina(url)

    return WebPageExtract(url=url, title=title, description=desc, headings=headings, text=text[:200_000])
