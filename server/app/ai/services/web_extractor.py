from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup


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
        raise RuntimeError("Unable to extract readable text from the webpage")
    return text[:200_000]
