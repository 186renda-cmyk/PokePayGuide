import urllib.request
import xml.etree.ElementTree as ET
import os

# Configuration
BAIDU_API_ENDPOINT = "http://data.zz.baidu.com/urls?site=https://pokepayguide.top&token=MkpV4it8Aq1PaVbS"
SITEMAP_PATH = "sitemap.xml"
MAX_URLS = 10  # 百度普通站点每日限额通常较低，限制单次推送数量

def get_urls_from_sitemap(sitemap_path):
    """Parses sitemap.xml to extract and prioritize URLs."""
    urls = []
    if not os.path.exists(sitemap_path):
        print(f"Error: Sitemap file not found at {sitemap_path}")
        return urls
    
    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # 提取 URL 及其优先级
        url_data = []
        for url in root.findall('ns:url', namespaces):
            loc = url.find('ns:loc', namespaces)
            priority = url.find('ns:priority', namespaces)
            
            if loc is not None and loc.text:
                p_val = float(priority.text) if priority is not None else 0.5
                url_data.append({'url': loc.text, 'priority': p_val})
        
        # 按优先级从高到低排序
        url_data.sort(key=lambda x: x['priority'], reverse=True)
        urls = [item['url'] for item in url_data]
        
        print(f"Found {len(urls)} URLs in sitemap.")
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
        
    return urls

def submit_to_baidu(url_list):
    """Submits the list of URLs to Baidu API."""
    if not url_list:
        print("No URLs to submit.")
        return

    # 限制推送数量
    to_submit = url_list[:MAX_URLS]
    print(f"Actually submitting top {len(to_submit)} prioritized URLs...")
    for u in to_submit:
        print(f" - {u}")

    data = "\n".join(to_submit).encode('utf-8')
    
    req = urllib.request.Request(
        BAIDU_API_ENDPOINT, 
        data=data, 
        headers={'Content-Type': 'text/plain'}
    )

    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print("\n✅ Baidu Submission Result:")
            print(result)
            if '"remain":0' in result:
                print("⚠️ Warning: Daily quota reached (remain is 0).")
    except urllib.error.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"\n❌ Error submitting to Baidu: {e}")

if __name__ == "__main__":
    print("--- Baidu Search Resource Platform Auto-Submitter (Optimized) ---")
    
    # Extract and prioritize URLs
    urls = get_urls_from_sitemap(SITEMAP_PATH)
    
    if urls:
        submit_to_baidu(urls)
    else:
        print("No URLs found to submit.")
