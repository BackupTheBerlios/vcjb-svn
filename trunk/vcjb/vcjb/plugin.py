# -*- coding: utf-8 -*-

""" core plugin support """
__revision__ = "$Revision: $"

class PluginBase:
    """ base class for plugins """
    def __init__(self, vcjb):
        """
        Initialize the plugin.
        """ 
        self.vcjb = vcjb

    def unload(self):
        """
        Unregister every handler installed etc. and return True if the plugin
        may safely be unloaded.
        """ 
        return False

    def session_started(self, stream):
        """
        Stream-related plugin setup (stanza handler registration, etc).
        """ 
        pass

    def session_ended(self, stream):
        """
        Called when a session is closed (the stream has been disconnected).
        """ 
        pass
    
    def message_chat(self, stanza):
        """
        Called when recieve a message.
        """ 
        pass
    
    def read_cfg(self):
        """
        Read plugin config file.
        """ 
        pass
    
    def save_cfg(self):
        """
        Save plugin config file.
        """ 
        pass
