var EXPORTED_SYMBOLS = ["setTimeout", "clearTimeout"];

__timerData = {
  nextID: Math.floor(Math.random() * 100) + 1,
  timers: {}
};

__TimerCallback = function __TimerCallback(callback) {
  Components.utils.import("resource://gre/modules/XPCOMUtils.jsm");

  this._callback = callback;
  this.QueryInterface = XPCOMUtils.generateQI([Components.interfaces.nsITimerCallback]);
};
__TimerCallback.prototype = {
  notify : function notify(timer) {
    for(timerID in __timerData.timers) {
      if(__timerData.timers[timerID] == timer) {
        delete __timerData.timers[timerID];
        break;
      }
    }
    this._callback();
  }
};

var setTimeout = function (callback, delay) {
  var classObj = Components.classes["@mozilla.org/timer;1"];
  var timer = classObj.createInstance(Components.interfaces.nsITimer);
  var timerID = __timerData.nextID;
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
