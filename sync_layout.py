import os
import re

# Configuration
PROJECT_ROOT = '/Users/xiaxingyu/Desktop/网站项目/PokePay'
INDEX_PATH = os.path.join(PROJECT_ROOT, 'index.html')
ARTICLES_DIR = os.path.join(PROJECT_ROOT, 'articles')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_section(content, tag_name):
    """Extracts content between <tag> and </tag> including the tags. Returns first match only."""
    pattern = re.compile(f'(<{tag_name}.*?</{tag_name}>)', re.DOTALL)
    match = pattern.search(content)
    return match.group(1) if match else None

def extract_master_css(content):
    """Extracts Master CSS between /* MASTER_CSS_START */ and /* MASTER_CSS_END */."""
    pattern = re.compile(r'/\* MASTER_CSS_START \*/(.*?)/\* MASTER_CSS_END \*/', re.DOTALL)
    match = pattern.search(content)
    return match.group(1).strip() if match else None

def extract_tailwind_config(content):
    pattern = re.compile(r'(<script>\s*tailwind\.config\s*=.*?</script>)', re.DOTALL)
    match = pattern.search(content)
    return match.group(1) if match else None

def clean_url_in_html(html_content):
    """Removes .html from href attributes in HTML content."""
    # Replace .html" with "
    html_content = re.sub(r'href="([^"]*?)\.html"', r'href="\1"', html_content)
    # Replace .html# with #
    html_content = re.sub(r'href="([^"]*?)\.html#', r'href="\1#', html_content)
    # Special case: /index or /index/ -> /
    html_content = html_content.replace('href="/index"', 'href="/"')
    html_content = html_content.replace('href="/index/"', 'href="/"')
    # Special case: index.html -> / (if strictly equal)
    html_content = re.sub(r'href="index"', 'href="/"', html_content)
    return html_content

def fix_seo_tags(content, file_path):
    """
    Updates Canonical, JSON-LD, OG, Twitter tags to use clean URLs.
    """
    filename = os.path.basename(file_path)
    relative_path = os.path.relpath(file_path, PROJECT_ROOT)
    
    # Calculate Clean URL
    if filename == 'index.html':
        if relative_path == 'index.html':
            clean_path = ''
        else:
            # e.g. zh-hant/index.html -> zh-hant/
            clean_path = os.path.dirname(relative_path) + '/'
    else:
        # e.g. articles/foo.html -> articles/foo
        clean_path = os.path.splitext(relative_path)[0]
    
    # Normalize path (remove backslashes on windows, though we are on macos)
    clean_path = clean_path.replace('\\', '/')
    
    # Ensure no leading slash for joining
    clean_path = clean_path.lstrip('/')
    
    # Construct full URL
    canonical_url = f"https://pokepayguide.top/{clean_path}"
    
    # 1. Update Canonical
    # <link rel="canonical" href="...">
    canonical_tag = f'<link rel="canonical" href="{canonical_url}">'
    if '<link rel="canonical"' in content:
        content = re.sub(r'<link rel="canonical"[^>]*>', canonical_tag, content)
    else:
        # Insert in head
        if '</head>' in content:
            content = content.replace('</head>', f'{canonical_tag}\n</head>')

    # 2. Update Social Meta (OG/Twitter)
    # <meta property="og:url" content="...">
    og_url_tag = f'<meta property="og:url" content="{canonical_url}">'
    if '<meta property="og:url"' in content:
        content = re.sub(r'<meta property="og:url"[^>]*>', og_url_tag, content)
    
    # <meta name="twitter:url" content="...">
    twitter_url_tag = f'<meta name="twitter:url" content="{canonical_url}">'
    if '<meta name="twitter:url"' in content:
        content = re.sub(r'<meta name="twitter:url"[^>]*>', twitter_url_tag, content)

    # 3. Update JSON-LD
    # Find JSON-LD block
    json_ld_pattern = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.DOTALL)
    match = json_ld_pattern.search(content)
    if match:
        json_content = match.group(2)
        
        # Regex replace all values ending in .html inside the JSON
        new_json_content = re.sub(r'"([^"]*?)\.html"', r'"\1"', json_content)
        
        # Also fix /index" -> /"
        new_json_content = new_json_content.replace('"/index"', '"/"')
        
        content = content.replace(json_content, new_json_content)

    return content

