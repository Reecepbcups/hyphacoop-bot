'''
Reece Williams | June 10th, 2022

A twitter bot to automatically post governance notifications,
    both for the forum & on chain.

Sections taken from
- https://github.com/Reecepbcups/cosmos-forum-notifications
- https://github.com/Reecepbcups/cosmos-governance-bot
'''

import os
import json
import requests
import schedule # not sure if required for akash
import time
import tweepy

from dotenv import dotenv_values

from utils import unecode_text, getForumTopicList, getForumUserMap
from utils import GOVERNANCE_PROPOSALS_API, EXPLORER, FORUM_URL, FORUM_API, SECRETS_FILE, FILENAME


############################################################################################

def main():   
    load_proposals_from_file()         

    USE_RUNNABLE_FOR_DOCKER = bool(config["USE_RUNNABLE_FOR_DOCKER"])
    RUNNABLE_MINUTES = int(config["RUNNABLE_MINUTES"])   

    if USE_RUNNABLE_FOR_DOCKER:
        print("Using a runnable so docker will stay alive")
        while True:
            checkForNewOnChainProposals()
            runForumCheck(ignorePinned=False)
            time.sleep(RUNNABLE_MINUTES * 60)


    print("One time run")
    checkForNewOnChainProposals()
    runForumCheck(ignorePinned=False)


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

def runForumCheck(ignorePinned : bool = True, onlyPrintLastCall : bool = True):
    threads = getForumTopicList(FORUM_API, key="topic_list")['topics']

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
                user = getForumUserMap(FORUM_API)[poster['user_id'] ]
                username = user["username"]
                # trustLevel = user["trust_level"]
                originalPoster = f"https://forum.cosmos.network/u/{username}"
                # adds their name to the end if they set it.
                name = user["name"]
                if len(name) > 0:
                    originalPoster += f" ({name})"
            
        if IN_PRODUCTION:      
            # update the ID ONLY in production so any new proposals don't not get tweeted                              
            update_proposal_value("forum", _id)
        else:
            print(f"Not in production, not writing to file.")
        
        # print(_id, createTime, title, originalPoster, tags)        
        post_tweet(
            ID=_id,
            title=title,
            location="forum"
        )
    print("Checked for new new forum proposals")


#####################################POST TWEET#############################################
def post_tweet(ID: int, title: str, location : str ="chain") -> None:
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
            print("Tweet failed " + str(err)) 
    else:
        # print(f"WOULD TWEET: {message}   - {IN_PRODUCTION=}")
        pass
############################################################################################


def getAllOnChainProposals() -> list:
    # Makes request to API & gets JSON reply in form of a list
    props = []
    try:
        response = requests.get(GOVERNANCE_PROPOSALS_API, headers={
            'accept': 'application/json', 
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}, 
            params={'proposal_status': '2'}) # 2=voting period, 3=passed, 4=Rejected. TODO: Change to 2
        props = response.json()['proposals']
    except Exception as e:
        print(f"Issue with request to {GOVERNANCE_PROPOSALS_API}: {e}")

    return props


def checkForNewOnChainProposals() -> None:
    # get our last tweeted proposal ID (that was in voting period), if it exists
    # if not, 0 is the value so we search through all proposals
    lastPropID = proposals.get("chain", 0)

    # gets JSON list of all proposals
    props = getAllOnChainProposals()

    # loop through out last stored voted prop ID & newest proposal ID
    for prop in props:
        current_prop_id = int(prop['proposal_id'])
        current_prop_title = prop['content']['title']

        # If this is a new proposal which is not the last one we tweeted for
        if current_prop_id <= lastPropID:
            continue

        print(f"Newest prop ID {current_prop_id} is greater than last prop ID {lastPropID}")
        
        if IN_PRODUCTION:      
            # save to proposals dict & to file (so we don't post again), unless its the first run                                 
            update_proposal_value("chain", current_prop_id)
        else:
            print(f"Not in production, not writing to file.")
        
        post_tweet(
            ID=current_prop_id,
            title=current_prop_title,
            location="chain"
        )
    print("Checked for new on-chain proposals")
    
############################################################################################


if __name__ == "__main__":
    # Load twitter secrets from the env vfile
    config = dotenv_values(".env")

    # Get the values needed for access to the twitter account.
    API_KEY = config["API_KEY"]
    API_KEY_SECRET = config["API_KEY_SECRET"]
    ACCESS_TOKEN = config["ACCESS_TOKEN"]
    ACCESS_TOKEN_SECRET = config["ACCESS_TOKEN_SECRET"]

    # # Authenticate to Twitter & Get API
    auth = tweepy.OAuth1UserHandler(API_KEY, API_KEY_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True) 

    IN_PRODUCTION = bool(config["IN_PRODUCTION"])

    main()