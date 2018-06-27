# -*- coding: utf-8 -*-

"""
    Tooloop Settings Server
    ~~~~~~~~~~~~~~~~~~~~~~~
    System adminisation tool for a Tooloop OS box.
    :copyright: (c) 2017 by Daniel Stock.
    :license: Beerware, see LICENSE for more details.
"""

from flask import Flask, jsonify, render_template, request, after_this_request, abort, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader

from controllers.system_controller import System
from controllers.presentation_controller import Presentation
from controllers.appcenter_controller import AppCenter
from controllers.services_controller import Services
from controllers.screenshot_controller import Screenshots
from utils.time_utils import *

import augeas
import time

from pprint import pprint
from subprocess import call

# ------------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_pyfile('config.cfg')


augtool = augeas.Augeas()
system = System(augtool)
presentation = Presentation()
appcenter = AppCenter(presentation, app)
services = Services(app)
screenshots = Screenshots()

# let jinja also look in the installed_app folder
template_loader = ChoiceLoader([
        app.jinja_loader,
        FileSystemLoader([app.root_path+'/templates', app.root_path+'/installed_app']),
    ])
app.jinja_loader = template_loader


# ------------------------------------------------------------------------------
# PAGE ROUTING
# ------------------------------------------------------------------------------

@app.route("/")
@app.route("/dashboard")
def render_dashboard():
    return render_template('dashboard.html', 
        page = 'dashboard', 
        installed_app = appcenter.get_installed_app(), 
        app_controller = appcenter.get_installed_app_controller(),
        screenshot_service_running = services.is_screenshot_service_running(),
        hostname = system.get_hostname(),
        uptime = time_to_ISO_string(system.get_uptime()),
        vnc_running = services.is_vnc_running(),
        ssh_running = services.is_ssh_running(),
    )

@app.route("/network")
def render_network():
    return render_template('network.html', 
        page='network', 
        installed_app = appcenter.get_installed_app(),
        interfaces = [{
            'ip': 'x.x.x.x',
            'subnet_mask': '255.255.255.0',
            'gateway': 'x.x.x.x'
        }]
    )

@app.route("/appcenter")
def render_appcenter():
    appcenter.check_available_apps()
    return render_template('appcenter.html', 
        page='appcenter', 
        installed_app = appcenter.get_installed_app(),
        available_apps = appcenter.get_availeble_apps(),
        time_stamp = time.time(),
    )

@app.route("/services")
def render_services():
    return render_template('services.html', 
        page='services', 
        installed_app = appcenter.get_installed_app(),
        services = services.get_status(),
    )

@app.route("/system")
def render_system():
    return render_template('system.html', 
        page='system', 
        installed_app = appcenter.get_installed_app(),
        hostname = system.get_hostname(),
        ip_address = system.get_ip(),
    )


# ------------------------------------------------------------------------------
# ADDITIONAL RESOURCE FOLDERS
# ------------------------------------------------------------------------------

@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    return send_from_directory('/assets/screenshots/', filename)

@app.route('/app/<path:filename>')
def serve_installed_app(filename):
    return send_from_directory('installed_app/', filename)

@app.route('/appcenter/<path:filename>')
def serve_available_apps(filename):
    return send_from_directory('/assets/apps/', filename)



# ------------------------------------------------------------------------------
# RESTFUL API
# ------------------------------------------------------------------------------


# System

@app.route('/tooloop/api/v1.0/system', methods=['GET'])
def get_system():
    return jsonify(system.to_dict())

@app.route('/tooloop/api/v1.0/system/hostname', methods=['GET'])
def get_hostname():
    try:
        return jsonify({'hostname':system.get_hostname()})
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/system/hostname', methods=['PUT'])
def set_hostname():
    if not request.form or not 'hostname' in request.form:
        abort(400)
    try:
        system.set_hostname(request.form['hostname'])
        return jsonify({
                'message': 'Hostname saved',
                'hostname': system.get_hostname(),
                'needsReboot': system.needs_reboot
        })
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/system/usage', methods=['GET'])
def get_usage():
    return jsonify({
        'hd': system.get_hd(),
        'cpu': system.get_cpu(),
        'gpu': system.get_gpu(),
        'memory': system.get_memory()
    })

@app.route('/tooloop/api/v1.0/system/uptime', methods=['GET'])
def get_uptime():
    return jsonify({'uptime': time_to_ISO_string(system.get_uptime())})

@app.route('/tooloop/api/v1.0/system/hd', methods=['GET'])
def get_hd():
    return jsonify(system.get_hd())

@app.route('/tooloop/api/v1.0/system/cpu', methods=['GET'])
def get_cpu():
    return jsonify(system.get_cpu())

@app.route('/tooloop/api/v1.0/system/gpu', methods=['GET'])
def get_gpu():
    return jsonify(system.get_gpu())

@app.route('/tooloop/api/v1.0/system/memory', methods=['GET'])
def get_memory():
    return jsonify(system.get_memory())

@app.route('/tooloop/api/v1.0/system/reboot', methods=['GET'])
def reboot():
    try:
        system.reboot()
        return jsonify({ 'message' : 'Rebooting' })
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/system/poweroff', methods=['GET'])
def poweroff():
    try:
        system.poweroff()
        return jsonify({ 'message' : 'Powering Off' })
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/system/password', methods=['PUT'])
def set_password():
    if not request.form or not 'oldPassword' in request.form or not 'newPassword' in request.form:
        abort(400)
    try:
        system.set_password(request.form['oldPassword'], request.form['newPassword'])
        return jsonify({ 'message' : 'Password saved'})
    except Exception as e:
        abort(500, e)


# presentation

