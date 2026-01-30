import os
import datetime
import re

BASE_URL = "https://pokepayguide.top"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()

def get_lastmod_from_file(filepath):
    """
    Extracts dateModified or datePublished from HTML file.
    Falls back to TODAY if not found.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Try to find dateModified first
        match = re.search(r'["\']dateModified["\']\s*:\s*["\'](\d{4}-\d{2}-\d{2})["\']', content)
        if match:
            return match.group(1)
            
        # Try to find datePublished
        match = re.search(r'["\']datePublished["\']\s*:\s*["\'](\d{4}-\d{2}-\d{2})["\']', content)
        if match:
            return match.group(1)
            
    except Exception:
        pass
        
    return TODAY

def get_files(directory, prefix=""):
    files = []
    if not os.path.exists(directory):
        return files
    
    for filename in os.listdir(directory):
        if filename.endswith(".html") and not filename.startswith("_") and not filename.startswith("google") and filename != "zujina.html":
            # Skip google verification file and partials
            path = os.path.join(directory, filename)
            url_path = os.path.join(prefix, filename).replace("\\", "/")
            if url_path.startswith("/"):
                url_path = url_path[1:]
            
            # Clean URL: remove index.html and .html extension
            if url_path.endswith("index.html"):
                if url_path == "index.html":
                    url_path = ""
                else:
                    url_path = url_path[:-10] # remove "index.html"
            elif url_path.endswith(".html"):
                url_path = url_path[:-5] # remove ".html"
            
            # Determine priority and frequency
            priority = "0.8"
            changefreq = "weekly"
            
            if filename == "index.html":
                if prefix == "": # Root index
                    priority = "1.0"
                    changefreq = "daily"
                elif "articles" in prefix:
                    priority = "0.9"
                    changefreq = "daily"
            elif filename in ["privacy-policy.html", "terms-of-service.html"]:
                priority = "0.3"
                changefreq = "monthly"
            
            # Get accurate lastmod
            lastmod = get_lastmod_from_file(path)

            files.append({
                "loc": f"{BASE_URL}/{url_path}",
                "lastmod": lastmod,
                "changefreq": changefreq,
                "priority": priority
            })
    return files

def generate_xml(urls):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for url in urls:
        xml.append('  <url>')
        xml.append(f'    <loc>{url["loc"]}</loc>')
        xml.append(f'    <lastmod>{url["lastmod"]}</lastmod>')
        xml.append(f'    <changefreq>{url["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{url["priority"]}</priority>')
        xml.append('  </url>')
    
    xml.append('</urlset>')
    return "\n".join(xml)

def generate_index(sitemaps):
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for sitemap in sitemaps:
        xml.append('  <sitemap>')
        xml.append(f'    <loc>{BASE_URL}/{sitemap}</loc>')
        xml.append(f'    <lastmod>{TODAY}</lastmod>')
        xml.append('  </sitemap>')
    
    xml.append('</sitemapindex>')
    return "\n".join(xml)

def main():
    # 1. Generate sitemap.xml (Simplified Chinese)
    sc_urls = []
    # Root files
    sc_urls.extend(get_files(PROJECT_ROOT, ""))
    # Articles
    sc_urls.extend(get_files(os.path.join(PROJECT_ROOT, "articles"), "articles"))
    
    # Sort URLs: Priority (desc), LastMod (desc)
    # This ensures home page is top, and newer articles appear before older ones
    sc_urls.sort(key=lambda x: (float(x['priority']), x['lastmod']), reverse=True)
    
    with open(os.path.join(PROJECT_ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(generate_xml(sc_urls))
    print("Generated sitemap.xml")

    # 3. Generate sitemap_index.xml
    index_content = generate_index(["sitemap.xml"])
    with open(os.path.join(PROJECT_ROOT, "sitemap_index.xml"), "w", encoding="utf-8") as f:
        f.write(index_content)
    print("Generated sitemap_index.xml")

if __name__ == "__main__":
    main()
