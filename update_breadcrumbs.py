import os
import re
import json

# Configuration
PROJECT_ROOT = '/Users/xiaxingyu/Desktop/网站项目/PokePay'
ARTICLES_DIR = os.path.join(PROJECT_ROOT, 'articles')
DOMAIN = "https://pokepayguide.top"

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_breadcrumb_html(title):
    return f"""
    <nav aria-label="Breadcrumb" class="flex text-sm font-medium text-slate-500 my-4">
      <ol class="flex items-center space-x-2">
        <li>
          <a href="/" class="hover:text-emerald-600 hover:underline transition-colors flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
            </svg>
            <span class="sr-only">首页</span>
          </a>
        </li>
        <li>
          <span class="mx-1 text-slate-300">/</span>
        </li>
        <li>
          <a href="/archive.html" class="hover:text-emerald-600 hover:underline transition-colors">教程归档</a>
        </li>
        <li>
          <span class="mx-1 text-slate-300">/</span>
        </li>
        <li aria-current="page" class="text-slate-800 font-semibold truncate max-w-[150px] sm:max-w-none" title="{title}">
          {title}
        </li>
      </ol>
    </nav>
    """

def generate_breadcrumb_json_ld(title, url):
    data = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [{
            "@type": "ListItem",
            "position": 1,
            "name": "首页",
            "item": DOMAIN + "/"
        },{
            "@type": "ListItem",
            "position": 2,
            "name": "教程归档",
            "item": DOMAIN + "/archive.html"
        },{
            "@type": "ListItem",
            "position": 3,
            "name": title,
            # Current page item usually doesn't need 'item' property if it's the last one, 
            # or it can be the canonical URL. Google recommends omitting 'item' for the last item 
            # or setting it to the current page URL.
            # We will set it to the current page URL for completeness.
            "item": url
        }]
    }
    return f'<script type="application/ld+json">\n{json.dumps(data, indent=2, ensure_ascii=False)}\n</script>'

def update_breadcrumbs():
    print(f"Processing articles in {ARTICLES_DIR}...")
    for filename in os.listdir(ARTICLES_DIR):
        if not filename.endswith('.html'):
            continue
            
        file_path = os.path.join(ARTICLES_DIR, filename)
        # Construct the canonical URL for this article
        article_url = f"{DOMAIN}/articles/{filename}"
        
        print(f"  Updating {filename}...")
        
        content = read_file(file_path)
        
        # 1. Extract Title
        # Try to find h1 first, then title tag
        h1_match = re.search(r'<h1.*?>(.*?)</h1>', content, re.DOTALL)
        title_match = re.search(r'<title>(.*?)</title>', content)
        
        if h1_match:
            # Remove any tags inside h1 if any
            title = re.sub(r'<.*?>', '', h1_match.group(1)).strip()
        elif title_match:
            title = title_match.group(1).split('-')[0].strip() # Assuming "Title - SiteName"
        else:
            print(f"    Warning: Could not determine title for {filename}, skipping breadcrumb update.")
            continue
            
        print(f"    Title: {title}")
        
        # 2. Generate new HTML
        new_breadcrumb_html = generate_breadcrumb_html(title)
        
        # 3. Replace or Insert Breadcrumb HTML
        # Look for existing breadcrumb nav
        # Pattern: <div class="... pt-6 pb-2"> ... <nav ... breadcrumb ...> </nav> ... </div>
        # Or just target the nav with "breadcrumb" class or aria-label="Breadcrumb"
        
        # Strategy:
        # Check for existing modern breadcrumb (aria-label="Breadcrumb")
        if 'aria-label="Breadcrumb"' in content:
            # Replace existing modern breadcrumb
            content = re.sub(r'<nav aria-label="Breadcrumb".*?</nav>', new_breadcrumb_html, content, flags=re.DOTALL)
        # Check for old breadcrumb (class="... breadcrumb ...")
        elif 'class="flex text-xs font-medium breadcrumb' in content:
             content = re.sub(r'<nav[^>]*class="[^"]*breadcrumb[^"]*"[^>]*>.*?</nav>', new_breadcrumb_html, content, flags=re.DOTALL)
        else:
            # Insert after the main nav. 
            # Main nav ends with </nav>. 
            # We assume the main nav is the first one.
            # But wait, we want it in the container: <div class="max-w-7xl ... pt-6 pb-2">
            
            # Let's try to find the container
            container_pattern = r'(<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-2">)'
            if re.search(container_pattern, content):
                # If container exists, replace its content (which might be empty or contain old nav)
                # This is risky if we don't know what's inside.
                # Let's just try to match the container AND the nav inside if possible.
                pass 
                
            # Fallback: Find the main nav closing tag and the next opening div
            # The structure in master_template is:
            # </nav>
            # <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-2">
            #   <nav ...>
            # </div>
            
            # Let's regex for that specific block structure from master template
            block_pattern = r'(<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-2">\s*<nav.*?</nav>\s*</div>)'
            
            if re.search(block_pattern, content, re.DOTALL):
                 content = re.sub(block_pattern, f'<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-2">\n{new_breadcrumb_html}\n</div>', content, flags=re.DOTALL)
            else:
                 # If we can't find the block, maybe insert it after the first </nav> (main nav)
                 print("    Inserting breadcrumb block after main nav...")
                 content = re.sub(r'(</nav>)', f'\\1\n\n<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-2">\n{new_breadcrumb_html}\n</div>', content, count=1)

        # 4. Inject JSON-LD
        # Check if BreadcrumbList JSON-LD already exists
        new_json_ld = generate_breadcrumb_json_ld(title, article_url)
        
        if '"@type": "BreadcrumbList"' in content:
            # Replace existing JSON-LD script block that contains BreadcrumbList
            # This is hard because multiple JSON-LD scripts or multiple items in one script.
            # Simple approach: Remove existing BreadcrumbList JSON-LD and append new one.
            # But regexing JSON is hard.
            
            # Let's assume it's in a <script type="application/ld+json"> block.
            # If we find it, we might just append the new one at the end of body, 
            # or try to replace the specific block if it's isolated.
            # Given the previous files, JSON-LD is usually at the end.
            pass
        
        # Append to end of body
        content = content.replace('</body>', f'{new_json_ld}\n</body>')
        
        write_file(file_path, content)

    print("Breadcrumb update completed.")

if __name__ == '__main__':
    update_breadcrumbs()
