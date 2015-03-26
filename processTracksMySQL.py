

import re, urlparse
import urllib2
import json
import requests
import csv
import pymongo # pip install pymongo
#from bson import json_util # Comes with pymongo
from datetime import datetime 
import soundcloud
import sys
import MySQLdb



#Get all (<1000) users who like a track (takes 20 seconds per song)
def getFanIds(songid):
    tid = songid 
    #print 'Track ID: %d' % tid
    #fans = [ (fan.id, fan.username) for fan in getAll('/tracks/%d/favoriters' % tid,50,1000)]
    fans =[]
    t0 = datetime.now()
    try:
        fans = [ fan.id for fan in getAll('/tracks/%d/favoriters' % tid,50,1000)]
    except requests.exceptions.HTTPError, e:
        print 'HTTP ERROR occured for song %s: ' %(songid)
    except requests.HTTPError, e:
        print 'HTTP ERROR occured for song %s: ' %(songid)
    except requests.SSLError ,e:
        print 'SSLError occured for song %d: %s' %(songid)    
    t1 = datetime.now()
    dur = (t1-t0).total_seconds()
    #for fan in client.get('/tracks/%d/favoriters' % tid) ]    
    #TODO cross check how many tracks the artist has
    #TODO store favoriters_count in tracks!
    print 'Track ID %d: %d Fans, Response time: %f' % (tid, len(fans),dur)
    #print tabulate(fans[1:10], headers=['Id', 'Username'])
    #print fans[0:10]
    #print '...'
    return fans
#_= getFanIds(132576206)



# helper function to paginate through all responses of a request
def getAll(path,default,at_most):  
    items=[]
    offset=0  
    page = client.get(path)    
    
    while (len(page) != 0): 
        items = items + [item for item in page]
        if len(items) >= at_most: 
            break          
        if len(page)>(default-1):          
            offset = offset + len(page)
            #print path
            try: 
                page = client.get(path, page_size = default,  offset=offset)
            except requests.exceptions.HTTPError, e:
                print 'HTTP ERROR occured for path %s: ' %(path)
            except requests.HTTPError, e:
                print 'HTTP ERROR occured for path %s: ' %(path)
            except requests.SSLError ,e:
                print 'SSLError occured for path %s:' %(uid)
        else: 
            page = []    
        #while (offset<=(at_most-page_size)):
        #items = items + [ item for item in page]           
    return items

# get all tracks a user likes
def getLikes(uid):
    likes = []
    response = []
    try:
        likes = getAll('/users/%d/favorites' % uid, 50, 250)
        #return [l.fields() for l in likes]
    except requests.exceptions.HTTPError, e:
        print 'HTTP ERROR occured for user %s: ' %(uid)
    except requests.HTTPError, e:
        print 'HTTP ERROR occured for user %s: ' %(uid)
    except requests.SSLError ,e:
        print 'SSLError occured for uid %d: %s' %(uid)    
    for l in likes:
        track = l.fields()
        pc=0
        lc=0
        cc=0
        try:
            pc= track['playback_count']
            lc= track['favoritings_count']
            cc= track['comment_count']
        except KeyError , e:
            #print 'KeyError occured for track %d: %s' %(track['id'], e)      
            pass  
        response += [{"id": track['id'], "aid": track['user_id'], "username": track['user']['username'], "title": track['title'], "likes": lc, "comments":cc, "plays":pc, "last_modified":track['last_modified'],"genre":track['genre'], "tags": track['tag_list'] }]
    return response


# helper function that inserts user favourites to mongo
def writeUserToMySQL(uid, ufavs, cursor, con):
    
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    data = []
    for u in ufavs:
        data.append((uid, u["id"], u["aid"], now))

    try:
        cursor.executemany('''INSERT IGNORE INTO likes VALUES (%s,%s,%s,%s)''',data)
        con.commit()

    except:
        con.rollback()


def writeUserToMongo(uid, ufavs, db):
    
    utc_timestamp = datetime.utcnow()
    ids=[]
    for u in ufavs:
        ids=ids+[u["id"]]
    try:
        collection = db.user_favorites  # adds collection soundcloud.user_favourites
        collection.ensure_index([("uid", pymongo.ASCENDING)], unique=True)
        collection.ensure_index("date", expireAfterSeconds=60*60*24*7)
        
        user = { 
                 "date": utc_timestamp,
                 "uid": uid,
                 "favorites": ids 
                }
        o = collection.insert(user)
    
    except pymongo.errors.DuplicateKeyError, e:
        #print e
        pass


