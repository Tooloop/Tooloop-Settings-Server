# -*- coding: utf-8 -*-

from flask import Flask, render_template, abort
from os import listdir, rename, mkdir, chown, utime
from os.path import isdir, isfile, join
import pwd
import grp
from subprocess import call
import json
from utils.file_utils import *
from shutil import copy, copytree, rmtree



class AppDefinition(object):
    def __init__(self, 
                 name=None,
                 description=None,
                 media=None,
                 version=None,
                 last_updated=None,
                 license=None,
                 category=None,
                 tags=None,
                 developer=None,
                 homepage=None,
                 compatibility=None,
                 has_controller=False, 
                 has_settings=False):
        self.name = name
        self.description = description
        self.media = media
        self.version = version
        self.last_updated = last_updated
        self.license = license
        self.category = category
        self.tags = tags
        self.developer = developer
        self.homepage = homepage
        self.compatibility = compatibility
        self.has_controller = has_controller
        self.has_settings = has_settings

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'media': self.media,
            'version': self.version,
            'last_updated': self.last_updated,
            'license': self.license,
            'category': self.category,
            'tags': self.tags,
            'developer': self.developer,
            'homepage': self.homepage,
            'compatibility': self.compatibility,
            'has_controller': self.has_controller,
            'has_settings': self.has_settings,
        }





class AppCenter(object):
    """Holds information of available apps."""
    def __init__(self, presentation, flask):
        super(AppCenter, self).__init__()
        self.presentation = presentation
        self.app_path = '/assets/apps/'
        self.root_path = flask.root_path
        self.available_apps = []
        self.check_available_apps()
        self.installed_app_definition = self.app_definition_from_bundle(self.root_path+'/installed_app')
        self.installed_app_controller = None

        if not self.installed_app_definition:
            return

        # import settings controller
        if self.installed_app_definition.has_controller:
            installed_app_module = __import__('installed_app.controller', fromlist=['InstalledApp'])
            InstalledApp = getattr(installed_app_module, 'InstalledApp')
            self.installed_app_controller = InstalledApp(flask)

        # add settings page route
        @flask.route("/appsettings")
        def render_appsettings():
            if self.installed_app_definition.has_settings:
                return render_template('settings.html', page='appsettings', installed_app = self.installed_app_definition, app_controller = self.installed_app_controller)
            else:
                abort(404)


    def get_installed_app(self):
        return self.installed_app_definition

    def get_installed_app_controller(self):
        return self.installed_app_controller

    def get_availeble_apps(self):
        return self.available_apps


    def check_available_apps(self):
        self.available_apps = []
        directory = listdir(self.app_path)
        for app in directory:
            if isfile(self.app_path+app+'/bundle/app.definition'):
                app_definition = self.app_definition_from_bundle(self.app_path+app+'/bundle')
                if app_definition:
                    self.available_apps.append(app_definition)
        self.available_apps.sort(key=lambda x : x.name)


    def app_definition_from_bundle(self, bundle_path):

        if not isfile(bundle_path+"/app.definition"):
            return None

        app_definition = AppDefinition()

        with open(bundle_path+"/app.definition") as json_data:
            d = json.load(json_data)

            app_definition.name = d.get('name', None)
            app_definition.description = d.get('description', None)
            app_definition.media = d.get('media', [])
            app_definition.version = d.get('version', None)
            app_definition.last_updated = d.get('last_updated', None)
            app_definition.license = d.get('license', None)
            app_definition.category = d.get('category', None)
            app_definition.tags = d.get('tags', None)
            app_definition.developer = d.get('developer', None)
            app_definition.homepage = d.get('homepage', None)
            app_definition.compatibility = d.get('compatibility', None)

        app_definition.has_controller = isfile(bundle_path+'/controller.py')
        app_definition.has_settings = isfile(bundle_path+'/settings.html')

        return app_definition



    def install(self, app):
        if isdir(self.app_path + app):
            # TODO: in case of an exception roll back and re-install old app

            # stop running presentation
            self.presentation.stop()

            # uninstall old app
            if isfile(self.root_path+'/installed_app/uninstall.sh'):
                call(['/bin/sh', self.root_path + '/installed_app/uninstall.sh'])

            # delete old bundle
            if isdir(self.root_path+'/installed_app'):
                rmtree(self.root_path+'/installed_app')

            # install new app dependencies
            if isfile(self.app_path+app+'/bundle/install.sh'):
                call(['/bin/sh', self.app_path+app+'/bundle/install.sh'])

            # copy bundle stuff
            copytree(self.app_path+app+'/bundle', self.root_path+'/installed_app')

            # copy data stuff
            if isdir(self.app_path+app+'/data'):
                if not isdir('/assets/data'):
                    copytree(self.app_path+app+'/data', '/assets/data')
                else:
                    self.copytree(self.app_path+app+'/data', '/assets/data')

            # make Python aware of controller module
            if isfile(self.root_path+'/installed_app/controller.py'):
                self.touch(self.root_path+'/installed_app/__init__.py')

            # copy presentation
            if isdir('/assets/presentation'):
                rmtree('/assets/presentation')
            copytree(self.app_path+app+'/presentation', '/assets/presentation')

            # chown everything to tooloop user
            self.chown_recursive(self.root_path, 'tooloop', 'tooloop')
            self.chown_recursive('/assets/data', 'tooloop', 'tooloop')
            self.chown_recursive('/assets/presentation', 'tooloop', 'tooloop')

            # restart presentation
            self.presentation.start()

            # get information and update self.installed_app_definition
            self.installed_app_definition = self.app_definition_from_bundle(self.root_path+'/installed_app')

            return self.installed_app_definition



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
