
import os
from bs4 import BeautifulSoup

path = '/Users/xiaxingyu/Desktop/网站项目/PokePay/articles/how-to-bind-pokepay-to-alipay.html'
try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        h1s = soup.find_all('h1')
        print(f"File: {path}")
        print(f"Content length: {len(content)}")
        print(f"H1 count: {len(h1s)}")
        if h1s:
            print(f"H1 content: {h1s[0].text.strip()}")
        else:
            print("No H1 found.")
            # Print first 500 chars to see if file is empty or weird
            print("Head of file:")
            print(content[:500])
except Exception as e:
    print(f"Error: {e}")
