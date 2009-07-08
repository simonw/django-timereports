import datetime
import models
import pygooglechart
from django.utils import dateformat

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
    
    def horizontal_labels(self, num_labels=11):
        points = list(self)
        gap = len(points) / float(num_labels - 1)
        labels = []
        for i in range(num_labels - 1):
            labels.append(points[int(gap * i)][0])
        # And the very last label in the sequence:
        labels.append(points[-1][0])
        return labels
    
    def max_value(self):
        return max([m[1] for m in self])
    
    def vertical_labels(self, num_labels=6):
        max_value = self.max_value()
        gap = max_value / float(num_labels - 1)
        labels = []
        for i in range(num_labels - 1):
            labels.append(int(gap * i))
        # And the very last label in the sequence:
        labels.append(int(max_value))
        return labels
    
    def google_chart(self):
        points = list(self)
        chart = pygooglechart.SimpleLineChart(800, 200, y_range = [0, self.max_value()])
        chart.add_data([p[1] for p in points])
        horizontal_labels = [
            dateformat.format(l, 'j M g:00') for l in self.horizontal_labels()
        ]
        chart.set_axis_labels(pygooglechart.Axis.BOTTOM, horizontal_labels)
        chart.set_axis_labels(pygooglechart.Axis.LEFT, self.vertical_labels())
        chart.set_grid(10, 20, 5, 2)
        # 10 = 10 vertical grid lines (10% gap between each)
        # 20 = 5 horizontal grid lines (20% gap between each)
        # 5, 2 = dashed lines, 5 pixels dash to 2 pixels blank
        return chart

    def google_chart_url(self):
        return self.google_chart().get_url()

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

