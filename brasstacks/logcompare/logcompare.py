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
    self.years = self.now.year - self.precisely.year
    self.months = self.now.month - self.precisely.month
    self.weeks = self.delta.days / 7
    self.days = self.delta.days
    self.hours = self.delta.seconds / 3600
    self.minutes = self.delta.seconds / 60
    self.seconds = self.delta.seconds
    self.string = self._string()
    
  def _string(self):
    if self.years > 1:
      return "over " + str(self.years) + " years ago"
    elif self.years == 1:
      return str(self.years) + " year ago"
    else:
      if self.months > 1:
        return str(self.months) + " months ago"
      elif self.months == 1:
        return str(self.months) + " month ago"
      else:
        if self.weeks > 1:
          return str(self.weeks) + " weeks ago"
        elif self.weeks > 1:
          return str(self.weeks) + " week ago"
        else:
          if self.days > 1:
            return str(self.days) + " days ago"
          elif self.days == 1:
            return "yesterday" # str(self.days) + " day ago"
          else: 
            if self.hours > 1:
              return str(self.hours) + " hours ago"
            elif self.hours == 1:
              return str(self.hours) + " hour ago"
            else:
              if self.minutes > 1:
                return str(self.minutes) + " minutes ago"
              else:
                return "just now"
        
        