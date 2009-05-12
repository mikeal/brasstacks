function(keys, values, rereduce) {
  var result = {};
  var numres = {};
  if (!rereduce) {
    for (i in keys) {
      if (result[keys[i]]) {
        result[keys[i]] += values[i];
        numres[keys[i]] += 1;
      } else {
        result[keys[i]] = values[i];
        numres[keys[i]] = 1;
      }
    }
  } else {
    for each(value in values) {
      for (i in value) {
        if (result[i]) {
          result[i] += value[i];
          rumres[i] += 1;
        } else {
          result[i] = value[i];
          numres[i] = 1;
        }
      }
    }
  }
  var r = {};
  for (k in result) {
    r[k] = result[k] / numres[k];
  }
  
  return r;
}
