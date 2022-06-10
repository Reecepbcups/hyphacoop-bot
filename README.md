# hyphacoop-bot

TODO:
- Move over core code from
  - https://github.com/Reecepbcups/cosmos-forum-notifications
  - https://github.com/Reecepbcups/cosmos-governance-bot

Only have the COSMOS HUB chain values (REST endpoint & Forum API)

Make a class for it so these can be called via an object.

## Compile with docker
```bash
sudo docker login

VERSION="1.0.1"
sudo docker build -t reecepbcups/hyphacoop_bot:$VERSION .
# sudo docker run -it reecepbcups/hyphacoop_bot:$VERSION
sudo docker push reecepbcups/hyphacoop_bot:$VERSION
```

## Setup

---
## Env Variables
### Twitter
```sh
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
```