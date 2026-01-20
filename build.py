import os
import re
import json
from datetime import datetime
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
        # Special handling for anchor links on non-index pages
        if url.startswith('#'):
            current_clean = get_clean_url(current_file_path)
            # If we are NOT on the home page (or effective home page), 
            # and the link is a known home-page anchor section, prepend /
            # Known sections from index.html: #features, #tutorial, #okx-tutorial, #faq
            known_home_anchors = ['#features', '#tutorial', '#okx-tutorial', '#faq', '#reviews']
            if current_clean != '/' and url in known_home_anchors:
                return '/' + url
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
        abs_path = url
    else:
        current_dir = os.path.dirname(current_file_path)
        combined = os.path.join(current_dir, url)
        normalized = os.path.normpath(combined)
        
        if not normalized.startswith(PROJECT_ROOT):
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
    if abs_path.endswith('/index'):
        abs_path = abs_path[:-6]
        if abs_path == '': abs_path = '/'
    
    if abs_path != '/' and abs_path.endswith('/'):
        abs_path = abs_path.rstrip('/')
        
    if not abs_path.startswith('/'):
        abs_path = '/' + abs_path
        
    return abs_path + query + anchor

def process_links_in_soup(soup, file_path):
    """
    Traverses soup and converts all links to absolute, clean URLs.
    """
    for a in soup.find_all('a', href=True):
        a['href'] = resolve_to_absolute(a['href'], file_path)
        
    for link in soup.find_all('link', href=True):
        href = link['href']
        # Preserve static assets extension
        if href.endswith(('.css', '.png', '.jpg', '.ico', '.js')):
             # Just ensure absolute path logic (without stripping extension)
             # But our resolve_to_absolute strips .html, so it is safe for assets too
             link['href'] = resolve_to_absolute(href, file_path)
        else:
             link['href'] = resolve_to_absolute(href, file_path)

