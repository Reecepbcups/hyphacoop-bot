'''
Reece Williams | June 10th, 2022

A twitter bot to automatically post governance notifications,
    both for the forum & on chain.

Sections taken from
- https://github.com/Reecepbcups/cosmos-forum-notifications
- https://github.com/Reecepbcups/cosmos-governance-bot
'''

import datetime
import json
import os
from re import L
import requests
import schedule
import time
import tweepy

from os.path import dirname as parentDir
from enum import Enum

IN_PRODUCTION = False # Don't actually tweet, just print
USE_PYTHON_RUNNABLE = False # only run 1 time, turn this on for docker

GOVERNANCE_PROPOSALS_API = 'https://lcd-cosmoshub.blockapsis.com/cosmos/gov/v1beta1/proposals'
EXPLORER = "https://www.mintscan.io/cosmos/proposals"
FORUM_URL = "https://forum.cosmos.network/t/{ID}"
FORUM_API = "https://forum.cosmos.network/c/hub-proposals/25.json" # governance section = 25


# ----
IS_FIRST_RUN = False
SECRETS_FILE = parentDir(parentDir(__file__)) + "/secrets.json"
FILENAME = parentDir(parentDir(__file__)) + "/storage.json"
# print(SECRETS_FILE, '\n', FILENAME)

proposals = {
    "forum": 0, # Forum proposal IDs
    "chain": 0 # on chain proposals IDs
}
def load_proposals_from_file() -> dict:
    global proposals
    with open(FILENAME, 'r') as f:
        proposals = json.load(f)        
    return proposals
def save_proposals() -> None:
    with open(FILENAME, 'w') as f:
        json.dump(proposals, f)
def update_proposal_value(location: str, newPropNumber):
    global proposals
    proposals[location] = newPropNumber
    save_proposals()

############################################################################################
import urllib.parse

def unecode_text(msg):
    return urllib.parse.unquote(msg)

def getTopicList(url, key="topic_list") -> dict:
    response = requests.get(url)
    data = response.json()
    if key in data:
        data = data[key]
    return data

def getCosmosUserMap(url) -> dict:
    '''
    Get a dict of userID to userName for cosmos hub proposals.
    '''
    tempUsers = getTopicList(url, key="users") # reuse this requests code
    users = {}
    for u in tempUsers:
        username = u['username']
        userID = u['id'] 
        name = u['name'] # can be ""
        trust_level = u['trust_level'] # higher is better (4 is admin, 1 is user)
        
        users[userID] = {"username": username, "name": name, "trust_level": trust_level}
    return users

def run(ignorePinned : bool = True, onlyPrintLastCall : bool = True):
    threads = getTopicList(FORUM_API, key="topic_list")['topics']

    for prop in sorted(threads, key=lambda k: k['id'], reverse=False):
        _id = prop['id']
        if ignorePinned and prop['pinned'] == True: continue

        if _id <= int(proposals.get("forum")): # print(_id, chainID, "Already did this")
            continue

        tags = list(prop['tags'])
        if onlyPrintLastCall and 'last-call' not in tags:
            continue # we skip if it isn't a last-call before it goes up on chain
    
        title = unecode_text(prop['title'])
        createTime = prop['created_at']
        originalPoster = ""

        # Add regex profanity check?
    
        for poster in prop['posters']:
            desc = str(poster['description'])
            if 'original' in desc.lower():
                user = getCosmosUserMap(FORUM_API)[poster['user_id'] ]
                username = user["username"]
                # trustLevel = user["trust_level"]
                originalPoster = f"https://forum.cosmos.network/u/{username}"
                # adds their name to the end if they set it.
                name = user["name"]
                if len(name) > 0:
                    originalPoster += f" ({name})"
            
        update_proposal_value("forum", _id)
        print(_id, createTime, title, originalPoster, tags)
        
        post_tweet(
            ID=_id,
            title=title,
            location="forum"
        )


############################################################################################


