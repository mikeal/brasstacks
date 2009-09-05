function (doc) {
  if (doc.type == "job" && doc.status == "done") {
    jobinfo = {'buildinfo':doc.buildinfo, 'id':doc._id, 'machine_name':doc.machine_name}
    for each(result in doc.results) {
      result.jobinfo = jobinfo;
      emit([result.url, result.reproduced, doc.endtime], result);
    }
  }
}