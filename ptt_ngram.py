import requests
import re
import string
import operator
import urllib.parse
from requests_html import HTML

def fetch(url):
    response = requests.get(url, cookies={'over18': '1'})  # 一直向 server 回答滿 18 歲了 !
    return response


def parse_article_entries(doc):
    html = HTML(html=doc)
    post_entries = html.find('div.r-ent')
    page_entries = html.find('div.btn-group-paging > a')
    return post_entries, page_entries


def parse_article_meta(entry):
    #  每筆資料都存在 dict() 類型中：key-value paird data
    article_meta = {
        'title': entry.find('div.title', first=True).text,
        'push': entry.find('div.nrec', first=True).text,
        'date': entry.find('div.date', first=True).text,
    }
    try:
        # Normal situation
        article_meta['author'] = entry.find('div.author', first=True).text
        article_meta['link'] = entry.find('div.title > a', first=True).attrs['href']
    except AttributeError:
        # if post had been deleted
        if '(本文已被刪除)' in article_meta['title']:
            # e.g., "(本文已被刪除)"
            match_author = re.search('\[(\w*)\]', article_meta['title'])
            if match_author:
                article_meta['author'] = match_author.group(1)
        elif re.search('已被\w*刪除', article_meta['title']):
            # e.g., "(已被xxxxxx刪除) <xxxxxx> op"
            match_author = re.search('\<(\w*)\>', article_meta['title'])
            if match_author:
                article_meta['author'] = match_author.group(1)
    return article_meta


def parse_content_entries(doc):
    html = HTML(html=doc)
    content_entries = html.find('div.bbs-screen')
    comment_entries = html.find('div.push')
    title_entries = html.find('div.article-metaline')
    return content_entries, title_entries, comment_entries


def parse_comment_meta(entry):
    return {
        'push_tag': entry.find('span.push-tag', first=True).text,
        'push_userid': entry.find('span.push-userid', first=True).text,
        'push_content': entry.find('span.push-content', first=True).text,
        'push_ipdatetime': entry.find('span.push-ipdatetime', first=True).text,
    }


def parse_title_meta(entry):
    return {
        'tag': entry.find('span.article-meta-tag', first=True).text,
        'value': entry.find('span.article-meta-value', first=True).text,
    }


def pretty_print(push, title, date, author):
    title = align_str('{0:　<31}'.format(title))
    if push == '':  # push is 0
        push = 0
    #  print("push = ",push)
    print('{0: >2}{1}{2}{3: <5}{4}{5: <15}'.format(push, ' ', title, date, '\t', author))


def comment_print(tag, user, content, date):
    content = align_str('{0:　<31}'.format(content))
    print('{0: <2}{1: <12}{2}{3}{4: >11}'.format(tag, user, content, '\t', date))


def align_str(string):
    eng = 0
    for s in string:
        if ord(s) <= 127:
            eng += 1
    for i in range(eng):
        string += ' '
    return string


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
        elif ('下頁' in entry.text) and (current_url != latest_url):
            next_url = prefix + entry.find('a.btn', first=True).attrs['href']
    if choice == 'a':
        url = oldest_url
    elif choice == 'b':
        url = prev_url
    elif choice == 'c':
        url = next_url
    elif choice == 'd':
        url = latest_url
    return url


def get_page_info(url):
    resp = fetch(url)  # step-1
    if str(resp) == '<Response [404]>':
        print('\n此板不存在')
        return 0, 0
    post_entries, page_entries = parse_article_entries(resp.text)  # step-2
    # print article title author etc...
    temp_title = ''
    for entry in post_entries:
        meta = parse_article_meta(entry)
        #pretty_print(meta['push'], meta['title'], meta['date'], meta['author'])  # for below results
        temp_title += re.sub('(.+])|(Re: )|(不是)|(是不)|(18夏)|(本文已被刪除)|(什麼)|(可以)|(八卦)|(有沒有)','',meta['title'])
    return post_entries, page_entries, temp_title


def ngram(input,n):
    input = re.sub(':|：|\[|\]|,|\?|？|\!|\(|\)| +|\n+','',input)
    ndict = {}
    for i in range(len(input)-n+1):
        nword = input[i:i+n]
        #print("nword is :",nword)
        if nword not in ndict:
            ndict[nword] = 0
        ndict[nword] += 1
    return ndict


all_title = ''
post_entries, page_entries = 0, 0
while post_entries == page_entries == 0:
    board = input('\n看哪個板 :').lower()
    url = 'https://www.ptt.cc/bbs/' + board + '/index.html'
    post_entries, page_entries, temp_title = get_page_info(url)
all_title += temp_title
for i in range(100):
    url = page_choose(url, page_entries, 'b')
    #print(url)
    post_entries, page_entries, temp_title = get_page_info(url)
    all_title += temp_title
print(sorted(ngram(all_title,3).items(),key=operator.itemgetter(1),reverse=True)[:10])
# User action
choice = input('\nA : 最舊\tB :< 上頁\tC :下頁 >\tD :最新 \tE :看文 --> ').lower()
try:
    # Choose page
    while choice != 'e':
        url = page_choose(url, page_entries, choice)
        # Get the page info
        post_entries, page_entries = get_page_info(url,all_title)
        choice = input('\nA : 最舊\tB :< 上頁\tC :下頁 >\tD :最新\tE :看文 --> ').lower()
    # Lookup article
    post_num = int(input('\n第幾篇文 : '))
    print('')
    article_meta = parse_article_meta(post_entries[post_num-1])
    link = article_meta['link']
    post_url = urllib.parse.urljoin('https://www.ptt.cc', link) # for post_content
    post_resp = fetch(post_url)
    content_entries, title_entries, comment_entries = parse_content_entries(post_resp.text)
    split_str = ''
    # print article info
    for entry in title_entries:
        title_meta = parse_title_meta(entry)
        if title_meta['tag'] == '時間':
            split_str += (title_meta['tag'] + title_meta['value'])
        print(title_meta['tag'] + '\t' + title_meta['value'])
    # print article content
    for entry in content_entries:
        if entry.find('div.bbs-content'):
            s = entry.text
            s = s.split(split_str)
            main_content = s[1].split('-- ※ 發信站')[0]
            main_content = main_content.replace(' ', '\n')
            print(main_content)
    # print article comment
    for entry in comment_entries:
        comment_meta = parse_comment_meta(entry)
        comment_print(comment_meta['push_tag'], comment_meta['push_userid'], comment_meta['push_content'], comment_meta['push_ipdatetime'])
# Exception handle
except IndexError:
    print('\n此文章不存在')
except KeyError:
    print('\n此頁面不存在')
except ValueError:
    print('\n此頁面不存在')