def sync_layout():
    print(f"Reading master layout from {INDEX_PATH}...")
    index_content = read_file(INDEX_PATH)
    
    # 1. Extract Master Components
    master_nav = extract_section(index_content, 'nav')
    master_footer = extract_section(index_content, 'footer')
    tailwind_config = extract_tailwind_config(index_content)
    master_css_content = extract_master_css(index_content)
    
    if not master_nav or not master_footer:
        print("Error: Could not find <nav> or <footer> in index.html")
        return
        
    if not master_css_content:
        print("Warning: No /* MASTER_CSS_START */ tags found in index.html. Skipping CSS sync.")
    
    # Prepare Master CSS Block
    master_css_block = f'/* MASTER_CSS_START */\n    {master_css_content}\n    /* MASTER_CSS_END */' if master_css_content else None

    # 2. Prepare Components for Articles (Clean URLs)
    
    # Clean up master_nav and master_footer first (remove .html from them)
    master_nav = clean_url_in_html(master_nav)
    master_footer = clean_url_in_html(master_footer)

    # Prepare Article Nav (Root Relative)
    # Fix Nav Links: href="#section" -> href="/#section"
    article_nav = re.sub(r'href="#', 'href="/#', master_nav)
    
    # Fix Footer Links: href="articles/" -> href="/articles/"
    # Note: clean_url_in_html already removed .html.
    article_footer = master_footer.replace('href="articles/', 'href="/articles/')
    article_footer = article_footer.replace('href="#', 'href="/#')

    # Fix Nav Links in article_nav (e.g. if nav has articles/ link)
    article_nav = article_nav.replace('href="articles/', 'href="/articles/')

    # 3. Process Files
    files_to_process = []
    
    # Root pages
    root_pages = ['index.html', 'terms-of-service.html', 'privacy-policy.html', '404.html']
    for f in root_pages:
        path = os.path.join(PROJECT_ROOT, f)
        if os.path.exists(path):
            files_to_process.append(path)

    # Root Zh-Hant
    zh_hant_dir = os.path.join(PROJECT_ROOT, 'zh-hant')
    if os.path.exists(zh_hant_dir):
        for f in os.listdir(zh_hant_dir):
             if f.endswith('.html'):
                files_to_process.append(os.path.join(zh_hant_dir, f))

    # Articles
    if os.path.exists(ARTICLES_DIR):
        for f in os.listdir(ARTICLES_DIR):
            if f.endswith('.html'):
                files_to_process.append(os.path.join(ARTICLES_DIR, f))
    
    # Articles Zh-Hant
    articles_zh_hant_dir = os.path.join(ARTICLES_DIR, 'zh-hant')
    if os.path.exists(articles_zh_hant_dir):
        for f in os.listdir(articles_zh_hant_dir):
            if f.endswith('.html'):
                files_to_process.append(os.path.join(articles_zh_hant_dir, f))

    print(f"Processing {len(files_to_process)} files...")

    for file_path in files_to_process:
        filename = os.path.basename(file_path)
        # print(f"  Updating {filename}...")
        
        content = read_file(file_path)
        
        # --- Update SEO Tags (Canonical, JSON-LD, etc.) ---
        content = fix_seo_tags(content, file_path)
        
        # --- Update Nav & Footer ---
        is_index = (file_path == INDEX_PATH) or (file_path.endswith('zh-hant/index.html'))
        
        if is_index:
            current_nav = master_nav
            current_footer = master_footer
        else:
            current_nav = article_nav
            current_footer = article_footer

        if '<nav' in content:
            content = re.sub(r'<nav.*?</nav>', current_nav, content, count=1, flags=re.DOTALL)
        
        if '<footer' in content:
            content = re.sub(r'<footer.*?</footer>', current_footer, content, count=1, flags=re.DOTALL)

        # --- Update Tailwind Config ---
        if tailwind_config:
            if 'tailwind.config' in content:
                 content = re.sub(r'<script>\s*tailwind\.config\s*=.*?</script>', tailwind_config, content, count=1, flags=re.DOTALL)
            else:
                 if '</head>' in content:
                     content = content.replace('</head>', f'{tailwind_config}\n</head>')

        # --- Update Master CSS ---
        if master_css_block:
            if '/* MASTER_CSS_START */' in content:
                content = re.sub(r'/\* MASTER_CSS_START \*/.*?/\* MASTER_CSS_END \*/', master_css_block, content, flags=re.DOTALL)
            else:
                if '<style>' in content:
                    content = content.replace('<style>', f'<style>\n    {master_css_block}\n')
                elif '</head>' in content:
                    content = content.replace('</head>', f'<style>\n    {master_css_block}\n  </style>\n</head>')
        
        # --- Final Clean Sweep of Links in Body ---
        # CAUTION: This replaces all .html in hrefs. 
        content = re.sub(r'href="([^"]*?)\.html"', r'href="\1"', content)
        # Also clean up double slashes if any created (except http://)
        # content = content.replace('//', '/') # Too dangerous for https://
        
        write_file(file_path, content)

    print("Sync completed successfully.")

if __name__ == '__main__':
    sync_layout()
