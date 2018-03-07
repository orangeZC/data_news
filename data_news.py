import requests
import re
from lxml import etree
import pymysql
import time
from create_id import create_id


def netease_data_news():
    conn = pymysql.connect(
        host='111.230.149.22',
        port=3306,
        user='root',
        password='liu3226677',
        db='data_news',
        charset='utf8'
    )

    cur = conn.cursor()

    insert_sql = 'insert into `netease_data_news`(`id`, `title`, `weburl`, `createtime`, `contents`, `keyword`, `comment`) VALUES (%s, %s, %s, %s, %s, %s, %s);'

    select_sql = 'select `weburl` from `netease_data_news`;'

    cur.execute(select_sql)
    result = cur.fetchall()

    url_list = [r[0] for r in result]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    }
    s = requests.session()
    r = s.get('http://data.163.com/special/datablog/', headers=headers)
    content = r.content.decode('gbk', errors='ignore')
    html = etree.HTML(content)
    script = html.xpath('//script[contains(text(), "keyword")]//text()')[0]
    news_list = re.findall(r'{\s.*"url.*\s.*title.*\s.*img.*\s.*time.*\s.*comment.*\s.*"keyword":.*', script, re.M)[:10]
    
    for new in news_list:
        new = eval(str(new.rstrip(',').rstrip('}') + '}'))
        url = new['url']
        if url in url_list:
            print('这条数据已经在数据库中了')
        else:
            r = s.get(url, headers=headers)
            content = r.content.decode('gbk', errors='ignore')
            main = re.findall(r'<p.*?/p>', content, re.M | re.S)
            if len(main) == 0:
                pass
            else:
                article = ''
                main = main[2:-5]
                for p in main:
                    article += p
                random_id = create_id()
                params = (random_id, new['title'], url, new['time'], article, new['keyword'], new['comment'])
                try:
                    cur.execute(insert_sql, params)
                    conn.commit()
                    print('插入成功')
                except Exception as e:
                    print(e)
                    conn.rollback()
    conn.close()


if __name__ == '__main__':
    while True:
        netease_data_news()
        print('等待更新...')
        time.sleep(86400)
