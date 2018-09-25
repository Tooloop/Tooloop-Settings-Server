# -*- coding: utf-8 -*-

from flask import Flask, render_template, abort

from os import listdir, rename, mkdir, chown, utime
from os.path import isdir, isfile, join
import pwd
import grp
from subprocess import Popen, PIPE, call
import json

import apt
import apt_pkg
import sys
# from apt.progress import base

from utils.file_utils import *
from shutil import copy, copytree, rmtree


# TODO: inherit from apt.package
class Package(object):
    def __init__(self, 
                 package_name=None,
                 version=None,
                 maintainer=None,
                 homepage=None,
                 bugs=None,
                 name=None,
                 short_description=None,
                 long_description=None,
                 media=None,
                 section=None,
                 architecture=None,
                 pre_depends=None,
                 depends=None,
                 recommends=None,
                 suggests=None,
                 has_controller=False, 
                 has_settings=False):
        self.package_name = package_name
        self.version = version
        self.maintainer = maintainer
        self.homepage = homepage
        self.bugs = bugs
        self.name = name
        self.short_description = short_description
        self.long_description = long_description
        self.media = media
        self.section = section
        self.architecture = architecture
        self.pre_depends = pre_depends
        self.depends = depends
        self.recommends = recommends
        self.suggests = suggests
        self.has_controller = has_controller
        self.has_settings = has_settings

    def to_dict(self):
        return {
            'package_name': self.package_name,
            'version': self.version,
            'maintainer': self.maintainer,
            'homepage': self.homepage,
            'bugs': self.bugs,
            'name': self.name,
            'short_description': self.short_description,
            'long_description': self.long_description,
            'media': self.media,
            'section': self.section,
            'architecture': self.architecture,
            'pre_depends': self.pre_depends,
            'depends': self.depends,
            'recommends': self.recommends,
            'suggests': self.suggests,
            'has_controller': self.has_controller,
            'has_settings': self.has_settings
        }



# class TextInstallProgress(InstallProgress):

#     def __init__(self):
#         apt.progress.InstallProgress.__init__(self)
#         self.last = 0.0

#     def updateInterface(self):
#         InstallProgress.updateInterface(self)
#         if self.last >= self.percent:
#             return
#         sys.stdout.write("\r[%s] %s\n" % (self.percent, self.status))
#         sys.stdout.flush()
#         self.last = self.percent

#     def conffile(self, current, new):
#         print "conffile prompt: %s %s" % (current, new)

#     def error(self, errorstr):
#         print "got dpkg error: '%s'" % errorstr



