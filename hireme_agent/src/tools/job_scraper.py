import requests
import re

def scrape_job_listing(url: str) -> str:
    """
    Fetches the HTML content of the job URL, strips script/style/HTML tags,
    collapses excess whitespace, and returns the first 1500 characters of text.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Warning: Scraper request failed with status code {response.status_code} for URL: {url}")
            return "Error: Could not retrieve the job details from the listing."

        # Pre-process: remove script and style blocks completely
        html = response.text
        html = re.sub(r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>", "", html, flags=re.IGNORECASE)
        html = re.sub(r"<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>", "", html, flags=re.IGNORECASE)

        # Strip all HTML tags
        clean_text = re.sub(r"<[^>]*>", "", html)
        
        # Collapse whitespace
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        
        capped_text = clean_text[:1500]
        print(f"Scraped listing URL: {url}")
        return capped_text

    except Exception as e:
        print(f"Warning: Scraper failed for URL {url}: {e}")
        return "Error: The details could not be fetched due to a connection or request error."
