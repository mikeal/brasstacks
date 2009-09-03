# Dependencies
import os
from datetime import datetime

# 
class Run(object):
    pass
    
# 
class Test(object):
    pass
    
# 
class Comparison(object):
    pass
    
# 
class RunSummary(object):
    pass
    
# 
class TestSummary(object):
    pass

#
class Then():
  def __init__(self, timestamp):
    parts = timestamp.split(".")
    t = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
    self.exactly = t
    t = t.replace(microsecond=int(parts[1]))
    self.precisely = t
    self.now = datetime.now()
    self.delta = self.now - self.precisely
    self.seconds = self.delta.seconds
    self.minutes = self.seconds / 60
    self.hours = self.minutes / 60
    self.days = self.delta.days
    self.weeks = self.days / 7
    self.months = self.weeks / 4
    self.years = self.months / 12
    self.approximately = self.words()
    
  def words(self):
    if self.minutes <= 5 and (self.hours + self.days + self.weeks + self.months + self.years) is 0:
      return "just now"
    
    if self.minutes > 5 and (self.hours + self.days + self.weeks + self.months + self.years) is 0:
      return str(self.minutes) + " minutes ago"
    
    if self.hours is 1 and (self.days + self.weeks + self.months + self.years) is 0:
      return str(self.minutes) + " minutes ago"
    
    if self.hours > 1 and (self.days + self.weeks + self.months + self.years) is 0:
      return str(self.hours) + " hours ago"
      
    if self.days is 1 and (self.weeks + self.months + self.years) is 0:
      return str(self.hours + self.days * 24) + " hours ago"
      
    if self.days > 1 and (self.weeks + self.months + self.years) is 0:
      return str(self.days) + " days ago"
      
    if self.weeks is 1 and (self.months + self.years) is 0:
      return str(self.days) + " days ago"
    
    if self.weeks > 1 and (self.months + self.years) is 0:
      return str(self.weeks) + " weeks ago"
      
    if self.months is 1 and self.years is 0:
      return str(self.weeks) + " weeks ago"
    
    if self.months > 1 and self.years is 0:
      return str(self.months) + " months ago"
      
    if self.years is 1:
      return str(self.months) + " months ago"
    
    if self.years > 1:
      return str(self.years) + " years ago"
        
        