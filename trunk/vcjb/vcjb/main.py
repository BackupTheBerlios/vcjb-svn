# -*- coding: utf-8 -*-
""" main application source """ 
__revision__ = "$Rev$"


import ConfigParser
import libxml2
import sys, os
import string
import traceback
from pyxmpp import JID, Message, StreamError, Presence, jabber
from pyxmpp.jabber import delay
import time

class Application(jabber.Client):
    """ Application class """
    def __init__(self, base_dir, config_file):
        """ Initialize the application. """
        self.configFile = config_file
        self.show_debug = None
        self.admin = None
        self.jid = None
        self.password = None
        self.cfg = ConfigParser.ConfigParser()
        self.read_cfg()
        self.base_dir = base_dir
        home = os.environ.get("HOME", "")
        self.home_dir = os.path.join(home, ".vcjb")
        
        self.plugin_dirs = [os.path.join(base_dir, "plugins"),
                            os.path.join(self.home_dir, "plugins")]
        self.plugins = {}
        self.plugin_modules = {}
        
    def read_cfg(self):
        """ Read application config file. """
        self.cfg.read(self.configFile)
        self.show_debug = (self.cfg.get('BASE','SHOW_DEBUG') == "1")
        self.show_info = (self.cfg.get('BASE','SHOW_INFO') == "1")
        self.admin = self.cfg.get('BASE', 'ADMIN')
        self.jid = JID(self.cfg.get('LOGIN', 'USER'),
                       self.cfg.get('LOGIN', 'HOST'),
                       self.cfg.get('LOGIN', 'RESOURCE')
                      )
        self.password = unicode(self.cfg.get('LOGIN', 'PASS'), 'iso-8859-2')
        self.auth_methods = string.split(self.cfg.get('LOGIN', 'AUTH_METHODS'))

    def run(self):
        """ 
        Connect and run the application main loop. 
        """
        try:
            self.load_plugins() 
            self.debug("creating stream...")
            jabber.Client.__init__(self,
                                   jid = self.jid,
                                   password = self.password,
                                   auth_methods = self.auth_methods
                                  )
            self.debug("connecting...")
            self.connect()
            self.debug("processing...")
            
            try:
                self.loop(1)
            finally:
                if self.stream:
                    self.disconnect()
        except KeyboardInterrupt:
            self.info("Quit request")
            self.exit()
        except StreamError:
            raise
    
    def _load_plugin(self, name):
        """ 
        Load the plugin. 
        """
        try:
            mod = self.plugin_modules.get(name)
            if mod:
                mod = reload(mod)
            else:
                mod = __import__(name)
            plugin = mod.Plugin(self)
            plugin.module = mod
            plugin.sys_path = sys.path
            self.plugins[name] = plugin
            self.plugin_modules[name] = mod
        except StandardError:
            self.print_exception()
            self.info("Plugin load failed")

    def load_plugin(self, name):
        """ 
        Find a plugin in filesystem and load it. 
        """
        sys_path = sys.path
        try:
            for path in self.plugin_dirs:
                sys.path = [path] + sys_path
                plugin_file = os.path.join(path, name + ".py")
                if not os.path.exists(plugin_file):
                    continue
                if self.plugins.has_key(name):
                    self.error("Plugin %s already loaded!" % (name,))
                    return
                self.info("Loading plugin %s..." % (name,))
                self._load_plugin(name)
                return
            self.error("Couldn't find plugin %s" % (name,))
        except StandardError:
            sys.path = sys_path

    def load_plugins(self):
        """ 
        Find all plugins in plugin paths and load them. 
        """
        sys_path = sys.path
        try:
            for path in self.plugin_dirs:
                sys.path = [path] + sys_path
                try:
                    directory = os.listdir(path)
                except (OSError,IOError),error:
                    self.debug("Couldn't get plugin list: %s" % (error,))
                    self.info("Skipping plugin directory %s" % (path,))
                    continue
                self.info("Loading plugins from %s:" % (path,))
                for plugin_file in directory:
                    if (plugin_file[0] == "." 
                        or 
                        not plugin_file.endswith(".py") 
                        or 
                        plugin_file == "__init__.py"
                       ):
                        continue
                    name = os.path.join(plugin_file[:-3])
                    if not self.plugins.has_key(name):
                        self.info("  %s" % (name,))
                        self._load_plugin(name)
        except StandardError:
            sys.path = sys_path

    def unload_plugin(self, name):
        """ 
        Unload the plugin. 
        """
        try:
            plugin = self.plugins[name]
        except KeyError:
            self.error("Plugin %s is not loaded" % (name,))
            return False
        self.info("Unloading plugin %s..." % (name,))
        try:
            ret = plugin.unload()
        except StandardError:
            ret = None
        if not ret:
            self.error("Plugin %s cannot be unloaded" % (name,))
            return False
        del self.plugins[name]
        return True
    
    def unload_plugins(self):
        """ 
        Unload all loaded plugins. 
        """
        loaded_plugins = {}
        for plugin in self.plugins:
            loaded_plugins[plugin] = plugin
        for plugin in loaded_plugins:
            self.unload_plugin(plugin)
    
    def reload_plugin(self, name):
        """ 
        Reload the plugin. 
        """
        self.unload_plugin(name)
        self.load_plugin(name)
        self.get_plugin(name).session_started(self.stream)
        
    def get_plugin(self, name):
        """ 
        Return reference to plugin. 
        """
        return self.plugins[name]

    def session_started(self):
        """
        Stream-related plugin setup (stanza handler registration, etc).
        Send bot presence, set message handler for chat message
        and call session_started for all loaded plugins.
        """ 
        presence = Presence();
        presence.set_priority(20);
        self.stream.send(presence)
        self.stream.set_message_handler("chat", self.message_chat)
        
        for plugin in self.plugins.values():
            try:
                plugin.session_started(self.stream)
            except StandardError:
                self.print_exception()
                self.info("Plugin call failed")
                
    def message_chat(self, stanza):
        """
        Handle incomming chat message.
        """ 
        if (stanza.get_from().bare().as_utf8() == self.admin):
            process = True
            message_delay = delay.get_delay(stanza)
            if (message_delay):
                if (message_delay.reason == "Offline Storage"):
                    self.info("Ingnoring offline message from " + \
                        message_delay.fr.as_string() + ": " + stanza.get_body()
                    )
                    process = False
            if process:
                command = string.split(stanza.get_body(), ' ')
                target = JID(stanza.get_from())
                if (command[0] == "down"):
                    self.exit()
                elif (command[0] == "unload"):
                    if (command[1] == "plugin"):
                        plugin = command[2]
                        self.unload_plugin(plugin)
                        msg = 'plugin ' + plugin + ' successfully unloaded' 
                        self.stream.send(Message(to=target, body=msg))
                elif (command[0] == "reload"):
                    if (command[1] == "plugin"):
                        plugin = command[2]
                        self.reload_plugin(plugin)
                        msg = 'plugin ' + plugin + ' successfully reloaded' 
                        self.stream.send(Message(to=target, body=msg))
                    elif (command[1] == "config"):
                        self.read_cfg()
                        self.stream.send(Message(to=target, body=u'config reloaded'))
                        for plugin in self.plugins.values():
                            try:
                                plugin.read_cfg()
                            except StandardError:
                                self.print_exception()
                                self.info("Plugin call failed")

                elif (command[0] == "load"):
                    if (command[1] == "plugin"):
                        plugin = command[2]
                        self.load_plugin(plugin)
                        self.get_plugin(plugin).session_started(self.stream)
                        msg = 'plugin ' + plugin + ' successfully loaded' 
                        self.stream.send(Message(to=target, body=msg))
                else:
                    self.plugins_message_chat(stanza)
                
        return 1
    
    def plugins_message_chat(self, stanza):
        """
        Call plugin handler for incomming chat message.
        """ 
        for plugin in self.plugins.values():
            try:
                plugin.message_chat(stanza)
            except StandardError:
                self.print_exception()
                self.info("Plugin call failed")
    def print_exception(self):
        """
        Print exception.
        """ 
        traceback.print_exc(file = sys.stderr)
        
    def stream_state_changed(self, state, arg):
        """
        Print info about state changes.
        """ 
        if state == "resolving":
            self.info("Resolving %r..." % (arg,))
        if state == "resolving srv":
            self.info("Resolving SRV for %r on %r..." % (arg[1], arg[0]))
        elif state == "connecting":
            self.info("Connecting to %s:%i..." % (arg[0], arg[1]))
        elif state == "connected":
            self.info("Connected to %s:%i." % (arg[0], arg[1]))
        elif state == "authenticating":
            self.info("Authenticating as %s..." % (arg,))
        elif state == "binding":
            self.info("Binding to resource %s..." % (arg,))
        elif state == "authorized":
            self.info("Authorized as %s." % (arg,))
        elif state == "tls connecting":
            self.info("Doing TLS handhake with %s." % (arg,))
    
    def error(self, error_text):
        """
        Print error.
        """ 
        print "ERROR: " + error_text.encode("utf-8", "replace")
        
    def info(self, info_text):
        """
        Print info.
        """ 
        if self.show_info:
            print "INFO: " + info_text.encode("utf-8", "replace")
    
    def debug(self, debug_text):
        """
        Print debug information.
        """ 
        if self.show_debug:
            print "DEBUG: " + debug_text.encode("utf-8", "replace")
    
    def exit(self):
        """
        Disconnect and exit.
        """ 
        self.unload_plugins()
        if self.stream:
            self.info(u"Disconnecting...")
            self.lock.acquire()
            self.stream.disconnect()
            self.stream.close()
            self.stream = None
            self.lock.release()
            time.sleep(1)
    
def main(base_dir):
    """
    Run the application.
    """ 
    libxml2.debugMemory(1)
    
    app = Application(base_dir, 'vcjb.cfg')
    
    app.run()
    
    libxml2.cleanupParser()
    if libxml2.debugMemory(1) == 0:
        print "OK"
    else:
        print "Memory leak %d bytes" % (libxml2.debugMemory(1))
        libxml2.dumpMemory()
