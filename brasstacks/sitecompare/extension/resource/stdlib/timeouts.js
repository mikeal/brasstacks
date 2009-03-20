var setTimeout = function (callback, delay) {
  var classObj = Components.classes["@mozilla.org/timer;1"];
  var timer = classObj.createInstance(Components.interfaces.nsITimer);
  var timerID = __stdlibholder.__timerData.nextID;
  // emulate window.setTimeout() by incrementing next ID by random amount
  __timerData.nextID += Math.floor(Math.random() * 100) + 1;
  __timerData.timers[timerID] = timer;

  timer.initWithCallback(new __TimerCallback(callback),
                         delay,
                         classObj.TYPE_ONE_SHOT);
  return timerID;
};

var clearTimeout = function (timerID) {
  if(!(timerID in __stdlibholder.__timerData.timers))
    return;
  var timer = __stdlibholder.__timerData.timers[timerID];
  timer.cancel();
  delete __stdlibholder.__timerData.timers[timerID];
};
