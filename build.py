import os
import re
from bs4 import BeautifulSoup, Tag, Comment

# Configuration
PROJECT_ROOT = '/Users/xiaxingyu/Desktop/网站项目/PokePay'
DOMAIN = 'https://pokepayguide.top'
MASTER_LAYOUT_PATH = os.path.join(PROJECT_ROOT, 'index.html')

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_clean_url(file_path):
    """
    Returns the clean URL path (relative to domain root) for a given file path.
    Example: /.../articles/foo.html -> /articles/foo
    """
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    
    # Normalize slashes
    rel_path = rel_path.replace('\\', '/')
    
    if rel_path == 'index.html':
        return '/'
    
    if rel_path.endswith('index.html'):
        return '/' + os.path.dirname(rel_path) + '/'
        
    base, ext = os.path.splitext(rel_path)
    if ext == '.html':
        return '/' + base
    return '/' + rel_path

def resolve_to_absolute(url, current_file_path):
    """
    Resolves a link to an absolute path (starting with /) based on the current file's location.
    Also cleans .html suffix.
    """
    if not url:
        return url
        
    # Skip special links
    if url.startswith(('http:', 'https:', '//', 'mailto:', 'tel:', 'javascript:', '#')):
        return url
        
    # Separate anchor/query
    anchor = ''
    query = ''
    if '#' in url:
        parts = url.split('#', 1)
        url = parts[0]
        anchor = '#' + parts[1]
    if '?' in url:
        parts = url.split('?', 1)
        url = parts[0]
        query = '?' + parts[1]

    # Normalize path
    if url.startswith('/'):
        # Already absolute
        abs_path = url
    else:
        # Relative: Resolve against current file directory
        current_dir = os.path.dirname(current_file_path)
        # We need to act as if we are in the filesystem
        # current_file_path is absolute file path
        
        # Combine
        combined = os.path.join(current_dir, url)
        # Normalize (resolve ..)
        normalized = os.path.normpath(combined)
        
        # Make relative to PROJECT_ROOT to get URL path
        # Check if it's within project root
        if not normalized.startswith(PROJECT_ROOT):
             # This happens if ../ goes above root. Should not happen for valid links.
             # Fallback: treat as /url
             abs_path = '/' + url.lstrip('/')
        else:
             rel_to_root = os.path.relpath(normalized, PROJECT_ROOT)
             rel_to_root = rel_to_root.replace('\\', '/')
             if rel_to_root == '.':
                 abs_path = '/'
             else:
                 abs_path = '/' + rel_to_root

    # Clean suffix
    if abs_path.endswith('.html'):
        abs_path = abs_path[:-5]
    elif abs_path.endswith('/index'):
        abs_path = abs_path[:-6]
        if abs_path == '': abs_path = '/'
    
    if abs_path != '/' and abs_path.endswith('/'):
        abs_path = abs_path.rstrip('/')
        
    # Ensure starts with /
    if not abs_path.startswith('/'):
        abs_path = '/' + abs_path
        
    return abs_path + query + anchor

def process_links_in_soup(soup, file_path):
    """
    Traverses soup and converts all links to absolute, clean URLs.
    """
    # <a> tags
    for a in soup.find_all('a', href=True):
        a['href'] = resolve_to_absolute(a['href'], file_path)
        
    # <link> tags (exclude css usually, but check)
    for link in soup.find_all('link', href=True):
        # We generally want to clean internal links, but be careful with static assets
        # CSS/JS/Images often don't need 'clean URL' logic (no removal of extension), 
        # but they DO need absolute path logic if we move things around.
        # But 'resolve_to_absolute' removes .html. It doesn't remove .css.
        # Let's verify.
        href = link['href']
        if href.endswith('.css') or href.endswith('.png') or href.endswith('.jpg') or href.endswith('.ico'):
             # Just ensure absolute path, don't strip extension
             # But our resolve_to_absolute only strips .html and /index
             # So it's safe to use!
             link['href'] = resolve_to_absolute(href, file_path)
        else:
             link['href'] = resolve_to_absolute(href, file_path)

