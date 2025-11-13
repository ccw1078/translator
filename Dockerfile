ARG BASE_IMG=python:3.12-slim

FROM $BASE_IMG

ARG PROJECT_DIR=/usr/translator
ARG APP_DIR=/usr/translator/app

WORKDIR $PROJECT_DIR

COPY requirements.txt requirements.txt

RUN pip install -i https://mirrors.aliyun.com/pypi/simple  -r requirements.txt

COPY app $APP_DIR
COPY constants.py main.py run.py config.py .

RUN groupadd -r user && useradd -r -g user user
RUN chown -R user:user $PROJECT_DIR
USER user


ENTRYPOINT ["gunicorn", "-c", "config.py", "run:app"]