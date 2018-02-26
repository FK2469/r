FROM python:2.7
RUN mkdir /code
COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN apt-get update && apt-get install -y cron
COPY ./task/crontab /etc/cron.d/r_cron
RUN touch /var/log/cron.log

WORKDIR /code
CMD /usr/sbin/cron && python app.py
