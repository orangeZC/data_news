import pymysql
import requests
import re
import time
import json
from lxml import etree
from create_id import create_id


def qc_spider(url, params, header):
    conn = pymysql.connect(
        host='0.0.0.0',
        port=3306,
        user='username',
        password='password',
        db='data_news',
        charset='utf8'
    )
    cur = conn.cursor()

    insert_sql = 'insert into `qc_news`(`id`, `weburl`, `title`, `contents`, `createtime`) VALUES (%s, %s, %s, %s, %s);'

    select_sql = 'select `weburl` from `qc_news`;'
    cur.execute(select_sql)
    results = cur.fetchall()
    inserted_url_list = [r[0] for r in results]

    s = requests.session()
    content = s.get(url=url, headers=header, params=params).content.decode('utf-8', errors='ignore').lstrip('(').rstrip(
        ')')
    json_content = json.loads(content, encoding='utf-8')
    article_list = json_content['data']['list']
    for article in article_list:
        title = article['Title']
        pub_time = article['PubTime']
        link_url = article['LinkUrl']
        if link_url in inserted_url_list:
            print('已经在库中了！')
        else:
            article_content = s.get(url=link_url, headers=header, params=params).content.decode('utf-8',
                                                                                                errors='ignore')
            main_content = ''.join(re.findall(r'<div class="article">.*?</div>', article_content, re.S | re.M))
            if main_content == '':
                pass
            else:
                random_id = create_id()
                sql_params = (random_id, link_url, title, main_content, pub_time)
                try:
                    cur.execute(insert_sql, sql_params)
                    conn.commit()
                    print('插入成功')
                except Exception as e:
                    print(e)
                    conn.rollback()
    conn.close()


if __name__ == '__main__':
    url = 'http://qc.wa.news.cn/nodeart/list'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    }
    params = {'nid': '11123634',
              'pgnum': '%s' % '1',
              'cnt': '16',
              'tp': '1',
              'orderby': '1?callback=jQuery17103229078936016574_1515396591620',
              '_': '1515396591652'}
    Frag = True
    while Frag:
        qc_spider(url, params, headers)
        print('等待更新...')
        time.sleep(80000)
