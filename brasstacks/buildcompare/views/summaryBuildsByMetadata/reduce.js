function (key, value) {

  //for some reason key is [key, doc._id]
  //so emit([doc.testtype, doc.build], doc.tests)
  //doc.build = key[0][0][1]
  //if (parseInt(key[0][0][1]) > 0) {
    retval = {};
    retval["pass"] = 0;
    retval["fail"] = 0;
    retval["todo"] = 0;
    for (v in value[0]) {
      test = value[0][v];
      retval.pass = retval.pass + test.pass;
      retval.fail = retval.fail + test.fail;
      retval.todo = retval.todo + test.todo;    
    }
    return retval;
  //}
  //return {};
