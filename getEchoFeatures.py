
import urllib
from pyechonest import config 
from pyechonest import track
import MySQLdb
import pandas.io.sql as sql
from pandas import Series
from pandas import DataFrame
from datetime import datetime
import numpy as np
from scipy import stats

config.ECHO_NEST_API_KEY='BMBMCA0YALXRFNCJP'

def echonest_audio(tid):
    url = 'https://api.soundcloud.com/tracks/%d/stream?consumer_key=17089d3c7d05cb2cfdffe46c2e486ff0' %tid
    print url
    attributes = {}
    try:
        t = track.track_from_url(url)
        wait = t.get_analysis()
        att = dir(t)
        eid = t.id
        
        attributes['tid'] = tid
        attributes['eid'] = eid
    
        key_attribute_list = ['instrumentalness', 'valence', 'loudness', 'duration', 'key', 'mode', 'danceability', 'acousticness', 'speechiness', 'tempo', 'liveness', 'energy']
        segment_attr_list = ['pitches', 'timbre']
        for a in att:
            if a in key_attribute_list:
                ta = getattr(t,a)
                attributes[a] = ta
        segment_data = t.segments
    
        # average loudness over all segments
        feature = 'loudness_max'
        
        subs = []
        for i in segment_data:
            subs.append(i[feature])
            attributes[feature+"_mean"] = np.mean(subs)
            attributes[feature+"_std"] = np.std(subs)
            attributes[feature+"_kurt"]= stats.kurtosis(subs)    
            attributes[feature+"_skew"] =stats.skew(subs)
    
        # pitch and timbre have multiple levels
        for feature in segment_attr_list:
            for j in range(len(segment_data[0][feature])):
                subs = []
                if j<9:
                    featurestr  = feature +"0"
                else:
                    featurestr = feature
                for i in segment_data:
                    subs.append(i[feature][j])
                attributes[featurestr+str(j+1)+"_mean"] = np.mean(subs)
                attributes[featurestr+str(j+1)+"_std"] = np.std(subs)
                attributes[featurestr+str(j+1)+"_kurt"] = stats.kurtosis(subs)
                attributes[featurestr+str(j+1)+"_skew"] = stats.skew(subs)

         import pdb; pdb.set_trace()

    except:
        pass  
    return attributes


def processTrackEcho(tuple):
    track =int(tuple[0])
    aid=int(tuple[1])
    con = MySQLdb.connect(host="bigblasta.chiim1n4uxwu.eu-central-1.rds.amazonaws.com", user="bigblasta", passwd="Jo27051980", db="bigblasta")
    cursor = con.cursor()
    t0 = datetime.now()
    attribute_dict = echonest_audio(track)
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    attribute_dict['aid']=aid
    attribute_dict['date']=now
    t1 = datetime.now()
    ser = Series(attribute_dict)
    df = DataFrame(ser).T
    sql.write_frame(df, con=con, name='echonest', if_exists='append', flavor='mysql')
    t2 = datetime.now()
    dur1 = (t1-t0).total_seconds()
    dur2 = (t2-t1).total_seconds()
    print  "Echonest response: %f, MySQL: %f" %(dur1, dur2)

def main():
    con = MySQLdb.connect(host="bigblasta.chiim1n4uxwu.eu-central-1.rds.amazonaws.com", user="bigblasta", passwd="Jo27051980", db="bigblasta")
    cursor = con.cursor()
    df = sql.read_frame('select t2.tid, t2.aid from (select tid from start_tracks order by rand() limit 1000)t1 inner join tracks t2 on t1.tid = t2.tid group by 1,2', con)
    subset = df[['tid', 'aid']]
    start_tracks = [tuple(x) for x in subset.values]
    if len(start_tracks)>0:
        # create a client object with your app credentials
        from multiprocessing.dummy import Pool as ThreadPool 
        pool = ThreadPool(1) 
        pool.map(processTrackEcho, start_tracks)
        pool.close()
        #processTrack(start_tracks[0])


if __name__ == '__main__': 
    main()

