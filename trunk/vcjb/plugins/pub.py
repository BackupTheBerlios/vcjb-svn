# -*- coding: utf-8 -*-

""" Plugin for Publish messages """ 
__revision__ = "$Rev: 7 $"

import datetime
import threading
import ConfigParser
import string
from pyxmpp import JID, Message
from time import sleep 
from vcjb.plugin import PluginBase

class Plugin(PluginBase):
    """ base class for plugins """
    def __init__(self, app, name):
        """
        Initialize the plugin.
        """ 
        self.app = app
        self.name = name
        self.last_rev = {}
        self.exit_time = False
        self.cfg = ConfigParser.ConfigParser()
        self.repos = []
        self.users = {}
        self.threads = {}
        self.read_cfg()
        
    def read_cfg(self):
        """
        Read plugin config file.
        """ 
        self.cfg.read(self.app.base_dir + '/' + self.name +'.cfg')
        if self.cfg.has_section(self.name):
            if self.cfg.has_option(self.name, 'REPOS'):
                self.repos = string.split(self.cfg.get(self.name, 'REPOS'))
        else:
            self.cfg.add_section(self.name)
        
        self.users = {}
        for repo in self.repos:
            self.users[repo] = string.split(self.cfg.get(repo, 'USERS'))
        
    def session_started(self, stream):
        """
        Stream-related plugin setup (stanza handler registration, etc).
        """ 
        pass
    
    def get_info(self, command):
        """
        Return info about repositories.
        """ 
        if (len(command) > 2):
            dane = u"Repository: " + command[2] + u"\nUSERS: " \
                + unicode(string.join(self.users[command[2]], \
                    u"; "))
        else:
            dane = "Repositories: " + \
                string.join(self.repos, ' ')
            dane = unicode(dane, 'iso-8859-2')
        return dane
    
    def add_repository(self, command, stanza):
        """
        Add repository to check list.
        """ 
        if (not self.cfg.has_option(self.name, 'REPOS') 
            or
            string.find(self.cfg.get(self.name, 'REPOS'), 
                command[2]) == -1
           ):
            if (self.cfg.has_option(self.name, 'REPOS')):
                self.cfg.set(
                    self.name, 
                    'REPOS', 
                    self.cfg.get(self.name, 'REPOS') + ' ' + command[2]
                   )
            else:
                self.cfg.set(
                    self.name, 
                    'REPOS', 
                    command[2]
                   )
            self.cfg.add_section(command[2])
            self.cfg.set(
                command[2], 
                'USERS', 
                stanza.get_from().bare()
               )
            self.save_cfg()
            self.read_cfg()
            dane = u"Repository: " + command[2] + \
                u" succesfully added"
            self.app.reload_plugin(self.name)
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
        
        return dane
        
    def message_chat(self, stanza):
        """
        Called when receive a chat message from admin.
        """ 
        self.app.debug(
            "From %r body: %r" % 
            (stanza.get_from(), stanza.get_body())
           )
        
        command = string.split(stanza.get_body(), ' ')
        try:
            if (command[0] == self.name):
                dane = None
                target = JID(stanza.get_from())
                if (command[1] == "info"):
                    dane = self.get_info(command)
                    
                elif (command[1] == "del" and len(command) == 3):
                    dane = self.delete_repository(command)
                    
                elif (command[1] == "add" and len(command) == 3):
                    dane = self.add_repository(command, stanza)
                        
                elif (command[1] == "modify"):
                    dane = self.modify_repository(command)
                    
                self.app.stream.send(Message(to=target, body=dane))
                    
        except (KeyError):
            target = JID(stanza.get_from())
            dane = u"Ther's no repository called " + command[2]
            self.app.stream.send(Message(to=target, body=dane))
    
    def message_normal(self, stanza):
        """
        Called when receive a normal message from publish module.
        """ 
        if (stanza.get_from().bare().as_utf8() == self.app.jid.bare().as_utf8()
           ):
            
            self.app.debug(
                "From %r body: %r" % 
                (stanza.get_from(), stanza.get_body())
               )
            
            log_msg = stanza.get_body()
            repo = stanza.get_subject()
            self.app.debug(u'repo: ' + repo)
            self.app.debug(u'log message: ' + log_msg)
            log_msg = u'Repository: ' + repo + '\n' +log_msg
            try:
                for user in self.users[repo]:
                    self.app.debug('send message to: ' + user)
                    self.app.stream.send(Message(
                                            to=JID(user),
                                            body=log_msg)
                           )
            except (KeyError):
                self.app.debug(u"Ther's no repository called " + repo)
            
