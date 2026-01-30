import os
import re
import json
import random
from datetime import datetime
from bs4 import BeautifulSoup, Tag, Comment
import generate_sitemap

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
    Also adds rel="nofollow noopener noreferrer" to external links for security and SEO.
    """
    for a in soup.find_all('a', href=True):
        raw_href = a['href']
        # Resolve to absolute/clean first
        resolved_href = resolve_to_absolute(raw_href, file_path)
        a['href'] = resolved_href
        
        # Check for external link protection
        # External links start with http/https and do not match our domain
        if resolved_href.startswith(('http:', 'https:')):
            if not resolved_href.startswith(DOMAIN):
                # It is external
                rel = a.get('rel', [])
                if isinstance(rel, str):
                    rel = rel.split()
                
                # Add required protection attributes
                for val in ['nofollow', 'noopener', 'noreferrer']:
                    if val not in rel:
                        rel.append(val)
                
                a['rel'] = rel
        
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
    has_schema = False
    for schema in schemas:
        schema_content = schema.string
        if schema_content:
            has_schema = True
            # Clean .html extensions in schema
            schema_content = re.sub(r'"([^"]*?)\.html"', r'"\1"', schema_content)
            schema_content = schema_content.replace('"/index"', '"/"')
            schema_content = schema_content.replace('/index"', '/"')
            schema_content = schema_content.replace('/articles/index"', '/articles"')
            schema.string = schema_content
        head.append(schema)
        head.append(BeautifulSoup('\n  ', 'html.parser'))
    
    # Generate default schema if missing for standard pages
    if not has_schema:
        schema_data = None
        if clean_path == '/privacy-policy':
            schema_data = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": "隐私政策",
                "url": DOMAIN + "/privacy-policy",
                "description": "Pokepay 隐私政策说明"
            }
        elif clean_path == '/terms-of-service':
            schema_data = {
                "@context": "https://schema.org",
                "@type": "WebPage",
                "name": "服务条款",
                "url": DOMAIN + "/terms-of-service",
                "description": "Pokepay 服务条款说明"
            }
            
        if schema_data:
            new_schema = soup.new_tag('script', type='application/ld+json')
            new_schema.string = json.dumps(schema_data, indent=2, ensure_ascii=False)
            head.append(new_schema)
            head.append(BeautifulSoup('\n  ', 'html.parser'))

    head.append(BeautifulSoup('\n  ', 'html.parser')) 

    # 7. Group D: Resources
    for icon in icons:
        head.append(icon)
        head.append(BeautifulSoup('\n  ', 'html.parser'))

    for res in resources:
        head.append(res)
        head.append(BeautifulSoup('\n  ', 'html.parser'))

def inject_breadcrumb(soup, file_path):
    """Injects breadcrumb navigation for SEO."""
    clean_path = get_clean_url(file_path)
    if clean_path == '/' or clean_path == '/index':
        return

    # Check if breadcrumb already exists
    if soup.find('nav', attrs={'aria-label': 'breadcrumb'}):
        return

    # Determine breadcrumb items
    items = [('/', '首页')]
    
    if clean_path.startswith('/articles/'):
        items.append(('/articles/', '深度文章'))
        if clean_path != '/articles/':
            # Try to get title from h1 or title tag
            h1 = soup.find('h1')
            title = h1.get_text().strip() if h1 else '文章详情'
            # Truncate if too long
            if len(title) > 20: title = title[:20] + '...'
            items.append((None, title))
    elif clean_path == '/privacy-policy':
        items.append((None, '隐私政策'))
    elif clean_path == '/terms-of-service':
        items.append((None, '服务条款'))
    elif clean_path == '/articles': # Handle /articles without trailing slash if needed, though get_clean_url handles it
        items.append((None, '深度文章'))
    else:
        # Generic fallback
        h1 = soup.find('h1')
        title = h1.get_text().strip() if h1 else '详情'
        items.append((None, title))

    # Build HTML
    lis = ""
    for i, (url, text) in enumerate(items):
        if i > 0:
            lis += '<li class="text-slate-300">/</li>'
        
        if url:
            lis += f'<li><a href="{url}" class="hover:text-emerald-600 transition">{text}</a></li>'
        else:
            lis += f'<li><span class="text-slate-900 font-medium line-clamp-1">{text}</span></li>'

    html = f'''
    <nav aria-label="breadcrumb" class="py-3 bg-slate-50 border-b border-slate-100">
        <ol class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center gap-2 text-xs text-slate-500">
            {lis}
        </ol>
    </nav>
    '''
    
    # Insert:
    # 1. After fixed header (if exists)
    # 2. Or at start of <main>
    # 3. Or at start of <body> (after header)
    
    breadcrumb_tag = BeautifulSoup(html, 'html.parser')
    
    main = soup.find('main')
    if main:
        main.insert(0, breadcrumb_tag)
    else:
        # Fallback: try to insert after header
        header = soup.find('header', class_='fixed top-0')
        if header:
            header.insert_after(breadcrumb_tag)
        elif soup.body:
            soup.body.insert(0, breadcrumb_tag)

def inject_recommended_reading(soup, file_path):
    """Injects recommended reading block at the bottom of <article>."""
    # Always try to remove existing block first (cleanup)
    existing_reading = soup.find('div', id='recommended-reading')
    if existing_reading:
        existing_reading.decompose()

    clean_path = get_clean_url(file_path)
    # Exclude index pages, root pages, and non-article pages
    if clean_path == '/' or clean_path.endswith('/index') or clean_path == '/articles' or clean_path == '/articles/' or 'articles' not in file_path:
        return
        
    article_tag = soup.find('article')
    if not article_tag:
        return

    recommendations = [
        (
            "/articles/pokepay-recharge-guide",
            "PokePay 充值全能教程",
            "2026最新：USDT、银行转账、Wise三种方式全覆盖。"
        ),
        (
            "/articles/how-to-bind-pokepay-to-alipay",
            "绑定支付宝教程",
            "国内消费神器，支持淘宝、美团、线下扫码。"
        ),
        (
            "/articles/pokepay-virtual-card-guide",
            "虚拟卡开卡全流程",
            "手把手教你注册、KYC认证、开卡。新手入门第一课。"
        ),
        (
            "/articles/pokepay-bind-paypal-chatgpt",
            "绑定 PayPal 订阅 ChatGPT",
            "解决 Plus 订阅支付失败问题，成功率 99%。"
        ),
        (
            "/articles/subscription-failure-checklist",
            "支付被拒？排查清单",
            "遇到 Card Declined 怎么办？余额、IP、地址全方位排查。"
        ),
        (
            "/articles/pokepay-kaopu-ma",
            "Pokepay 靠谱吗？",
            "深度解析金融牌照、资金安全与合规性。"
        )
    ]

    current_clean = get_clean_url(file_path)
    valid_recs = [r for r in recommendations if r[0] != current_clean]
    
    # Randomize recommendations to ensure better internal link coverage across the site
    # This helps SEO by distributing link equity more evenly
    random.shuffle(valid_recs)
    
    selected = valid_recs[:4]
    
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

def generate_articles_index():
    """
    Generates the articles aggregation page (articles/index.html) with:
    1. Pagination (if needed)
    2. Classification (Tabs)
    3. Auto-populated list of articles sorted by date
    """
    articles_index_path = os.path.join(PROJECT_ROOT, 'articles', 'index.html')
    if not os.path.exists(articles_index_path):
        print(f"Warning: Articles index not found at {articles_index_path}")
        return
        
    print("Generating articles/index.html...")
    content = read_file(articles_index_path)
    try:
        soup = BeautifulSoup(content, 'lxml')
    except:
        soup = BeautifulSoup(content, 'html.parser')

    # 1. Gather all articles metadata
    articles_data = []
    articles_dir = os.path.join(PROJECT_ROOT, 'articles')
    
    for filename in os.listdir(articles_dir):
        if not filename.endswith('.html') or filename == 'index.html':
            continue
            
        file_path = os.path.join(articles_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            f_content = f.read()
            
        # Parse minimal info
        try:
            f_soup = BeautifulSoup(f_content, 'html.parser')
        except:
            continue
            
        # Title
        title_tag = f_soup.find('h1')
        title = title_tag.get_text().strip() if title_tag else filename
        
        # Desc
        desc_tag = f_soup.find('meta', attrs={'name': 'description'})
        desc = desc_tag['content'] if desc_tag else ""
        
        # Date
        # Try dateModified first, then datePublished, then lastmod logic
        date_str = "2026-01-01" # Default
        date_mod = re.search(r'["\']dateModified["\']\s*:\s*["\'](\d{4}-\d{2}-\d{2})["\']', f_content)
        date_pub = re.search(r'["\']datePublished["\']\s*:\s*["\'](\d{4}-\d{2}-\d{2})["\']', f_content)
        if date_mod:
            date_str = date_mod.group(1)
        elif date_pub:
            date_str = date_pub.group(1)
            
        # Category
        cat_tag = f_soup.find('meta', attrs={'name': 'category'})
        category = cat_tag['content'] if cat_tag else "其他"
        
        # URL
        url = "/articles/" + filename.replace('.html', '')
        
        articles_data.append({
            'title': title,
            'desc': desc,
            'date': date_str,
            'category': category,
            'url': url
        })
        
    # Sort by date desc
    articles_data.sort(key=lambda x: x['date'], reverse=True)
    
    # 2. Build HTML Grid
    # Find container
    grid_container = soup.find('div', role='list')
    if not grid_container:
        # Try to find by class if role missing
        grid_container = soup.find('div', class_='grid md:grid-cols-2 gap-6')
        
    if grid_container:
        grid_container.clear()
        
        for art in articles_data:
            cat_display = art['category']
            
            # Category styling map
            cat_color = "bg-slate-100 text-slate-600"
            if "新手" in cat_display: cat_color = "bg-emerald-50 text-emerald-700"
            elif "充值" in cat_display: cat_color = "bg-blue-50 text-blue-700"
            elif "高阶" in cat_display: cat_color = "bg-purple-50 text-purple-700"
            elif "故障" in cat_display: cat_color = "bg-red-50 text-red-700"
            elif "评测" in cat_display: cat_color = "bg-orange-50 text-orange-700"
            
            card_html = f'''
            <article class="h-full article-item" data-category="{cat_display}">
                <a href="{art['url']}" class="block bg-white p-6 rounded-2xl border border-slate-200 transition article-card group hover:shadow-lg hover:-translate-y-1">
                    <div class="flex items-center justify-between mb-4">
                        <span class="px-2 py-1 {cat_color} text-xs font-bold rounded flex items-center gap-1">
                            {cat_display}
                        </span>
                        <span class="text-xs text-slate-400 font-mono">{art['date'].replace('-', '.')}</span>
                    </div>
                    <h3 class="text-xl font-bold text-slate-900 mb-2 group-hover:text-emerald-600 transition line-clamp-2">{art['title']}</h3>
                    <p class="text-sm text-slate-500 line-clamp-2 leading-relaxed">{art['desc']}</p>
                </a>
            </article>
            '''
            grid_container.append(BeautifulSoup(card_html, 'html.parser'))
            
    # 3. Add Filter Tabs (Insert before grid)
    # Check if already exists
    filter_container = soup.find('div', id='article-filters')
    if not filter_container:
        # Collect all unique categories
        all_cats = sorted(list(set(d['category'] for d in articles_data)))
        
        tabs_html = f'''
        <div id="article-filters" class="flex flex-wrap justify-center gap-2 mb-10">
            <button class="filter-btn active px-4 py-2 rounded-full bg-slate-900 text-white text-sm font-bold transition hover:opacity-90" data-filter="all">全部</button>
            {''.join([f'<button class="filter-btn px-4 py-2 rounded-full bg-white border border-slate-200 text-slate-600 text-sm font-bold transition hover:border-emerald-500 hover:text-emerald-600" data-filter="{c}">{c}</button>' for c in all_cats])}
        </div>
        '''
        
        # Insert before grid
        if grid_container:
            grid_container.insert_before(BeautifulSoup(tabs_html, 'html.parser'))
            
    # 4. Add Pagination Controls (Insert after grid)
    pagination_container = soup.find('div', id='article-pagination')
    if not pagination_container:
        pag_html = f'''
        <div id="article-pagination" class="mt-12 flex justify-center gap-2">
            <!-- JS will populate this -->
        </div>
        '''
        if grid_container:
            grid_container.insert_after(BeautifulSoup(pag_html, 'html.parser'))

    # 5. Inject JS logic
    script_id = "articles-logic"
    existing_script = soup.find('script', id=script_id)
    if not existing_script:
        js_code = '''
        <script id="articles-logic">
        document.addEventListener('DOMContentLoaded', () => {
            const items = document.querySelectorAll('.article-item');
            const filters = document.querySelectorAll('.filter-btn');
            const paginationContainer = document.getElementById('article-pagination');
            const itemsPerPage = 6; // Pagination limit
            let currentPage = 1;
            let currentFilter = 'all';
            let visibleItems = [];

            function filterItems(category) {
                currentFilter = category;
                visibleItems = [];
                items.forEach(item => {
                    const itemCat = item.getAttribute('data-category');
                    if (category === 'all' || itemCat === category) {
                        item.style.display = 'none'; // Hide initially, show by pagination
                        visibleItems.push(item);
                    } else {
                        item.style.display = 'none';
                    }
                });
                currentPage = 1;
                renderPagination();
                showPage(1);
            }

            function showPage(page) {
                currentPage = page;
                const start = (page - 1) * itemsPerPage;
                const end = start + itemsPerPage;
                
                // Hide all first (already done in filter, but ensure)
                items.forEach(i => i.style.display = 'none');
                
                // Show current page items
                visibleItems.slice(start, end).forEach(item => {
                    item.style.display = 'block';
                    // Add fade-in animation
                    item.style.opacity = '0';
                    item.style.transform = 'translateY(10px)';
                    setTimeout(() => {
                        item.style.transition = 'all 0.3s ease';
                        item.style.opacity = '1';
                        item.style.transform = 'translateY(0)';
                    }, 50);
                });
                
                renderPagination();
                
                // Scroll to top of list if needed
                // const listTop = document.querySelector('#article-filters').offsetTop;
                // window.scrollTo({top: listTop - 100, behavior: 'smooth'});
            }

            function renderPagination() {
                paginationContainer.innerHTML = '';
                const totalPages = Math.ceil(visibleItems.length / itemsPerPage);
                
                if (totalPages <= 1) return;

                // Prev
                const prevBtn = document.createElement('button');
                prevBtn.className = `px-3 py-1 rounded border ${currentPage === 1 ? 'text-slate-300 border-slate-100 cursor-not-allowed' : 'text-slate-600 border-slate-200 hover:border-emerald-500'}`;
                prevBtn.innerHTML = '←';
                prevBtn.disabled = currentPage === 1;
                prevBtn.onclick = () => showPage(currentPage - 1);
                paginationContainer.appendChild(prevBtn);

                // Pages
                for (let i = 1; i <= totalPages; i++) {
                    const btn = document.createElement('button');
                    btn.className = `px-3 py-1 rounded border font-bold ${currentPage === i ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-slate-600 border-slate-200 hover:border-emerald-500'}`;
                    btn.innerText = i;
                    btn.onclick = () => showPage(i);
                    paginationContainer.appendChild(btn);
                }

                // Next
                const nextBtn = document.createElement('button');
                nextBtn.className = `px-3 py-1 rounded border ${currentPage === totalPages ? 'text-slate-300 border-slate-100 cursor-not-allowed' : 'text-slate-600 border-slate-200 hover:border-emerald-500'}`;
                nextBtn.innerHTML = '→';
                nextBtn.disabled = currentPage === totalPages;
                nextBtn.onclick = () => showPage(currentPage + 1);
                paginationContainer.appendChild(nextBtn);
            }

            // Init Filters
            filters.forEach(btn => {
                btn.addEventListener('click', () => {
                    filters.forEach(b => {
                        b.classList.remove('bg-slate-900', 'text-white');
                        b.classList.add('bg-white', 'text-slate-600');
                    });
                    btn.classList.remove('bg-white', 'text-slate-600');
                    btn.classList.add('bg-slate-900', 'text-white');
                    filterItems(btn.getAttribute('data-filter'));
                });
            });

            // Initial Load
            filterItems('all');
        });
        </script>
        '''
        if soup.body:
            soup.body.append(BeautifulSoup(js_code, 'html.parser'))

    write_file(articles_index_path, str(soup))

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

        # --- C2. Breadcrumbs ---
        inject_breadcrumb(soup, file_path)

        # --- D. Recommended Reading ---
        inject_recommended_reading(soup, file_path)

        # --- Save ---
        output_html = str(soup)
        if not output_html.startswith('<!DOCTYPE html>'):
             output_html = '<!DOCTYPE html>\n' + output_html
             
        write_file(file_path, output_html)

    print("Build completed.")
    
    # Auto-generate Articles Index (Pagination & Classification)
    generate_articles_index()
    
    # Auto-generate Sitemap
    print("Generating sitemap...")
    generate_sitemap.main()

if __name__ == '__main__':
    run_build()
