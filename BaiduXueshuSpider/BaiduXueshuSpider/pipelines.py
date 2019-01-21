# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

# from pipelines import BaiduxueshuspiderPipeline


class BaiduxueshuspiderPipeline(object):
    
    def process_item(self, item, spider):
        self.log("论文标题：" + item['thesistitle'])
        self.log("论文作者：" + item['thesisauthor'])
        self.log("论文PDF存储路径：" + item['thesispath'])
        return item
