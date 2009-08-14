function (keys, values, rereduce) {
  retval = {pass:0, fail:0, todo:0}
  var doTest = function (test) {
    retval.pass = retval.pass + test.pass;
    retval.fail = retval.fail + test.fail;
    retval.todo = retval.todo + test.todo;
  }
  if (!rereduce) {
    for (i in values) {
      for (v in values[i]) {
        doTest(values[i][v]);
      }
    }
  } else {
    for (i in values) {
      doTest(values[i]);
    }
  }
  return retval;
}
