"""
Command line handling for Cobbler.

Copyright 2007, Red Hat, Inc
Michael DeHaan <mdehaan@redhat.com>

This software may be freely redistributed under the terms of the GNU
general public license.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
"""

import optparse
from cexceptions import *
from rhpl.translate import _, N_, textdomain, utf8
import sys

HELP_FORMAT = "%-25s%s"

#=============================================================

class FunctionLoader:

    """
    The F'n Loader controls processing of cobbler commands.
    """

    def __init__(self):
        """
        When constructed the loader has no functions.
        """
        self.functions = {}

    def add_func(self, obj):
        """
        Adds a CobblerFunction instance to the loader.
        """
        self.functions[obj.command_name()] = obj

    def run(self, args):
        """
        Runs a command line sequence through the loader.
        """

        # if no args given, show all loaded fns
        if len(args) == 1:
            return self.show_options()
        called_name = args[1]

        # also show avail options if command name is bogus
        if not called_name in self.functions.keys():
            return self.show_options()
        fn = self.functions[called_name]

        # some functions require args, if none given, show subcommands
        #if len(args) == 2:
        #    no_args_rc = fn.no_args_handler()
        #    if no_args_rc:
        #        return True

        # finally let the object parse its own args
        loaded_ok = fn.parse_args(args)
        if not loaded_ok:
            raise CX(_("Invalid arguments"))
        return fn.run()

    def show_options(self):
        """
        Prints out all loaded functions.
        """

        print "commands:"
        print "========="

        names = self.functions.keys()
        names.sort()

        for name in names:
            help = self.functions[name].help_me()
            if help != "":
                print help

#=============================================================

class CobblerFunction:

    def __init__(self,api):
        """
        Constructor requires a Cobbler API handle.
        """
        self.api = api

    def command_name(self):
        """
        The name of the command, as to be entered by users.
        """
        return "unspecified"

    def subcommands(self):
        """
        The names of any subcommands, such as "add", "edit", etc
        """
        return [ ]

    def run(self):
        """
        Called after arguments are parsed.  Return True for success.
        """
        return True

    def add_options(self, parser, args):
        """
        Used by subclasses to add options.  See subclasses for examples.
        """
        pass

    def parse_args(self,args):
        """
        Processes arguments, called prior to run ... do not override.
        """

        accum = ""
        for x in args[1:]:
            if not x.startswith("-"):
                accum = accum + "%s " % x
            else:
                break
        p = optparse.OptionParser(usage="cobbler %s [ARGS]" % accum)
        self.add_options(p, args)

        # if using subcommands, ensure one and only one is used
        subs = self.subcommands()
        if len(subs) > 0:
            count = 0
            for x in subs:
                if x in args:
                    count = count + 1               
            if count != 1:
                print "usage:"
                print "======"
                for x in subs: 
                    print "cobbler %s %s [ARGS|--help]" % (self.command_name(), x)
                sys.exit(1)    

        (self.options, self.args) = p.parse_args(args)
        return True

    def object_manipulator_start(self,new_fn,collect_fn,subobject=False):
        """
        Boilerplate for objects that offer add/edit/delete/remove/copy functionality.
        """

        if "add" in self.args:
            obj = new_fn(is_subobject=subobject)
        else:
            if not self.options.name:
                raise CX(_("name is required"))
            if "delete" in self.args:
                collect_fn().remove(self.options.name, with_delete=True)
                return None
            obj = collect_fn().find(self.options.name)

        if not "copy" in self.args and not "rename" in self.args and self.options.name:
            obj.set_name(self.options.name)

        return obj

    def object_manipulator_finish(self,obj,collect_fn):
        """
        Boilerplate for objects that offer add/edit/delete/remove/copy functionality.
        """

        if "copy" in self.args or "rename" in self.args:
            if self.options.newname:
                obj = obj.make_clone()
                obj.set_name(self.options.newname)
            else:
                raise CX(_("--newname is required"))

        rc = collect_fn().add(obj, with_copy=True)

        if "rename" in self.args:
            return collect_fn().remove(self.options.name, with_delete=True)

        return rc


    #def no_args_handler(self):
    #
    #    """
    #    Used to accept/reject/explain subcommands.  Do not override.
    #    """
    #
    #    subs = self.subcommands()
    #    if len(subs) == 0:
    #        return False
    #    for x in subs:
    #        print "   cobbler %s %s [ARGS|--help]" % (self.command_name(), x)
    #    return True # stop here