def writeTracksToMySQL(ufavs, cursor, con):
    
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    tags_time_share=0.0
    tracks = []
    if len(ufavs)>0:
        for t in ufavs:  
            #print utc_timestamp, t["id"]          
            lm = t["last_modified"]
            dt = datetime.strptime(lm, '%Y/%m/%d %H:%M:%S +%f')
            lm = dt.strftime('%Y-%m-%d %H:%M:%S')
            tracks.append((t["id"], t["aid"], t["username"], t["title"], t["likes"], t["comments"], t["plays"], t["genre"], lm, now))
            
            
            if len(t["tags"])>0:
                tid =t["id"]
                aid =t["aid"]
                tagged_tracks = []
                tags = t["tags"].split(' "')
                for t in tags:
                    tagged_tracks.append((tid, aid, t.replace('"',"")))

        t1 = datetime.now()
        try:
            cursor.executemany('''INSERT IGNORE INTO tracks VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',tracks)
            con.commit()
        except:
            con.rollback()
        t2 = datetime.now()
        try:
            cursor.executemany('''INSERT IGNORE INTO tags VALUES (%s,%s, %s)''',tagged_tracks)
            con.commit()
        except:
            con.rollback()

        t3 = datetime.now()
        dur1 = (t3-t2).total_seconds()
        dur2 = (t2-t1).total_seconds()
        tags_time_ratio = dur1/(dur1+dur2)
    else:
        pass

    return tags_time_share
    



def writeTracksToMongo(ufavs, db):
    collection = db.tracks  # adds collection soundcloud.user_favourites 
    collection.ensure_index([("tid", pymongo.ASCENDING)], unique=True)
    collection.ensure_index("date", expireAfterSeconds=60*60*24*7)
    
    utc_timestamp = datetime.utcnow()
    tracks = []
    if len(ufavs)>0:
        for t in ufavs:  
            #print utc_timestamp, t["id"]          
            track = {
                     "date": utc_timestamp,
                     "tid": t["id"],
                     "aid": t["aid"],
                     "username": t["username"],
                     "title": t["title"], 
                     "likes": t["likes"], 
                     "comments": t["comments"], 
                     "plays": t["plays"],
                     "genre": t["genre"],
                     "tags": t["tags"],
                     "last_modified": t["last_modified"]
                    }
            tracks.append(track)
        try:        
            o = collection.insert(tracks)
        except pymongo.errors.DuplicateKeyError, e:
            #print e
            pass
    else:
        pass
        



def processTrackMySQL(track):

    con = MySQLdb.connect(
        host="bigblasta.chiim1n4uxwu.eu-central-1.rds.amazonaws.com", 
        user="bigblasta", 
        passwd="Jo27051980", 
        db="bigblasta")

    cursor = con.cursor()

    stmt = "SELECT tid FROM start_tracks where tid = %d LIMIT 1" %track
    result = cursor.execute(stmt)
    numrows = int(cursor.rowcount)
    if numrows>0: 
        pass
    else:
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        try:
            cursor.execute('''INSERT IGNORE INTO start_tracks VALUES (%s,%s)''',(track,now))
            con.commit()
        except:
            con.rollback()
        fans = getFanIds(track)
        sum_items = 0.0
        sum_dur =0.0
        sum_usr = 0.0
        sum_tr =0.0
        sum_tts = 0.0
        tracktime =0.0
        usertime = 0.0
        if len(fans)>0:
            for i, fan in enumerate(fans):
                t1 = datetime.now()
                strfan = str(fan)
                stmt = "SELECT * FROM likes where uid = %d LIMIT 1" %fan
                result = cursor.execute(stmt)
                numrows = int(cursor.rowcount)
                if numrows>0: 
                    pass
                else:
                    likes = getLikes(fan)
                    #likeids = [l['id'] for l in likes]
                    t3 = datetime.now()
                    writeUserToMySQL(fan, likes, cursor, con) 
                    t4 = datetime.now()
                    tts = writeTracksToMySQL(likes, cursor, con) 
                    t5 = datetime.now()
                    tracktime = (t5-t4).total_seconds()
                    usertime = (t4-t3).total_seconds()

            
                t2 = datetime.now()
                dur = t2 - t1
                #print "- ", i, fan, str(dur.total_seconds()) 
                sum_dur += dur.total_seconds()
                sum_usr += usertime
                sum_tr += tracktime
                sum_tts += tts
                sum_items+=1.0
                if i%10==0:
                    print 'average time after %d: %f, track: %f (tags: %f), user: %f ' %(i, sum_dur/sum_items, sum_dur/sum_tr, sum_dur/sum_tr, sum_dur/sum_usr)

    con.close()


def processTrack(track):

    fans = getFanIds(track)
    sum_items = 0.0
    sum_dur =0.0
    for i, fan in enumerate(fans):
        t1 = datetime.now()
        strfan = str(fan)
        user =  [u['favorites'] for u in db.user_favorites.find({"uid" : fan})] # does user exist in mongo?
        if len(user)>0: 
            pass
        else:
            likes = getLikes(fan)
            #likeids = [l['id'] for l in likes]
            writeUserToMongo(fan, likes, db) 
            writeTracksToMongo(likes, db) 
    
        t2 = datetime.now()
        dur = t2 - t1
        #print "- ", i, fan, str(dur.total_seconds()) 
        sum_dur += dur.total_seconds()
        sum_items+=1.0
        if i%100==0:
            print 'average time after %d: %f' %(i, sum_dur/sum_items)


clientid= '17089d3c7d05cb2cfdffe46c2e486ff0'
client = soundcloud.Client(client_id='17089d3c7d05cb2cfdffe46c2e486ff0') # 'YOUR_CLIENT_ID'

MONGODB_URI = 'mongodb://blasta:blasta@ds031641.mongolab.com:31641/soundcloud' 
mongo_client = pymongo.MongoClient(MONGODB_URI)
db = mongo_client.soundcloud



def main():
    filename = sys.argv[1]
    #print filename
    ## load tracks
    
    if len(filename)>0:

        with open(filename) as f:
            reader=csv.reader(f,delimiter='\t')
            rows = list(reader)
        start_tracks = [int(r[0]) for r in rows]
        

        if len(start_tracks)>0:
            # create a client object with your app credentials
    
            from multiprocessing.dummy import Pool as ThreadPool 
            pool = ThreadPool(25) 
            pool.map(processTrackMySQL, start_tracks)
            pool.close()
            #processTrack(start_tracks[0])


if __name__ == '__main__': 
    main()


