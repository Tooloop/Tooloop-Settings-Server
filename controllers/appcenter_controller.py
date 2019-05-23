# -*- coding: utf-8 -*-

from flask import Flask, render_template, abort, jsonify
from flask.json import JSONEncoder

from os import listdir, rename, mkdir, chown, utime
from os.path import isdir, isfile, join
import pwd
import grp
from subprocess import Popen, PIPE, call
import json

import apt
import apt_pkg
import sys
import time
import apt.progress.base
from apt import Package

# from utils.file_utils import *
from utils.exceptions import *
# from shutil import copy, copytree, rmtree
from pprint import pprint



# ------------------------------------------------------------------------------
# DictFetchProgress
# ------------------------------------------------------------------------------
class DictFetchProgress(apt.progress.base.AcquireProgress):
    """Monitor object for downloads"""

    def __init__(self, progress_dict):
        self.progress_dict = progress_dict

    def start(self):
        """Invoked when the Acquire process starts running."""
        self.progress_dict['step'] = 'Downloading packages'
        self.progress_dict['task'] = 'start downloading'

    def stop(self):
        """Invoked when the Acquire process stops running."""
        self.progress_dict['task'] = 'finished downloading'

    def fail(self, item):
        """Invoked when an item could not be fetched."""
        self.progress_dict['task'] = item+' could not be downloaded'
        self.progress_dict['status'] = 'fail'

    def fetch(self, item):
        """Invoked when some of the item's data is fetched."""
        self.progress_dict['task'] = item+' downloaded'

    def ims_hit(self, item):
        """Invoked when an item is confirmed to be up-to-date.

        Invoked when an item is confirmed to be up-to-date. For instance,
        when an HTTP download is informed that the file on the server was
        not modified.
        """
        self.progress_dict['task'] = item+' is already the latest version'

    def pulse(self, owner):
        """Periodically invoked while the Acquire process is underway.

        This method gets invoked while the Acquire progress given by the
        parameter 'owner' is underway. It should display information about
        the current state.

        This function returns a boolean value indicating whether the
        acquisition should be continued (True) or cancelled (False).
        """
        # self.current_bytes
        # self.current_cps
        # self.current_items
        # self.elapsed_time
        # self.fetched_bytes
        # self.last_bytes
        # self.total_bytes
        # self.total_items
        self.progress_dict['percent'] = self.current_bytes/self.total_bytes

        return self.progress_dict['status'] == 'ok'



# ------------------------------------------------------------------------------
# DictInstallProgress
# ------------------------------------------------------------------------------
class DictInstallProgress(apt.progress.base.InstallProgress):
    """Class to report the progress of installing packages."""

    def __init__(self, progress_dict):
        apt.progress.base.InstallProgress.__init__(self)
        self.progress_dict = progress_dict

    def start_update(self):
        """Start update."""
        self.progress_dict['percent'] = 0
        self.progress_dict['step'] = 'Installing'
        self.progress_dict['task'] = 'start installation'
        self.progress_dict['status'] = 'ok'

    def finish_update(self):
        """Called when update has finished."""
        self.progress_dict['task'] = 'done'
        self.progress_dict['status'] = 'done'
        self.progress_dict['percent'] = 100

    def status_change(self, pkg, percent, status):
        """Called when the APT status changed."""
        self.progress_dict['percent'] = percent
        self.progress_dict['task'] = status

    def update_interface(self):
        apt.progress.base.InstallProgress.update_interface(self)
        # usefull to e.g. redraw a GUI
        time.sleep(0.1)



# ------------------------------------------------------------------------------
# PackageJSONEncoder
# ------------------------------------------------------------------------------
class PackageJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, Package):
                return {
                    'package_name': obj.shortname,
                    'version': obj.candidate.version,
                    'homepage': obj.candidate.homepage,
                    'maintainer': obj.maintainer,
                    'bugs': obj.bugs,
                    'name': obj.prettyname,
                    'summary': obj.candidate.summary,
                    'description': obj.candidate.description,
                    'section': obj.section,
                    'architecture': obj.architecture(),
                    'preview_image': obj.preview_image,
                    'media': obj.media,
                    # TODO:
                    # 'pre_depends': pre_depends,
                    # 'depends': depends,
                    # 'recommends': recommends,
                    # 'suggests': suggests,
                    # 'has_controller': has_controller,
                    # 'has_settings': has_settings
                }
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)