'''
Represents an audio file and its analysis from The Echo Nest.
    All public methods in this module return Track objects.

    Depending on the information available, a Track may have some or all of the
    following attributes:

        acousticness            float: confidence the track is "acoustic" (0.0 to 1.0)
        analysis_url            URL to retrieve the complete audio analysis (time expiring)
        analyzer_version        str: e.g. '3.01a'
        artist                  str or None: artist name
        artist_id               Echo Nest ID of artist, if known
        danceability            float: relative danceability (0.0 to 1.0)
        duration                float: length of track in seconds
        energy                  float: relative energy (0.0 to 1.0)
        id                      str: Echo Nest Track ID, e.g. 'TRTOBXJ1296BCDA33B'
        key                     int: between 0 (key of C) and 11 (key of B flat) inclusive
        liveness                float: confidence the track is "live" (0.0 to 1.0)
        loudness                float: overall loudness in decibels (dB)
        md5                     str: 32-character checksum of the original audio file, if available
        mode                    int: 0 (major) or 1 (minor)
        song_id                 The Echo Nest song ID for the track, if known
        speechiness             float: likelihood the track contains speech (0.0 to 1.0)
        status                  str: analysis status, e.g. 'complete'
        tempo                   float: overall BPM (beats per minute)
        time_signature          beats per measure (e.g. 3, 4, 5, 7)
        title                   str or None: song title
        valence                 float: a range from negative to positive emotional content (0.0 to 1.0)

    The following attributes are available only after calling Track.get_analysis():
    
        analysis_channels       int: the number of audio channels used during analysis
        analysis_sample_rate    int: the sample rate used during analysis
        bars                    list of dicts: timing of each measure
        beats                   list of dicts: timing of each beat
        codestring              ENMFP code string
        code_version            version of ENMFP code generator
        decoder                 audio decoder used by the analysis (e.g. ffmpeg)
        echoprintstring         fingerprint string using Echoprint (http://echoprint.me)
        echoprint_version       version of Echoprint code generator
        end_of_fade_in          float: time in seconds track where fade-in ends
        key_confidence          float: confidence that key detection was accurate
        meta                    dict: other track metainfo (bitrate, album, genre, etc.)
        mode_confidence         float: confidence that mode detection was accurate
        num_samples             int: total samples in the decoded track
        offset_seconds          unused, always 0
        sample_md5              str: 32-character checksum of the decoded audio file
        samplerate              the audio sample rate detected in the file
        sections                list of dicts: larger sections of song (chorus, bridge, solo, etc.)
        segments                list of dicts: timing, pitch, loudness and timbre for each segment
        start_of_fade_out       float: time in seconds where fade out begins
        synchstring             string providing synchronization points throughout the track
        synch_version           version of the synch string algorithm
        tatums                  list of dicts: the smallest metrical unit (subdivision of a beat)
        tempo_confidence        float: confidence that tempo detection was accurate
        time_signature_confidence float: confidence that time_signature detection was accurate
    
    Each bar, beat, section, segment and tatum has a start time, a duration, and a confidence,
    in addition to whatever other data is given.

    Examples:

    >>> t = track.track_from_id('TRJSEBQ1390EC0B548')
    >>> t
    <track - Dark Therapy>

    >>> t = track.track_from_md5('96fa0180d225f14e9f8cbfffbf5eb81d')
    >>> t
    <track - Spoonful - Live At Winterland>
    >>>

    >>> t = track.track_from_filename('Piano Man.mp3')
    >>> t.meta
    AttributeError: 'Track' object has no attribute 'meta'
    >>> t.get_analysis()
    >>> t.meta
    {u'album': u'Piano Man',
     u'analysis_time': 8.9029500000000006,
     u'analyzer_version': u'3.1.3',
     u'artist': u'Billy Joel',
     u'bitrate': 160,
     u'detailed_status': u'OK',
     u'filename': u'/tmp/tmphrBQL9/fd2b524958548e7ecbaf758fb675fab1.mp3',
     u'genre': u'Soft Rock',
     u'sample_rate': 44100,
     u'seconds': 339,
     u'status_code': 0,
     u'timestamp': 1369400122,
     u'title': u'Piano Man'}
    >>>
 '''