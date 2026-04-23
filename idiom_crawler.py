import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import random
import os
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://cy.hwxnet.com/"
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
]

class IdiomCrawler:
    def __init__(self, concurrency=2, filename='idioms.json'):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=30.0,
            headers={"User-Agent": random.choice(USER_AGENTS)},
            http2=True
        )
        self.results = []
        self.seen_idioms = set()
        self.save_interval = 50
        self.pbar = None
        self.results_lock = asyncio.Lock()
        self.filename = filename
        
        # Load existing progress
        self.load_results()

    def load_results(self):
        """Load existing results from the JSON file."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.results = data
                        for item in self.results:
                            if 'url' in item:
                                self.seen_idioms.add(item['url'])
                        logger.info(f"Loaded {len(self.results)} existing idioms from {self.filename}")
            except Exception as e:
                logger.error(f"Error loading existing results: {e}")

    def save_results(self):
        """Save the current results to the JSON file."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    async def fetch(self, url, retries=3):
        async with self.semaphore:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            for i in range(retries):
                try:
                    # Increase delay to be more polite
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    response = await self.client.get(url, headers=headers)
                    response.raise_for_status()
                    return response.text
                except (httpx.HTTPStatusError, httpx.RequestError) as e:
                    if i < retries - 1:
                        wait_time = (i + 1) * 2
                        logger.warning(f"Error fetching {url}: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Failed to fetch {url} after {retries} retries: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error fetching {url}: {e}")
                    break
            return None

    async def get_level1_links(self):
        """Get A-Z links from home page."""
        html = await self.fetch("/")
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.select('a.subnavpy'):
            href = a.get('href')
            if href:
                links.append(href)
        return list(set(links))

    async def get_level2_links(self, level1_url):
        """Get sub-pinyin links from a letter page (e.g., ai, an from A)."""
        html = await self.fetch(level1_url)
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.select('a.pinyin_sub_idx'):
            href = a.get('href')
            if href:
                links.append(href)
        # Also include the current page as it might contain idioms (like 'a' in 'a.html')
        links.append(level1_url)
        return list(set(links))

    async def get_level3_links(self, level2_url):
        """Get idiom links from a pinyin list page."""
        html = await self.fetch(level2_url)
        if not html:
            return []
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        for a in soup.select('.pinyin_ul li a'):
            href = a.get('href')
            if href:
                links.append(href)
        return list(set(links))

    async def parse_detail(self, idiom_url):
        """Extract idiom, pinyin, and explanation."""
        full_url = urljoin(BASE_URL, idiom_url)
        if full_url in self.seen_idioms:
            return
            
        html = await self.fetch(idiom_url)
        if not html:
            return
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Idiom name
        idiom_tag = soup.select_one('.view_title .dullred')
        idiom = idiom_tag.text.strip() if idiom_tag else ""
        
        # Pinyin
        pinyin_tag = soup.select_one('.view_title .pinyin')
        pinyin = pinyin_tag.text.strip() if pinyin_tag else ""
        
        # Explanation
        explanation = ""
        dl = soup.select_one('.view_con dl')
        if dl:
            # Find the dd that follows dt containing "[成语解释]"
            for dt in dl.find_all('dt'):
                if "[成语解释]" in dt.text:
                    dd = dt.find_next_sibling('dd')
                    if dd:
                        explanation = dd.text.strip()
                    break
        
        if idiom:
            async with self.results_lock:
                # Double check to prevent duplicates in concurrent execution
                full_url = urljoin(BASE_URL, idiom_url)
                if full_url in self.seen_idioms:
                    return
                self.seen_idioms.add(full_url)
                
                data = {
                    "idiom": idiom,
                    "pinyin": pinyin,
                    "explanation": explanation,
                    "url": full_url
                }
                self.results.append(data)
                
                if self.pbar:
                    self.pbar.update(1)
                else:
                    logger.info(f"Scraped: {idiom}")

                # Periodic save
                if len(self.results) % self.save_interval == 0:
                    self.save_results()

    async def run_limited(self, letters=None):
        """Run the crawler, optionally limited to specific letters."""
        logger.info("Starting crawler...")
        l1_links = await self.get_level1_links()
        
        if letters:
            letters_lower = [let.lower() for let in letters]
            l1_filtered = []
            for l in l1_links:
                filename = l.split('/')[-1]
                if any(filename.startswith(let) for let in letters_lower):
                    l1_filtered.append(l)
            l1_links = l1_filtered
        
        logger.info(f"Level 1 links found: {len(l1_links)} ({l1_links})")
        
        # Step 2: Get all level 2 sub-pinyin links
        level2_tasks = [self.get_level2_links(l1) for l1 in l1_links]
        level2_results = await asyncio.gather(*level2_tasks)
        l2_links = set()
        for r in level2_results:
            l2_links.update(r)
        
        logger.info(f"Level 2 sub-pinyin links found: {len(l2_links)}")
        
        # Step 3: Get all idiom links from level 2 pages
        level3_tasks = [self.get_level3_links(l2) for l2 in l2_links]
        level3_results = await asyncio.gather(*level3_tasks)
        idiom_links = set()
        for r in level3_results:
            idiom_links.update(r)
        
        logger.info(f"Total idioms found: {len(idiom_links)}")
        
        # Filter out already seen idioms for resume capability
        remaining_links = [url for url in idiom_links if urljoin(BASE_URL, url) not in self.seen_idioms]
        logger.info(f"Already crawled: {len(self.results)}, Remaining to crawl: {len(remaining_links)}")
        
        if not remaining_links:
            logger.info("All idioms in this category are already crawled.")
            await self.client.aclose()
            return self.results

        # Step 4: Parse all idiom details with progress bar
        try:
            self.pbar = tqdm(total=len(remaining_links), desc="Crawling idioms", unit="idiom")
            detail_tasks = [self.parse_detail(url) for url in remaining_links]
            await asyncio.gather(*detail_tasks)
        finally:
            if self.pbar:
                self.pbar.close()
            # Final save
            self.save_results()
        
        logger.info(f"Crawling finished. Total scraped: {len(self.results)}")
        await self.client.aclose()
        return self.results

def urljoin(base, rel):
    if rel.startswith('http'):
        return rel
    return base.rstrip('/') + '/' + rel.lstrip('/')

async def main():
    import sys
    # Example usage: python3 idiom_crawler.py [letter1 letter2 ...]
    # If no letters provided, it crawls ALL letters.
    # WARNING: Crawling all letters will take a long time due to politeness delays.
    letters = sys.argv[1:] if len(sys.argv) > 1 else None
    
    # We use a conservative concurrency to avoid being blocked.
    crawler = IdiomCrawler(concurrency=3)
    data = await crawler.run_limited(letters=letters)
    
    output_file = 'idioms.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Results saved to {output_file}. Total count: {len(data)}")

if __name__ == "__main__":
    asyncio.run(main())
