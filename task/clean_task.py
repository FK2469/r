#! /usr/bin/env python
# coding=utf-8

import datetime
import os
import sys

ROOT_DIR = '/code/'
sys.path.append(ROOT_DIR)

from app import app, db, PasteFile


if __name__ == '__main__':
    current_time = datetime.datetime.utcnow()
    ten_days_ago = current_time - datetime.timedelta(days=10)
    rs = PasteFile.query.filter(PasteFile.uploadTime < ten_days_ago).order_by(PasteFile.uploadTime).all()
    a, d = 0, 0
    for file in rs:
        print file.uploadTime
        path = os.path.join(ROOT_DIR, file.path)
        if os.path.isfile(path):
            os.remove(path)
            d = d + 1
            print 'remove', path
        else:
            print 'not exists', path
        a = a + 1
        db.session.delete(file)
        db.session.commit()
    print '%s  Total %d, Deleted %d' % (current_time.strftime("%Y-%m-%d %H:%M"), a, d)
