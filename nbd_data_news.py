import requests, re, pymysql, time
from lxml import etree
from create_id import create_id


class Config:
    # url config
    url = 'http://www.nbd.com.cn/columns/442'
    # headers config
    headers = {
        'Accept': '*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'}
    # params config
    params = {'display_way': 'article_list',
              'page': '17'}
    # proxy config
    proxies = {}
    # cookies config
    cookies = {}


class DBConfig:
    # host config
    host = 'localhost'
    # port config
    port = 3306
    # user config
    user = 'root'
    # password config
    password = ''
    # db config
    db = 'data_news'
    # charset config
    charset = 'utf8'
    # autocommit set, should be True
    autocommit = True


class Spider:
    @staticmethod
    def start_content():
        """get start html content"""
        s = requests.session()
        r = s.get(url=Config.url, headers=Config.headers, params=Config.params, proxies=Config.proxies,
                  cookies=Config.cookies)
        r_content = r.content.decode('utf-8', errors='ignore')
        return r_content

    @staticmethod
    def get_content(url, headers, params, proxies, cookies):
        """get html content"""
        s = requests.session()
        r = s.get(url=url, headers=headers, params=params, proxies=proxies, cookies=cookies)
        r_content = r.content.decode('utf-8', errors='ignore')
        return r_content

    @staticmethod
    def get_content_html(content):
        """get xpath"""
        content_html = etree.HTML(content)
        return content_html

    @staticmethod
    def find_by_re(pattern, string, flags):
        """find element by re"""
        result = re.findall(pattern=pattern, string=string, flags=flags)
        return result

    @staticmethod
    def sub_by_re(pattern, sub_string, string):
        """sub element by re"""
        result = re.sub(pattern=pattern, repl=sub_string, string=string)
        return result

    @staticmethod
    def find_by_xpath(xpath_html, xpath=''):
        """find element by xpath"""
        result = xpath_html.xpath(xpath)
        return result

    @staticmethod
    def connect_to_db():
        """connect"""
        conn = pymysql.connect(
            host=DBConfig.host,
            port=DBConfig.port,
            user=DBConfig.user,
            password=DBConfig.password,
            db=DBConfig.db,
            charset=DBConfig.charset,
            autocommit=DBConfig.autocommit
        )
        cur = conn.cursor()
        return conn, cur

    @staticmethod
    def select_where_sql(sql, size=None):
        conn, cur = Spider.connect_to_db()
        cur.execute(sql)
        if size:
            rs = cur.fetchmany(size)
        else:
            rs = cur.fetchall()
        cur.close()
        return rs

    @staticmethod
    def save_into_table(sql, args):
        affected = Spider.execute(sql, args)
        print('insert successfully, %s rows affected' % affected)

    @staticmethod
    def update_table(sql, args):
        affected = Spider.execute(sql, args)
        print('update successfully, %s rows affected' % affected)

    @staticmethod
    def execute(sql, args):
        conn, cur = Spider.connect_to_db()
        try:
            cur.execute(sql, args)
            affected = cur.rowcount
            cur.close()
        except BaseException as e:
            raise e
        return affected


if __name__ == '__main__':
    Flag = True
    while Flag:
        spider = Spider()
        Config.params = {'display_way': 'article_list',
                         'page': '%s' % '1'}
        content = spider.start_content()
        content = spider.sub_by_re(r'\\', '', content)
        news_list = spider.find_by_re(r'<li.*?</li>', content, re.S | re.M)
        select_sql = 'select `weburl` from `nbd_data_news`;'
        results = spider.select_where_sql(select_sql)
        url_list = [r[0] for r in results]
        for new in news_list:
            new_html = spider.get_content_html(new)

            new_url = spider.find_by_xpath(new_html, '//li/a[1]//@href')[0]
            if new_url in url_list:
                print('这条数据已经插入过了')
                pass
            else:
                new_title = spider.sub_by_re(r'n', '', new_html.xpath('//li/a[2]//text()')[0])
                new_title = spider.sub_by_re(r' ', '', new_title)

                try:
                    new_des = spider.find_by_xpath(new_html, '//div[@class="qrcode-box"]/p/a//text()')[0]
                except Exception:
                    new_des = ''

                new_time = spider.sub_by_re(r'n', '', new_html.xpath('//p[@class="news-time"]//text()')[0])
                new_time = spider.sub_by_re(r' ', '', new_time)

                main_content = spider.get_content(url=new_url,
                                                  headers={
                                                      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36'
                                                  },
                                                  params={},
                                                  proxies={},
                                                  cookies={})
                article_content = ''.join(
                    spider.find_by_re(r'<div class="article_content">.*?</div>', main_content, re.S | re.M))
                random_id = create_id()
                insert_sql = 'insert into `nbd_data_news`(`id`, `weburl`, `title`, `createtime`, `contents`, `description`) values (%s, %s, %s, %s, %s, %s);'
                params = (random_id, new_url, new_title, new_time, article_content, new_des)
                spider.save_into_table(insert_sql, params)
                time.sleep(2)
        print('等待更新....')
        time.sleep(86400)
