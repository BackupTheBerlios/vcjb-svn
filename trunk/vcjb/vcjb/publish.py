# -*- coding: utf-8 -*-
""" main application source """ 
__revision__ = "$Rev: 7 $"


import ConfigParser
import libxml2
import sys, os
import string
import traceback
from pyxmpp import JID, Message, StreamError, Presence, jabber
from pyxmpp.jabber import delay
import time

class publishApplication(jabber.Client):
    """ Publish application """
    def __init__(self, base_dir, config_file, pub_repo, pub_msg):
        """ Initialize the application. """
        self.base_dir = base_dir
        self.pub_msg = pub_msg
        self.pub_repo = pub_repo
        cfg = ConfigParser.ConfigParser()
        cfg.read(config_file)
        self.jid = JID(cfg.get('LOGIN', 'USER'),
                       cfg.get('LOGIN', 'HOST'),
                       cfg.get('LOGIN', 'RESOURCE')
                      )
        self.vcjb_jid = JID(cfg.get('LOGIN', 'USER'),
                       cfg.get('LOGIN', 'HOST'),
                       cfg.get('LOGIN', 'VCJB_RESOURCE')
                      )
        self.password = unicode(cfg.get('LOGIN', 'PASS'), 'iso-8859-2')
        self.auth_methods = string.split(cfg.get('LOGIN', 'AUTH_METHODS'))

    def run(self):
        """ 
        Connect and run the application main loop. 
        """
        try:
            jabber.Client.__init__(self,
                                   jid = self.jid,
                                   password = self.password,
                                   auth_methods = self.auth_methods
                                  )
            self.connect()
            
            try:
                self.loop(1)
            finally:
                if self.stream:
                    self.disconnect()
        except KeyboardInterrupt:
            self.exit()
        except StreamError:
            raise
        
    def session_started(self):
        """
        Stream-related plugin setup (stanza handler registration, etc).
        Send bot presence, set message handler for chat message
        and call session_started for all loaded plugins.
        """ 
        presence = Presence();
        presence.set_priority(0);
        self.stream.send(presence)
                
    def authorized(self):
        jabber.Client.authorized(self)
        self.stream.send(Message(to=self.vcjb_jid,
            subject=unicode(self.pub_repo,'iso-8859-2'),
            body=unicode(self.pub_msg,'iso-8859-2')
           ))
        self.stream.disconnect()
        
def publish(base_dir, pub_cfg, pub_repo, pub_msg):
    """
    Run the publish application.
    """ 
    libxml2.debugMemory(1)
    
    app = publishApplication(base_dir, pub_cfg, pub_repo, pub_msg)
    
    app.run()
    
    libxml2.cleanupParser()
    
