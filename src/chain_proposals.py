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
FORUM_URL = "https://forum.cosmos.network"



# ----
IS_FIRST_RUN = False
SECRETS_FILE = parentDir(parentDir(__file__)) + "/secrets.json"
FILENAME = parentDir(parentDir(__file__)) + "/storage.json"
# print(SECRETS_FILE, '\n', FILENAME)

class Location(Enum):
    CHAIN = "chain"
    FORUM = "forum"

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
def update_proposal_value(location: Enum, newPropNumber):
    global proposals
    proposals[location] = newPropNumber
    save_proposals()


def post_update(propID, title, description=""):
    message = f"Cosmos Proposal #{propID} | VOTING | {title} | {EXPLORER}/{propID} | @cosmos"
    print(f"{message=}")

    if IN_PRODUCTION:
        try:
            tweet = api.update_status(message)
            print(f"Tweet sent for {tweet.id}: {message}")
        except Exception as err:
            print("Tweet failed due to being duplicate OR " + str(err)) 
    else:
        print(f"WOULD TWEET: {message}   - {IN_PRODUCTION=}")


def getAllProposals(ticker) -> list:
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
        print(f"Issue with request to {ticker}: {e}")
    return props


def checkIfNewestProposalIDIsGreaterThanLastTweet(ticker):
    # get our last tweeted proposal ID (that was in voting period), if it exists
    # if not, 0 is the value so we search through all proposals
    lastPropID = 0
    if ticker in proposals:
        lastPropID = int(proposals[ticker])

    # gets JSON list of all proposals
    props = getAllProposals(ticker)
    if len(props) == 0:
        return

    # loop through out last stored voted prop ID & newest proposal ID
    for prop in props:
        current_prop_id = int(prop['proposal_id'])

        # If this is a new proposal which is not the last one we tweeted for
        if current_prop_id > lastPropID:   
            print(f"Newest prop ID {current_prop_id} is greater than last prop ID {lastPropID}")
            
            if IS_FIRST_RUN or IN_PRODUCTION:      
                # save to proposals dict & to file (so we don't post again), unless its the first run                                 
                update_proposal_value(ticker, current_prop_id)
            else:
                print("Not in production, not writing to file.")

            post_update(
                ticker=ticker,
                propID=current_prop_id, 
                title=prop['content']['title'], 
                description=prop['content']['description'], # for discord embeds
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
        checkIfNewestProposalIDIsGreaterThanLastTweet(chain)
    except Exception as e:
        print(f"{chain} checkProp failed: {e}")

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

    # Authenticate to Twitter & Get API
    auth = tweepy.OAuth1UserHandler(API_KEY, API_KEY_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)  