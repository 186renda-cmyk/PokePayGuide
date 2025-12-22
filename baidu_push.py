import requests

# 百度推送接口
api_url = "http://data.zz.baidu.com/urls?site=https://pokepayguide.top&token=MkpV4it8Aq1PaVbS"

# 需要推送的链接列表
urls = [
    "https://pokepayguide.top/",
    "https://pokepayguide.top/archive.html",
    "https://pokepayguide.top/articles/pokepay-virtual-card-guide.html",
    "https://pokepayguide.top/articles/pokepay-bind-paypal-chatgpt.html",
    "https://pokepayguide.top/articles/okx-usdt-topup-trc20.html",
    "https://pokepayguide.top/articles/subscription-failure-checklist.html",
    "https://pokepayguide.top/articles/pokepay-kaopu-ma.html",
    "https://pokepayguide.top/articles/pokepay-fees-and-limits.html"
]

headers = {
    'User-Agent': 'curl/7.12.1',
    'Content-Type': 'text/plain'
}

try:
    print("正在向百度推送链接...")
    response = requests.post(api_url, data="\n".join(urls), headers=headers)
    print("【推送结果】:", response.text)
except Exception as e:
    print("发生错误:", e)
