# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class EventItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    venueID = scrapy.Field()
    venueName = scrapy.Field()
    venueFans = scrapy.Field()
    #venueAbout = scrapy.Field()
    venueMostListed = scrapy.Field()
    eventID = scrapy.Field()
    eventDate = scrapy.Field()
    eventName = scrapy.Field()
    #djs = scrapy.Field()
    lineup = scrapy.Field()
    url = scrapy.Field()
    attending = scrapy.Field()


class VenueItem(scrapy.Item):
    venueID = scrapy.Field()
    venueName = scrapy.Field()
    venueFans = scrapy.Field()
    venueAbout = scrapy.Field()
    venueMostListed = scrapy.Field()
    venueLocation = scrapy.Field()
    venueLinks = scrapy.Field()
    


