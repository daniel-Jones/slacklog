#!/usr/bin/env python3

import urllib.request;
import json;
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
    f = urllib.request.urlopen(url);
    content = f.read();
    f.close();
    return content;

def getstaticapidata():
    '''
    downloads our api data and stores them
    returns nothing
    i hate this function
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
    #
def getchannelid(channel):
    ''' 
    returns channel id gathered from the name provided via the slack api 
    args (all interpreted as strings):
        channel = channel name (human readable, exclude the #)
    '''
    # do magic here
    j = json.loads(channeljson);
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
    returns https request from the slack api containing channel message history.
    args (all interpreted as strings):
        channelid = channel id (use getchannelid() to retrieve this from the human readable name)
    '''
    url = "https://slack.com/api/channels.history?token={}&channel={}&count={}";
    url = url.format(token, channelid, count);
    content = getjson(url);
    j = json.loads(content);
    totalmessages = len(j['messages']);
    for x in range(totalmessages):
        # handle message here
        print("<" + getusername(j['messages'][x]['user']) + "> " + str(j['messages'][x]['text'].encode('utf8')));
    return str(totalmessages);

def getuserid(username):
    '''
    returns the user id gathered from the username provided via the slack api
    args (all interpreted as strings):
        username = human readable username (daniel_j for example)
    '''
    # do magic here
    j = json.loads(usersjson);
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
    j = json.loads(usersjson);
    totalusers = len(j['members']);
    for x in range(totalusers):
        if (j['members'][x]['id'] == userid):
                username = j['members'][x]['name'];
        try:
            username;
        except NameError:
            username = "not found";
    return username;


if __name__ == "__main__":
    cfg = configparser.ConfigParser();
    cfg.read("config/settings.cfg");
    token = cfg.get("slack", "token");
    # static api data = channel info and user info
    getstaticapidata();
    #print(cfg.get("slack", "token"));
    #print(getchannelmsghistory(cfg.get('slack', 'token'), "C03UGEJ38", cfg.get("messagelog", "count")));
    print("channel id from name: " + getchannelid("modmail"));
    print("id from username: " + getuserid("daniel_j"));
    print("username from id: " + getusername("U2S719P6Y"));
    print("total messages retrieved: " + getchannelmsghistory(token, getchannelid("general"), cfg.get('messagelog', 'count')));
