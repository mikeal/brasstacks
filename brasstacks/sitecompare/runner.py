# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Corporation Code.
#
# The Initial Developer of the Original Code is
# Mikeal Rogers.
# Portions created by the Initial Developer are Copyright (C) 2008
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#  Mikeal Rogers <mikeal.rogers@gmail.com>
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

import os, sys
import math
import operator
import copy
from distutils import dir_util
from datetime import datetime
from time import sleep
from PIL import Image, ImageChops
from optparse import OptionParser

copytree = dir_util.copy_tree

import httplib2
import couchquery
import jsbridge
import mozrunner

test_all_sites = {
        # "myspace": "http://www.myspace.com", # Frame Buster
        # "rapidshare": "http://rapidshare.com", # Frame Buster
        "busted": "http://miketaylr.com/test/block_anchors.html",
        "google": "http://www.google.com",
        "yahoo": "http://www.yahoo.com",            
        "wikipedia": "http://en.wikipedia.org/wiki/Main_Page",
        "ebay": "http://www.ebay.com",
        "google-china": "http://www.google.cn",
        "fc2": "http://fc2.com",
        "craigslist": "http://www.craigslist.com",
        "hi5": "http://www.hi5.com",
        "mail-ru": "http://www.mail.ru",
        "aol": "http://www.aol.com",
        "flickr": "http://www.flickr.com",
        "amazon": "http://www.amazon.com",
        "google-jp": "http://www.google.co.jp",
        "doubleclick": "http://www.doubleclick.com",
        "photobucket": "http://www.photobucket.com",
        "orkut": "http://orkut.com.br",
        "twitter": "http://www.twitter.com",
        "youtube": "http://www.youtube.com",
        "facebook": "http://www.facebook.com",
        "windows-live": "http://live.com",
        "msn": "http://www.msn.com",
        "blogger": "http://blogger.com",
        "baidu": "http://baidu.com",
        "qq": "http://qq.com",
        "microsoft": "http://www.microsoft.com",
        "sina": "http://sina.com.cn",
        "google.fr": "http://google.fr",
        "wordpress": "http://www.wordpress.com",
        }

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
    def __init__(self, runner1, runner2, report, comparison_info, all_sites=None, store=True, db=None):
        self.runner1 = runner1; self.runner2 = runner2
        self.report = report; 
        self.base_directory = os.path.abspath(os.path.dirname(__file__))
        self.finished = False
        
        self.db = db
        
        if all_sites is None:
            rows = self.db.views.sitecompare.pageByURI().rows
            self.all_sites = dict([(r._id, r.uri,) for r in rows if not hasattr(r, 'enabled') or r.enabled ])
        else:
            self.all_sites = all_sites
        self.saved_release_images = []
        self.saved_nightly_images = []
        self.store = store
        
        self.comparison_info = comparison_info
        
    def start(self):
        self.runner1.start()
        self.runner2.start()
        
        self.back_channel1, self.bridge1 = jsbridge.wait_and_create_network('127.0.0.1', 24242)
        self.back_channel2, self.bridge2 = jsbridge.wait_and_create_network('127.0.0.1', 24243)
        self.back_channel1.add_listener(self.save_release_listener,
                                        eventType='sitecompare.save')
        self.back_channel2.add_listener(self.save_nightly_listener, 
                                        eventType='sitecompare.save')
        
        self.back_channel1.add_listener(self.framebust_listener,
                                        eventType='sitecompare.framebust')
        self.back_channel2.add_listener(self.framebust_listener, 
                                        eventType='sitecompare.framebust')
        
        self.back_channel1.add_listener(self.timeout_listener,
                                        eventType='sitecompare.timeout')
        self.back_channel2.add_listener(self.timeout_listener, 
                                        eventType='sitecompare.timeout')
                                        
        # def gl(name, obj):
        #     print 'gl', name, obj
        # self.back_channel1.add_global_listener(gl)
        sleep(5)
        
        js = "Components.utils.import('resource://sitecompare/modules/compare.js')"
        self.c1 = jsbridge.JSObject(self.bridge1, js)
        self.c2 = jsbridge.JSObject(self.bridge2, js)
        
        if self.store:
            self.build1 = self.get_build(self.bridge1)
            self.build2 = self.get_build(self.bridge2)
            run = {"type":"comparison-run", "allsites":self.all_sites, 
                   "starttime":datetime.now().isoformat(), "status":"running"}
            run.update(self.comparison_info)
            run['release_buildid'] = self.build1.buildid
            run['release_docid'] = self.build1._id
            run['release_buildstring'] = self.build1.productType+'-'+self.build1['appInfo.platformVersion']+'-'+self.build1.buildid
            run['nightly_buildid'] = self.build2.buildid

            run['nightly_docid'] = self.build2._id
            run['nightly_buildstring'] = self.build2.productType+'-'+self.build2['appInfo.platformVersion']+'-'+self.build2.buildid
            
            self.run_info = self.db.create(run)
        else:
            import uuid
            self.run_info = {"id":str(uuid.uuid1())}
                     
        self.directory = os.path.join(self.base_directory, 'static', 'runs', self.run_info['id'])
        os.mkdir(self.directory)
        
        
        self.do_all_images()
        
        if self.store:
            obj = self.db.get(self.run_info['id'])
            obj = self.db.get(self.run_info['id'])
            obj['endtime'] = datetime.now().isoformat()
            obj['status'] = "done"
            self.db.update(dict(obj))
    
    def get_build(self, bridge):    
        appInfo = jsbridge.JSObject(bridge, appInfoJs)
        buildid = appInfo.appBuildID
        query = self.db.views.sitecompare.firefoxByBuildid(startkey=buildid, endkey=buildid+"0")
        if len(query.rows) is 0:
            build = {}
            build['appInfo.id'] = str(appInfo.ID)
            build['type'] = 'productBuild'
            build['productType'] = 'firefox'
            build['buildid'] = str(appInfo.appBuildID)
            build['appInfo.platformVersion'] = appInfo.platformVersion
            build['appInfo.platformBuildID'] = appInfo.platformBuildID
            if self.store:
                build = self.db.get(self.db.create(build)['id'])
            return build
        else:
            return query.rows[0]
        
    def save_nightly_listener(self, obj):
        self.saved_nightly_images.append(obj)
    def save_release_listener(self, obj):
        self.saved_release_images.append(obj)
    
    framebusters = []
    def framebust_listener(self, uri):
        self.framebusters.append(uri)
    
    timeouts = []
    def timeout_listener(self, uri):
        self.timeouts.append(uri)
        
    def test_uri(self, name, uri):
        filename = os.path.join(self.directory, name)
        file1 = filename+'.runner1.png'
        file2 = filename+'.runner2.png'
        self.c1.doURI(uri, file1)
        self.c2.doURI(uri, file2)

        while ( file1 not in self.saved_release_images and file2 not in self.saved_nightly_images ) and (
                uri not in self.framebusters) and (uri not in self.timeouts):
            sleep(1)
        if (uri in self.framebusters):
            print "FrameBusted "+uri
            return
        if (uri in self.timeouts):
            print "Timeout "+uri
            return
            
        rms = None
        while rms is None:
            try:
                rms, image1, image2, hist1, hist2 = diff_images(file1, file2)
            except:
                print 'Image is not ready, waiting 10 seconds.'
                sleep(10)
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
            print 'testing '+site
            result = self.test_uri(name, site)
            if result is not None:
                obj = {"type":"comparison-test", "page-id":name, "uri":site, 
                       "run-id":self.run_info['id'], "result":result,
                       "timestamp":datetime.now().isoformat()}
                obj.update(self.comparison_info)
                if self.store:
                    try:
                        self.db.create(obj)
                    except Exception, e:
                        print "Exception while creating result object ", e
                print site, 'differs by ', str(result['difference'])
            else:
                print "test_uri() returned none, likely due to framebust or timeout"
    
    def stop(self):
        sleep(3)
        self.runner1.stop()
        self.runner2.stop()    