class AppCenter(object):
    """Holds information of available apps."""
    def __init__(self, presentation_controller, flask):
        super(AppCenter, self).__init__()
        self.presentation_controller = presentation_controller
        self.root_path = flask.root_path
        self.package_path = '/assets/packages/'
        self.packages = None
        # self.update_packages()

        # get information of installed packages
        self.installed_presentation = None
        self.installed_presentation_controller = None
        # TODO
        # self.installed_presentation = self.read_package_information(self.root_path+'/installed_app')
        # self.installed_presentation_controller = None

        if not self.installed_presentation:
            return

        # TODO
        # import custom settings controller
        # if self.installed_presentation.has_controller:
        #     installed_app_module = __import__('installed_app.controller', fromlist=['InstalledApp'])
        #     InstalledApp = getattr(installed_app_module, 'InstalledApp')
        #     self.installed_presentation_settings_controller = InstalledApp(flask)

        # add settings page route
        # @flask.route("/appsettings")
        # def render_appsettings():
        #     if self.installed_presentation.has_settings:
        #         return render_template('settings.html', page='appsettings', installed_app = self.installed_presentation, app_controller = self.installed_presentation_settings_controller)
        #     else:
        #         abort(404)


    def get_installed_presentation(self):
        return self.installed_presentation

    def get_installed_presentation_controller(self):
        return self.installed_presentation_controller

    def get_availeble_packages(self):
        return self.packages


    # TODO: this can be slow, maybe we shouldn’t do this at app start/boot store result
    def update_packages(self):
        self.packages = {
            'presentations': [],
            'addons': []
        }

        # update local repository
        ps = Popen('/opt/tooloop/scripts/tooloop-update-packages', shell=True, stdout=PIPE)
        
        # search for tooloop packages
        ps = Popen('aptitude -F"%p" search "?section(tooloop)"', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        print(output)

        # for package in directory:
        #     if isfile(self.package_path+package+XXXXXXXXX'.deb'):
        #         package = self.read_package_information(self.package_path+package+'/xxxxxxxx')
        #         if package:
        #             if '/tooloop/addon' in package.section:
        #                 self.packages['addons'].append(package)
        #             else if '/tooloop/presentation' in package.section:
        #                 self.packages['presentations'].append(package)
        #             else:
        #                 # TODO: log error, no type
        #                 pass
        # self.packages.sort(key=lambda x : x.name)


    def read_package_information(self, deb_file):

        if not isfile(deb_file):
            return None

        package = Package()

        # TODO: read info from control file

        # TODO: look up fils in /opt/tooloop/settings-server/installed_app
        # package.has_controller = isfile(bundle_path+'/controller.py')
        # package.has_settings = isfile(bundle_path+'/settings.html')

        return package



    def install(self, package):
        cache = apt.Cache()
        # cache = apt.Cache(apt.progress.OpTextProgress())
        # fprogress = apt.progress.TextFetchProgress()
        # iprogress = TextInstallProgress()

        pkg = cache["3dchess"]

        if pkg.is_installed:
            print "%s is already installed" % pkg.name
        else:
            pkg.mark_install()

        try:
            print "Installing %s" % pkg.name
            result = cache.commit()
            print result
        except Exception, arg:
            print >> sys.stderr, "Sorry, package installation failed [{err}]".format(err=str(arg))


        # TODO: if package is apresentation and there is a presentation already
        # --> return with error

        # stop running presentation
        # self.presentation_controller.stop()

        # TODO: apt install package

        # make Python aware of controller module
        # if isfile(self.root_path+'/installed_app/controller.py'):
        #     self.touch(self.root_path+'/installed_app/__init__.py')

        # restart presentation
        # self.presentation_controller.start()

        # get information and update self.installed_presentation
        # self.installed_presentation = self.read_package_information(self.root_path+'/installed_app')


    def uninstall(self, package):
        # TODO: if current presentation depends on package
        # --> return with error

        # TODO: if is current presentation
        # --> stop running presentation

        cache = apt.Cache()
        # cache = apt.Cache(apt.progress.OpTextProgress())
        # fprogress = apt.progress.TextFetchProgress()
        # iprogress = TextInstallProgress()

        if pkg.is_installed:
            pkg.mark_delete()
        else:
            print "%s is not installed" % pkg.name

        try:
            print "Unnstalling %s" % pkg.name
            result = cache.commit()
            print result
        except Exception, arg:
            print >> sys.stderr, "Sorry, purging package failed [{err}]".format(err=str(arg))



    def copy_files(self, src_dir, dest_dir):
        for file in listdir(src_dir):
            full_file_name = join(src_dir, file)
            if isfile(full_file_name):
                copy(full_file_name, dest_dir)

    def copytree(self, src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, symlinks, ignore)
            else:
                shutil.copy2(s, d)

    def chown_recursive(self, path, user, group):
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(group).gr_gid
        os.chown(path, uid, gid)
        for root, dirs, files in os.walk(path):
            for name in dirs:
                os.chown(os.path.join(root, name), uid, gid)
            for name in files:
                os.chown(os.path.join(root, name), uid, gid)

    def touch(self, filename, times=None):
        with open(filename, 'a'):
            os.utime(filename, times)

    def uninstall(self):
        pass
