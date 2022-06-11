# hyphacoop-bot

## Compile with docker
```bash
sudo docker login

VERSION="1.0.2"
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