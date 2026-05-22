from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config import REQUEST_HEADERS, REQUEST_TIMEOUT


def fetch_html(url):
    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text
    except requests.RequestException as exc:
        print(f"  [Lỗi] Không thể tải {url}: {exc}")
        return None


def normalize_url(url, base_url=None):
    if not url:
        return None
    url = url.strip()
    if base_url:
        url = urljoin(base_url, url)
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    # Chỉ bỏ fragment (#...), giữ nguyên path để không làm hỏng link .html/.htm
    return url.split("#")[0]


def _select_text(soup, selector):
    if not selector:
        return None
    for part in selector.split(","):
        part = part.strip()
        if not part:
            continue
        element = soup.select_one(part)
        if element:
            text = element.get_text(" ", strip=True)
            if text:
                return text
    return None


def _select_image(soup, selector):
    if not selector:
        return None
    for part in selector.split(","):
        part = part.strip()
        if not part:
            continue
        element = soup.select_one(part)
        if not element:
            continue
        src = element.get("src") or element.get("data-src")
        if src:
            return src
    return None


def extract_article_links(html, source):
    soup = BeautifulSoup(html, "html.parser")
    selector = source.link_selector or "a"
    seen = set()
    articles = []

    for anchor in soup.select(selector):
        href = (
            anchor.get("href")
            or anchor.get("data-href")
            or anchor.get("data-url")
        )
        title = anchor.get_text(strip=True)
        url = normalize_url(href, source.link)
        if not url or not title or len(title) < 5:
            continue
        if url in seen:
            continue
        seen.add(url)
        articles.append({"title": title, "link": url})

    return articles


def extract_article_detail(html, source):
    soup = BeautifulSoup(html, "html.parser")

    title = _select_text(soup, source.title_selector)
    description = _select_text(soup, source.description_selector)
    image = _select_image(soup, source.image_selector)

    content = None
    if source.content_selector:
        for part in source.content_selector.split(","):
            part = part.strip()
            if not part:
                continue
            block = soup.select_one(part)
            if block:
                for tag in block.find_all(["script", "style", "iframe"]):
                    tag.decompose()
                content = block.get_text("\n", strip=True)
                if content:
                    break

    if not description and content:
        description = content[:300].strip()
        if len(content) > 300:
            description += "..."

    return {
        "title": title,
        "description": description,
        "content": content,
        "image": image,
    }


def crawl_links_for_source(source, existing_links):
    print(f"  Đang quét link từ: {source.name}")
    html = fetch_html(source.link)
    if not html:
        return []

    items = extract_article_links(html, source)
    new_items = [item for item in items if item["link"] not in existing_links]
    print(f"  Tìm thấy {len(items)} link, {len(new_items)} link mới.")
    return new_items


def crawl_content_for_article(article, source):
    print(f"  Đang lấy nội dung: {article.title or article.link}")
    html = fetch_html(article.link)
    if not html:
        return None
    detail = extract_article_detail(html, source)
    if not detail.get("content") and not detail.get("description"):
        print(f"  [Cảnh báo] Không trích xuất được nội dung từ {article.link}")
        return None
    return detail
