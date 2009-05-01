import tempfile
import os
import math
import operator
from time import sleep
from PIL import Image, ImageChops
from optparse import OptionParser

import jsbridge
import mozrunner

parent_path = os.path.abspath(os.path.dirname(__file__))
extension_path = os.path.join(parent_path, 'extension')

def diff_images(file1, file2):
    """Image diff code from http://snipplr.com/view/757/compare-two-pil-images-in-python/"""
    image1, image2 = Image.open(file1), Image.open(file2)
    h1, h2 = image1.histogram(), image2.histogram()
    if image1.size != image2.size:
        raise Exception('Image sizes do not match! image1 :: '+str(image1.size)+', image2 :: '+str(image2.size))
    rms = math.sqrt(reduce(operator.add, map(lambda a,b: (a-b)**2, h1, h2))/len(h1))
    return ( rms, image1, image2, h1, h2, )

class CompareSites(object):
    def __init__(self, runner1, runner2, report, directory):
        self.runner1 = runner1; self.runner2 = runner2
        self.report = report; self.directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            os.mkdir(directory)
        self.finished = False
        
        self.all_sites = {"yahoo":"http://www.yahoo.com", "google":"http://www.google.com"}
        
    def start(self):
        self.runner1.start()
        self.runner2.start()
        
        self.back_channel1, self.bridge1 = jsbridge.wait_and_create_network('127.0.0.1', 24242)
        self.back_channel2, self.bridge2 = jsbridge.wait_and_create_network('127.0.0.1', 24243)
        
        js = "Components.utils.import('resource://sitecompare/modules/compare.js')"
        self.c1 = jsbridge.JSObject(self.bridge1, js)
        self.c2 = jsbridge.JSObject(self.bridge2, js) 
        
        sleep(5)
        self.do_all_images()
        
    def test_uri(self, name, uri):
        filename = os.path.join(self.directory, name)
        file1 = filename+'.release.png'
        file2 = filename+'.nightly.png'
        self.c1.doURI(uri, file1)
        self.c2.doURI(uri, file2)
        sleep(5)
        rms, image1, image2, hist1, hist2 = diff_images(file1, file2)
        result = {"uri":uri, "release_image":file1, "nightly_image":file2, "difference":rms}
        if rms  != 0:
            result["images_differ"] = True
            image1RGB = image1.convert('RGB')
            image2RGB = image2.convert('RGB')
            
            ImageChops.difference(image1RGB, image2RGB).save(filename+'.diff.difference.png')
            result["diff_difference_image"] = filename+'.diff.difference.png'
            
            ImageChops.multiply(image1, image2).save(filename+'.diff.multiply.png')
            result["diff_multiply_image"] = filename+'.diff.multiply.png'
            
            ImageChops.screen(image1, image2).save(filename+'.diff.screen.png')
            result["diff_screen_image"] = filename+'.diff.screen.png'
            
            ImageChops.add(image1, image2).save(filename+'diff.add.png')
            result["diff_add_image"] = filename+'.diff.add.png'
            
            ImageChops.subtract(image1RGB, image2RGB).save(filename+'diff.subtract.png')
            result["diff_subtract_image"] = filename+'.diff.subtract.png'
            
            ImageChops.lighter(image1, image2).save(filename+'diff.lighter.png')
            result["diff_lighter_image"] = filename+'.diff.lighter.png'
            
            ImageChops.darker(image1, image2).save(filename+'diff.darker.png')
            result["diff_darker_image"] = filename+'.diff.darker.png'
        else:
            result["images_differ"] = False
        return result
        
    def do_all_images(self):
        for name, site in self.all_sites.items():
            self.test_uri(name, site)
    
    def stop(self):
        sleep(3)
        self.runner1.stop()
        self.runner2.stop()    

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
    if options.directory is None:
        raise Exception("Must specify directory for tests to be saved to.")
    c = CompareSites(runner1, runner2, options.report, options.directory)
    c.start()
    
    sleep(2)
    c.stop()
    
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
    cli()

