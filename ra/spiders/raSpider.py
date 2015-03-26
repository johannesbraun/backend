from scrapy.spider import Spider
from scrapy.selector import Selector
from scrapy.http.request import Request
from ra.items import EventItem
from ra.items import VenueItem
import re

# -- coding: utf-8 --

class RaSpider(Spider):
    name = "ra"
    allowed_domains = ["www.residentadvisor.net"]
    start_urls = [
        "http://www.residentadvisor.net/club.aspx?id=3067",
        "http://www.residentadvisor.net/club.aspx?id=3213",
        "http://www.residentadvisor.net/club.aspx?id=5031",
        "http://www.residentadvisor.net/club.aspx?id=6949",
        "http://www.residentadvisor.net/club.aspx?id=5494",
        "http://www.residentadvisor.net/club.aspx?id=28354",
        "http://www.residentadvisor.net/club.aspx?id=8556",
        "http://www.residentadvisor.net/club.aspx?id=8009",
        "http://www.residentadvisor.net/club.aspx?id=6950",
        "http://www.residentadvisor.net/club.aspx?id=5828",
        "http://www.residentadvisor.net/club.aspx?id=17071",
        "http://www.residentadvisor.net/club.aspx?id=19299"
    ]

    def parse(self, response):
        """
        ...
        """
        sel = Selector(response)
        head = sel.xpath('//div[@id="sectionHead"]/h1/span/text()')
        #events = sel.xpath('//div[@class="bbox"]')
        articles = sel.xpath('//ul[@class="list"]/li/article[contains(@class,"event-item")]')
        items = []
        venue = VenueItem()
        venue['venueID'] = response.url.split("=")[1]
        venue['venueName'] = head[0].extract()
        venue['venueFans'] = sel.xpath('//h1[@class="favCount"]/text()').extract()
        about_section  = response.xpath('//section[contains(@class,"content generic")]/div/div/div/div/text()').extract()
        about = ""
        for a in about_section:
             if (a[0:2]=='\r'):
                 pass
             else:
                about += a
        venue['venueAbout'] = about
        venue['venueMostListed'] = sel.xpath('//ul[@class="top-list"]/li/a/text()').extract()
        venue['venueLocation'] = sel.xpath('//span[@itemprop="street-address"]/text()').extract()
        venue['venueLinks'] = sel.xpath('//*[@id="detail"]/ul/li/a/@href').extract()

        #yield venue
        items.append(venue)


        for art in articles:
            item = EventItem()
            item['venueID'] = venue['venueID']
            item['venueName'] = venue['venueName']
            item['eventID'] = art.xpath('.//@href')[0].extract().split("?")[1]
            item['eventDate'] = art.xpath('./div/h1/text()')[0].extract().split("/")[0]
            item['eventName'] = art.xpath('./div/h1[@class="title"]/a/text()')[0].extract()
            item['attending'] = art.xpath('.//p[@class="counter"]/span/text()').extract()
            eurl = "http://www.residentadvisor.net"+art.xpath('.//@href')[0].extract()
            item['url'] = eurl
            request = Request(eurl, callback = self.parse_page2)
            request.meta['item']=item            
            items.append(request)
            #items.append(item)

        return items


    def parse_page2(self, response):
        item = response.meta['item']
        #item['lineup'] = response.xpath('//p[@class="lineup large"]/a/text()').extract()
        item['lineup'] = response.xpath('//p[contains(@class,"lineup")]/a/text()').extract()
        return item