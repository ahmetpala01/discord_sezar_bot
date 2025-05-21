import yt_dlp as youtube_dl
import sys

print(f"Python version: {sys.version}")
print(f"yt-dlp version: {youtube_dl.version.__version__}")

# Test a specific search term
search_term = "basgaza aşkım"
print(f"\nSearching for: {search_term}")

# Configure options
ydl_opts = {
    'quiet': False,
    'format': 'bestaudio/best',
    'default_search': 'auto',
    'noplaylist': True,
    'nocheckcertificate': True
}

# Use the ytsearch: prefix
search_query = f"ytsearch:{search_term}"

try:
    print(f"Executing search with query: {search_query}")
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        
        if info and 'entries' in info and info['entries']:
            video = info['entries'][0]
            print(f"\nSuccess! Found video:")
            print(f"Title: {video.get('title', 'No title')}")
            print(f"URL: {video.get('webpage_url', 'No URL')}")
            print(f"Duration: {video.get('duration', 0)} seconds")
        else:
            print("No results found")
            
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc() 