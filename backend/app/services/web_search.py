import json
import logging
from typing import Dict, List, Optional
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WebSearchService:
    def __init__(self, num_results: int = 5, lang: str = "en", timeout: int = 5):
        """Initialize the web search service.
        
        Args:
            num_results: Number of search results to return
            lang: Language for search results
            timeout: Timeout in seconds for the search operation
        """
        self.num_results = num_results
        self.lang = lang
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json'
        }

    async def search_web(self, query: str) -> List[Dict[str, str]]:
        """Perform a web search and return formatted results.
        
        Args:
            query: The search query
            
        Returns:
            List of dictionaries containing search results with metadata
        """
        try:
            # Encode the query
            encoded_query = quote_plus(query)
            
            # Construct the search URL for DuckDuckGo HTML endpoint
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}&df=d"
            self.logger.info(f"Searching DuckDuckGo with URL: {search_url}")
            
            # Update headers for HTML endpoint
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://html.duckduckgo.com/'
            }
            
            # Perform the search
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=self.timeout) as response:
                    if response.status != 200:
                        self.logger.error(f"Search request failed with status {response.status}")
                        return []
                    
                    # Get the response content
                    content = await response.text()
                    self.logger.debug(f"Received response content: {content[:200]}...")
                    
                    # Parse HTML content
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract search results
                    search_results = []
                    
                    # Find all result divs
                    result_divs = soup.find_all('div', class_='result')
                    
                    for div in result_divs[:self.num_results]:
                        try:
                            # Extract title and link
                            title_elem = div.find('a', class_='result__a')
                            if not title_elem:
                                continue
                                
                            title = title_elem.get_text(strip=True)
                            link = title_elem.get('href', '')
                            
                            # Extract snippet
                            snippet_elem = div.find('a', class_='result__snippet')
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                            
                            # Add to results
                            search_results.append({
                                'title': title,
                                'link': link,
                                'snippet': snippet
                            })
                        except Exception as e:
                            self.logger.error(f"Error parsing result: {e}")
                            continue
                    
                    self.logger.info(f"Returning {len(search_results)} search results")
                    self.logger.info(f"Search results: {search_results}")
                    return search_results
                    
        except Exception as e:
            self.logger.error(f"Error performing web search: {e}")
            return []

    async def _extract_metadata(self, url: str) -> Dict[str, Optional[str]]:
        """Extract metadata from a webpage.
        
        Args:
            url: URL of the webpage
            
        Returns:
            Dictionary containing extracted metadata
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to fetch URL: {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title = None
                    og_title = soup.find('meta', property='og:title')
                    if og_title:
                        title = og_title.get('content')
                    if not title:
                        title = soup.find('title')
                        title = title.text if title else None
                    if not title:
                        title = url
                    
                    # Extract description
                    description = None
                    og_desc = soup.find('meta', property='og:description')
                    if og_desc:
                        description = og_desc.get('content')
                    if not description:
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        description = meta_desc.get('content') if meta_desc else None
                    
                    # Extract snippet (first paragraph or meta description)
                    snippet = None
                    if description:
                        snippet = description
                    else:
                        first_para = soup.find('p')
                        if first_para:
                            snippet = first_para.text.strip()
                    
                    # Extract image
                    image = None
                    og_image = soup.find('meta', property='og:image')
                    if og_image:
                        image = og_image.get('content')
                    if not image:
                        twitter_image = soup.find('meta', name='twitter:image')
                        if twitter_image:
                            image = twitter_image.get('content')
                    if not image:
                        article_image = soup.find('img')
                        if article_image:
                            image = article_image.get('src')
                    
                    # Make image URL absolute if it's relative
                    if image and not image.startswith(('http://', 'https://')):
                        from urllib.parse import urljoin
                        image = urljoin(url, image)
                    
                    return {
                        'title': title,
                        'description': description,
                        'snippet': snippet,
                        'image': image
                    }
                    
        except Exception as e:
            self.logger.error(f"Error extracting metadata from {url}: {e}")
            return {
                'title': url,
                'description': None,
                'snippet': None,
                'image': None
            } 