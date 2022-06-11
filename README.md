# hyphacoop-bot
This bot is to automatically tweet out the following:
- Cosmos Governance On Chain proposals
- Cosmos Forum Proposals (only if they have been tagged with "last-call")


### Example Draft Tweet
Cosmos Draft | 'Telegram bot test' | https://forum.cosmos.network/t/6710 | By: https://forum.cosmos.network/u/lexa (Lexa Michaelides) | @cosmos

### Example On Chain Tweet
Cosmos Proposal #71 | VOTE NOW | 'Recover EVMOS channel by upgrading to new client' | https://www.mintscan.io/cosmos/proposals/71 | @cosmos


## Compile with docker
```bash
sudo docker login

VERSION="1.0.2"
sudo docker build -t reecepbcups/hyphacoop_bot:$VERSION .
# sudo docker run -it reecepbcups/hyphacoop_bot:$VERSION
sudo docker push reecepbcups/hyphacoop_bot:$VERSION
```

---

# Setup

## Install
```sh
git clone https://github.com/Reecepbcups/hyphacoop-bot
cd hyphacoop-bot

# use penv if you want
python3 -m pip install --no-cache-dir -r requirements/requirements.txt

cp .env.example .env
# Edit these with your values OR use the Environment Variables

python3 src/bot.py
```

---

## Environment Variables
### Twitter
```sh
# https://developer.twitter.com/en/portal/petition/use-case
API_KEY=
API_KEY_SECRET=
ACCESS_TOKEN=
ACCESS_TOKEN_SECRET=
```
### Production
```sh
IN_PRODUCTION=True

# required for docker
USE_PYTHON_RUNNABLE=True
RUNNABLE_MINUTES=60
```

---

### Run in Akash
```sh
docker login

docker build -t <username>/hyphacoop_bot .
docker push <username>/hyphacoop_bot:latest

# open the akashalytics deploy panel tool
# https://www.akashlytics.com/deploy
#
# - Create Deployment
# - From a File
#
# - Select 'akash/hyphacoop-bot.yml' file
#    - Update the image: to point to your location (<username>/hyphacoop_bot:latest)
#      [If none is provided, your .env will be used as default.]
#
# - You can alter the compute resources, however CPU is the majority of the cost.
#          0.1CPU, 0.5GB RAM, and 1GB storage are recommended.
```