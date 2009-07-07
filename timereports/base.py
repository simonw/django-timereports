import datetime
import models

def MINUTELY(self, dt):
    return dt.replace(microsecond = 0, second = 0)

def HOURLY(self, dt):
    return dt.replace(microsecond = 0, second = 0, minute = 0)

def DAILY(self, dt):
    return dt.replace(microsecond = 0, second = 0, minute = 0, hour = 0)

class Report(object):
    slug = None
    name = None
    description = ''
    units = ''
    frequency = lambda self, x: x

    def value(self):
        raise NotImplementedError

    def value_at(self, dt):
        raise NotImplementedError

    value_at.not_implemented = True
    
    def current_point(self):
        if hasattr(self.value_at, 'not_implemented'):
            return datetime.datetime.now(), self.value()
        else:
            dt = self.frequency(datetime.datetime.now())
            return dt, self.value_at(dt)
    
    def record(self):
        report = self.get_db_object()
        dt, value = self.current_point()
        report.points.get_or_create(sampled = dt, defaults = {'value': value})

    def record_at(self, dt):
        report = self.get_db_object()
        dt = self.frequency(dt)
        value = self.value_at(dt)
        report.points.get_or_create(sampled = dt, defaults = {'value': value})
    
    def get_db_object(self):
        return models.Report.objects.get_or_create(
            slug = self.slug, defaults = {
                'slug': self.slug,
                'name': self.name,
                'description': self.description,
                'units': self.units,
            }
        )[0]