def reorganize_head(soup, file_path, clean_path):
    """
    Reorganizes the <head> section according to the specified groups.
    """
    head = soup.head
    if not head:
        return

    # 1. Extract existing data
    title_tag = head.find('title')
    title_text = title_tag.string if title_tag else ""
    
    desc_tag = head.find('meta', attrs={'name': 'description'})
    desc_content = desc_tag['content'] if desc_tag else ""
    
    kw_tag = head.find('meta', attrs={'name': 'keywords'})
    kw_content = kw_tag['content'] if kw_tag else ""
    
    # Extract Scripts and Styles (Group D)
    resources = []
    for tag in head.find_all(['script', 'style', 'link']):
        if tag.name == 'link' and tag.get('rel') != ['stylesheet']:
            continue 
        resources.append(tag)

    # Extract Icons
    icons = head.find_all('link', attrs={'rel': re.compile(r'icon')})

    # Extract Schema
    schemas = head.find_all('script', type='application/ld+json')

    # 2. Clear Head
    head.clear()
    
    # 3. Insert Charset & Viewport
    head.append(BeautifulSoup('<meta charset="utf-8">', 'html.parser'))
    head.append(BeautifulSoup('\n  ', 'html.parser'))
    head.append(BeautifulSoup('<meta name="viewport" content="width=device-width, initial-scale=1">', 'html.parser'))
    head.append(BeautifulSoup('\n  ', 'html.parser'))

    # 4. Group A: Basic SEO
    if title_text:
        new_title = soup.new_tag('title')
        new_title.string = title_text
        head.append(new_title)
        head.append(BeautifulSoup('\n  ', 'html.parser'))
    
    if desc_content:
        new_desc = soup.new_tag('meta', attrs={'name': 'description', 'content': desc_content})
        head.append(new_desc)
        head.append(BeautifulSoup('\n  ', 'html.parser'))

    if kw_content:
        new_kw = soup.new_tag('meta', attrs={'name': 'keywords', 'content': kw_content})
        head.append(new_kw)
        head.append(BeautifulSoup('\n  ', 'html.parser'))

    # Canonical
    canonical_url = DOMAIN + clean_path
    new_canonical = soup.new_tag('link', rel='canonical', href=canonical_url)
    head.append(new_canonical)
    head.append(BeautifulSoup('\n\n  ', 'html.parser')) 

    # 5. Group B: Indexing & Geo
    head.append(BeautifulSoup('<meta name="robots" content="index, follow">', 'html.parser'))
    head.append(BeautifulSoup('\n  ', 'html.parser'))
    
    # Default to zh-CN
    head.append(BeautifulSoup('<meta http-equiv="content-language" content="zh-CN">', 'html.parser'))
    head.append(BeautifulSoup('\n\n  ', 'html.parser')) 

    # 6. Group C: Schema
    for schema in schemas:
        schema_content = schema.string
        if schema_content:
            schema_content = re.sub(r'"([^"]*?)\.html"', r'"\1"', schema_content)
            schema_content = schema_content.replace('"/index"', '"/"')
            schema_content = schema_content.replace('/index"', '/"')
            schema_content = schema_content.replace('/articles/index"', '/articles"')
            schema.string = schema_content
        head.append(schema)
        head.append(BeautifulSoup('\n  ', 'html.parser'))
    head.append(BeautifulSoup('\n  ', 'html.parser')) 

    # 7. Group D: Resources
    for icon in icons:
        head.append(icon)
        head.append(BeautifulSoup('\n  ', 'html.parser'))

    for res in resources:
        head.append(res)
        head.append(BeautifulSoup('\n  ', 'html.parser'))

