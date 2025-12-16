"""Modal deployment for BrandTruth AI.

Deploy with:
    modal deploy modal_app.py

Run single extraction:
    modal run modal_app.py --url https://careerfied.ai
"""

import json
import os
from typing import Optional

import modal

# Create Modal app
app = modal.App("brandtruth-ai")

# Define the image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "anthropic>=0.40.0",
        "playwright>=1.49.0",
        "pydantic>=2.10.0",
        "httpx>=0.28.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.3.0",
    )
    .run_commands("playwright install chromium", "playwright install-deps chromium")
)


# Secret for API keys
secrets = [modal.Secret.from_name("anthropic-api-key")]


@app.function(
    image=image,
    secrets=secrets,
    timeout=300,  # 5 minutes max
    memory=2048,  # 2GB RAM for Playwright
)
async def extract_brand_profile(url: str, max_pages: int = 5) -> dict:
    """
    Extract brand profile from a website URL.
    
    This is the Modal-deployed version of the brand extractor.
    Returns a dictionary (JSON-serializable) of the brand profile.
    """
    # Import here to avoid issues with Modal serialization
    import asyncio
    import anthropic
    from playwright.async_api import async_playwright
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin, urlparse
    import re
    
    # ========== SCRAPER ==========
    
    async def scrape_page(page, target_url):
        """Scrape a single page."""
        try:
            response = await page.goto(target_url, timeout=30000, wait_until="networkidle")
            if response is None or response.status >= 400:
                return None
            
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            
            # Remove unwanted elements
            for tag in soup.find_all(["script", "style", "nav", "footer"]):
                tag.decompose()
            
            # Extract title
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)
            
            # Extract meta description
            meta_desc = None
            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                meta_desc = meta["content"]
            
            # Extract headings
            headings = []
            for tag in ["h1", "h2", "h3"]:
                for h in soup.find_all(tag):
                    text = h.get_text(strip=True)
                    if text and len(text) > 3:
                        headings.append(text)
            
            # Extract paragraphs
            paragraphs = []
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if 20 < len(text) < 2000:
                    paragraphs.append(text)
            
            # Extract CTAs
            ctas = []
            for btn in soup.find_all(["button", "a"]):
                text = btn.get_text(strip=True)
                if text and any(kw in text.lower() for kw in 
                    ["get started", "sign up", "try", "start", "join", "buy", "learn"]):
                    if 2 < len(text) < 50:
                        ctas.append(text)
            
            return {
                "url": target_url,
                "title": title,
                "meta_description": meta_desc,
                "headings": headings[:20],
                "paragraphs": paragraphs[:15],
                "ctas": list(set(ctas))[:10],
            }
        except Exception as e:
            print(f"Error scraping {target_url}: {e}")
            return None
    
    async def scrape_website(target_url, max_pages=5):
        """Scrape multiple pages from a website."""
        parsed = urlparse(target_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        key_paths = ["/", "/about", "/pricing", "/features", "/faq"]
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            pages = []
            scraped_urls = set()
            
            # Scrape homepage first
            homepage = await scrape_page(page, target_url)
            if homepage:
                pages.append(homepage)
                scraped_urls.add(target_url.rstrip('/'))
            
            # Scrape other key pages
            for path in key_paths:
                if len(pages) >= max_pages:
                    break
                page_url = urljoin(base_url, path)
                if page_url.rstrip('/') not in scraped_urls:
                    result = await scrape_page(page, page_url)
                    if result:
                        pages.append(result)
                        scraped_urls.add(page_url.rstrip('/'))
            
            await browser.close()
            return pages
    
    # ========== EXTRACTION ==========
    
    EXTRACTION_PROMPT = """Analyze this website content and extract brand information as JSON:

<content>
{content}
</content>

Return JSON with this structure:
{{
  "brand_name": "Company name",
  "tagline": "Main tagline",
  "industry": "Industry category",
  "value_propositions": ["benefit 1", "benefit 2"],
  "target_audience": "Who it's for",
  "claims": [
    {{"claim": "text", "claim_type": "statistic|feature|benefit", "risk_level": "low|medium|high", "source_text": "original context"}}
  ],
  "social_proof": [
    {{"proof_type": "testimonial|statistic|award", "content": "text", "attribution": "source"}}
  ],
  "tone_analysis": {{
    "primary_tone": "professional|casual|friendly|empowering|technical",
    "tone_summary": "1-2 sentence description of brand voice"
  }},
  "key_terms": ["important", "keywords"],
  "confidence_score": 0.85,
  "warnings": ["any issues found"]
}}

Only include explicitly stated information. Return valid JSON only."""

    # Scrape
    print(f"Scraping {url}...")
    pages = await scrape_website(url, max_pages)
    
    if not pages:
        raise ValueError(f"Failed to scrape any pages from {url}")
    
    print(f"Scraped {len(pages)} pages")
    
    # Prepare content
    sections = []
    for page in pages:
        section = f"""
=== {page['url']} ===
Title: {page['title']}
Description: {page.get('meta_description', 'N/A')}

Headings: {', '.join(page['headings'][:10])}

Content:
{chr(10).join(page['paragraphs'][:8])}

CTAs: {', '.join(page['ctas'])}
"""
        sections.append(section)
    
    content = "\n\n".join(sections)[:40000]  # Truncate
    
    # Extract with Claude
    print("Analyzing with Claude...")
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(content=content)}]
    )
    
    # Parse response
    response_text = response.content[0].text
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]
    
    extracted = json.loads(response_text.strip())
    
    # Add metadata
    extracted["website_url"] = url
    extracted["pages_analyzed"] = len(pages)
    
    print(f"Extraction complete. Confidence: {extracted.get('confidence_score', 'N/A')}")
    
    return extracted


@app.local_entrypoint()
def main(url: str, max_pages: int = 5, output: Optional[str] = None):
    """Run brand extraction from CLI."""
    result = extract_brand_profile.remote(url, max_pages)
    
    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        print(f"Saved to {output}")
    else:
        print(json.dumps(result, indent=2))


# For batch processing
@app.function(image=image, secrets=secrets, timeout=600)
async def extract_batch(urls: list[str]) -> list[dict]:
    """Extract brand profiles for multiple URLs."""
    results = []
    for url in urls:
        try:
            result = await extract_brand_profile.local(url)
            results.append({"url": url, "status": "success", "profile": result})
        except Exception as e:
            results.append({"url": url, "status": "error", "error": str(e)})
    return results
