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
    
    def get_db_object(self):
        return models.Report.objects.get_or_create(
            slug = self.slug, defaults = {
                'slug': self.slug,
                'name': self.name,
                'description': self.description,
                'units': self.units,
            }
        )[0]

