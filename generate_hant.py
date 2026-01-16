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

def clean_url_path(path):
    """
    Removes .html and index.html from path to form a clean URL path.
    path: relative file path (e.g. articles/foo.html)
    """
    # Remove .html extension
    if path.endswith('.html'):
        path = path[:-5]
    
    # Remove index (e.g. articles/index -> articles/)
    if path.endswith('index'):
        path = path[:-5]
        
    # Ensure no backslashes
    path = path.replace('\\', '/')
    
    # Ensure no leading slash for joining
    path = path.lstrip('/')
    
    # Ensure trailing slash for directory-like paths (optional, but consistent with folder structure)
    # If it was index.html, it becomes empty string or folder name.
    # Logic:
    # index.html -> ""
    # articles/index.html -> articles/
    # articles/foo.html -> articles/foo
    
    return path

def process_file(file_path):
    """读取文件，转换内容，并保存到对应的繁体目录"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. 转换全文本
        content_hant = convert_text(content)
        
        # 2. 修正 lang 属性
        content_hant = content_hant.replace('lang="zh-CN"', 'lang="zh-Hant"')
        
        # 3. 修正 meta 标签中的简体字 (如 "简体中文" -> "繁体中文")
        
        # 4. 添加 hreflang 标签 (关键步骤)
        # 获取相对路径
        rel_path = os.path.relpath(file_path, start='.')
        if rel_path.startswith('./'):
            rel_path = rel_path[2:]
            
        # 构建 Clean URL
        base_url = "https://pokepayguide.top"
        
        # Hans URL
        hans_clean_path = clean_url_path(rel_path)
        zh_hans_url = f"{base_url}/{hans_clean_path}"
        
        # Hant URL and Path
        if 'articles' in rel_path:
             target_rel_path = rel_path.replace('articles/', 'articles/zh-hant/')
             hant_clean_path = clean_url_path(target_rel_path)
             canonical_url = f"{base_url}/{hant_clean_path}"
        else:
             target_rel_path = f"zh-hant/{rel_path}"
             hant_clean_path = clean_url_path(target_rel_path)
             canonical_url = f"{base_url}/{hant_clean_path}"
        
        # 插入 hreflang 标签到 <head> 中
        hreflang_tags = f'''
  <link rel="alternate" hreflang="zh-CN" href="{zh_hans_url}" />
  <link rel="alternate" hreflang="zh-Hant" href="{canonical_url}" />
  <link rel="canonical" href="{canonical_url}">
'''
        # 替换原有的 canonical (如果有)
        content_hant = re.sub(r'<link rel="canonical" href="[^"]+">', '', content_hant)
        
        # 插入新的标签
        content_hant = content_hant.replace('</head>', f'{hreflang_tags}</head>')
        
        # 5. 修正内部链接 (将 .html 链接指向对应的繁体版本)
        # 这一步由 sync_layout.py 统一处理 Clean URL，这里只需要处理路径映射
        # 但是 sync_layout.py 不知道 zh-hant 映射，它只是 clean .html。
        # 所以我们需要在这里把链接指向 zh-hant 版本。
        
        # Replace root link
        content_hant = content_hant.replace('href="/"', 'href="/zh-hant/"')
        content_hant = content_hant.replace('href="/index.html"', 'href="/zh-hant/"')
        
        # Replace article archive link
        content_hant = content_hant.replace('href="/articles/"', 'href="/articles/zh-hant/"')
        
        # Replace other internal links?
        # If we have href="/articles/foo.html", we want href="/articles/zh-hant/foo"
        # Since sync_layout will strip .html, we can just replace "/articles/" with "/articles/zh-hant/"
        # But be careful not to double replace.
        
        # Regex replace for /articles/ (excluding /articles/zh-hant/)
        # Look for href="/articles/(?!zh-hant)
        content_hant = re.sub(r'href="/articles/(?!zh-hant)', 'href="/articles/zh-hant/', content_hant)

        # 保存文件
        target_path = Path(target_rel_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content_hant)
            
        print(f"Generated: {target_path}")
        return target_rel_path

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def main():
    # 1. 处理根目录 HTML
    for file in os.listdir('.'):
        if file.endswith('.html') and file not in IGNORE_FILES:
            process_file(file)

    # 2. 处理 articles 目录 HTML
    if os.path.exists('articles'):
        for file in os.listdir('articles'):
            if file.endswith('.html') and file not in IGNORE_FILES:
                process_file(os.path.join('articles', file))

if __name__ == '__main__':
    main()
