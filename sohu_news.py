import requests
import json
import re
import time
from urllib.parse import unquote
import pymysql
from create_id import create_id


def sohu_news():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    }

    conn = pymysql.connect(
    host='0.0.0.0',
    port=3306,
    user='username',
    password='password',
    db='data_news',
    charset='utf8'
    )

    cur = conn.cursor()

    insert_sql = 'insert into `sohu_news`(`id`, `weburl`, `title`, `contents`) VALUES (%s, %s, %s, %s);'

    select_sql = 'select `weburl` from `sohu_news`;'
    cur.execute(select_sql)
    result = cur.fetchall()

    exist_url_list = [r[0] for r in result]

    s = requests.session()
    url = 'http://mp.sohu.com/apiV2/profile/newsListAjax'
    # for i in range(1, 29):
    params = {
        'xpt': 'NzJCMERBNUNDN0NEODJBOTkwMTZFMkM2NkU3REM3QjBAcXEuc29odS5jb20=',
        'pageNumber': 1,
        'pageSize': 10,
    }
    content = s.get(url=url, headers=headers, params=params).json()
    with open('data.json', 'w') as f:
        f.write(content)
    with open('data.json', 'r') as f:
        data = json.load(f)
    for article in data['data']:
        article_url = 'http:' + article['url']
        if article_url in exist_url_list:
            print('已经在库中了！')
        else:
            article_title = unquote(article['title'])
            r = s.get(url=article_url, headers=headers)
            article_content = r.content.decode('utf-8', errors='ignore')
            main_content = re.findall(r'<article class="article" id="mp-editor">.*?</article>', article_content, re.M | re.S)
            main = ''
            for c in main_content:
                main += c
            random_id = create_id()
            sql_params = (random_id, article_url, article_title, main)
            print(main)
            try:
                cur.execute(insert_sql, sql_params)
                conn.commit()
                print("插入成功")
            except Exception as e:
                print(e)
                conn.rollback()
    conn.close()


if __name__ == '__main__':
    while True:
        sohu_news()
        print('等待更新...')
        time.sleep(86400)
