
import os
from bs4 import BeautifulSoup

PROJECT_ROOT = '/Users/xiaxingyu/Desktop/网站项目/PokePay/articles'

def refactor_article(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Check if it has the old grid layout
    main_grid = soup.find('main', class_='lg:grid lg:grid-cols-12 lg:gap-12')
    if not main_grid:
        print(f"Skipping {os.path.basename(file_path)}: Grid layout not found.")
        return

    # Extract article
    article = main_grid.find('article', class_='lg:col-span-8')
    if not article:
        print(f"Skipping {os.path.basename(file_path)}: Article column not found.")
        return
        
    # Modify article classes
    article['class'] = ['max-w-4xl', 'mx-auto'] # Remove col-span-8, add centering
    
    # Create new main container
    new_main = soup.new_tag('main', attrs={'class': 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12'})
    
    # Create a wrapper for the article to ensure proper centering and spacing
    # Actually, putting article directly in main with max-w-3xl or 4xl is better for reading.
    # The user wants "clean layout". A single column centered text is best.
    
    # Let's clean up the article header as well if needed, but for now just structure.
    # The article tag contains the header and content.
    
    # We will remove the sidebar completely.
    
    # Replace the old main with new structure
    new_main.append(article)
    main_grid.replace_with(new_main)
    
    # Save
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Refactored {os.path.basename(file_path)}")

def run():
    for filename in os.listdir(PROJECT_ROOT):
        if filename.endswith('.html') and filename != 'index.html':
            refactor_article(os.path.join(PROJECT_ROOT, filename))

if __name__ == '__main__':
    run()
