FROM python:2.7
RUN mkdir /code
COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN apt-get update && apt-get install -y cron
RUN touch /var/log/cron.log
# Setup cron job
RUN (crontab -l ; echo "0 0 * * * root /usr/local/bin/python /code/task/clean_task.py >> /var/log/cron.log 2>&1") | crontab

WORKDIR /code
CMD /usr/sbin/cron && python app.py
