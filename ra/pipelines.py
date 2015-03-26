# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import io
from ra.items import EventItem
from ra.items import VenueItem

# -- coding: utf-8 --

class RaPipeline(object):
    def process_item(self, item, spider):
        if isinstance(item, EventItem):
            with io.open('pipedevents.json', 'a', encoding='utf-8') as file1:
                file1.write(unicode(json.dumps(dict(item), ensure_ascii=False)))
                file1.write(u"\n")
            return item
        else:
            #file1 = open('pipedvenues.json', 'a')
            #line = json.dumps(dict(item)) + "\n"
            #file1.write(line)
            with io.open('pipedvenues.json', 'a', encoding='utf-8') as file1:
                file1.write(unicode(json.dumps(dict(item), ensure_ascii=False)))
                file1.write(u"\n")
            return item

