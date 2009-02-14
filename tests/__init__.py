import brasstacks
import threading

def setup_module(module):
    module.httpd = brasstacks.setup()
    module.thread = threading.Thread(target=httpd.start)
    module.thread.start()
    
def teardown_module(module):
    while module.thread.isAlive():
        module.httpd.stop()