@app.route('/tooloop/api/v1.0/presentation/start', methods=['GET'])
def start_presentation():
    # try:
    return_code = presentation.start()
    return jsonify({ 'message' : 'Called start script with return code '+str(return_code) })
    # except Exception as e:
    #     abort(500)

@app.route('/tooloop/api/v1.0/presentation/stop', methods=['GET'])
def stop_presentation():
    return_code = presentation.stop()
    try:
        return jsonify({ 'message' : 'Called stop script with return code '+str(return_code) })
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/presentation/reset', methods=['GET'])
def reset_presentation():
    try:
        return_code = presentation.reset()
        return jsonify({ 'message' : 'Called reset script with return code '+str(return_code) })
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/presentation/displayon', methods=['GET'])
def display_on():
    try:
        state = presentation.display_on()
        return jsonify({ 'Display' : state })
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/presentation/displayoff', methods=['GET'])
def display_off():
    try:
        state = presentation.display_off()
        return jsonify({ 'Display' : state })
    except Exception as e:
        abort(500)

@app.route('/tooloop/api/v1.0/presentation/displaystate', methods=['GET'])
def display_state():
    try:
        state = presentation.check_display_state()
        return jsonify({ 'Display' : state })
    except Exception as e:
        abort(500)

# appcenter

@app.route('/tooloop/api/v1.0/appcenter/installed', methods=['GET'])
def get_installed_app():
    return jsonify(appcenter.get_installed_app().to_dict())

@app.route('/tooloop/api/v1.0/appcenter/available', methods=['GET'])
def get_availeble_apps():
    available = appcenter.get_availeble_apps()
    available_as_dict = []
    for app in available:
        available_as_dict.append(app.to_dict())
    return jsonify(available_as_dict)

@app.route('/tooloop/api/v1.0/appcenter/refresh', methods=['GET'])
def check_available_apps():
    appcenter.check_available_apps()
    return get_availeble_apps()

@app.route('/tooloop/api/v1.0/appcenter/install/<string:name>', methods=['GET'])
def install_app(name):
    @after_this_request
    def add_header(response):
        response.headers['X-Foo'] = 'Parachute'
        return response

    appcenter.install(name)

    # call(['systemctl','restart','tooloop-settings-server'])

    try:
        return jsonify(appcenter.get_installed_app().to_dict())
    except Exception as e:
        abort(500)


# services

@app.route('/tooloop/api/v1.0/services', methods=['GET'])
def get_services_status():
    return jsonify(services.get_status())


@app.route('/tooloop/api/v1.0/services/vnc', methods=['GET'])
def vnc_status():
    return jsonify({'vnc':services.is_vnc_running()})

@app.route('/tooloop/api/v1.0/services/vnc/enable', methods=['GET'])
def enable_vnc():
    services.enable_vnc()
    return jsonify({ 'message' : 'VNC enabled' })

@app.route('/tooloop/api/v1.0/services/vnc/disable', methods=['GET'])
def disable_vnc():
    services.disable_vnc()
    return jsonify({ 'message' : 'VNC disabled' })


@app.route('/tooloop/api/v1.0/services/ssh', methods=['GET'])
def ssh_status():
    return jsonify({'ssh':services.is_ssh_running()})

@app.route('/tooloop/api/v1.0/services/ssh/enable', methods=['GET'])
def enable_ssh():
    services.enable_ssh()
    return jsonify({ 'message' : 'SSH enabled' })

@app.route('/tooloop/api/v1.0/services/ssh/disable', methods=['GET'])
def disable_ssh():
    services.disable_ssh()
    return jsonify({ 'message' : 'SSH disabled' })


@app.route('/tooloop/api/v1.0/services/remoteconfiguration', methods=['GET'])
def remote_configuration_status():
    return jsonify({'remote_configuration':services.is_remote_configuration_running()})

@app.route('/tooloop/api/v1.0/services/remoteconfiguration/enable', methods=['GET'])
def enable_remote_configuration():
    services.enable_remote_configuration()
    return jsonify({ 'message' : 'Remote configuration enabled' })

@app.route('/tooloop/api/v1.0/services/remoteconfiguration/disable', methods=['GET'])
def disable_remote_configuration():
    services.disable_remote_configuration()
    return jsonify({ 'message' : 'Remote configuration disabled' })


@app.route('/tooloop/api/v1.0/services/screenshots', methods=['GET'])
def screenshot_service_status():
    return jsonify({'screenshot_service':services.is_screenshot_service_running()})

@app.route('/tooloop/api/v1.0/services/screenshots/enable', methods=['GET'])
def enable_screenshot_service():
    services.enable_screenshot_service()
    return jsonify({ 'message' : 'Screenshot service enabled' })

@app.route('/tooloop/api/v1.0/services/screenshots/disable', methods=['GET'])
def disable_screenshot_service():
    services.disable_screenshot_service()
    return jsonify({ 'message' : 'Screenshot service disabled' })


# screenshots

@app.route('/tooloop/api/v1.0/screenshot/latest', methods=['GET'])
def get_latest_screenshot():
    return jsonify(screenshots.get_latest_screenshot())

@app.route('/tooloop/api/v1.0/screenshot/<int:index>', methods=['GET'])
def get_screenshot(index):
    return jsonify(screenshots.get_screenshot(index))

@app.route('/tooloop/api/v1.0/screenshot/date/<string:date>', methods=['GET'])
def get_screenshot_at_date(date):
    return jsonify(screenshots.get_screenshot_at_date(date))

@app.route('/tooloop/api/v1.0/screenshot/grab', methods=['GET'])
def grab_screenshot():
    try:
        return jsonify(screenshots.grab_screenshot())
    except Exception as e:
        abort(500)


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        debug=True,
        host=app.config['HOST'],
        port=80
    )