def reorganize_head(soup, file_path, clean_path):
    """
    Reorganizes the <head> section for Global SEO.
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
    
    # Extract Scripts and Styles
    resources = []
    for tag in head.find_all(['script', 'style', 'link']):
        if tag.name == 'link' and tag.get('rel') != ['stylesheet'] and 'icon' not in str(tag.get('rel')):
             # Skip canonical/hreflang as we will regenerate them
             if tag.get('rel') in [['canonical'], ['alternate']]:
                 continue
        resources.append(tag)

    # Extract Icons
    icons = head.find_all('link', attrs={'rel': re.compile(r'icon')})

    # Extract Schema (Keep existing ones if not replaced later)
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

    # 5. Group B: Indexing & Geo (Global Targeting)
    head.append(BeautifulSoup('<meta name="robots" content="index, follow, max-image-preview:large">', 'html.parser'))
    head.append(BeautifulSoup('\n  ', 'html.parser'))
    head.append(BeautifulSoup('<meta name="distribution" content="global">', 'html.parser'))
    head.append(BeautifulSoup('\n  ', 'html.parser'))
    head.append(BeautifulSoup('<meta http-equiv="content-language" content="zh-CN">', 'html.parser'))
    head.append(BeautifulSoup('\n  ', 'html.parser'))
    
    # Hreflang Matrix
    hreflangs = [
        ('zh', canonical_url),
        ('zh-CN', canonical_url),
        ('x-default', canonical_url)
    ]
    for lang, url in hreflangs:
        link = soup.new_tag('link', rel='alternate', href=url, hreflang=lang)
        head.append(link)
        head.append(BeautifulSoup('\n  ', 'html.parser'))
    head.append(BeautifulSoup('\n', 'html.parser'))

    # 6. Group C: Schema
    # Preserve existing schemas but clean their content
    for schema in schemas:
        schema_content = schema.string
        if schema_content:
            # Clean .html extensions in schema
            schema_content = re.sub(r'"([^"]*?)\.html"', r'"\1"', schema_content)
            schema_content = schema_content.replace('"/index"', '"/"')
            schema_content = schema_content.replace('/index"', '/"')
            schema_content = schema_content.replace('/articles/index"', '/articles"')
            schema.string = schema_content
        head.append(schema)
        head.append(BeautifulSoup('\n  ', 'html.parser'))
    
    # TODO: Generate BlogPosting schema if missing (Phase 3 requirement)
    
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
    if 'articles' not in file_path or file_path.endswith('index.html'):
        return
        
    article_tag = soup.find('article')
    if not article_tag:
        return
        
    if soup.find('div', id='recommended-reading'):
        return

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

    current_clean = get_clean_url(file_path)
    valid_recs = [r for r in recommendations if r[0] != current_clean]
    selected = valid_recs[:2]
    
    if not selected:
        return

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
    
    # 1. Load Master Layout & Prepare Header/Footer/MobileNav
    if not os.path.exists(MASTER_LAYOUT_PATH):
        print(f"Error: Master layout not found at {MASTER_LAYOUT_PATH}")
        return

    master_content = read_file(MASTER_LAYOUT_PATH)
    try:
        master_soup = BeautifulSoup(master_content, 'lxml')
    except Exception:
        master_soup = BeautifulSoup(master_content, 'html.parser')
    
    process_links_in_soup(master_soup, MASTER_LAYOUT_PATH)
    
    # Extract Master Components
    # Use select_one for robust class matching
    master_header = master_soup.select_one('header.fixed.top-0')
    master_footer = master_soup.find('footer')
    # Use select_one or find for mobile nav. It usually has aria-label="Mobile Navigation"
    master_mobile_nav = master_soup.find('nav', attrs={'aria-label': 'Mobile Navigation'})
    
    if not master_header:
        # Fallback: try finding just header
        master_header = master_soup.find('header')
        if master_header and ('fixed' not in master_header.get('class', []) or 'top-0' not in master_header.get('class', [])):
             print("Warning: Found header but it might not be the fixed top one.")
    
    if not master_header:
        print("Warning: Master header not found (looking for <header class='fixed top-0'>)")
    if not master_footer:
        print("Warning: Master footer not found")
    if not master_mobile_nav:
        print("Warning: Master mobile nav not found")

    # 2. Traverse Files
    files_to_process = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
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
        process_links_in_soup(soup, file_path)

        # --- B. Layout Sync ---
        # 1. Sync Header
        if master_header:
            # Try to find existing header to replace
            target_header = soup.select_one('header.fixed.top-0')
            if not target_header:
                # Fallback: try finding ANY header
                target_header = soup.find('header')
            
            if target_header:
                # Check if it is INSIDE main (which implies it's a page title header, not site header)
                # But our site header is usually fixed top-0.
                if 'fixed' in target_header.get('class', []) and 'top-0' in target_header.get('class', []):
                     # Safe to replace
                     new_header = BeautifulSoup(str(master_header), 'html.parser').find('header')
                     target_header.replace_with(new_header)
                else:
                     # If the found header is NOT the fixed top nav, we might need to inject the nav BEFORE it
                     # Or check if there is a separate <nav class="fixed top-0">
                     target_nav = soup.find('nav', class_='fixed top-0')
                     if target_nav:
                         # This is likely the "old" header masquerading as nav
                         new_header = BeautifulSoup(str(master_header), 'html.parser').find('header')
                         target_nav.replace_with(new_header)
                     else:
                         # Insert at top of body
                         if soup.body:
                             new_header = BeautifulSoup(str(master_header), 'html.parser').find('header')
                             soup.body.insert(0, new_header)
            else:
                # No header found, check for nav acting as header
                target_nav = soup.find('nav', class_='fixed top-0')
                if target_nav:
                     new_header = BeautifulSoup(str(master_header), 'html.parser').find('header')
                     target_nav.replace_with(new_header)
                elif soup.body:
                     new_header = BeautifulSoup(str(master_header), 'html.parser').find('header')
                     soup.body.insert(0, new_header)

        # Cleanup: Remove duplicate fixed headers/navs if any
        # Find all fixed top-0 elements
        fixed_tops = soup.find_all(lambda tag: tag.has_attr('class') and 'fixed' in tag['class'] and 'top-0' in tag['class'])
        if len(fixed_tops) > 1:
            # Keep the first one (which should be the one we just injected/replaced at the top), remove others
            # But wait, make sure we don't remove something else.
            # Usually we only want one site header.
            for i in range(1, len(fixed_tops)):
                fixed_tops[i].decompose()

        # 2. Sync Footer
        if master_footer:
            target_footer = soup.find('footer')
            if target_footer:
                new_footer = BeautifulSoup(str(master_footer), 'html.parser').find('footer')
                target_footer.replace_with(new_footer)
            else:
                # Append to body
                if soup.body:
                    new_footer = BeautifulSoup(str(master_footer), 'html.parser').find('footer')
                    soup.body.append(new_footer)

        # 3. Sync Mobile Nav
        if master_mobile_nav:
            # Look for existing mobile nav
            # It usually has aria-label="Mobile Navigation" OR class="fixed bottom-0"
            target_mobile_nav = soup.find('nav', attrs={'aria-label': 'Mobile Navigation'})
            if not target_mobile_nav:
                # Try finding by class
                target_mobile_nav = soup.find(lambda tag: tag.name in ['nav', 'div'] and tag.has_attr('class') and 'fixed' in tag['class'] and 'bottom-0' in tag['class'] and 'z-50' in tag['class'])
            
            new_mobile_nav = BeautifulSoup(str(master_mobile_nav), 'html.parser').find('nav')
            
            if target_mobile_nav:
                target_mobile_nav.replace_with(new_mobile_nav)
            else:
                # Append to body (before script tags)
                if soup.body:
                    scripts = soup.body.find_all('script')
                    if scripts:
                        scripts[0].insert_before(new_mobile_nav)
                    else:
                        soup.body.append(new_mobile_nav)

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
