import os
import re

# Configuration
PROJECT_ROOT = '/Users/xiaxingyu/Desktop/网站项目/PokePay'
ARTICLES_DIR = os.path.join(PROJECT_ROOT, 'articles')

# The new navigation HTML
NEW_NAV = """<nav class="fixed top-0 w-full z-50 glass-nav transition-all duration-300 h-20 flex items-center border-b border-slate-200/60">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex items-center justify-between">
    <a href="/" class="flex items-center gap-3 group">
      <div class="relative w-10 h-10 flex items-center justify-center bg-transparent group-hover:scale-105 transition-transform duration-200">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="w-10 h-10 drop-shadow-md"><rect width="100" height="100" rx="24" fill="#059669"/><path d="M35 25h15c15 0 20 5 20 15s-5 15-20 15h-5v20h-10V25z m10 22h5c8 0 10-2 10-7s-2-7-10-7h-5v14z" fill="white"/></svg>
      </div>
      <div class="flex flex-col"><span class="font-extrabold text-xl tracking-tight text-slate-900 leading-none">Pokepay<span class="text-emerald-600">Guide</span></span><span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mt-1">Unofficial Guide</span></div>
    </a>
    <div class="hidden md:flex items-center gap-6 text-sm font-bold text-slate-600">
      <a href="/index.html#features" class="hover:text-emerald-600 transition">优势</a>
      <a href="/index.html#tutorial" class="hover:text-emerald-600 transition">教程</a>
      <a href="/index.html#okx-tutorial" class="hover:text-emerald-600 transition">充值</a>
      <a href="/index.html#faq" class="hover:text-emerald-600 transition">问答</a>
    </div>
    <div class="hidden md:flex items-center gap-4">
      <a href="/go/okx" target="_blank" class="text-sm font-bold text-slate-500 hover:text-emerald-600 transition flex items-center gap-1.5 px-2">
        <span class="relative flex h-2.5 w-2.5"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span><span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span></span>
        USDT买币
      </a>
      <a href="/go/pokepay" target="_blank" class="inline-flex items-center justify-center px-6 py-2.5 text-sm font-bold text-white bg-slate-900 rounded-full hover:bg-slate-800 transition shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0">立即开卡</a>
    </div>
  </div>
</nav>"""

# The new footer HTML
NEW_FOOTER = """<footer class="bg-slate-900 text-slate-400 py-16 border-t border-slate-800 mt-20">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12 mb-16">
      <div class="space-y-6">
        <div class="flex items-center gap-2 text-white">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" class="w-8 h-8 fill-current text-emerald-500"><rect width="100" height="100" rx="24" fill="currentColor"/><path d="M35 25h15c15 0 20 5 20 15s-5 15-20 15h-5v20h-10V25z m10 22h5c8 0 10-2 10-7s-2-7-10-7h-5v14z" fill="white"/></svg>
          <span class="text-xl font-bold tracking-tight">Pokepay<span class="text-emerald-500">Guide</span></span>
        </div>
        <p class="text-sm text-slate-500 leading-relaxed">您的 Web3 跨境支付第一站。致力于解决 ChatGPT、OnlyFans 等海外订阅支付难题，连接加密资产与现实消费。</p>
      </div>
      <div>
        <h4 class="text-white font-bold mb-6">产品与服务</h4>
        <ul class="space-y-4 text-sm">
          <li><a href="/articles/pokepay-virtual-card-guide.html" class="hover:text-emerald-500 transition">Pokepay 虚拟卡</a></li>
          <li><a href="/articles/pokepay-fees-and-limits.html" class="hover:text-emerald-500 transition">费率与限额</a></li>
          <li><a href="/articles/okx-usdt-topup-trc20.html" class="hover:text-emerald-500 transition">USDT 充值</a></li>
        </ul>
      </div>
      <div>
        <h4 class="text-white font-bold mb-6">热门教程</h4>
        <ul class="space-y-4 text-sm">
          <li><a href="/articles/pokepay-bind-paypal-chatgpt.html" class="hover:text-emerald-500 transition">绑定 PayPal 教程</a></li>
          <li><a href="/articles/pokepay-kaopu-ma.html" class="hover:text-emerald-500 transition">安全性深度评测</a></li>
          <li><a href="/articles/subscription-failure-checklist.html" class="hover:text-emerald-500 transition">解决 Visa 支付被拒</a></li>
        </ul>
      </div>
      <div>
        <h4 class="text-white font-bold mb-6">合规声明</h4>
        <div class="text-xs text-slate-500 space-y-4 leading-relaxed">
          <p><strong class="text-slate-400">非官方指南：</strong>本站 (PokepayGuide.top) 为第三方测评与教程网站，非 Pokepay 官方运营。</p>
          <p><strong class="text-slate-400">风险提示：</strong>加密资产属于高风险投资，请用户在充值和消费时注意资金安全。</p>
        </div>
      </div>
    </div>
    <div class="pt-8 border-t border-slate-800 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-slate-600">
      <div>&copy; 2026 PokepayGuide.top. All rights reserved.</div>
      <div class="flex gap-6"><a href="/" class="hover:text-slate-400 transition">返回首页</a></div>
    </div>
  </div>
</footer>"""

# The mobile bottom bar HTML to check/insert
MOBILE_BAR = """<div class="fixed bottom-0 left-0 right-0 p-4 bg-white/90 backdrop-blur-lg border-t border-slate-200 lg:hidden z-50 safe-area-bottom">
    <div class="flex gap-3">
      <a href="/go/okx" class="flex-1 flex items-center justify-center px-4 py-3 rounded-xl border border-slate-200 text-slate-700 font-bold text-sm bg-white">USDT充值</a>
      <a href="/go/pokepay" class="flex-1 flex items-center justify-center px-4 py-3 rounded-xl bg-brand-600 text-white font-bold text-sm shadow-lg">立即开卡</a>
    </div>
  </div>"""

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_articles():
    print(f"Processing articles in {ARTICLES_DIR}...")
    for filename in os.listdir(ARTICLES_DIR):
        if not filename.endswith('.html'):
            continue
            
        file_path = os.path.join(ARTICLES_DIR, filename)
        print(f"  Updating {filename}...")
        
        content = read_file(file_path)
        
        # 1. Replace Nav
        if '<nav' in content:
            content = re.sub(r'<nav.*?</nav>', NEW_NAV, content, flags=re.DOTALL)
        else:
            print(f"    Warning: No <nav> found in {filename}, inserting...")
            content = content.replace('<body class="font-sans pt-24 pb-24 md:pb-0">', f'<body class="font-sans pt-24 pb-24 md:pb-0">\n{NEW_NAV}', 1)

        # 2. Replace Footer
        if '<footer' in content:
            content = re.sub(r'<footer.*?</footer>', NEW_FOOTER, content, flags=re.DOTALL)
        else:
            print(f"    Warning: No <footer> found in {filename}, inserting...")
            content = content.replace('</body>', f'{NEW_FOOTER}\n</body>')

        # 3. Ensure Mobile Bar exists
        # Use a simple check for "fixed bottom-0" which is characteristic of the bar
        if 'fixed bottom-0' not in content:
            print(f"    Adding mobile bar to {filename}...")
            # Insert before </body>
            content = content.replace('</body>', f'{MOBILE_BAR}\n</body>')
        
        write_file(file_path, content)

    print("Batch update completed.")

if __name__ == '__main__':
    update_articles()
