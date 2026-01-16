import os
import datetime

BASE_URL = "https://pokepayguide.top"
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().isoformat()

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
                if prefix in ["", "zh-hant"]: # Root index or zh-hant root index
                    priority = "1.0"
                    changefreq = "daily"
                elif "articles" in prefix:
                    priority = "0.9"
                    changefreq = "daily"
            elif filename in ["privacy-policy.html", "terms-of-service.html"]:
                priority = "0.3"
                changefreq = "monthly"
            
            files.append({
                "loc": f"{BASE_URL}/{url_path}",
                "lastmod": TODAY,
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
    
    with open(os.path.join(PROJECT_ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(generate_xml(sc_urls))
    print("Generated sitemap.xml")

    # 2. Generate sitemap-hant.xml (Traditional Chinese)
    tc_urls = []
    # Root zh-hant
    tc_urls.extend(get_files(os.path.join(PROJECT_ROOT, "zh-hant"), "zh-hant"))
    # Articles zh-hant
    tc_urls.extend(get_files(os.path.join(PROJECT_ROOT, "articles", "zh-hant"), "articles/zh-hant"))
    
    with open(os.path.join(PROJECT_ROOT, "sitemap-hant.xml"), "w", encoding="utf-8") as f:
        f.write(generate_xml(tc_urls))
    print("Generated sitemap-hant.xml")

    # 3. Generate sitemap_index.xml
    index_content = generate_index(["sitemap.xml", "sitemap-hant.xml"])
    with open(os.path.join(PROJECT_ROOT, "sitemap_index.xml"), "w", encoding="utf-8") as f:
        f.write(index_content)
    print("Generated sitemap_index.xml")

if __name__ == "__main__":
    main()
