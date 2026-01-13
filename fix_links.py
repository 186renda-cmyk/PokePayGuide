import os
import re

def fix_sales_links(target_paths):
    # Mapping for /go/ links to homepage anchors
    GO_MAPPING = {
        'pokepay': '/index.html#tutorial',
        'okx': '/index.html#okx-tutorial'
    }

    all_files = []
    for path in target_paths:
        if os.path.isdir(path):
            all_files.extend([os.path.join(path, f) for f in os.listdir(path) if f.endswith('.html')])
        elif os.path.isfile(path) and path.endswith('.html'):
            all_files.append(path)

    report = []

    for file_path in all_files:
        filename = os.path.basename(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Fix /go/ links
        pattern_go = r'<a\s+[^>]*?href="/go/([^"]+)"[^>]*?>.*?</a>'
        
        def replace_go_link(match):
            full_tag = match.group(0)
            go_path = match.group(1)
            
            # For index.html itself, /index.html#anchor should just be #anchor
            is_index = filename == "index.html"
            base_url = "" if is_index else "/index.html"
            new_href = GO_MAPPING.get(go_path, "/index.html")
            if is_index and new_href.startswith("/index.html#"):
                new_href = new_href.replace("/index.html", "")
            
            # Replace href
            new_tag = re.sub(r'href="/go/[^"]+"', f'href="{new_href}"', full_tag)
            # Remove target="_blank"
            new_tag = re.sub(r'\s*target="_blank"\s*', ' ', new_tag)
            # Remove rel attributes entirely for internal links
            new_tag = re.sub(r'\s*rel="[^"]*"\s*', ' ', new_tag)
            # Clean up whitespace
            new_tag = re.sub(r'\s+>', '>', new_tag)
            new_tag = re.sub(r'\s+', ' ', new_tag)
            
            report.append(f"[{filename}] Fixed /go/{go_path} -> {new_href}")
            return new_tag

        new_content = re.sub(pattern_go, replace_go_link, content, flags=re.DOTALL)

        # 2. Fix /index.html links (ensure they have anchors and NO nofollow)
        pattern_index = r'<a\s+[^>]*?href="/index\.html(?:#[^"]*)?"[^>]*?>.*?</a>'

        def replace_index_link(match):
            full_tag = match.group(0)
            
            # Extract link text to guess anchor
            link_text_match = re.search(r'>(.*?)</a>', full_tag, re.DOTALL)
            link_text = link_text_match.group(1) if link_text_match else ""
            
            current_href_match = re.search(r'href="(/index\.html(?:#[^"]*)?)"', full_tag)
            current_href = current_href_match.group(1) if current_href_match else "/index.html"
            
            new_href = current_href
            if '#' not in current_href:
                anchor = ""
                if any(k in link_text for k in ["开卡", "注册", "免费", "账户"]):
                    anchor = "#tutorial"
                elif any(k in link_text for k in ["充值", "买币", "USDT", "欧易"]):
                    anchor = "#okx-tutorial"
                elif any(k in link_text for k in ["下载", "APP", "安装"]):
                    anchor = "#download"
                
                if anchor:
                    new_href = f"/index.html{anchor}"
                    report.append(f"[{filename}] Added anchor {anchor} to /index.html")

            # Remove rel attributes for all internal links to homepage
            new_tag = re.sub(r'href="/index\.html(?:#[^"]*)?"', f'href="{new_href}"', full_tag)
            new_tag = re.sub(r'\s*rel="[^"]*"\s*', ' ', new_tag)
            new_tag = re.sub(r'\s*target="_blank"\s*', ' ', new_tag)
            
            # Clean up whitespace
            new_tag = re.sub(r'\s+>', '>', new_tag)
            new_tag = re.sub(r'\s+', ' ', new_tag)
            
            if new_tag != full_tag:
                report.append(f"[{filename}] Cleaned internal link {new_href}")
            
            return new_tag

        new_content = re.sub(pattern_index, replace_index_link, new_content, flags=re.DOTALL)

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

    return report

if __name__ == "__main__":
    base_dir = "/Users/xiaxingyu/Desktop/网站项目/PokePay"
    targets = [
        os.path.join(base_dir, "articles"),
        os.path.join(base_dir, "index.html"),
        os.path.join(base_dir, "archive.html"),
        os.path.join(base_dir, "privacy-policy.html"),
        os.path.join(base_dir, "terms-of-service.html"),
        os.path.join(base_dir, "_master_template.html")
    ]
    fixes = fix_sales_links(targets)
    for fix in fixes:
        print(fix)
    print(f"\nTotal fixes: {len(fixes)}")