class CLI(object):
    parser = OptionParser()
    parser.add_option("-b", "--binary1", dest="binary1",
                      help="The latest release binary.")
    parser.add_option("-B", "--binary2", dest="binary2",
                      help="The next release binary.")
    parser.add_option("-p", "--profile1", dest="profile1", default=None,
                      help="The latest release default profile.")
    parser.add_option("-P", "--profile2", dest="profile2", default=None,
                      help="The next release default profile.")
    parser.add_option("-r", "--report", dest="report", default=None,
                      help="URI for report server.")
    parser.add_option("-t", "--test", dest="test", default=False, action="store_true",
                       help="Run the test dataset")
    
    run_info = {'runner1_name':'release', 'runner2_name':'nightly', 'comparison_type':'releaseVSnightly'}
    
    jsbridge_port = 24242
    
    def get_runner_and_profile(self, binary, default_profile, profile_class=mozrunner.FirefoxProfile,
                                                              runner_class=mozrunner.FirefoxRunner):
        if default_profile:
            profile = profile_class(default_profile=default_profile)
        else: 
            profile = None
            runner_class.profile_class = profile_class
        runner = runner_class(binary=binary, profile=profile,
                              cmdargs=['-jsbridge', str(self.jsbridge_port)])
        self.jsbridge_port += 1
        
        # Install necessary plugins
        base_path = os.path.dirname(__file__)
        runner.profile.install_plugin(jsbridge.extension_path)
        runner.profile.install_plugin(extension_path)
        runner.profile.install_plugin(os.path.join(base_path, 'adblock_plus-1.0.2-fx+sm+tb.xpi'))
        copytree(os.path.join(base_path, 'adblockplus'), 
                 os.path.join(runner.profile.profile, 'adblockplus'))
        return runner, profile
    
    def get_runners(self):
        runner1, profile1 = self.get_runner_and_profile(self.options.binary1, self.options.profile1)
        runner2, profile2 = self.get_runner_and_profile(self.options.binary2, self.options.profile2)
        return runner1, runner2, profile1, profile2
    
    def run(self):
        (options, args) = self.parser.parse_args()
        self.options = options; self.args = args
        runner1, runner2, profile1, profile2 = self.get_runners()
        
        if sys.platform == 'linux2':
            try:
                from Xlib import X, display
                d = display.Display()
                s = d.screen()
                root = s.root
                root.warp_pointer(0,0)
                d.sync()
            except ImportError:
                print "Xlib is not installed. Mouse may interfere with screenshots."
            
        
        if options.test is True:
            all_sites = test_all_sites
            store = False
        else:
            all_sites = None
            store = True

        if options.report is None:
            db = couchquery.CouchDatabase("http://127.0.0.1:5984/sitecompare")
        else:
            if '@' in options.report:
                user, password = options.report.strip('http://').split('@')[0].split(':')
                url = 'http://'+options.report.split('@')[1]
                http = httplib2.Http('.cache')
                http.add_credentials(user, password)
                db = couchquery.CouchDatabase(url, http=http)
            else: db = couchquery.CouchDatabase(options.report)

        c = CompareSites(runner1, runner2, options.report, self.run_info, all_sites=all_sites, store=store, db=db)
        c.start()

        sleep(2)
        c.stop()
        sleep(3)

