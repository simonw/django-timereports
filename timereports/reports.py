from base import Report, Hourly, Daily
from django.db.models import Min
import os, re

load_average_re = re.compile('load average: ([\d.]+)')

class LoadAverage(Report):
    slug = 'load_average'
    name = 'Load average'
    description = 'From the uptime system command'

    def value(self):
        s = os.popen('uptime').read().strip()
        return int(100 * float(load_average_re.search(s).group(1)))

class CreatedObjectsReport(Report):
    model = None
    created_field = None
    frequency = Hourly()
    
    def earliest_date(self):
        return self.model.objects.aggregate(x = Min(self.created_field))['x']

    def value_at(self, dt):
        return self.model.objects.filter(**{
            '%s__lt' % self.created_field: dt
        }).count()

from expenses.models import User
class CreatedUsers(CreatedObjectsReport):
    slug = 'user_accounts'
    name = 'User accounts'
    model = User
    created_field = 'created'
    frequency = Daily()

from expenses.models import Vote, Page
class ReviewedPages(Report):
    slug = 'reviewed_pages'
    name = 'Reviewed pages'
    frequency = Daily()
    
    def earliest_date(self):
        return Vote.objects.aggregate(x = Min('created'))['x']

    def value_at(self, dt):
        return Vote.objects.filter(created__lte = dt).values('page').distinct().count()

