import tempfile
import os
from time import sleep
from optparse import OptionParser

import jsbridge
import mozrunner

parent_path = os.path.abspath(os.path.dirname(__file__))
extension_path = os.path.join(parent_path, 'extension')

class CompareSites(object):
    def __init__(self, runner1, runner2, report, directory):
        self.runner1 = runner1; self.runner2 = runner2
        self.report = report; self.directory = directory
        self.finished = False
    def start(self):
        self.runner1.start()
        self.runner2.start()
        
        self.back_channel1, self.bridge1 = jsbridge.wait_and_create_network('127.0.0.1', 24242)
        self.back_channel2, self.bridge2 = jsbridge.wait_and_create_network('127.0.0.1', 24243)
        
        js = "Components.utils.import('resource://sitecompare/modules/compare.js')"
        self.c1 = jsbridge.JSObject(self.bridge1, js)
        self.c2 = jsbridge.JSObject(self.bridge2, js) 
        self.tempdir = tempfile.mkdtemp()
        sleep(5)
        
    def test_uri(self, uri):
        filename = os.path.join(self.tempdir, uri.split('?')[0])
        file1 = self.c1.doURI(uri, filename+'.release.png')
        file2 = self.c2.doURI(uri, fileanem+'.nightly.png')
        
        

def cli():
    parser = OptionParser()
    parser.add_option("-d", "--directory", dest="directory",
                      help="Save directory.")
    parser.add_option("-b", "--binary1", dest="binary1",
                      help="The latest release binary.")
    parser.add_option("-B", "--binary2", dest="binary2",
                      help="The next release binary.")
    parser.add_option("-p", "--profile1", dest="profile1", default=None,
                      help="The latest release default profile.")
    parser.add_option("-P", "--profile2", dest="profile2", default=None,
                      help="The next release default profile.")
    parser.add_option("-r", "--report", dest="report",
                      help="URI for report server.")
    
    (options, args) = parser.parse_args()
    
    if options.profile1:
        profile1 = mozrunner.FirefoxProfile(default_profile=options.profile1)
    else: profile1 = None
    if options.profile2:
        profile2 = mozrunner.FirefoxProfile(default_profile=options.profile2)
    else: profile2 = None
    
    runner1 = mozrunner.FirefoxRunner(binary=options.binary1, profile=profile1, 
                                      cmdargs=['-jsbridge', '24242'])
    runner2 = mozrunner.FirefoxRunner(binary=options.binary2, profile=profile2,
                                      cmdargs=['-jsbridge', '24243'])
    
    runner1.profile.install_plugin(jsbridge.extension_path)
    runner2.profile.install_plugin(jsbridge.extension_path) 
    
    runner1.profile.install_plugin(extension_path)
    runner2.profile.install_plugin(extension_path)  
    
    c = CompareSites(runner1, runner2, options.report, options.directory)
    c.start()
    
    
def test():
    runner = mozrunner.FirefoxRunner(binary='/Applications/Shiretoko.app',  cmdargs=['-jsbridge', '24242'])
    runner.profile.install_plugin(jsbridge.extension_path)
    runner.profile.install_plugin(extension_path)
    runner.profile.install_plugin('/Users/mikeal/tmp/xush')
    runner.start()
    
    back_channel, bridge = jsbridge.wait_and_create_network('127.0.0.1', 24242)
    sleep(3)
    js = "Components.utils.import('resource://sitecompare/modules/compare.js')"
    c = jsbridge.JSObject(bridge, js)
    sleep(3)
    c.doURI('http://www.google.com', '/Users/mikeal/Desktop/screenshot.png')
    sleep(5)
    c.doURI('http://www.yahoo.com', '/Users/mikeal/Desktop/screenshot2.png')
    sleep(5)
    try:
        runner.wait()
    except KeyboardInterrupt:
        runner.stop()


if __name__ == "__main__":
    test()

