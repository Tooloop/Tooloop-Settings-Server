# -*- coding: utf-8 -*-

from flask import Flask, render_template
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
                 support_url=None,
                 compatibility=None,
                 has_controller=False, 
                 has_settings=False, 
                 has_widget=False):
        self.name = name
        self.description = description
        self.media = media
        self.version = version
        self.last_updated = last_updated
        self.license = license
        self.category = category
        self.tags = tags
        self.developer = developer
        self.support_url = support_url
        self.compatibility = compatibility
        self.has_controller = has_controller
        self.has_settings = has_settings
        self.has_widget = has_widget

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
            'support_url': self.support_url,
            'compatibility': self.compatibility,
            'has_controller': self.has_controller,
            'has_settings': self.has_settings,
            'has_widget': self.has_widget
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
        if self.installed_app_definition.has_settings:
            @flask.route("/appsettings")
            def render_appsettings():
                return render_template('settings.html', page='appsettings', installed_app = self.installed_app_definition, app_controller = self.installed_app_controller
            )


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
            if isfile(self.app_path+app+'/app.definition'):
                app_definition = self.app_definition_from_bundle(self.app_path+app)
                if app_definition:
                    self.available_apps.append(app_definition)
        self.available_apps.sort(key=lambda x : x.name)


    def app_definition_from_bundle(self, bundle_path):

        if not isfile(bundle_path+"/app.definition"):
            return None

        has_controller = isfile(bundle_path+'/controller.py')
        has_settings = isfile(bundle_path+'/settings.html')
        has_widget = isfile(bundle_path+'/widget.html')

        try:
            with open(bundle_path+"/app.definition") as json_data:
                d = json.load(json_data)
                app_definition = AppDefinition()
                if d['name']: app_definition.name = d['name']
                if d['description']: app_definition.description = d['description']
                if d['media']: app_definition.media = d['media']
                if d['version']: app_definition.version = d['version']
                if d['last_updated']: app_definition.last_updated = d['last_updated']
                if d['license']: app_definition.license = d['license']
                if d['category']: app_definition.category = d['category']
                if d['tags']: app_definition.tags = d['tags']
                if d['developer']: app_definition.developer = d['developer']
                if d['support_url']: app_definition.support_url = d['support_url']
                if d['compatibility']: app_definition.compatibility = d['compatibility']
                app_definition.has_controller = has_controller
                app_definition.has_settings = has_settings
                app_definition.has_widget = has_widget

                return app_definition
                
        except ValueError as e:
            print "Could not read app.definition from bundle " + bundle_path
            return None



    def install(self, app):
        if isdir(self.app_path + app):
            # TODO: in case of an exception roll back and re-install old app

            # stop running presentation
            self.presentation.stop()

            # uninstall old app
            call(['/bin/sh', self.root_path + '/installed_app/uninstall.sh'])

            # delete old backup
            if isdir(self.root_path+'/installed_app_BAK'):
                rmtree(self.root_path+'/installed_app_BAK')

            if isdir('/assets/presentation_BAK'):
                rmtree('/assets/presentation_BAK')
            
            # backup old app
            if isdir(self.root_path+'/installed_app'):
                rename(self.root_path+'/installed_app', self.root_path+'/installed_app_BAK')
                mkdir(self.root_path+'/installed_app')
            
            if isdir('/assets/presentation'):
                rename('/assets/presentation', '/assets/presentation_BAK')


            # install new app
            call(['/bin/sh', self.app_path+app+'/scripts/install.sh'])

            # copy bundle stuff
            self.copy_files(self.app_path+app, self.root_path+'/installed_app')
            self.copy_files(self.app_path+app+'/scripts', self.root_path+'/installed_app')
            self.copy_files(self.app_path+app+'/settings', self.root_path+'/installed_app')
            self.copy_files(self.app_path+app+'/data', '/assets/data')
            self.touch(self.root_path+'/installed_app/__init__.py')

            # copy presentation
            copytree(self.app_path+app+'/presentation', '/assets/presentation/')

            # delete backup
            if isdir(self.root_path+'/installed_app_BAK'):
                rmtree(self.root_path+'/installed_app_BAK')

            if isdir(self.root_path+'/assets/presentation_BAK'):
                rmtree('/assets/presentation_BAK')    

            # get information and update self.installed_app_definition
            if isfile(self.app_path+app+'/app.definition'):
                self.installed_app_definition = self.app_definition_from_bundle(self.app_path+app)

            # chown everything to tooloop user
            self.chown_recursive(self.app_path, 'tooloop', 'tooloop')
            self.chown_recursive('/assets/data', 'tooloop', 'tooloop')
            self.chown_recursive('/assets/presentation', 'tooloop', 'tooloop')

            # restart presentation
            self.presentation.start()

            return self.installed_app_definition


    def copy_files(self, src_dir, dest_dir):
        for file in listdir(src_dir):
            full_file_name = join(src_dir, file)
            if isfile(full_file_name):
                copy(full_file_name, dest_dir)
                
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
