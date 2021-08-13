FROM python:3

WORKDIR /home/graphSearchEngine/restApi

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN python3 -m spacy download en_core_web_sm
COPY . .

CMD [ "python", "./run.py" ]