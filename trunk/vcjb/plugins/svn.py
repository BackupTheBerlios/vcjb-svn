# -*- coding: utf-8 -*-

""" Plugin for Subversion """ 
__revision__ = "$Revision: $"

import threading
import datetime
import os
import libxml2
import ConfigParser
import string
from vcjb.plugin import PluginBase
from pyxmpp import JID, Message
from time import sleep 

class Plugin(PluginBase):
    """
    Class inherited from PluginBase.
    """ 
    def __init__(self, app):
        """
        Initialize the plugin.
        """ 
        PluginBase.__init__(self, app)
        self.app = app
        self.svn_thread = None
        self.last_rev = {}
        self.exit_time = False
        self.cfg = ConfigParser.ConfigParser()
        self.repos = []
        self.users = {}
        self.repos_url = {}
        self.read_cfg()
    
    def read_cfg(self):
        """
        Read plugin config file.
        """ 
        self.cfg.read(self.app.base_dir + '/svn.cfg')
        try:
            if self.cfg.has_option('SVN', 'REPOS'):
                self.repos = string.split(self.cfg.get('SVN', 'REPOS'))
                
        except ConfigParser.NoSectionError:
            self.cfg.add_section('SVN')
        
        self.users = {}
        for repo in self.repos:
            self.users[repo] = string.split(self.cfg.get(repo, 'USERS'))
            self.repos_url[repo] = self.cfg.get(repo, 'URL')
    
    def save_cfg(self):
        """
        Save plugin config file.
        """ 
        config_file = open(self.app.base_dir + '/svn.cfg', 'w')
        self.cfg.write(config_file)
        config_file.close()
        
    def session_started(self, stream):
        """
        Stream-related plugin setup (stanza handler registration, etc).
        """ 
        self.svn_thread = threading.Thread(None, self.svn_loop, "SVN")
        self.svn_thread.setDaemon(1)
        self.svn_thread.start()
    
    def session_ended(self, stream):
        """
        Called when session is closed (the stream has been disconnected).
        """ 
        self.unload()
    
    def svn_loop(self):
        """
        Plugin main loop - waiting for a new version and send log into 
        subscribed users.
        """ 
        rev = {}
        try:
            for repos in self.repos:
                command = 'svn log --xml -v -r HEAD ' + self.repos_url[repos]
                results = os.popen(command)
                dane = results.read()
                results.close()
                doc = libxml2.parseDoc(dane)
                root = doc.children
                child = root.children

                while child is not None:
                    if child.name == "logentry":
                        self.last_rev[repos] = child.prop("revision")
                    child = child.next

                doc.freeDoc()
                rev[repos] = self.last_rev[repos]
                self.app.info("Start revision " + repos + ": " + rev[repos])

            last_active = datetime.datetime.now()
            while (not self.exit_time):
                sleep(0.25) 
                now = datetime.datetime.now()
                dif = now - last_active
                if (dif.seconds > 120): # sleep for 120 sec.
                    try:
                        self.app.info("checking version")
                        for repos in self.repos:
                            command = 'svn log --xml -v -r HEAD ' \
                                    + self.repos_url[repos]
                            results = os.popen(command)
                            dane = results.read()
                            results.close()
                            doc = libxml2.parseDoc(dane)
                            root = doc.children
                            child = root.children

                            while child is not None:
                                if child.name == "logentry":
                                    rev[repos] = child.prop("revision")
                                child = child.next

                            doc.freeDoc()
                            self.app.info("Last " + repos + \
                                          " revision: " + self.last_rev[repos]\
                                          + ", Actual revision: " + rev[repos])
                            if (rev[repos] != self.last_rev[repos]):
                                cmd = 'svn log -v -r ' + \
                                    str(int(self.last_rev[repos]) + 1) + ':' +\
                                    rev[repos] + ' ' + self.repos_url[repos]
                                self.app.debug('svn log -v -r '\
                                    + str(int(self.last_rev[repos]) + 1) + ':'\
                                    + rev[repos] + ' ' + self.repos_url[repos])
                                results = os.popen(cmd)
                                dane = results.read()
                                results.close()
                                dane = 'Repozytorium ' + repos + '\n' + dane
                                for user in self.users['produkt']:
                                    self.app.debug('send message to: ' + user)
                                    self.app.stream.send(Message(
                                                            to=JID(user),
                                                            body=unicode(dane,
                                                                'iso-8859-2'
                                                               )
                                                           ))
                                self.last_rev[repos] = rev[repos]
                            last_active = datetime.datetime.now()
                    except StandardError:
                        last_active = datetime.datetime.now()
        except StandardError:
            self.app.print_exception()
        self.app.debug("loop exit")
        
    def message_chat(self, stanza):
        """
        Called when receive a message from admin.
        """ 
        self.app.debug(
            "From %r body: %r" % 
            (stanza.get_from(), stanza.get_body())
           )
        
        command = string.split(stanza.get_body(), ' ')
        try:
            if (command[0] == "svn"):
                target = JID(stanza.get_from())
                if (command[1] == "log"):
                    dane = unicode(self.get_version_log(command), 'iso-8859-2')
                    
                elif (command[1] == "info"):
                    dane = self.get_info(command)
                    
                elif (command[1] == "del" and len(command) == 3):
                    dane = self.delete_repository(command)
                    
                elif (command[1] == "add" and len(command) == 4):
                    dane = self.add_repository(command, stanza)
                        
                elif (command[1] == "modify"):
                    dane = self.modify_repository(command)
                    
                self.app.stream.send(Message(to=target, body=dane))
                    
        except (KeyError):
            target = JID(stanza.get_from())
            dane = u"Ther's no repository called " + command[2]
            self.app.stream.send(Message(to=target, body=dane))
    
    def get_version_log(self, command):
        """
        Parse command and return version's log message.
        """
        if (len(command) > 3):
            command = 'svn log -v -r ' + command[3] + ' '\
                + self.repos_url[command[2]]
        else:
            command = 'svn log -v -r HEAD '\
                + self.repos_url[command[2]]

        results = os.popen(command)
        dane = results.read()
        results.close()
        return dane
        
    def get_info(self, command):
        """
        Return info about repositories.
        """ 
        if (len(command) > 2):
            dane = u"Repository: " + command[2] + u"\nURL: " \
                + unicode(self.repos_url[command[2]]) \
                + u"\nUSERS: " \
                + unicode(string.join(self.users[command[2]], \
                    u"; "))
        else:
            dane = "Repositories: " + \
                string.join(self.repos, ' ')
            dane = unicode(dane, 'iso-8859-2')
        return dane
    
    def delete_repository(self, command):
        """
        Delete repository from check list.
        """ 
        if (len(self.repos) > 1 
            and 
            self.repos_url[command[2]] != ""
           ):
            self.cfg.set('SVN', 
                'REPOS', 
                string.replace(self.cfg.get('SVN', 'REPOS'), command[2], ''))
            self.cfg.remove_section(command[2])
            self.save_cfg()
            self.read_cfg()
            dane = u"Repository " + command[2] + u" succesfully deleted"
            self.app.reload_plugin('svn')
        else:
            dane = u"You can't remove the last tepository"
        
        return dane
                        
    def add_repository(self, command, stanza):
        """
        Add repository to check list.
        """ 
        if (not self.cfg.has_option('SVN', 'REPOS') 
            or
            string.find(self.cfg.get('SVN', 'REPOS'), 
                command[2]) == -1
           ):
            if (self.cfg.has_option('SVN', 'REPOS')):
                self.cfg.set(
                    'SVN', 
                    'REPOS', 
                    self.cfg.get('SVN', 'REPOS') + ' ' + command[2]
                   )
            else:
                self.cfg.set(
                    'SVN', 
                    'REPOS', 
                    command[2]
                   )
            self.cfg.add_section(command[2])
            self.cfg.set(command[2], 'URL', command[3])
            self.cfg.set(
                command[2], 
                'USERS', 
                stanza.get_from().bare()
               )
            self.save_cfg()
            self.read_cfg()
            dane = u"Repository: " + command[2] + \
                u" succesfully added"
            self.app.reload_plugin('svn')
        else:
            dane = u"Repository: " + command[2] + u" already added"
        
        return dane            
    
    def modify_repository(self, command):
        """
        Modify repository information.
        """ 
        if (len(command) == 5 and command[3] == "add"):
            if (string.find(
                    self.cfg.get(command[2], 'USERS'), 
                    command[4]
                   ) == -1
               ):
                self.cfg.set(
                    command[2], 
                    'USERS', 
                    self.cfg.get(command[2], 'USERS') + ' ' + \
                        command[4]
                   )
                self.save_cfg()
                self.read_cfg()
                dane = u"User: " + command[4] + \
                    u" added to repository " + command[2]
            else:
                dane = u"User: " + command[4] + \
                    u" already added to repository " + command[2]
        
        elif (len(command) == 5 and command[3] == "del"):
            if (string.find(
                    self.cfg.get(command[2], 'USERS'),
                    command[4]
                   ) != -1
               ):
                if (len(self.users[command[2]]) > 1 ):
                    self.cfg.set(
                        command[2], 
                        'USERS', 
                        string.replace(
                            self.cfg.get(command[2], 'USERS'),
                            command[4],
                            ''
                           )
                       )
                    self.save_cfg()
                    self.read_cfg()
                    dane = u"User: " + command[4] + \
                        u" deleted from repository " + command[2]
                else:
                    dane = u"You can't remove the last user " + \
                        "from repository"
            else:
                dane = u"Ther's no user " + command[4] + \
                    u" in repository " + command[2]
        
        elif (len(command) == 5 and command[3] == "url"):
            self.cfg.set(command[2], 'URL', command[4])
            self.save_cfg()
            self.read_cfg()
            dane = u"Done"
        
        return dane
        
    def cmd_close(self):
        """
        Exit from plugin's main loop.
        """ 
        self.exit_time = True
        
    def unload(self):
        """
        Unregister every handler installed etc. and return True if the plugin
        may safely be unloaded.
        """ 
        self.cmd_close()
        sleep(0.5) 
        return True
    
    
