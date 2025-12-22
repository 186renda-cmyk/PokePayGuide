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
    """Extracts content between <tag> and </tag> including the tags."""
    pattern = re.compile(f'(<{tag_name}.*?</{tag_name}>)', re.DOTALL)
    match = pattern.search(content)
    return match.group(1) if match else None

def extract_head_extras(content):
    """Extracts the Tailwind config script and custom styles from head."""
    # Extract Tailwind config
    tailwind_pattern = re.compile(r'(<script>\s*tailwind\.config\s*=.*?</script>)', re.DOTALL)
    tailwind_match = tailwind_pattern.search(content)
    
    # Extract Style block
    style_pattern = re.compile(r'(<style>.*?</style>)', re.DOTALL)
    style_match = style_pattern.search(content)
    
    return (tailwind_match.group(1) if tailwind_match else "", 
            style_match.group(1) if style_match else "")

def sync_layout():
    print(f"Reading master layout from {INDEX_PATH}...")
    index_content = read_file(INDEX_PATH)
    
    # 1. Extract Master Components
    master_nav = extract_section(index_content, 'nav')
    master_footer = extract_section(index_content, 'footer')
    tailwind_config, master_style = extract_head_extras(index_content)
    
    if not master_nav or not master_footer:
        print("Error: Could not find <nav> or <footer> in index.html")
        return

    # 2. Prepare Components for Articles
    # Fix Nav Links: #section -> /index.html#section
    article_nav = re.sub(r'href="#', 'href="/index.html#', master_nav)
    
    # Fix Nav Links: Active state handling (optional, but good)
    # For now, we just ensure links back to home work.
    
    # Fix Footer Links: articles/foo.html -> /articles/foo.html (Absolute path is safer)
    # We want to ensure that links in the footer pointing to articles work from anywhere.
    # In index.html, they are likely "articles/foo.html".
    # We will convert "articles/" to "/articles/" to make them absolute.
    article_footer = master_footer.replace('href="articles/', 'href="/articles/')
    article_footer = article_footer.replace('href="#', 'href="/index.html#')

    # Also fix footer links in article_nav if any
    article_nav = article_nav.replace('href="articles/', 'href="/articles/')

    # 3. Process Article Files
    print(f"Processing articles in {ARTICLES_DIR}...")
    for filename in os.listdir(ARTICLES_DIR):
        if not filename.endswith('.html'):
            continue
            
        file_path = os.path.join(ARTICLES_DIR, filename)
        print(f"  Updating {filename}...")
        
        content = read_file(file_path)
        
        # Replace Nav
        # Find existing nav and replace it
        if '<nav' in content:
            content = re.sub(r'<nav.*?</nav>', article_nav, content, flags=re.DOTALL)
        else:
            # If no nav, insert after body open (simple heuristic)
            content = content.replace('<body', f'<body\n{article_nav}', 1)

        # Replace Footer
        # Find existing footer and replace it
        if '<footer' in content:
            content = re.sub(r'<footer.*?</footer>', article_footer, content, flags=re.DOTALL)
        else:
            # If no footer, insert before body close
            content = content.replace('</body>', f'{article_footer}\n</body>')

        # Update Head (Tailwind & Styles)
        # We need to replace the old tailwind config and styles with the master ones
        # This is a bit aggressive but ensures consistency.
        
        # Remove old tailwind config if exists
        content = re.sub(r'<script>\s*tailwind\.config\s*=.*?</script>', tailwind_config, content, flags=re.DOTALL)
        
        # Remove old style block and replace
        # Note: Articles might have specific styles. We should APPEND master styles or REPLACE?
        # The user asked for "Unified CSS styles". Let's replace the common base styles.
        # But articles have specific prose styles. 
        # Strategy: Inject master style at the start of <head> or before </head>, 
        # but let's try to merge. 
        # Actually, the index.html styles are mostly global (glass-nav, footer). 
        # Let's just ensure the Master Style block is present.
        
        if master_style not in content:
            # If there is an existing style block, we might want to keep it BUT add the master classes.
            # Index styles: .glass-nav, .hero-card-gradient, etc.
            # Article styles: .prose, etc.
            # Let's prepend master styles to the existing style block if it exists, or create one.
            if '<style>' in content:
                # Insert master CSS content into existing style tag
                # We strip the <style> tags from master_style for this injection
                css_content = master_style.replace('<style>', '').replace('</style>', '')
                content = content.replace('<style>', f'<style>\n{css_content}\n')
            else:
                content = content.replace('</head>', f'{master_style}\n</head>')

        write_file(file_path, content)

    print("Sync completed successfully.")

if __name__ == '__main__':
    sync_layout()
