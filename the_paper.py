import pymysql
import requests
import re
import time
from lxml import etree
from create_id import create_id


def the_paper(url, params, headers):
    conn = pymysql.connect(
        host='0.0.0.0',
        port=3306,
        user='username',
        password='password',
        db='data_news',
        charset='utf8'
    )
    cur = conn.cursor()

    insert_sql = 'insert into `the_paper`(`id`, `weburl`, `title`, `contents`, `keyword`) VALUES (%s, %s, %s, %s, %s);'
    select_sql = 'select `weburl` from `the_paper`;'

    cur.execute(select_sql)
    result = cur.fetchall()
    inserted_url_list = [r[0] for r in result]

    s = requests.session()
    r = s.get(url=url, headers=headers, params=params)
    content = r.content.decode('utf-8', errors='ignore')
    html = etree.HTML(content)

    title_list = html.xpath('//div[@class="news_li"]//h2//a//text()')
    href_list = html.xpath('//div[@class="news_li"]//h2//a//@href')
    description_list = html.xpath('//div[@class="news_li"]//p//text()')

    for title, href, description in zip(title_list, href_list, description_list):
        href = 'http://www.thepaper.cn/' + href
        if href in inserted_url_list:
            print('已经插入过了！')
        else:
            try:
                q = s.get(href, headers=headers)
                text_content = q.content.decode('utf-8', errors='ignore')
                text_html = etree.HTML(text_content)
                main_content = re.findall(r'<div class="news_txt" data-size="standard">.*?<script>',
                                          text_content,
                                          re.M | re.S)
                main = re.sub(r'\n', '', ''.join(main_content).rstrip('<script>').encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))
                if main == '':
                    pass
                else:
                    try:
                        keywords = ','.join(str(text_html.xpath('//div[@class="news_keyword"]//text()')[0]).lstrip('关键词 >> ').split(' '))
                    except Exception:
                        keywords = ''
                    random_id = create_id()
                    sql_params = (random_id, href, title, main, keywords)
                    try:
                        cur.execute(insert_sql, sql_params)
                        conn.commit()
                        print('插入成功')
                    except Exception as e:
                        print(e)
                        conn.rollback()
            except Exception:
                pass
    conn.close()


if __name__ == '__main__':
    url = 'http://www.thepaper.cn/load_index.jsp'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
    }
    params = {'nodeids': '25635', 'pageidx': '%s' % '1'}
    Frag = True
    while Frag:
        the_paper(url, params, headers)
        print('等待更新...')
        time.sleep(80000)
