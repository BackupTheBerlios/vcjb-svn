# -*- coding: utf-8 -*-

""" core plugin support """
__revision__ = "$Rev$"

import datetime
import threading
import ConfigParser
import string
from pyxmpp import JID, Message
from time import sleep 

class PluginBase:
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
        self.repos_url = {}
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
            self.repos_url[repo] = self.cfg.get(repo, 'URL')
    
    def save_cfg(self):
        """
        Save plugin config file.
        """ 
        config_file = open(self.app.base_dir + '/' + self.name + '.cfg', 'w')
        self.cfg.write(config_file)
        config_file.close()
        
    def unload(self):
        """
        Unregister every handler installed etc. and return True if the plugin
        may safely be unloaded.
        """ 
        self.cmd_close()
        sleep(0.5) 
        return True
    
    def session_started(self, stream):
        """
        Stream-related plugin setup (stanza handler registration, etc).
        """ 
        self.threads[self.name] = threading.Thread(None, 
                                                   self.main_loop, 
                                                   self.name)
        self.threads[self.name].setDaemon(1)
        self.threads[self.name].start()
    
    def session_ended(self, stream):
        """
        Called when session is closed (the stream has been disconnected).
        """ 
        self.unload()
    
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
            self.cfg.set(self.name, 
                'REPOS', 
                string.replace(self.cfg.get(self.name, 'REPOS'), command[2], ''))
            self.cfg.remove_section(command[2])
            self.save_cfg()
            self.read_cfg()
            dane = u"Repository " + command[2] + u" succesfully deleted"
            self.app.reload_plugin(self.name)
        else:
            dane = u"You can't remove the last tepository"
        
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
            if (command[0] == self.name):
                dane = None
                target = JID(stanza.get_from())
                if (command[1] == "log"):
                    if (len(command) > 3):
                        dane = unicode(self.get_version_log(command[2], 
                                command[3]
                               ), 
                            'iso-8859-2'
                           )
                    else:
                        dane = unicode(self.get_version_log(command[2], None), 
                            'iso-8859-2'
                           )
                    
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
    
    def main_loop(self):
        """
        Plugin main loop - waiting for a new version and send log into 
        subscribed users.
        """ 
        rev = {}
        try:
            for repos in self.repos:
                self.last_rev[repos] = self.get_revision(repos)
                
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
                            rev[repos] = self.get_revision(repos)
                            
                            self.app.info("Last " + repos + \
                                          " revision: " + self.last_rev[repos]\
                                          + ", Actual revision: " + rev[repos])
                            if (rev[repos] != self.last_rev[repos]):
                                
                                dane = self.get_version_log(repos, 
                                    str(int(self.last_rev[repos]) + 1), 
                                    rev[repos]
                                   )
                                
                                dane = 'Repozytorium ' + repos + '\n' + dane
                                for user in self.users[repos]:
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
    
    def get_revision(self, repo_name):
        """
        Return current revision number.
        """
        return None
    
    def get_version_log(self, 
                        repo_name, 
                        rev_from, 
                        rev_to = None, 
                        options = None):
        """
        Parse command and return version's log message.
        """
        return None
    
    
