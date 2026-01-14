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

    # 2. Prepare Components for Articles
    # Fix Nav Links: #section -> /index.html#section
    article_nav = re.sub(r'href="#', 'href="/index.html#', master_nav)
    
    # Fix Footer Links: articles/foo.html -> /articles/foo.html
    article_footer = master_footer.replace('href="articles/', 'href="/articles/')
    article_footer = article_footer.replace('href="#', 'href="/index.html#')

    # Fix Nav Links in article_nav (e.g. if nav has articles/ link)
    article_nav = article_nav.replace('href="articles/', 'href="/articles/')

    # 3. Process Files
    files_to_process = []
    
    # Articles
    if os.path.exists(ARTICLES_DIR):
        for f in os.listdir(ARTICLES_DIR):
            if f.endswith('.html'):
                files_to_process.append(os.path.join(ARTICLES_DIR, f))
    
    # Root pages
    root_pages = ['terms-of-service.html', 'privacy-policy.html', '404.html']
    for f in root_pages:
        path = os.path.join(PROJECT_ROOT, f)
        if os.path.exists(path):
            files_to_process.append(path)

    print(f"Processing {len(files_to_process)} files...")

    for file_path in files_to_process:
        filename = os.path.basename(file_path)
        print(f"  Updating {filename}...")
        
        content = read_file(file_path)
        
        # --- Update Nav ---
        # Only replace the FIRST <nav> found.
        if '<nav' in content:
            content = re.sub(r'<nav.*?</nav>', article_nav, content, count=1, flags=re.DOTALL)
        else:
            # Simple heuristic insertion
            if '<body' in content:
                # Try to insert after body tag opener
                content = re.sub(r'(<body.*?>)', f'\\1\n{article_nav}', content, count=1)
            else:
                 content = article_nav + content

        # --- Update Footer ---
        if '<footer' in content:
            content = re.sub(r'<footer.*?</footer>', article_footer, content, count=1, flags=re.DOTALL)
        else:
            if '</body>' in content:
                content = content.replace('</body>', f'{article_footer}\n</body>')
            else:
                content += article_footer

        # --- Update Tailwind Config ---
        if tailwind_config:
            if 'tailwind.config' in content:
                 content = re.sub(r'<script>\s*tailwind\.config\s*=.*?</script>', tailwind_config, content, count=1, flags=re.DOTALL)
            else:
                 # Insert before head close if not exists
                 if '</head>' in content:
                     content = content.replace('</head>', f'{tailwind_config}\n</head>')

        # --- Update Master CSS ---
        if master_css_block:
            if '/* MASTER_CSS_START */' in content:
                # Replace existing block
                content = re.sub(r'/\* MASTER_CSS_START \*/.*?/\* MASTER_CSS_END \*/', master_css_block, content, flags=re.DOTALL)
            else:
                # No tags found.
                if '<style>' in content:
                    # Prepend to existing style
                    content = content.replace('<style>', f'<style>\n    {master_css_block}\n')
                elif '</head>' in content:
                    # No style tag, create one
                    content = content.replace('</head>', f'<style>\n    {master_css_block}\n  </style>\n</head>')

        write_file(file_path, content)

    print("Sync completed successfully.")

if __name__ == '__main__':
    sync_layout()
