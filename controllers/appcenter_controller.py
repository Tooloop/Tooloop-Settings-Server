# -*- coding: utf-8 -*-

from flask import Flask, render_template
from os import listdir, rename
from os.path import isdir, isfile
from subprocess import call
import json
from utils.file_utils import *
from shutil import copy, copytree, rmtree



class AppDefinition(object):
    def __init__(self, name, description, media, version, last_updated, license, price_euro, category, tags, developer, support_url, compatibility, has_controller=False, has_settings=False, has_widget=False):
        self.name = name
        self.description = description
        self.media = media
        self.version = version
        self.last_updated = last_updated
        self.license = license
        self.price_euro = price_euro
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
            'price_euro': self.price_euro,
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
            if isfile(self.app_path+app+'/bundle/app.definition'):
                app_definition = self.app_definition_from_bundle(self.app_path+app+'/bundle')
                self.available_apps.append(app_definition)
        self.available_apps.sort(key=lambda x : x.name)


    def app_definition_from_bundle(self, bundle_path):

        if not isfile(bundle_path+"/app.definition"):
            return None

        has_controller = isfile(bundle_path+'/controller.py')
        has_settings = isfile(bundle_path+'/settings.html')
        has_widget = isfile(bundle_path+'/widget.html')

        with open(bundle_path+"/app.definition") as json_data:
            d = json.load(json_data)
            return AppDefinition(
                d['name'],
                d['description'],
                d['media'],
                d['version'],
                d['last_updated'],
                d['license'],
                d['price_euro'],
                d['category'],
                d['tags'],
                d['developer'],
                d['support_url'],
                d['compatibility'],
                has_controller,
                has_settings,
                has_widget
            )


    def install(self, app):
        # TODO: try catch backup
        if isdir(self.app_path + app):
            # stopp the running presentation
            self.presentation.stop()

            # make backup
            # - /assets/presentation
            # - self.root_path + '/installed_app/
            
            # uninstall old app
            call(['/bin/sh', self.root_path + '/installed_app/uninstall.sh'])
            
            # delete old app
            rename(self.root_path+'/installed_app', self.root_path+'/installed_app_BAK')
            rename('/assets/presentation', '/assets/presentation_BAK')

            # install new app
            call(['/bin/sh', self.app_path+app+'/install.sh'])

            # copy bundle stuff to installed_app folder
            copytree(self.app_path+app+'/bundle', self.root_path+'/installed_app')

            # copy uninstall script
            copy(self.app_path+app+'/uninstall.sh', self.root_path + '/installed_app/uninstall.sh')

            # copy settings template
            copy(self.app_path+app+'/settings.html', self.root_path + '/templates/')

            # copy data
            # if isdir(self.app_path+app+'/data'):
                # TODO: copy_contents( self.app_path+app+'/data/*', '/assets/data/')
            # copy presentation
            copytree(self.app_path+app+'/presentation', '/assets/presentation/')

            # delete backup
            rmtree(self.root_path+'/installed_app_BAK')
            rmtree('/assets/presentation_BAK')
            # TODO: in case of an axception roll back
            # restart presentation
            self.presentation.start()

            # get information and update self.installed_app_definition
            if isfile(self.app_path+app+'/bundle/app.definition'):
                self.installed_app_definition = self.app_definition_from_bundle(self.app_path+app+'/bundle')

            return self.installed_app_definition

    def uninstall(self):
        pass
