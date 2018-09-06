# Ptt_Crawler/Ptt爬蟲試作
## ptt爬蟲的練習 主要參考 <https://github.com/leVirve/CrawlerTutorial>

### 目前能夠 

### 1)選擇板
```python
board = input('\n看哪個板 :').lower()
url = 'https://www.ptt.cc/bbs/' + board + '/index.html'
post_entries, page_entries = get_page_info(url)
```
### 2)選擇上頁or下頁
```python
def page_choose(current_url, page_entries, choice):
    prefix = 'https://www.ptt.cc'
    latest_url, oldest_url, prev_url, next_url, url = '', '', '', '', ''
    for entry in page_entries:
        if '最新' in entry.text:
            latest_url = prefix + entry.find('a.btn', first=True).attrs['href'].lower()
        elif '最舊' in entry.text:
            oldest_url = prefix + entry.find('a.btn', first=True).attrs['href'].lower()
    for entry in page_entries:
        if '上頁' in entry.text and current_url != oldest_url:
            prev_url = prefix + entry.find('a.btn', first=True).attrs['href']
        elif ('下頁' in entry.text) and current_url != latest_url:
            next_url = prefix + entry.find('a.btn', first=True).attrs['href']
            
url = page_choose(url, page_entries, choice)
# Get the page info
post_entries, page_entries = get_page_info(url)
```
### 3)選擇文章 取得作者、標題、時間、內文，以及推文等資訊
```python
def parse_content_entries(doc):  # 取得內文
    html = HTML(html=doc)
    content_entries = html.find('div.bbs-screen')
    comment_entries = html.find('div.push')
    title_entries = html.find('div.article-metaline')
    return content_entries, title_entries, comment_entries


def parse_comment_meta(entry):  # 取得推文
    return {
        'push_tag': entry.find('span.push-tag', first=True).text,
        'push_userid': entry.find('span.push-userid', first=True).text,
        'push_content': entry.find('span.push-content', first=True).text,
        'push_ipdatetime': entry.find('span.push-ipdatetime', first=True).text,
    }


def parse_title_meta(entry):  # 取得作者標題時間
    return {
        'tag': entry.find('span.article-meta-tag', first=True).text,
        'value': entry.find('span.article-meta-value', first=True).text,
    }
```

#### 之後可能會再加上搜尋文章的功能，或是搜尋作者。
