FROM python:3.11.0-slim

COPY ./req.txt ./req.txt

COPY . ./code/

COPY ./.env ./.env

RUN apt-get -y update

RUN apt-get install -y ffmpeg git gcc

RUN apt install ttf* -y

RUN apt-get install -y python3-dev python3-setuptools 

RUN apt-get install -y libtiff5-dev libjpeg62-turbo-dev libopenjp2-7-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk libharfbuzz-dev libfribidi-dev libxcb1-dev

RUN (sed -E -n 's/[^#]+/export &/ p' .env | sed 's/[ \t]*=[ \t]*/=/' | tr -d '"' | tr -d "'") > ./env.sh && . ./env.sh && rm ./env.sh && git config --global url."https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir --upgrade -r req.txt

WORKDIR /code

CMD ["python", "-u", "main.py"]

ENTRYPOINT ["python", "-u", "main.py"]
