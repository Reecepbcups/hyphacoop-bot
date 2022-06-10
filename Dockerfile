# sudo docker build -t hyphabot:1.0.0 .
# sudo docker run -it --rm --name hyphabot hyphabot

FROM python:3-alpine

LABEL Maintainer="reecepbcups"

WORKDIR /usr/app/src

COPY requirements/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./src/chain_proposals.py"]