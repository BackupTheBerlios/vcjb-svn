# -*- coding: utf-8 -*-

""" Plugin for Subversion """ 
__revision__ = "$Rev$"

import datetime
import os
import libxml2
from vcjb.plugin import PluginBase
from pyxmpp import JID, Message
from time import sleep 

class Plugin(PluginBase):
    """
    Class inherited from PluginBase.
    """ 
    def main_loop(self):
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
