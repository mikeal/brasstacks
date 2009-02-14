function (keys, values, rereduce) {
  
  var reduceSum = function(array) {
    var s = 0;
    for each(n in array) {
      s = s + n;
    }
    return s
  }
  
  totals = {};
  
  if (!rereduce) {
    for each(testRun in values) {
      var build = testRun['appInfo.id'] + '|' + testRun['buildid'];
      if (totals[build] == undefined) {
        totals[build] = {'passed':0, 'failed':0, 'skipped':0}
      }
      var results = [[test.passed, test.failed] for each(test in testRun.tests)]
      totals[build].passed = totals[build].passed + reduceSum([r[0] for each(r in results)]);
      totals[build].failed = totals[build].failed + reduceSum([r[1] for each(r in results)]);
      totals[build].skipped = totals[build].skipped + reduceSum([1 for each(r in results) if (r[2] != undefined)]);  
    }
  } else {
    
    for each(total in values) {
      for (build in total) {
        if (totals[build] == undefined) {
          totals[build] = {'passed':0, 'failed':0, 'skipped':0}
        }
        totals[build].passed = totals[build].passed + total[build].passed;
        totals[build].failed = totals[build].failed + total[build].failed;
        totals[build].skipped = totals[build].skipped + total[build].skipped;
      }
    }
    
  }
  return totals;
  
}