import datetime
import models

class Secondly(object):
    def round_down(self, dt):
        return dt.replace(microsecond = 0)
    timedelta = datetime.timedelta(seconds = 1)

class Minutely(object):
    def round_down(self, dt):
        return dt.replace(microsecond = 0, second = 0)
    timedelta = datetime.timedelta(seconds = 60)

class Hourly(object):
    def round_down(self, dt):
        return dt.replace(microsecond = 0, second = 0, minute = 0)
    timedelta = datetime.timedelta(seconds = 60 * 60)

class Daily(object):
    def round_down(self, dt):
        return dt.replace(microsecond = 0, second = 0, minute = 0)
    timedelta = datetime.timedelta(seconds = 60 * 60 * 24)

class Report(object):
    slug = None
    name = None
    description = ''
    units = ''
    frequency = Secondly()

    def value(self):
        raise NotImplementedError

    def value_at(self, dt):
        raise NotImplementedError
    value_at.not_implemented = True
    
    def earliest_date(self):
        raise NotImplementedError
    earliest_date.not_implemented = True
    
    def current_point(self):
        if hasattr(self.value_at, 'not_implemented'):
            return datetime.datetime.now(), self.value()
        else:
            dt = self.frequency.round_down(datetime.datetime.now())
            return dt, self.value_at(dt)
    
    def record(self):
        report = self.get_db_object()
        dt, value = self.current_point()
        report.points.get_or_create(sampled = dt, defaults = {'value': value})

    def record_at(self, dt):
        report = self.get_db_object()
        dt = self.frequency.round_down(dt)
        value = self.value_at(dt)
        report.points.get_or_create(sampled = dt, defaults = {'value': value})
    
    def backfill(self):
        earliest_date = self.frequency.round_down(self.earliest_date())
        timedelta = self.frequency.timedelta
        
        current = earliest_date
        while current < datetime.datetime.now():
            self.record_at(current)
            current += timedelta
    
    def graph(self, start=None, end=None):
        return DateGraph(self, start, end)
    
    def get_db_object(self):
        return models.Report.objects.get_or_create(
            slug = self.slug, defaults = {
                'slug': self.slug,
                'name': self.name,
                'description': self.description,
                'units': self.units,
            }
        )[0]

LAST_VALUE = object()

class DateGraph(object):
    def __init__(self, report, start=None, end=None):
        self.report = report
        self.start = start and report.frequency.round_down(start) or None
        self.end = end and report.frequency.round_down(end) or None
        self.default_value = LAST_VALUE
    
    def last_30_days(self):
        return self.last_x_days(30)
    
    def last_x_days(self, x):
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days = x)
        return DateGraph(self.report, start, end)
    
    def all_time(self):
        earliest = self.report.earliest_date()
        return DateGraph(self.report, earliest, datetime.datetime.now())
    
    def all_dates(self):
        from django.db.models import Max
        earliest = self.report.earliest_date()
        latest = self.report.get_db_object().points.aggregate(
            m = Max('sampled')
        )['m']
        return DateGraph(self.report, earliest, latest)
    
    def __iter__(self):
        assert self.start is not None, '.start property must be set'
        assert self.end is not None, '.end property must be set'
        round_down = self.report.frequency.round_down
        timedelta = self.report.frequency.timedelta
        
        current = round_down(self.start)
        end = round_down(self.end)
        
        points = {}
        for point in self.report.get_db_object().points.all():
            sampled = round_down(point.sampled)
            points[sampled] = point.value
        
        last_yielded = None
        
        while current <= end:
            if self.default_value is LAST_VALUE:
                default_value = last_yielded
            else:
                default_value = self.default_value
            value = points.get(current, default_value)
            yield (current, value)
            last_yielded = value
            current += timedelta