class Html4Profile(mozrunner.FirefoxProfile):
    preferences = copy.copy(mozrunner.FirefoxProfile.preferences)
    preferences['html5.enable'] = False

class Html5Profile(mozrunner.FirefoxProfile):
    preferences = copy.copy(mozrunner.FirefoxProfile.preferences)
    preferences['html5.enable'] = True

class Html4v5CLI(CLI):
    parser = OptionParser()
    parser.add_option("-b", "--binary", dest="binary",
                      help="Firefox binary.")
    parser.add_option("-p", "--profile", dest="profile", default=None,
                      help="Firefox default profile.")
    parser.add_option("-r", "--report", dest="report", default=None,
                      help="URI for report server.")
    parser.add_option("-t", "--test", dest="test", default=False, action="store_true",
                       help="Run the test dataset")
                       
    run_info = {"runner1_name":"html4", "runner2_name":"html5", "comparison_type":"html4VShtml5"}
    def get_runners(self):
        runner1, profile1 = self.get_runner_and_profile(self.options.binary, self.options.profile,
                                                        profile_class=Html4Profile)
        runner2, profile2 = self.get_runner_and_profile(self.options.binary, self.options.profile,
                                                        profile_class=Html5Profile)

        return runner1, runner2, profile1, profile2
        
def cli():
    CLI().run()

