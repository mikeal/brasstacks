#!/usr/bin/env python
import tempfile
import os
import math
import operator
import shutil
from distutils import dir_util
from datetime import datetime
from time import sleep
from PIL import Image, ImageChops
from optparse import OptionParser

copytree = dir_util.copy_tree

import couchquery
import jsbridge
import mozrunner

db = couchquery.CouchDatabase("http://127.0.0.1:5984/brasstacks")

parent_path = os.path.abspath(os.path.dirname(__file__))
extension_path = os.path.join(parent_path, 'extension')

appInfoJs = "Components.classes['@mozilla.org/xre/app-info;1'].getService(Components.interfaces.nsIXULAppInfo)"

def diff_images(file1, file2):
    """Image diff code from http://snipplr.com/view/757/compare-two-pil-images-in-python/"""
    image1, image2 = Image.open(file1), Image.open(file2)
    h1, h2 = image1.histogram(), image2.histogram()
    if image1.size != image2.size:
        raise Exception('Image sizes do not match! image1 :: '+str(image1.size)+', image2 :: '+str(image2.size))
    rms = math.sqrt(reduce(operator.add, map(lambda a,b: (a-b)**2, h1, h2))/len(h1))
    return ( rms, image1, image2, h1, h2, )

class CompareSites(object):
    def __init__(self, runner1, runner2, report):
        self.runner1 = runner1; self.runner2 = runner2
        self.report = report; 
        self.base_directory = os.path.abspath(os.path.dirname(__file__))
        self.finished = False
        
        rows = db.views.sitecompare.pageByURI().rows
        self.all_sites = dict([(r._id, r.uri,) for r in rows if not hasattr(r, 'enabled') or r.enabled ])
        
        # self.all_sites = {
        #     "google": "http://www.google.com",
        #     "yahoo": "http://www.yahoo.com",            
        #     "wikipedia": "http://en.wikipedia.org/wiki/Main_Page",
        #     "ebay": "http://www.ebay.com",
        #     "google-china": "http://www.google.cn",
        #     "fc2": "http://fc2.com",
        #     "craigslist": "http://www.craigslist.com",
        #     "hi5": "http://www.hi5.com",
        #     "mail-ru": "http://www.mail.ru",
        #     "aol": "http://www.aol.com",
        #     "flickr": "http://www.flickr.com",
        #     "amazon": "http://www.amazon.com",
        #     "google-jp": "http://www.google.co.jp",
        #     "doubleclick": "http://www.doubleclick.com",
        #     "photobucket": "http://www.photobucket.com",
        #     "orkut": "http://orkut.com.br",
        #     "twitter": "http://www.twitter.com",
        #     "youtube": "http://www.youtube.com",
        #     "facebook": "http://www.facebook.com",
        #     "windows-live": "http://live.com",
        #     "msn": "http://www.msn.com",
        #     "blogger": "http://blogger.com",
        #     "baidu": "http://baidu.com",
        #     "qq": "http://qq.com",
        #     "microsoft": "http://www.microsoft.com",
        #     # "sina": "http://sina.com.cn",
        #     "rapidshare": "http://rapidshare.com",
        #     "google.fr": "http://google.fr",
        #     "wordpress": "http://www.wordpress.com",
        #     }
            
        self.saved_release_images = []
        self.saved_nightly_images = []
        
    def start(self):
        self.runner1.start()
        self.runner2.start()
        
        self.back_channel1, self.bridge1 = jsbridge.wait_and_create_network('127.0.0.1', 24242)
        self.back_channel2, self.bridge2 = jsbridge.wait_and_create_network('127.0.0.1', 24243)
        self.back_channel1.add_listener(self.save_release_listener,
                                        eventType='sitecompare.save')
        self.back_channel2.add_listener(self.save_nightly_listener, 
                                        eventType='sitecompare.save')
                                        
        # def gl(name, obj):
        #     print 'gl', name, obj
        # self.back_channel1.add_global_listener(gl)
        sleep(5)
        
        self.build1 = self.get_build(self.bridge1)
        self.build2 = self.get_build(self.bridge2)
        
        js = "Components.utils.import('resource://sitecompare/modules/compare.js')"
        self.c1 = jsbridge.JSObject(self.bridge1, js)
        self.c2 = jsbridge.JSObject(self.bridge2, js)
        
        run = {"type":"comparison-run", "allsites":self.all_sites, 
               "starttime":datetime.now().isoformat(), "status":"running"}
        
        self.run_info = db.create(run)         
        self.directory = os.path.join(self.base_directory, 'static', 'runs', self.run_info['id'])
        os.mkdir(self.directory)
        
        self.do_all_images()
        
        obj = db.get(self.run_info['id'])
        obj['release_buildid'] = self.build1.buildid
        obj['release_docid'] = self.build1._id
        obj['release_buildstring'] = self.build1.productType+'-'+self.build1['appInfo.platformVersion']+'-'+self.build1.buildid
        obj['nightly_buildid'] = self.build2.buildid
        
        obj['nightly_docid'] = self.build2._id
        obj['nightly_buildstring'] = self.build2.productType+'-'+self.build2['appInfo.platformVersion']+'-'+self.build2.buildid
        obj['endtime'] = datetime.now().isoformat()
        obj['status'] = "done"
        db.update(dict(obj))
    
    def get_build(self, bridge):    
        appInfo = jsbridge.JSObject(bridge, appInfoJs)
        buildid = appInfo.appBuildID
        query = db.views.sitecompare.firefoxByBuildid(startkey=buildid, endkey=buildid+"0")
        if len(query.rows) is 0:
            build = {}
            build['appInfo.id'] = str(appInfo.ID)
            build['type'] = 'productBuild'
            build['productType'] = 'firefox'
            build['buildid'] = str(appInfo.appBuildID)
            build['appInfo.platformVersion'] = appInfo.platformVersion
            build['appInfo.platformBuildID'] = appInfo.platformBuildID
            return db.get(db.create(build)['id'])
        else:
            return query.rows[0]
        
    def save_nightly_listener(self, obj):
        self.saved_nightly_images.append(obj)
    def save_release_listener(self, obj):
        self.saved_release_images.append(obj)
        
    def test_uri(self, name, uri):
        filename = os.path.join(self.directory, name)
        file1 = filename+'.release.png'
        file2 = filename+'.nightly.png'
        self.c1.doURI(uri, file1)
        self.c2.doURI(uri, file2)

        while file1 not in self.saved_release_images and file2 not in self.saved_nightly_images:
            sleep(1)
        try:
            rms, image1, image2, hist1, hist2 = diff_images(file1, file2)
        except:
            sleep(120)
            try:
                rms, image1, image2, hist1, hist2 = diff_images(file1, file2)
            except:
                print "Images for "+uri+" weren't created."
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
            
            ImageChops.add(image1, image2).save(filename+'.diff.add.png')
            result["diff_add_image"] = filename+'.diff.add.png'
            
            ImageChops.subtract(image1RGB, image2RGB).save(filename+'.diff.subtract.png')
            result["diff_subtract_image"] = filename+'.diff.subtract.png'
            
            ImageChops.lighter(image1, image2).save(filename+'.diff.lighter.png')
            result["diff_lighter_image"] = filename+'.diff.lighter.png'
            
            ImageChops.darker(image1, image2).save(filename+'.diff.darker.png')
            result["diff_darker_image"] = filename+'.diff.darker.png'
        else:
            result["images_differ"] = False
        return result
        
    def do_all_images(self):
        for name, site in self.all_sites.items():
            result = self.test_uri(name, site)
            obj = {"type":"comparison-test", "page-id":name, "uri":site, 
                   "run-id":self.run_info['id'], "result":result,
                   "timestamp":datetime.now().isoformat()}
            db.create(obj)
            print site, 'differs by ', str(result['difference'])
    
    def stop(self):
        sleep(3)
        self.runner1.stop()
        self.runner2.stop()    

