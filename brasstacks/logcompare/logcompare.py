import os
from datetime import datetime

class Build():
  def __init__(self, doc):
   
    self.doc = doc[0]['value']
    self.docid = self.doc['_id']
    self.buildid = self.doc['build']
    self.product = self.doc['product']
    self.os = self.doc['os']
    self.testtype = self.doc['testtype']
    self.timestamp = self.doc['timestamp']
    self.tests = self.doc['tests']

  def getTests(self):
    return TestsResult(self.tests)
    
  def compare(self, build):
    
    newtestfiles = []
    missingtestfiles = []
    
    prevlynotfails = []
    prevlynotpasses = []
    prevlynottodos = []
    
    missingfails = []
    missingpasses = []
    missingtodos = []
    
    newfails = []
    newpasses = []
    newtodos = []
    
    stabletests = []
    
    tests1 = self.tests
    tests2 = build.tests
    
    for testfile in tests1:
      
      if testfile not in tests2:
        newtestfiles.append({'testfile': testfile, 'result': tests1[testfile]})
      else:
        result1 = tests1[testfile]
        result2 = tests2[testfile]

        sum1 = result1['fail'] + result1['pass'] + result1['todo']
        sum2 = result2['fail'] + result2['pass'] + result2['todo']
        
        if sum1 == sum2: 
          if result1['fail'] == result2['fail'] and result1['pass'] == result2['pass'] and result1['todo'] == result2['todo']:
            stabletests.append({'testfile': testfile, 'result': tests1[testfile]})
          else:
            if result1['fail'] > result2['fail']:
              # prevlynotfails.append({'testfile': testfile, 'delta': result1['fail'] - result2['fail'], 'failnotes': result1['note'].split(', ')})
              prevlynotfails.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})
            if result1['pass'] > result2['pass']:
              prevlynotpasses.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['pass'] - result2['pass']})
            if result1['todo'] > result2['todo']:
              prevlynottodos.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['todo'] - result2['todo']})
        
        elif sum1 < sum2:
          if result1['fail'] < result2['fail']:
            missingfails.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result2['fail'] - result1['fail']})
          if result1['pass'] < result2['pass']:
            missingpasses.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result2['fail'] - result1['fail']})
          if result1['todo'] < result2['todo']:
            missingtodos.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result2['fail'] - result1['fail']})
        
        else:
          if result1['fail'] > result2['fail']:
            newfails.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})
          if result1['pass'] > result2['pass']:
            newpasses.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})
          if result1['todo'] > result2['todo']:
            newtodos.append({'testfile': testfile, 'result1': tests1[testfile], 'result2': tests2[testfile], 'delta': result1['fail'] - result2['fail']})

        del tests2[testfile]
    
    for remainingtestfile in tests2:
      missingtestfiles.append({'testfile': remainingtestfile, 'result': tests2[remainingtestfile]})
    
    result = {}
    result['newtestfiles'] = newtestfiles
    result['missingtestfiles'] = missingtestfiles
  
    result['stabletests'] = stabletests
    
    result['prevlynotfails'] = prevlynotfails
    result['prevlynotpasses'] = prevlynotpasses
    result['prevlynottodos'] = prevlynottodos
    
    result['missingfails'] = missingfails
    result['missingpasses'] = missingpasses
    result['missingtodos'] = missingtodos
    
    result['newfails'] = newfails
    result['newpasses'] = newpasses
    result['newtodos'] = newtodos
    
    return result
  
  # note: %f directive not supported in python 2.5 so microsecond needs to be parsed manually
  def newer(self, build):
    
    directives = "%Y-%m-%d %H:%M:%S"
    
    parts = self.timestamp.split(".")
    dt1 = datetime.strptime(parts[0], directives)
    dt1 = dt1.replace(microsecond = int(parts[1]))
    
    parts = build.timestamp.split(".")
    dt2 = datetime.strptime(parts[0], directives)
    dt2 = dt2.replace(microsecond = int(parts[1]))
    
    # true if self's time is later than build's time
    return dt > dt2

class TestsResult():
  def __init__(self, tests):
    self.numtestfiles = len(tests)
    items = tests.iteritems()
    
    self.totalfails = 0
    self.totalpasses = 0
    self.totaltodos = 0
    
    for (key, value) in items:
      self.totalfails = self.totalfails + value['fail']
      self.totalpasses = self.totalpasses + value['pass']
      self.totaltodos = self.totaltodos + value['todo']
    
    self.totaltests = self.totalfails + self.totalpasses + self.totaltodos
    self.tests = tests.iteritems()
    
class TestDelta():
  def __init__(self, name, notes, delta):
    self.name = ''
    self.failnotes = ''
    self.count = 0
  def parsefailnotes(self):
    return False

class Test():
  def __init__(self, testfile, result):
    self.testfile = testfile
    self.result = result
    self.totalfail = self.result['fail']
    self.totalpass = self.result['pass']
    self.totaltodo = self.result['todo']
    # self.notes = self.result['note'].split(',')
    self.notes = self.result['note']
  def totaltests():
    return self.totalfail + totalpass + totaltodo
  
# class ComparisonResult():
  # def __init__(self):
    # pass
  # def compare(self, build1, build2):
    # tests1 = build1['rows'][0]['value'][]
    # thisbuild = {}
    # thisbuild = build1['rows'][0]['value']
    # return thisbuild
    