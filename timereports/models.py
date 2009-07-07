from django.db import models

class Report(models.Model):
    slug = models.SlugField(unique = True)
    name = models.CharField(max_length = 100)
    units = models.CharField(max_length = 20, blank = True)
    description = models.TextField(blank = True)
    
    def __unicode__(self):
        return self.name

class Point(models.Model):
    report = models.ForeignKey(Report, related_name = 'points')
    sampled = models.DateTimeField(db_index = True)
    value = models.IntegerField()
    
    def __unicode__(self):
        return u'%s: %s' % (self.sampled, self.value)

