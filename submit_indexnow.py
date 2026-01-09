import urllib.request
import json
import xml.etree.ElementTree as ET
import os

# Configuration
HOST = "pokepayguide.top"
KEY = "4cfc536934b44b82913e41903bd6b264"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
SITEMAP_PATH = "sitemap.xml"
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"

def get_urls_from_sitemap(sitemap_path):
    """Parses sitemap.xml to extract all URLs."""
    urls = []
    if not os.path.exists(sitemap_path):
        print(f"Error: Sitemap file not found at {sitemap_path}")
        return urls
    
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        # Namespace map to handle xmlns
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url in root.findall('ns:url', namespaces):
            loc = url.find('ns:loc', namespaces)
            if loc is not None and loc.text:
                urls.append(loc.text)
                
        print(f"Found {len(urls)} URLs in sitemap.")
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
        
    return urls

def submit_to_indexnow(url_list):
    """Submits the list of URLs to IndexNow."""
    if not url_list:
        print("No URLs to submit.")
        return

    payload = {
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": url_list
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        INDEXNOW_ENDPOINT, 
        data=data, 
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            if status_code == 200:
                print("✅ Submission Successful!")
                print(f"Submitted {len(url_list)} URLs to IndexNow.")
            elif status_code == 202:
                print("✅ Submission Accepted (202).")
                print(f"Submitted {len(url_list)} URLs to IndexNow.")
            else:
                print(f"⚠️ Submission received status code: {status_code}")
                print(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Error submitting to IndexNow: {e}")

if __name__ == "__main__":
    print("--- IndexNow Auto-Submitter ---")
    print(f"Target Host: {HOST}")
    
    # Extract URLs
    urls = get_urls_from_sitemap(SITEMAP_PATH)
    
    # Filter only URLs belonging to the host to be safe
    valid_urls = [u for u in urls if HOST in u]
    
    if valid_urls:
        print("Submitting the following URLs:")
        for u in valid_urls[:5]: # Show first 5
            print(f" - {u}")
        if len(valid_urls) > 5:
            print(f" ... and {len(valid_urls)-5} more.")
            
        submit_to_indexnow(valid_urls)
    else:
        print("No valid URLs found to submit.")
