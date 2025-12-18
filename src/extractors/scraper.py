# src/extractors/scraper.py
"""Web scraping module using Playwright.

This module handles all website scraping for brand extraction.
It scrapes multiple pages and extracts structured content.
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser


@dataclass
class ScrapedPage:
    """Content extracted from a single webpage."""
    url: str
    title: str
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    headings: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)  # {text, href}
    images: list[dict] = field(default_factory=list)  # {src, alt}
    ctas: list[str] = field(default_factory=list)
    raw_text: str = ""
    html: str = ""
    error: Optional[str] = None


class WebScraper:
    """
    Playwright-based web scraper for brand extraction.
    
    Scrapes key pages from a website and extracts structured content
    suitable for brand profile analysis.
    """
    
    # Pages to scrape (relative to domain)
    KEY_PAGES = [
        "/",           # Homepage
        "/about",      # About page
        "/about-us",
        "/pricing",    # Pricing page
        "/features",   # Features page
        "/product",    # Product page
        "/faq",        # FAQ
        "/testimonials",  # Testimonials
        "/customers",  # Customer stories
    ]
    
    def __init__(self, timeout: int = 30000, max_pages: int = 5):
        """
        Initialize the scraper.
        
        Args:
            timeout: Page load timeout in milliseconds
            max_pages: Maximum number of pages to scrape
        """
        self.timeout = timeout
        self.max_pages = max_pages
        self._browser: Optional[Browser] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        playwright = await async_playwright().start()
        self._browser = await playwright.chromium.launch(headless=True)
        self._playwright = playwright
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def scrape_website(self, url: str) -> list[ScrapedPage]:
        """
        Scrape key pages from a website.

        Args:
            url: The website URL (e.g., https://careerfied.ai or careerfied.ai)

        Returns:
            List of ScrapedPage objects
        """
        # Normalize URL - add https:// if no scheme provided
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        pages: list[ScrapedPage] = []
        scraped_urls: set[str] = set()
        
        # Create browser context
        context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            # Always scrape the provided URL first
            homepage = await self._scrape_page(page, url)
            pages.append(homepage)
            scraped_urls.add(url.rstrip('/'))
            
            # Discover and scrape additional pages
            for path in self.KEY_PAGES:
                if len(pages) >= self.max_pages:
                    break
                    
                page_url = urljoin(base_url, path)
                normalized_url = page_url.rstrip('/')
                
                if normalized_url in scraped_urls:
                    continue
                
                # Check if page exists
                scraped_page = await self._scrape_page(page, page_url)
                if scraped_page.error is None:
                    pages.append(scraped_page)
                    scraped_urls.add(normalized_url)
            
            # Also look for links from homepage that might be important
            if homepage.error is None:
                important_links = self._find_important_links(homepage.links, base_url)
                for link_url in important_links:
                    if len(pages) >= self.max_pages:
                        break
                    normalized_url = link_url.rstrip('/')
                    if normalized_url not in scraped_urls:
                        scraped_page = await self._scrape_page(page, link_url)
                        if scraped_page.error is None:
                            pages.append(scraped_page)
                            scraped_urls.add(normalized_url)
            
        finally:
            await context.close()
        
        return pages
    
    async def _scrape_page(self, page: Page, url: str) -> ScrapedPage:
        """Scrape a single page."""
        try:
            response = await page.goto(url, timeout=self.timeout, wait_until="networkidle")
            
            if response is None or response.status >= 400:
                return ScrapedPage(
                    url=url,
                    title="",
                    error=f"HTTP {response.status if response else 'No response'}"
                )
            
            # Wait for content to load
            await page.wait_for_load_state("domcontentloaded")
            
            # Get HTML content
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # Extract structured content
            return ScrapedPage(
                url=url,
                title=self._extract_title(soup),
                meta_description=self._extract_meta(soup, "description"),
                meta_keywords=self._extract_meta(soup, "keywords"),
                headings=self._extract_headings(soup),
                paragraphs=self._extract_paragraphs(soup),
                links=self._extract_links(soup, url),
                images=self._extract_images(soup, url),
                ctas=self._extract_ctas(soup),
                raw_text=self._extract_raw_text(soup),
                html=html,
            )
            
        except Exception as e:
            return ScrapedPage(
                url=url,
                title="",
                error=str(e)
            )
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        
        return ""
    
    def _extract_meta(self, soup: BeautifulSoup, name: str) -> Optional[str]:
        """Extract meta tag content."""
        meta = soup.find("meta", attrs={"name": name})
        if meta and meta.get("content"):
            return meta["content"]
        
        # Also check og: tags
        og_meta = soup.find("meta", attrs={"property": f"og:{name}"})
        if og_meta and og_meta.get("content"):
            return og_meta["content"]
        
        return None
    
    def _extract_headings(self, soup: BeautifulSoup) -> list[str]:
        """Extract all headings (h1-h4)."""
        headings = []
        for tag in ["h1", "h2", "h3", "h4"]:
            for heading in soup.find_all(tag):
                text = heading.get_text(strip=True)
                if text and len(text) > 3:  # Filter out very short headings
                    headings.append(text)
        return headings[:30]  # Limit to prevent huge lists
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> list[str]:
        """Extract meaningful paragraphs."""
        paragraphs = []
        
        # Remove script, style, nav, footer elements
        for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            # Filter out very short or very long paragraphs
            if 20 < len(text) < 2000:
                paragraphs.append(text)
        
        return paragraphs[:30]
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        """Extract links with their text."""
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            
            # Make absolute URL
            if href.startswith("/"):
                parsed = urlparse(base_url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            
            if text and href.startswith("http"):
                links.append({"text": text, "href": href})
        
        return links[:50]
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        """Extract images with alt text."""
        images = []
        for img in soup.find_all("img", src=True):
            src = img["src"]
            alt = img.get("alt", "")
            
            # Make absolute URL
            if src.startswith("/"):
                parsed = urlparse(base_url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            elif not src.startswith("http"):
                src = urljoin(base_url, src)
            
            # Filter out tracking pixels and tiny images
            if src.startswith("http") and not any(x in src.lower() for x in ["pixel", "tracking", "1x1"]):
                images.append({"src": src, "alt": alt})
        
        return images[:20]
    
    def _extract_ctas(self, soup: BeautifulSoup) -> list[str]:
        """Extract call-to-action button/link text."""
        ctas = []
        
        # Look for buttons
        for button in soup.find_all(["button", "a"]):
            text = button.get_text(strip=True)
            classes = button.get("class", [])
            
            # Check if it looks like a CTA
            is_cta = any(
                kw in " ".join(classes).lower() 
                for kw in ["cta", "btn", "button", "primary", "action"]
            ) or any(
                kw in text.lower() 
                for kw in ["get started", "sign up", "try", "start", "join", "buy", "learn more", "contact"]
            )
            
            if is_cta and text and 2 < len(text) < 50:
                ctas.append(text)
        
        return list(set(ctas))[:15]
    
    def _extract_raw_text(self, soup: BeautifulSoup) -> str:
        """Extract all visible text from the page."""
        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "nav", "footer"]):
            tag.decompose()
        
        text = soup.get_text(separator=" ", strip=True)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text[:15000]  # Limit size
    
    def _find_important_links(self, links: list[dict], base_url: str) -> list[str]:
        """Find potentially important links from the homepage."""
        important_keywords = [
            "about", "pricing", "features", "product", "solution",
            "testimonial", "customer", "case", "review", "faq",
            "how-it-works", "why", "demo", "tour"
        ]
        
        important_urls = []
        parsed_base = urlparse(base_url)
        
        for link in links:
            href = link.get("href", "")
            text = link.get("text", "").lower()
            
            # Only internal links
            parsed = urlparse(href)
            if parsed.netloc and parsed.netloc != parsed_base.netloc:
                continue
            
            # Check if text or URL contains important keywords
            if any(kw in text or kw in href.lower() for kw in important_keywords):
                important_urls.append(href)
        
        return important_urls[:10]


# Convenience function for one-off scraping
async def scrape_website(url: str, max_pages: int = 5) -> list[ScrapedPage]:
    """
    Scrape a website and return structured content.
    
    Args:
        url: Website URL to scrape
        max_pages: Maximum pages to scrape
        
    Returns:
        List of ScrapedPage objects
    """
    async with WebScraper(max_pages=max_pages) as scraper:
        return await scraper.scrape_website(url)
