import urllib.parse

# misc
def unecode_text(msg):
    return urllib.parse.unquote(msg)



# forums
import requests
def getForumTopicList(url, key="topic_list") -> dict:
    response = requests.get(url)
    data = response.json()
    if key in data:
        data = data[key]
    return data

def getForumUserMap(url) -> dict:
    '''
    Get a dict of userID to userName for cosmos hub proposals.
    '''
    tempUsers = getForumTopicList(url, key="users") # reuse this requests code
    users = {}
    for u in tempUsers:
        username = u['username']
        userID = u['id'] 
        name = u['name'] # can be ""
        trust_level = u['trust_level'] # higher is better (4 is admin, 1 is user)
        
        users[userID] = {"username": username, "name": name, "trust_level": trust_level}
    return users