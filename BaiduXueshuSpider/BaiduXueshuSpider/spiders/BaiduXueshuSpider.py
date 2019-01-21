
import os
import re
import scrapy
# import fcntl
import Levenshtein
import urllib.parse
# from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import CrawlSpider
# from BaiduXueshuSpider.items import BaiduxueshuspiderItem


class BaiduXueshuSpider(CrawlSpider):
    # 名单路径
    listpath = 'F:\MyWorkSpace\PythonWorkspace\BaiduXueshuSpider\论文列表汇总.txt'

    # 存储路径
    savepath = 'F:\MyWorkSpace\PythonWorkspace\BaiduXueshuSpider\pdfs'

    # 论文名字和作者列表 path
    thesisauthorpath = 'F:\MyWorkSpace\PythonWorkspace\BaiduXueshuSpider\\1.论文标题及作者关联表.txt'

    # 编辑距离内论文名字和作者列表 path
    disinthesispath = 'F:\MyWorkSpace\PythonWorkspace\BaiduXueshuSpider\\2.符合编辑距离的论文列表.txt'

    # 编辑距离外论文名字和作者列表 path
    disoutthesispath = 'F:\MyWorkSpace\PythonWorkspace\BaiduXueshuSpider\\3.不符合编辑距离的论文列表.txt'

    # 没有免费下载连接的论文名字和作者列表 path
    nulldownthesispath = 'F:\MyWorkSpace\PythonWorkspace\BaiduXueshuSpider\\4.无免费下载的论文列表.txt'

    # 论文名称编辑距离
    distance = 4

    # 名单列表
    thesislist = []
    start_urls = []

    # 爬虫名称
    name = "BaiduXueshuSpider"

    freedownflag = "(全网免费下载)"
    mainurl = "http://xueshu.baidu.com/s?wd="
    tailurl = "&rsv_bp=0&tn=SE_baiduxueshu_c1gjeupa&rsv_spt=3&ie=utf-8&f=8&rsv_sug2=1&sc_f_para=sc_tasktype%3D%7BfirstSimpleSearch%7D&rsv_n=2"

    # titlexpath = "//div[@id='dtl_l']/div[1]/h3[1]/a/text()"
    titlexpath = "//div[@id='dtl_l']/div[1]/h3[1]/a"
    # authorxpath = "//div[@id='dtl_l']//div[@class='author_wr']/p[@class='author_text']"
    # authorxpath = "//div[@id='dtl_l']//div[@class='author_wr']/p[@class='author_text']/a/@href"
    authorxpath = "//div[@id='dtl_l']//div[@class='author_wr']/p[@class='author_text']/a"
    pdfdownspanxpath = "//*[@id='allversion_wr']/div/span"
    pdfdownlinkxpath = "./a/@href"
    pdffreedownfalgxpath = ".//span[@class='dl_lib']/text()"

    authorregex = "author:\((.*)\)"

    def __init__(self, name=None, **kwargs):
        super(BaiduXueshuSpider, self).__init__()
        # 预先打开所有保存文件
        # self.fdall = open(self.thesisauthorpath, "a+", encoding='utf-8');
        # self.fddisin = open(self.disinthesispath, "a+", encoding='utf-8');
        # self.fddisout = open(self.disoutthesispath, "a+", encoding='utf-8');
        # self.fdnulldown = open(self.nulldownthesispath, "a+", encoding='utf-8');
        # 检查存储路径是否完整
        if os.path.exists(self.savepath) is False:
            os.makedirs(self.savepath)

    def start_requests(self):
        # 读取论文标题列表，并构建检索URL
        self.readlist()
        for title in self.thesislist:
            yield scrapy.Request((self.mainurl+title+self.tailurl), self.parse, meta={"keyword": (title.replace("+", ' '))})


    def parse(self, response):
        self.log("\n\n")
        keyword = str(response.meta['keyword']).strip()
        self.log("检索关键字：" + keyword)
        # 抽取标题
        stitle = str(self.extractfirst(response, self.titlexpath)).strip()
        self.log("论文标题：" + stitle)
        # 抽取作者列表
        sauthor = self.extractauthors(response, self.authorxpath)
        self.log("作者列表：" + sauthor)
        # 抽取可用于下载的链接
        linklist = self.extractdownlinks(response, self.pdfdownspanxpath)
        # 保存相关文件列表
        # 1. 保存所有论文标题及作者对应表
        # 2. 保存编辑距离的论文标题及作者对应表
        # 3. 保存无免费下载通道的论文标题及作者对应表
        self.savethesisauthorbypath(self.thesisauthorpath, keyword, "", sauthor)
        if self.calcdistance(stitle, keyword) is True:
            self.savethesisauthorbypath(self.disinthesispath, keyword, "", sauthor)
        else:
            self.savethesisauthorbypath(self.disoutthesispath, keyword, stitle, sauthor)
            return -1
        if len(linklist) > 0:
            idx = 0
            for link in linklist:
                idx += 1
                self.log("全网免费下载：" + link + ", 开始下载......")
                yield scrapy.Request(link, self.parsepdf, meta={"keyword": keyword, "stitle": stitle, "sauthor": sauthor, "idx": idx})
        else:
            self.savethesisauthorbypath(self.nulldownthesispath, keyword, "", sauthor)



    def parsepdf(self, response):
        filename = response.meta['keyword']
        # filesize = int(response.headers['content-length'])
        # self.log("论文《" + filename +"》预计总大小：" + str(filesize) + "B")
        # pdf文件名：keyword_idx.pdf
        filename = urllib.parse.quote(filename.strip()).replace("%20", " ") + "_" + str(response.meta['idx']) + ".pdf"
        filepath = (self.savepath + "\\" + filename)
        self.log("PDF存储路径：" + filepath)
        with open(filepath, 'wb') as fpdf:
            fpdf.write(response.body)

    def extractfirst(self, response, xpath):
        nodes = response.xpath(xpath)
        # self.log("Xpath节点数目：" + str(len(nodes)))
        if len(nodes) >= 1:
            return str(nodes.xpath("string(.)").extract_first())
        else:
            return ""

    def extractauthors(self, response, xpath):
        # authors = []
        authors = ""
        nodes = response.xpath(xpath)
        self.log("作者个数：" + str(len(nodes)))
        if len(nodes) >= 1:
            idx = 0
            for node in nodes:
                authorlink = urllib.parse.unquote(str(node.xpath('@href').extract_first()).strip())
                authortext = str(node.xpath("string(.)").extract_first()).strip()
                authorstr = self.regexauthor(authorlink)
                self.log("缩写作者名：" + authortext + "，全称作者名：" + authorstr)
                if len(authorstr) == 0:
                    continue
                idx += 1
                if idx == 1:
                    authors += authorstr
                else:
                    authors += ("," + authorstr)
            return authors
        else:
            return ""



    def extractdownlinks(self, response, xpath):
        links = []
        nodes = response.xpath(xpath)
        # self.log("Xpath节点数目：" + str(len(nodes)))
        if len(nodes) >= 1:
            for node in nodes:
                flag = str(node.xpath(self.pdffreedownfalgxpath).extract_first())
                if flag == self.freedownflag:
                    links.append(str(node.xpath(self.pdfdownlinkxpath).extract_first()))
                    # self.log("全部免费下载来源：" + flag)
                    # self.log("免费下载链接：" + str(node.xpath(self.pdfdownlinkxpath).extract_first()))
        return links


    def readlist(self):
        for line in open(self.listpath, mode='r+'):
            leng = len(line.strip())
            if leng > 0:
                self.thesislist.append(line.replace(" ", "+"))

    def savethesisauthor(self, fd, thesis, diff, author):
        if len(diff) <= 0:
            fd.write(thesis + "||" + author + "\n")
        else:
            fd.write(thesis + "||" + diff + "||" + author + "\n")
        # fd.close()

    def savethesisauthorbypath(self, path, thesis, diff, author):
        fd = open(path, "a+", encoding='utf-8');
        if len(diff) <= 0:
            fd.write(thesis + "||" + author + "\n")
        else:
            fd.write(thesis + "||" + diff + "||" + author + "\n")
        fd.close()

    def lock(self, fd):
        b = True
        try:
            fcntl.lock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB) #给文件加锁，使用了fcntl.LOCK_NB
        except:
            self.log('文件加锁，无法执行，请稍后运行。')
            b = False
        finally:
            return b

    def unlock(self, fd):
        try:
            fcntl.unlock(fd, fcntl.LOCK_UN) #给文件解锁
        except:
            self.log('文件加锁，无法执行，请稍后运行。')

    def calcdistance(self, src, tar):
        if Levenshtein.distance(src.lower(), tar.lower()) <= self.distance:
            return True
        else:
            return False

    def regexauthor(self, authorlink):
        self.log("作者链接：" + authorlink)
        if authorlink == 'None':
            self.log("这是一个假的作者链接")
            return ""
        if len(authorlink) > 0:
            mat = re.search(self.authorregex, authorlink)
            if mat is None:
                return ""
            if len(mat.group()) > 0:
                austr = mat.group(1)
                austr = austr.replace(',', ' ')
                austr = re.sub('\t+', ' ', austr)
                austr = re.sub('\s+', ' ', austr)
                return austr
            else:
                return ""
        else:
            return ""