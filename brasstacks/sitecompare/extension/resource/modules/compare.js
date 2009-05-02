var EXPORTED_SYMBOLS = ["getActiveTab", "currentURI", "doURI", 
                        "saveDirectory", "URI", "PATH", "sleep"];

var hwindow = Components.classes["@mozilla.org/appshell/appShellService;1"]
                .getService(Components.interfaces.nsIAppShellService)
                .hiddenDOMWindow;
var aConsoleService = Components.classes["@mozilla.org/consoleservice;1"].
     getService(Components.interfaces.nsIConsoleService);
     
var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"]
          .getService(Components.interfaces.nsIWindowMediator);

function sleep (milliseconds) {
  var self = {};

  // We basically just call this once after the specified number of milliseconds
  function wait() {
    self.timeup = true;
  }

  // Calls repeatedly every X milliseconds until clearInterval is called
  var interval = hwindow.setInterval(wait, milliseconds);

  var thread = Components.classes["@mozilla.org/thread-manager;1"]
            .getService()
            .currentThread;
  // This blocks execution until our while loop condition is invalidated.  Note
  // that you must use a simple boolean expression for the loop, a function call
  // will not work.
  while(!self.timeup)
    thread.processNextEvent(true);
  hwindow.clearInterval(interval);

  return true;
}

function getActiveTab() {
  var browserWindow = wm.getMostRecentWindow("navigator:browser");
  return browserWindow.gBrowser.selectedBrowser.contentDocument;
}

currentURI = null;

saveDirectory = null;

URI = null;
PATH = null;

function doURI(uri, path) {
  currentURI = uri;
  URI = uri;
  PATH = path;
  getActiveTab().location.href = "chrome://sitecompare/content/index.html";
}

var browserWindow = wm.getMostRecentWindow("navigator:browser");
browserWindow.getBrowser().selectedTab = browserWindow.getBrowser().addTab("about:blank");
