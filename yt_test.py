import yt_dlp as youtube_dl
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import traceback
import sys

# Configure logger
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("yt_test")

async def test_search(query):
    """Test searching YouTube with the same method as in the bot"""
    print(f"Searching for: {query}")
    
    # Setup thread pool
    thread_pool = ThreadPoolExecutor(max_workers=2)
    
    # Method 1: Direct YouTube search URL
    direct_search_query = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': False,  # Changed to False for more verbose output
        'no_warnings': False,  # Changed to False for more warnings
        'extract_flat': False,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'geo_bypass': True,
        'nocheckcertificate': True,
        'verbose': True  # Added verbose mode
    }
    
    # First try direct search URL method
    try:
        print(f"Method 1: Trying direct search URL: {direct_search_query}")
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                print("Executing extract_info with Method 1...")
                search_results = await asyncio.get_event_loop().run_in_executor(
                    thread_pool,
                    lambda: ydl.extract_info(direct_search_query, download=False, process=False)
                )
                
                print(f"Method 1 results received: {search_results is not None}")
                
                if search_results and 'entries' in search_results and search_results['entries']:
                    print(f"Found {len(search_results['entries'])} results")
                    entry = search_results['entries'][0]
                    print(f"Method 1 succeeded! First result: {entry.get('title', 'No title')} - {entry.get('url', 'No URL')}")
                    return entry
                else:
                    if search_results:
                        print(f"Method 1 results structure: {search_results.keys()}")
                    print("Method 1 failed: No search results found")
            except Exception as e:
                print(f"Inner Method 1 error: {e}")
                print(traceback.format_exc())
    except Exception as e:
        print(f"Method 1 error: {e}")
        print(traceback.format_exc())
    
    # Second method: ytsearch prefix
    try:
        print(f"Method 2: Trying ytsearch prefix: ytsearch:{query}")
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                print("Executing extract_info with Method 2...")
                search_results = await asyncio.get_event_loop().run_in_executor(
                    thread_pool,
                    lambda: ydl.extract_info(f"ytsearch:{query}", download=False)
                )
                
                print(f"Method 2 results received: {search_results is not None}")
                
                if search_results and 'entries' in search_results and search_results['entries']:
                    print(f"Found {len(search_results['entries'])} results")
                    entry = search_results['entries'][0]
                    print(f"Method 2 succeeded! First result: {entry.get('title', 'No title')} - {entry.get('url', 'No URL')}")
                    return entry
                else:
                    if search_results:
                        print(f"Method 2 results structure: {search_results.keys()}")
                    print("Method 2 failed: No search results found")
            except Exception as e:
                print(f"Inner Method 2 error: {e}")
                print(traceback.format_exc())
    except Exception as e:
        print(f"Method 2 error: {e}")
        print(traceback.format_exc())
    
    print("All search methods failed")
    return None

async def main():
    print(f"Python version: {sys.version}")
    print(f"yt-dlp version: {youtube_dl.version.__version__}")
    
    # Test a few searches
    search_terms = [
        "Rick Astley Never Gonna Give You Up",
        "Duman Seni Duman Etti",
        "basgaza aşkım"  # The same query from the error message
    ]
    
    for term in search_terms:
        print("\n" + "="*50)
        print(f"TESTING: {term}")
        try:
            result = await test_search(term)
            if result:
                print(f"SUCCESS: Found video: {result.get('title')}")
            else:
                print(f"FAILED: Could not find any video for: {term}")
        except Exception as e:
            print(f"ERROR testing search term {term}: {e}")
            print(traceback.format_exc())
        print("="*50 + "\n")
    
    # Close thread pool
    ThreadPoolExecutor().shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
        print(traceback.format_exc()) 