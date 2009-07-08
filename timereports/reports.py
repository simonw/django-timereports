from base import Report, Hourly
import os, re

load_average_re = re.compile('load average: ([\d.]+)')

class LoadAverage(Report):
    slug = 'load_average'
    name = 'Load average'
    description = 'From the uptime system command'

    def value(self):
        s = os.popen('uptime').read().strip()
        return int(100 * float(load_average_re.search(s).group(1)))

class CreatedUsers(Report):
    slug = 'user_accounts'
    name = 'User accounts'
    frequency = Hourly()
    
    def earliest_date(self):
        from django.db.models import Min
        from expenses.models import User
        return User.objects.aggregate(x = Min('created'))['x']

    def value_at(self, dt):
        from expenses.models import User
        return User.objects.filter(created__lt = dt).count()
