import uuid
from datetime import datetime, timedelta

from mongoengine import *


connect('projdoc', host='localhost', port=27017)


class UserStatistics(EmbeddedDocument):
    correct_answers_lst = ListField(IntField(), default=list)
    notifications_count = IntField(default=0)
    success_date = DateTimeField(null=True)
    url_clicks = ListField(DateTimeField(), default=list)


class User(Document):
    uid = IntField()
    name = StringField(null=True)
    surname = StringField(null=True)
    email = StringField(null=True)
    # password = StringField(null=True)
    cookies = StringField(null=True)
    chosen_time = DateTimeField()
    group = StringField()
    seminars = MapField(EmbeddedDocumentField(UserStatistics))

    notify_dt = DateTimeField()
    start_test_dt = DateTimeField()
    stop_test_dt = DateTimeField()

    meta = {'collection': 'users'}

    def notify_tommorow(self):
        tommorow = datetime.now() + timedelta(days=1)
        self.notify_dt = tommorow.replace(hour=self.chosen_time.hour,
                                          minute=self.chosen_time.minute,
                                          second=0, microsecond=0)
        self.save()


class Url(Document):
    key = StringField(default=str(uuid.uuid4())[:8])
    uid = IntField()
    url = StringField()
    sem_num = StringField()
    exp_dt = DateTimeField(default=datetime.now() + timedelta(minutes=30))

    meta = {'collection': 'urls'}
