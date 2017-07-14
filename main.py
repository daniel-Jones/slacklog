#!/usr/bin/env python3

'''
AFTER TESTING BIND MONGODB TO LOCALHOST/ARGO HOST
CLEAR CONFIG/SETTINGS.CFG BEFORE COMMITTING
'''

import urllib.request;
import time;
import json;
from pymongo import MongoClient;
import configparser;

'''
slack logging run via a cronjob and stored in MongoDB
for r/GlobalOffensive
'''

def getjson(url):
    '''
    returns json data from the url
    args:
        url = url to request data from
    '''
    try:
        f = urllib.request.urlopen(url);
        content = f.read();
        f.close();
    except urllib.error.URLError:
        print("error getting json, api down probably, try later");
        raise SystemExit;
    return content;

def dbconnect():
    '''
    connects to our database
    returns nothing (globals, i feel dirty doing this)
    args:
        none
    '''
    global client;
    global db;
    global messagedb;
    client = MongoClient(cfg.get("database", "host"), int(cfg.get("database", "port")));
    db = client[cfg.get("database", "db")];
    db.authenticate(cfg.get("database", "user"), cfg.get("database", "password")); 
    messagedb = db.messages;

def getstaticapidata():
    '''
    downloads our api data and stores them
    returns nothing
    args:
        none
    '''
    # channel json
    channelurl = "https://slack.com/api/channels.list?token={}&exclude_archived={}&exclude_members={}";
    channelurl = channelurl.format(token, cfg.get('channels', 'archived'), cfg.get('channels', 'members'));
    global channeljson;
    channeljson = getjson(channelurl);

    # users json
    usersurl = "https://slack.com/api/users.list?token={}";
    usersurl = usersurl.format(token);
    global usersjson;
    usersjson = getjson(usersurl);
    
def getchannelid(channel):
    ''' 
    returns channel id gathered from the name provided via the slack api 
    args (all interpreted as strings):
        channel = channel name (human readable, exclude the #)
    '''
    # do magic here
    j = json.loads(channeljson.decode("utf-8"));
    totalchannels = len(j['channels']);
    for x in range(totalchannels):
        if (j['channels'][x]['name'] == channel):
                channelid = j['channels'][x]['id']; 
        try:
            channelid;
        except NameError:
            channelid = "not found";
    return channelid;

def getchannelmsghistory(token, channelid, count):
    '''
    returns json channel history
    args (all interpreted as strings):
        channelid = channel id (use getchannelid() to retrieve this from the human readable name)
    '''
    url = "https://slack.com/api/channels.history?token={}&channel={}&count={}";
    url = url.format(token, channelid, count);
    content = getjson(url);
    j = json.loads(content.decode("utf-8"));
    return j;

def getuserid(username):
    '''
    returns the user id gathered from the username provided via the slack api
    args (all interpreted as strings):
        username = human readable username (daniel_j for example)
    '''
    # do magic here
    j = json.loads(usersjson.decode("utf-8"));
    totalusers = len(j['members']);
    for x in range(totalusers):
        if (j['members'][x]['name'] == username):
                userid = j['members'][x]['id'];
        try:
            userid;
        except NameError:
            userid = "not found";
    return userid;

def getusername(userid):
    '''
    returns the username gathered from the userid and slack api
    args (all interpreted as strings):
        userid = users userid
    '''
    # do magic here
    j = json.loads(usersjson.decode("utf-8"));
    totalusers = len(j['members']);
    for x in range(totalusers):
        if (j['members'][x]['id'] == userid):
                username = j['members'][x]['name'];
        try:
            username;
        except NameError:
            username = "not found";
    return username;

def checkifentryexists(channel, ts):
    '''
    database call to check if the message exists
    returns true or false depending on conditions met
    args:
        ts = timestamp to check for
    '''
    ret = messagedb.find_one({"channel": channel, "timestamp":ts}); 
    #print(ret);
    if (ret):
        return True;
    return False;

def getmsg(channel, ts):
    '''
    retrieves a message from the database
    returns message from the database corresponding to the timestamp provided
    args: ts = timestamp to search for
    '''
    return messagedb.find_one({"channel": channel, "timestamp": ts})['message'];

def collectbants():
    '''
    collects and stores messages, handles message edits
    returns nothing
    args:
        none
    '''
    j = json.loads(channeljson.decode('utf-8'));
    totalchannels = len(j['channels']);
    for x in range(totalchannels):
        print("doing channel", j['channels'][x]['name']);
        data = getchannelmsghistory(token, getchannelid(j['channels'][x]['name']), cfg.get("messagelog", "count"));
        totalmessages = len(data['messages']);
        for i in range(totalmessages):
    #    print("<" + getusername(data['messages'][x]['user']) + "> " + str(data['messages'][x]['text'].encode('utf8')));
            try:
                author = getusername(data['messages'][i]['user']);
            except KeyError:
                # user is a bot (vac'd son bot doesn't have a username?)
                author = getusername(data['messages'][i]['username'])
            if (checkifentryexists(j['channels'][x]['name'], data['messages'][i]['ts']) != True):
                print("message not logged, logging");
                query = {"author": author,
                         "channel": j['channels'][x]['name'],
                         "message": str(data['messages'][i]['text']),
                         "timestamp": data['messages'][i]['ts']};
                message_id = messagedb.insert_one(query).inserted_id;
            else:
                print("message exists:", data['messages'][i]['ts']);
                if ("edited" in data['messages'][i]):
                    print("messaged has been edited at some point, checking", data['messages'][i]['ts']);
                    if (getmsg(j['channels'][x]['name'], data['messages'][i]['ts']) != data['messages'][i]['text']):
                        print("message does NOT match the database, updating");
                        messagedb.update({"channel": j['channels'][x]['name'], "timestamp" : data['messages'][i]['ts']}, {"$set":{"message": data['messages'][i]['text']}})
                    else:
                        print("message matches, nothing to do.");

if __name__ == "__main__":
    start_time = time.time();
    cfg = configparser.ConfigParser();
    cfg.read("config/settings.cfg");
    token = cfg.get("slack", "token");
    # static api data = channel info and user info
    getstaticapidata();
    dbconnect();
    collectbants();
    print("===========finished in %s seconds===========" % (time.time() - start_time));

    '''
    Total API calls should be 10 (8 channels) + (channels list, members list)
    '''
    