# have this different for on chain VS in forum
def post_tweet(ID, title, location="chain"):
    if location == "chain":
        # ID here is the actual proposal ID (ex #71)
        message = f"Cosmos Proposal #{ID} | VOTE NOW | {title} | {EXPLORER}/{ID} | @cosmos"
    else:
        # ID here is the forum ID, > 6700
        message = f"Cosmos Forum Proposal (last-call) | {title} | {FORUM_URL.format(ID=ID)} | @cosmos"

    if IN_PRODUCTION:
        try:
            tweet = api.update_status(message)
            print(f"Tweet sent for {tweet.id}: {message}")
        except Exception as err:
            print("Tweet failed due to being duplicate OR " + str(err)) 
    else:
        print(f"WOULD TWEET: {message}   - {IN_PRODUCTION=}")





def getAllProposals() -> list:
    # Makes request to API & gets JSON reply in form of a list
    props = []
    try:
        response = requests.get(GOVERNANCE_PROPOSALS_API, headers={
            'accept': 'application/json', 
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}, 
            params={'proposal_status': '2'}) # 2 = voting period
        # print(response.url)
        props = response.json()['proposals']
    except Exception as e:
        print(f"Issue with request to {GOVERNANCE_PROPOSALS_API}: {e}")
    return props


def checkIfNewestProposalIDIsGreaterThanLastTweet():
    # get our last tweeted proposal ID (that was in voting period), if it exists
    # if not, 0 is the value so we search through all proposals
    lastPropID = 0

    # gets JSON list of all proposals
    props = getAllProposals()
    if len(props) == 0:
        return # This should never happen with cosmos

    # loop through out last stored voted prop ID & newest proposal ID
    for prop in props:
        current_prop_id = int(prop['proposal_id'])
        current_prop_title = prop['content']['title']

        # If this is a new proposal which is not the last one we tweeted for
        if current_prop_id <= lastPropID:
            continue

        print(f"Newest prop ID {current_prop_id} is greater than last prop ID {lastPropID}")
        
        if IS_FIRST_RUN or IN_PRODUCTION:      
            # save to proposals dict & to file (so we don't post again), unless its the first run                                 
            update_proposal_value("chain", current_prop_id)
        else:
            print("Not in production, not writing to file.")

        post_tweet(
            ID=current_prop_id,
            propID=current_prop_id, 
            title=current_prop_title,
            location="chain"
        )


def updateChainsToNewestProposalsIfThisIsTheFirstTimeRunning():
    global IN_PRODUCTION, IS_FIRST_RUN
    '''
    Updates JSON file to the newest proposals provided this is the first time running
    '''
    if os.path.exists(FILENAME):
        print(f"{FILENAME} exists, not updating")
        return

    IS_FIRST_RUN = True
    if IN_PRODUCTION:
        IN_PRODUCTION = False
        
    print("Updating chains to newest values since you have not run this before, these will not be posted")
    runChecks()
    save_proposals()
    print("Run this again now, chains have been populated")
    exit(0)

def runChecks():   
    print("Running check...") 
    try:
        checkIfNewestProposalIDIsGreaterThanLastTweet()
    except Exception as e:
        print(f"{e}")

    print(f"All chains checked {time.ctime()}, waiting")


if __name__ == "__main__":
    # Load twitter secrets from the filename
    twitSecrets = json.load(open("secrets.json", 'r'))

    # Get the values needed for access to the twitter account.
    # Need to add support for ENV Variables here.
    # Add an easy way to get these as ENV variables? (f"{var=}.split("=")" < would get the var name, then we get this from os.env)
    API_KEY = twitSecrets['API_KEY']
    API_KEY_SECRET = twitSecrets['API_KEY_SECRET']
    ACCESS_TOKEN = twitSecrets['ACCESS_TOKEN']
    ACCESS_TOKEN_SECRET = twitSecrets['ACCESS_TOKEN_SECRET']  

    # # Authenticate to Twitter & Get API
    auth = tweepy.OAuth1UserHandler(API_KEY, API_KEY_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    run(ignorePinned=False)