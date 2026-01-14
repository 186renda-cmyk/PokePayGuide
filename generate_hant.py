import os
import opencc
import re
from pathlib import Path

# 配置 OpenCC (简体 -> 繁体)
converter = opencc.OpenCC('s2t.json')

# 目录配置
SOURCE_DIRS = ['.', 'articles']
HANT_DIR_NAME = 'zh-hant'

# 需要排除的文件
IGNORE_FILES = ['googlea685aa8ff3686b48.html', 'BingSiteAuth.xml', '_master_template.html', 'zujina.html']

def convert_text(text):
    """转换文本，但保留 HTML 标签和特定属性"""
    return converter.convert(text)

def process_file(file_path):
    """读取文件，转换内容，并保存到对应的繁体目录"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 转换全文本 (OpenCC 会智能处理，但我们可能需要后续修正 hreflang 和 lang)
        content_hant = convert_text(content)
        
        # 2. 修正 lang 属性
        content_hant = content_hant.replace('lang="zh-CN"', 'lang="zh-Hant"')
        
        # 3. 修正 meta 标签中的简体字 (如 "简体中文" -> "繁体中文")
        # OpenCC 应该已经处理了大部分，这里做特定检查
        
        # 4. 添加 hreflang 标签 (关键步骤)
        # 获取相对路径
        rel_path = os.path.relpath(file_path, start='.')
        if rel_path.startswith('./'):
            rel_path = rel_path[2:]
            
        # 构建 URL
        base_url = "https://pokepayguide.top"
        zh_hans_url = f"{base_url}/{rel_path}".replace('//', '/')
        zh_hant_url = f"{base_url}/{rel_path}".replace('articles/', 'articles/zh-hant/').replace('index.html', 'zh-hant/index.html') 
        
        # 简单处理：对于根目录文件，繁体版放在 zh-hant/ 下
        # 对于 articles/ 下的文件，繁体版放在 articles/zh-hant/ 下
        
        if 'articles' in rel_path:
             target_rel_path = rel_path.replace('articles/', 'articles/zh-hant/')
             canonical_url = f"{base_url}/{target_rel_path}"
             alternate_hans = f"{base_url}/{rel_path}"
        else:
             target_rel_path = f"zh-hant/{rel_path}"
             canonical_url = f"{base_url}/{target_rel_path}"
             alternate_hans = f"{base_url}/{rel_path}"

        # 插入 hreflang 标签到 <head> 中
        hreflang_tags = f'''
  <link rel="alternate" hreflang="zh-CN" href="{alternate_hans}" />
  <link rel="alternate" hreflang="zh-Hant" href="{canonical_url}" />
  <link rel="canonical" href="{canonical_url}">
'''
        # 替换原有的 canonical (如果有)
        content_hant = re.sub(r'<link rel="canonical" href="[^"]+">', '', content_hant)
        
        # 插入新的标签
        content_hant = content_hant.replace('</head>', f'{hreflang_tags}</head>')
        
        # 5. 修正内部链接 (将 .html 链接指向对应的繁体版本，如果存在)
        # 这一步比较复杂，暂略，或者通过 JS 动态处理，或者简单地让用户通过 hreflang 切换
        # 为了简单起见，我们假设内部链接还是指向简体，但通过 hreflang 告诉 Google 关系
        # 更好的做法是将导航栏链接也替换为 /zh-hant/xxx.html
        
        # 简单替换常见导航链接
        content_hant = content_hant.replace('href="/articles/"', 'href="/articles/zh-hant/"')
        content_hant = content_hant.replace('href="/index.html"', 'href="/zh-hant/index.html"')
        content_hant = content_hant.replace('href="/"', 'href="/zh-hant/"')
        
        # 替换文章链接
        # 查找所有 .html 链接并添加 zh-hant 前缀 (如果不是外部链接)
        def replace_link(match):
            url = match.group(1)
            if url.startswith('http') or url.startswith('#') or 'zh-hant' in url:
                return f'href="{url}"'
            
            if url.startswith('/'):
                if url.startswith('/articles/'):
                    return f'href="/articles/zh-hant/{url.split("/")[-1]}"'
                return f'href="/zh-hant{url}"'
            else:
                # 相对路径
                return f'href="{url}"' # 保持相对路径，因为文件结构改变了，可能需要调整

        # 这一步风险较大，先不做大规模正则替换，依靠 base tag 或者后续优化
        
        # 保存文件
        target_path = Path(target_rel_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content_hant)
            
        print(f"Generated: {target_path}")
        return target_rel_path, canonical_url

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, None

def main():
    generated_pages = []
    
    # 1. 处理根目录 HTML
    for file in os.listdir('.'):
        if file.endswith('.html') and file not in IGNORE_FILES:
            res = process_file(file)
            if res[0]: generated_pages.append(res)

    # 2. 处理 articles 目录 HTML
    if os.path.exists('articles'):
        for file in os.listdir('articles'):
            if file.endswith('.html') and file not in IGNORE_FILES:
                res = process_file(os.path.join('articles', file))
                if res[0]: generated_pages.append(res)

    # 3. 生成 sitemap-hant.xml
    generate_sitemap(generated_pages)

def generate_sitemap(pages):
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for path, url in pages:
        priority = "0.8"
        if "index.html" in path: priority = "1.0"
        
        sitemap_content += f'''  <url>
    <loc>{url}</loc>
    <lastmod>2026-01-14</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{priority}</priority>
  </url>
'''
    sitemap_content += '</urlset>'
    
    with open('sitemap-hant.xml', 'w', encoding='utf-8') as f:
        f.write(sitemap_content)
    print("Generated sitemap-hant.xml")

if __name__ == '__main__':
    main()
