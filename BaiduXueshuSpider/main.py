

# from BaiduXueshuSpider import BaiduXueshuSpider
from scrapy import cmdline

def _main():
    print("开始执行：")

    # cmdline.execute("scrapy crawl SearchEnginesSpider --set LOG_FILE=logfile".split())
    cmdline.execute("scrapy crawl BaiduXueshuSpider".split())

    print("执行结束！")
    return 0

if __name__ == "__main__":
    _main()