def inject_recommended_reading(soup, file_path):
    """Injects recommended reading block at the bottom of <article>."""
    # Skip non-article pages and the articles index itself
    if 'articles' not in file_path or file_path.endswith('index.html'):
        return
        
    article_tag = soup.find('article')
    if not article_tag:
        return
        
    if soup.find('div', id='recommended-reading'):
        return

    # Define a pool of recommended articles
    # Format: (URL, Title, Description)
    recommendations = [
        (
            "/articles/how-to-bind-pokepay-to-alipay",
            "绑定支付宝教程",
            "国内消费神器，支持淘宝、美团、线下扫码。"
        ),
        (
            "/articles/pokepay-usdt-recharge",
            "USDT 充值指南",
            "TRC20 网络充值教程，3分钟极速到账。"
        ),
        (
            "/articles/pokepay-virtual-card-guide",
            "虚拟卡开卡全流程",
            "手把手教你注册、KYC认证、开卡。新手入门第一课。"
        ),
        (
            "/articles/subscription-failure-checklist",
            "支付被拒？排查清单",
            "遇到 Card Declined 怎么办？余额、IP、地址全方位排查。"
        )
    ]

    # Filter out current page
    current_clean = get_clean_url(file_path)
    # Ensure current_clean has no trailing slash for comparison if needed, 
    # but our pool has no trailing slash.
    # get_clean_url returns /articles/foo
    
    valid_recs = [r for r in recommendations if r[0] != current_clean]
    
    # Pick top 2
    selected = valid_recs[:2]
    
    if not selected:
        return

    # Build HTML
    items_html = ""
    for url, title, desc in selected:
        items_html += f'''
            <a href="{url}" class="block group bg-slate-50 p-4 rounded-xl border border-slate-100 hover:border-emerald-500 transition">
                <div class="font-bold text-slate-900 group-hover:text-emerald-600 mb-2">{title}</div>
                <p class="text-xs text-slate-500">{desc}</p>
            </a>
        '''

    html = f'''
    <div id="recommended-reading" class="mt-12 pt-8 border-t border-slate-200">
        <h3 class="text-xl font-bold text-slate-900 mb-6">推荐阅读</h3>
        <div class="grid md:grid-cols-2 gap-6">
            {items_html}
        </div>
    </div>
    '''
    article_tag.append(BeautifulSoup(html, 'html.parser'))

def run_build():
    print("Starting build process...")
    
    # 1. Load Master Layout & Prepare Header/Footer
    if not os.path.exists(MASTER_LAYOUT_PATH):
        print(f"Error: Master layout not found at {MASTER_LAYOUT_PATH}")
        return

    master_content = read_file(MASTER_LAYOUT_PATH)
    # Use lxml for better parsing handling
    try:
        master_soup = BeautifulSoup(master_content, 'lxml')
    except Exception:
        master_soup = BeautifulSoup(master_content, 'html.parser')
    
    # Process Master Links to be Absolute FIRST
    # We pass MASTER_LAYOUT_PATH so relative links in master are resolved correctly relative to root
    process_links_in_soup(master_soup, MASTER_LAYOUT_PATH)
    
    master_nav = master_soup.find('header')
    if not master_nav:
        master_nav = master_soup.find('nav')
        
    master_footer = master_soup.find('footer')
    
    # 2. Traverse Files
    files_to_process = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip ignored dirs
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]
        for file in files:
            if file.endswith('.html') and not file.startswith('_') and file != 'zujina.html' and 'google' not in file:
                files_to_process.append(os.path.join(root, file))

    print(f"Found {len(files_to_process)} HTML files.")

    for file_path in files_to_process:
        print(f"Processing {os.path.basename(file_path)}...")
        content = read_file(file_path)
        try:
            soup = BeautifulSoup(content, 'lxml')
        except:
            soup = BeautifulSoup(content, 'html.parser')
        
        # --- A. Clean URLs & Absolute Paths ---
        # Resolve all links in the current file relative to the current file
        process_links_in_soup(soup, file_path)

        # --- B. Layout Sync ---
        # Sync Header
        if master_nav:
            target_nav = soup.find('header')
            if not target_nav:
                target_nav = soup.find('nav')
            
            if target_nav:
                # Replace with master copy (which is already absolute)
                try:
                    new_nav = BeautifulSoup(str(master_nav), 'lxml').find(master_nav.name)
                except:
                    new_nav = BeautifulSoup(str(master_nav), 'html.parser').find(master_nav.name)
                target_nav.replace_with(new_nav)
        
        # Sync Footer
        if master_footer:
            target_footer = soup.find('footer')
            if target_footer:
                try:
                    new_footer = BeautifulSoup(str(master_footer), 'lxml').find('footer')
                except:
                    new_footer = BeautifulSoup(str(master_footer), 'html.parser').find('footer')
                target_footer.replace_with(new_footer)

        # --- C. Head Reorganization ---
        clean_path = get_clean_url(file_path)
        reorganize_head(soup, file_path, clean_path)

        # --- D. Recommended Reading ---
        inject_recommended_reading(soup, file_path)

        # --- Save ---
        output_html = str(soup)
        if not output_html.startswith('<!DOCTYPE html>'):
             output_html = '<!DOCTYPE html>\n' + output_html
             
        write_file(file_path, output_html)

    print("Build completed.")

if __name__ == '__main__':
    run_build()