def cli():
    parser = OptionParser()
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

    base_path = os.path.dirname(__file__)
    
    runner1 = mozrunner.FirefoxRunner(binary=options.binary1, profile=profile1, 
                                      cmdargs=['-jsbridge', '24242'])
    runner2 = mozrunner.FirefoxRunner(binary=options.binary2, profile=profile2,
                                      cmdargs=['-jsbridge', '24243'])
    
    runner1.profile.install_plugin(jsbridge.extension_path)
    runner2.profile.install_plugin(jsbridge.extension_path) 
    
    runner1.profile.install_plugin(extension_path)
    runner2.profile.install_plugin(extension_path)  
    
    runner1.profile.install_plugin(os.path.join(base_path, 'adblock_plus-1.0.2-fx+sm+tb.xpi'))
    runner2.profile.install_plugin(os.path.join(base_path, 'adblock_plus-1.0.2-fx+sm+tb.xpi'))
    
    copytree(os.path.join(base_path, 'adblockplus'), 
             os.path.join(runner1.profile.profile, 'adblockplus'))
    copytree(os.path.join(base_path, 'adblockplus'), 
             os.path.join(runner2.profile.profile, 'adblockplus'))
    
    c = CompareSites(runner1, runner2, options.report)
    c.start()
    
    sleep(2)
    c.stop()
    sleep(3)
    
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
    sleep(5)
    c.doURI('http://http://en.wikipedia.org/wiki/Main_Page', '/Users/mikeal/Desktop/screenshot2.png')
    sleep(5)
    try:
        runner.wait()
    except KeyboardInterrupt:
        runner.stop()


if __name__ == "__main__":
    cli()