# ------------------------------------------------------------------------------
# AppCenter
# ------------------------------------------------------------------------------
class AppCenter(object):
    """Holds information of available packages and manages their installation."""
    def __init__(self, presentation_controller, flask):
        super(AppCenter, self).__init__()
        self.presentation_controller = presentation_controller
        self.root_path = flask.root_path

        self.apt_cache = apt.Cache()
        self.packages = None
        self.get_available_packages()
        self.progress = {
            'percent':0,
            'step': '',
            'task': '',
            'status':'ok'
            }

        # get information of installed packages
        self.installed_presentation = None
        self.installed_presentation_settings_controller = None

        # check installed presentation
        for presentation in self.packages['presentations']:
            if presentation.is_installed:
                self.installed_presentation = presentation
                break

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

    def get_installed_presentation_settings_controller(self):
        return self.installed_presentation_settings_controller

    def get_available_packages(self):
        # lazy loading
        if not self.packages:
            self.packages = {
                'presentations': [],
                'addons': []
            }
            # search for tooloop packages
            ps = Popen('aptitude -F"%p" search "?section(tooloop)"', shell=True, stdout=PIPE)
            output = ps.stdout.read()
            ps.stdout.close()
            ps.wait()
            packages = output.splitlines()
            for index in range(len(packages)):
                packages[index] = packages[index].replace(" ", "")

            for package in packages:
                pkg = self.apt_cache[package]
                self.add_tooloop_metainfo(pkg)

                if "tooloop/presentation" in pkg.section:
                    self.packages['presentations'].append(pkg)
                elif "tooloop/addon" in pkg.section:
                    self.packages['addons'].append(pkg)

        return self.packages


    def add_tooloop_metainfo(self, package):
        try:
            package.maintainer = package.candidate.record["Maintainer"]
        except Exception as e:
            pass

        package.bugs = None
        try:
            package.bugs = package.candidate.record["Bugs"] 
        except Exception as e:
            pass

        package.prettyname = None
        try:
            package.prettyname = package.candidate.record["Name"]
        except Exception as e:
            pass

        package.preview_image = None
        url_path = '/appcenter/'+package.shortname+'/preview_image'
        file_path = '/assets/packages/media/'+package.shortname+'/preview_image'
        if isfile(file_path+'.png'):
            package.preview_image = url_path+'.png'
        elif isfile(file_path+'.jpg'):
            package.preview_image = url_path+'.jpg'

        package.media = []


    def update_packages(self):
        # update local repository
        ps = Popen('/opt/tooloop/scripts/tooloop-update-packages', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()


    def install(self, package):
        pkg = self.apt_cache[package]
        self.add_tooloop_metainfo(pkg)

        # only handle tooloop packages
        if not "tooloop" in pkg.section:
            # 403 – Forbidden
            raise InvalidUsage(package+" is not a tooloop package", status_code=403);

        # package is apresentation and there is a presentation already
        if "tooloop/presentation" in pkg.section and self.installed_presentation:
            # 409 – Conflict
            raise InvalidUsage("Only one presentation can be installed at a time", status_code=409);

        # package is installed already
        if pkg.is_installed:
            # 304 – Not Modified
            raise InvalidUsage(package + " is already installed", status_code=400);

        pkg.mark_install()

        try:
            # stop running presentation
            if "tooloop/presentation" in pkg.section:
                self.presentation_controller.stop()
            
            # install
            # self.progress = {
            #     'percent':0,
            #     'step': '',
            #     'task': '',
            #     'status':'ok'
            #     }
            # print self.progress
            
            result = self.apt_cache.commit(DictFetchProgress(self.progress), DictInstallProgress(self.progress)) # True if all was fine
            self.apt_cache.update()
            self.apt_cache.open()

            # make Python aware of controller module
            # if isfile(self.root_path+'/installed_app/controller.py'):
            #     self.touch(self.root_path+'/installed_app/__init__.py')


            if "tooloop/presentation" in pkg.section:
                self.installed_presentation = pkg
                # restart presentation
                self.presentation_controller.start()

        except Exception, arg:
            raise Exception("Sorry, package installation failed [{err}]".format(err=str(arg)))


    def uninstall(self, package):
        pkg = self.apt_cache[package]
        self.add_tooloop_metainfo(pkg)

        # if current presentation depends on package (e. g. an addon)
        if self.installed_presentation:
            for dep_list in self.installed_presentation.candidate.dependencies:
                for dep in dep_list:
                    if package in dep.name:
                        # 409 – Conflict
                        raise InvalidUsage('Cannot uninstall '+package+ ' because current presentation '+self.installed_presentation.name+' depends on it.', status_code=409);
            # if it is the current presentation
            if pkg.name == self.installed_presentation.name:
                self.presentation_controller.stop()
                self.installed_presentation = None


        # only handle tooloop packages
        if not "tooloop" in pkg.section:
            raise Exception(package+" is not a tooloop package");

        if pkg.is_installed:
            pkg.mark_delete()
        else:
            # 304 – Not Modified
            raise InvalidUsage(package + " is not installed", status_code=400);

        try:
            # self.progress = {
            #     'percent':0,
            #     'step': '',
            #     'task': '',
            #     'status':'ok'
            #     }
            # print self.progress
            result = self.apt_cache.commit(DictFetchProgress(self.progress), DictInstallProgress(self.progress)) # True if all was fine
            self.apt_cache.update()
            self.apt_cache.open()
        except Exception, arg:
            raise Exception("Sorry, purging package failed [{err}]".format(err=str(arg)))


    def get_progress(self):
        return self.progress





    # def copy_files(self, src_dir, dest_dir):
    #     for file in listdir(src_dir):
    #         full_file_name = join(src_dir, file)
    #         if isfile(full_file_name):
    #             copy(full_file_name, dest_dir)

    # def copytree(self, src, dst, symlinks=False, ignore=None):
    #     for item in os.listdir(src):
    #         s = os.path.join(src, item)
    #         d = os.path.join(dst, item)
    #         if os.path.isdir(s):
    #             shutil.copytree(s, d, symlinks, ignore)
    #         else:
    #             shutil.copy2(s, d)

    # def chown_recursive(self, path, user, group):
    #     uid = pwd.getpwnam(user).pw_uid
    #     gid = grp.getgrnam(group).gr_gid
    #     os.chown(path, uid, gid)
    #     for root, dirs, files in os.walk(path):
    #         for name in dirs:
    #             os.chown(os.path.join(root, name), uid, gid)
    #         for name in files:
    #             os.chown(os.path.join(root, name), uid, gid)

    # def touch(self, filename, times=None):
    #     with open(filename, 'a'):
    #         os.utime(filename, times)