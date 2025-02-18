import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
import xml.etree.ElementTree as ET

# Настройки
BASE_URL = "https://cdn.changes.tg/gifts/"
LOCAL_UPLOAD_DIR = "upload"
SITEMAP_FILE = "sitemap.xml"

# Создание локальной директории, если она не существует
def create_directory(path):
    Path(path).mkdir(parents=True, exist_ok=True)

# Проверка, является ли ссылка файлом
def is_file_link(link):
    extensions = ['.json', '.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.txt', '.mp4', '.webm']
    return any(link.lower().endswith(ext) for ext in extensions)

# Скачивание файла
def download_file(url, local_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {url}")
        else:
            print(f"Failed to download: {url} (Status Code: {response.status_code})")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Рекурсивное обход дерева файлов
def crawl_and_download(base_url, current_url, local_dir):
    response = requests.get(current_url)
    if response.status_code != 200:
        print(f"Failed to access: {current_url}")
        return []
   
    soup = BeautifulSoup(response.text, 'html.parser')
    links = []
    
    """
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(current_url, href)
        
        if full_url.startswith(base_url):
            relative_path = full_url.replace(base_url, "")
            local_file_path = os.path.join(local_dir, relative_path)
            
            if is_file_link(full_url):
                # Это файл - скачиваем его
                create_directory(os.path.dirname(local_file_path))
                download_file(full_url, local_file_path)
                links.append(full_url)
            elif href.endswith('/'):  # Это папка
                # Рекурсивно обходим папку
                crawl_and_download(base_url, full_url, local_dir)
    """
    # Парсим таблицу с файлами и папками
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')[1:]  # Пропускаем заголовок таблицы
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                a_tag = cols[1].find('a')
                if a_tag and 'href' in a_tag.attrs:
                    href = a_tag['href'].strip()
                    if not href:  # Пропускаем пустые ссылки
                        continue

                    full_url = urljoin(current_url, href)

                    # Пропускаем ссылки, которые выходят за пределы базового URL
                    if not full_url.startswith(base_url):
                        continue

                    relative_path = full_url.replace(base_url, "")
                    local_file_path = os.path.join(local_dir, relative_path)

                    if is_file_link(full_url):
                        # Это файл - скачиваем его
                        create_directory(os.path.dirname(local_file_path))
                        download_file(full_url, local_file_path)
                        links.append(full_url)
                    elif href.endswith('/'):  # Это папка
                        # Рекурсивно обходим папку
                        sub_links = crawl_and_download(base_url, full_url, local_dir)
                        links.extend(sub_links)  # Добавляем найденные ссылки из подпапки

    print(links)
    return links

# Создание sitemap.xml
def create_sitemap(file_links, sitemap_file_path):
    root = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    
    for link in file_links:
        url = ET.SubElement(root, "url")
        loc = ET.SubElement(url, "loc")
        loc.text = link
    
    tree = ET.ElementTree(root)
    tree.write(sitemap_file_path, encoding='utf-8', xml_declaration=True)
    print(f"Sitemap created: {sitemap_file_path}")

# Основной скрипт
if __name__ == "__main__":
    create_directory(LOCAL_UPLOAD_DIR)
    all_file_links = crawl_and_download(BASE_URL, BASE_URL, LOCAL_UPLOAD_DIR)
    create_sitemap(all_file_links, os.path.join(LOCAL_UPLOAD_DIR, SITEMAP_FILE))