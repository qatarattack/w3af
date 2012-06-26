'''
test_spiderman.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''
import threading
import time
import urllib2

from nose.plugins.skip import Skip, SkipTest

from ..helper import PluginTest, PluginConfig

BROWSE_URLS = (
               ('GET', 'http://moth/w3af/discovery/spiderMan/javascriptredirect.html', None),
               ('GET', 'http://moth/w3af/audit/sql_injection/select/sql_injection_integer.php', 'id=1'),
               ('POST', 'http://moth/w3af/discovery/spiderMan/data_receptor_js.php', 'user=abc'),
              )

TERMINATE_URL = (
                 ('GET', 'http://127.7.7.7/spiderMan', 'terminate'),
                 )

class BrowserThread(threading.Thread):
    
    def __init__(self):
        super(BrowserThread, self).__init__()
        self.responses = []
        
    def run(self):
        '''
        @see: Comment in test_spiderman_basic
        '''
        time.sleep(5.0)
        
        proxy_support = urllib2.ProxyHandler({'http': 'http://127.0.0.1:44444/'})
        opener = urllib2.build_opener(proxy_support)
        # Avoid this, it might influence other tests!
        #urllib2.install_opener(opener)
        
        all_urls = BROWSE_URLS + TERMINATE_URL
        
        for method, url, payload in all_urls:
            if method == 'POST':
                req = urllib2.Request(url, payload)
                response = opener.open(req)           
            else:
                if payload is None:
                    full_url = url
                else:
                    full_url = url + '?' + payload
                response = opener.open(full_url)
            
            self.responses.append(response.read())
            
        
class TestSpiderman(PluginTest):
    
    base_url = 'http://moth/'
    
    _run_configs = {
        'cfg': {
            'target': base_url,
            'plugins': {'discovery': (PluginConfig('spiderMan'),)}
            }
        }
    
    def test_spiderman_basic(self):
        '''
        The difficult thing with this test is that the scan will block until
        we browse through the spiderMan proxy to the spiderMan.TERMINATE_URL,
        so we need to start a "browser thread" that will sleep for a couple
        of seconds before browsing through the proxy.
        
        The first assert will be performed between the links that we browse 
        and the ones returned by the plugin to the core.
        
        The second assert will check that the proxy actually returned the expected
        HTTP response body to the browser.
        '''
        bt = BrowserThread()
        bt.start()
        
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        
        # Fetch all the results
        bt.join()
        kb_urls = self.kb.getData('urls', 'url_objects')
        responses = bt.responses
        
        EXPECTED_RESPONSE_CONTENTS = (
                                      '<title>Test spiderMan features</title>',
                                      '<b>Phone:</b> 47789900',
                                      'Welcome, abc!',
                                      'spiderMan plugin finished its execution.',
                                      )
        
        #
        #    First set of assertions
        #
        for index, e_response in enumerate(EXPECTED_RESPONSE_CONTENTS):
            self.assertTrue(e_response in responses[index], responses[index])

        #
        #    Second set of assertions
        #        
        kb_urls = [u.uri2url().url_string for u in kb_urls]
        for _, e_url, _ in BROWSE_URLS:
            self.assertTrue(e_url in kb_urls)

    def test_https(self):
        raise SkipTest('FIXME: Need to add this test.')