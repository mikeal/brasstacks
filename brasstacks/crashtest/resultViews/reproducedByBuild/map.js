function (doc) {
  if (doc.type == "job" && doc.status == "done") {
    jobinfo = {'buildinfo':doc.buildinfo, 'id':doc._id, 'os':doc.os, 'machine_name':doc.machine_name}
    for each(result in doc.results) {
      if (result.reproduced) {
        result.jobinfo = jobinfo;
        emit([doc.buildinfo.buildid, doc.endtime], result);
      }
    }
  }
}