def html4v5():
    Html4v5CLI().run()

# def cli():
#     parser = OptionParser()
#     parser.add_option("-b", "--binary1", dest="binary1",
#                       help="The latest release binary.")
#     parser.add_option("-B", "--binary2", dest="binary2",
#                       help="The next release binary.")
#     parser.add_option("-p", "--profile1", dest="profile1", default=None,
#                       help="The latest release default profile.")
#     parser.add_option("-P", "--profile2", dest="profile2", default=None,
#                       help="The next release default profile.")
#     parser.add_option("-r", "--report", dest="report", default=None,
#                       help="URI for report server.")
#     parser.add_option("-t", "--test", dest="test", default=False, action="store_true",
#                        help="Run the test dataset")
#     
#     (options, args) = parser.parse_args()
#     
#     if options.profile1:
#         profile1 = mozrunner.FirefoxProfile(default_profile=options.profile1)
#     else: profile1 = None
#     if options.profile2:
#         profile2 = mozrunner.FirefoxProfile(default_profile=options.profile2)
#     else: profile2 = None
# 
#     base_path = os.path.dirname(__file__)
#     
#     runner1 = mozrunner.FirefoxRunner(binary=options.binary1, profile=profile1, 
#                                       cmdargs=['-jsbridge', '24242'])
#     runner2 = mozrunner.FirefoxRunner(binary=options.binary2, profile=profile2,
#                                       cmdargs=['-jsbridge', '24243'])
#     
#     runner1.profile.install_plugin(jsbridge.extension_path)
#     runner2.profile.install_plugin(jsbridge.extension_path) 
#     
#     runner1.profile.install_plugin(extension_path)
#     runner2.profile.install_plugin(extension_path)  
#     
#     runner1.profile.install_plugin(os.path.join(base_path, 'adblock_plus-1.0.2-fx+sm+tb.xpi'))
#     runner2.profile.install_plugin(os.path.join(base_path, 'adblock_plus-1.0.2-fx+sm+tb.xpi'))
#     
#     copytree(os.path.join(base_path, 'adblockplus'), 
#              os.path.join(runner1.profile.profile, 'adblockplus'))
#     copytree(os.path.join(base_path, 'adblockplus'), 
#              os.path.join(runner2.profile.profile, 'adblockplus'))
#     
#     if options.test is True:
#         all_sites = test_all_sites
#         store = False
#     else:
#         all_sites = None
#         store = True
#     
#     if options.report is None:
#         db = couchquery.CouchDatabase("http://127.0.0.1:5984/sitecompare")
#     else:
#         if '@' in options.report:
#             user, password = options.report.strip('http://').split('@')[0].split(':')
#             url = 'http://'+options.report.split('@')[1]
#             http = httplib2.Http('.cache')
#             http.add_credentials(user, password)
#             db = couchquery.CouchDatabase(url, http=http)
#         else: db = couchquery.CouchDatabase(options.report)
#     
#     c = CompareSites(runner1, runner2, options.report, all_sites=all_sites, store=store, db=db)
#     c.start()
#     
#     sleep(2)
#     c.stop()
#     sleep(3)