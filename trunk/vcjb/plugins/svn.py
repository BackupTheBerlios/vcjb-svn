# -*- coding: utf-8 -*-

""" Plugin for Subversion """ 
__revision__ = "$Rev$"

import os
import libxml2
from vcjb.plugin import PluginBase


class Plugin(PluginBase):
    """
    Class inherited from PluginBase.
    """ 
    def get_revision(self, repo_name):
        """
        Return current revision number.
        """
        dane = self.get_version_log(repo_name, 'HEAD', options = '--xml')
        
        doc = libxml2.parseDoc(dane)
        root = doc.children
        child = root.children

        while child is not None:
            if child.name == "logentry":
                revision = child.prop("revision")
            child = child.next

        doc.freeDoc()
        
        return revision
    
    def get_version_log(self, 
                        repo_name, 
                        rev_from, 
                        rev_to = None, 
                        options = None):
        """
        Parse command and return version's log message.
        """
        command = 'svn log -v -r '
        if (rev_from != None):
            command += rev_from
            if (rev_to != None):
                command += ':' + rev_to
        else:
            command += 'HEAD ' 
        if (options != None):
            command += ' ' + options
        
        command += ' ' + self.repos_url[repo_name]
        
        results = os.popen(command)
        dane = results.read()
        results.close()
        return dane
