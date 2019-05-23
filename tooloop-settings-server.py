# -*- coding: utf-8 -*-

"""
    Tooloop Settings Server
    ~~~~~~~~~~~~~~~~~~~~~~~
    System adminisation tool for a Tooloop OS box.
    :copyright: (c) 2017 by Daniel Stock.
    :license: Unlicense, see LICENSE for more details.
"""

from flask import Flask, jsonify, render_template, request, after_this_request, abort, send_from_directory, make_response, Response
from jinja2 import ChoiceLoader, FileSystemLoader

from controllers.system_controller import System
from controllers.presentation_controller import Presentation
from controllers.appcenter_controller import AppCenter, PackageJSONEncoder
from controllers.services_controller import Services
from controllers.screenshot_controller import Screenshots
from utils.time_utils import *
from utils.exceptions import *

# import augeas
import time
import json

from pprint import pprint
from subprocess import call

# ------------------------------------------------------------------------------
# INIT
# ------------------------------------------------------------------------------

app = Flask(__name__)
app.config.from_pyfile('data/config.cfg')


# augtool = augeas.Augeas()
system = System(app)
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
        installed_presentation = appcenter.get_installed_presentation(),
        installed_presentation_settings_controller = appcenter.get_installed_presentation_settings_controller(),
        hostname = system.get_hostname(),
        display_state = system.get_display_state(),
        audio_mute = system.get_audio_mute(),
        audio_volume = system.get_audio_volume(),
        uptime = time_to_ISO_string(system.get_uptime()),
        screenshot_service_running = services.is_screenshot_service_running()
    )

# @app.route("/network")
# def render_network():
#     return render_template('network.html', 
#         page='network', 
#         installed_presentation = appcenter.get_installed_presentation()
#     )

@app.route("/appcenter")
def render_appcenter():
    return render_template('appcenter.html', 
        page='appcenter', 
        installed_presentation = appcenter.get_installed_presentation(),
        available_packages = appcenter.get_available_packages(),
    )

@app.route("/appcenter/package/<string:package>")
def render_package_detail(package):
    try:
        package_info = appcenter.get_package_info(package)
    except Exception as e:
        abort(400, e)

    return render_template('package-detail.html', 
        page='appcenter',
        package=package,
        installed_presentation = appcenter.get_installed_presentation()
    )

@app.route("/services")
def render_services():
    return render_template('services.html', 
        page='services', 
        installed_presentation = appcenter.get_installed_presentation(),
        services = services.get_status(),
    )

@app.route("/system")
def render_system():
    return render_template('system.html', 
        page='system',
        installed_presentation = appcenter.get_installed_presentation(),
        os_version = "0.9 alpha",
        hostname = system.get_hostname(),
        ip_address = system.get_ip(),
        uptime = time_to_ISO_string(system.get_uptime()),
        ssh_running = services.is_ssh_running(),
        vnc_running = services.is_vnc_running(),
        runtime_schedule = system.get_runtime_schedule(),
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
def serve_package_media(filename):
    return send_from_directory('/assets/packages/media', filename)



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
        abort(500, e)

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
        abort(500, e)

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
        abort(500, e)

@app.route('/tooloop/api/v1.0/system/poweroff', methods=['GET'])
def poweroff():
    try:
        system.poweroff()
        return jsonify({ 'message' : 'Powering Off' })
    except Exception as e:
        abort(500, e)

@app.route('/tooloop/api/v1.0/system/password', methods=['PUT'])
def set_password():
    if not request.form or not 'oldPassword' in request.form or not 'newPassword' in request.form:
        abort(400)
    try:
        system.set_password(request.form['oldPassword'], request.form['newPassword'])
        return jsonify({ 'message' : 'Password saved'})
    except Exception as e:
        abort(500, e)

@app.route('/tooloop/api/v1.0/system/audiovolume', methods=['GET'])
def get_audio_volume():
    return jsonify(system.get_audio_volume())

@app.route('/tooloop/api/v1.0/system/audiovolume', methods=['PUT'])
def set_audio_volume():
    if not request.form or not 'volume' in request.form:
        abort(400)
    try:
        volume = int(float(request.form['volume']))
        system.set_audio_volume(volume)
        return jsonify({'message' : 'Volume set to ' + str(volume)})
    except Exception as e:
        raise e

@app.route('/tooloop/api/v1.0/system/audiomute', methods=['GET'])
def get_audio_mute():
    return json.jsonify(system.get_audio_mute())

@app.route('/tooloop/api/v1.0/system/audiomute', methods=['PUT'])
def set_audio_mute():
    if not request.form or not 'mute' in request.form:
        abort(400)
    try:
        mute = request.form['mute'].lower() == 'true' or request.form['mute'] == '1'
        system.set_audio_mute(mute)
        message = 'muted' if mute else 'unmuted'
        return jsonify({'message' : 'Audio' + message})
    except Exception as e:
        abort(500, e)


@app.route('/tooloop/api/v1.0/system/displaystate', methods=['GET'])
def get_display_state():
    try:
        state = system.get_display_state()
        return jsonify({ 'Display' : state })
    except Exception as e:
        abort(500,e)

@app.route('/tooloop/api/v1.0/system/displaystate', methods=['PUT'])
def set_display_state():
    if not request.form or not 'state' in request.form:
        abort(400)
    try:
        system.set_display_state(request.form['state'])
        state = system.get_display_state()
        return jsonify({ 'Display' : state })
    except Exception as e:
        abort(500, e)

@app.route('/tooloop/api/v1.0/system/runtimeschedule', methods=['GET'])
def get_runtime_schedule():
    try:
        return jsonify(system.get_runtime_schedule())
    except Exception as e:
        abort(500, e)

@app.route('/tooloop/api/v1.0/system/runtimeschedule', methods=['PUT'])
def set_runtime_schedule():
    if not request.get_json():
        abort(400)
    try:
        system.set_runtime_schedule(request.get_json())
        return jsonify({ 'schedule' : system.get_runtime_schedule() })
    except Exception as e:
      abort(500, e)



# presentation

@app.route('/tooloop/api/v1.0/presentation/start', methods=['GET'])
def start_presentation():
    # try:
    return_code = presentation.start()
    return jsonify({ 'message' : 'Called start script with return code '+str(return_code) })
    # except Exception as e:
    #     abort(500, e)

@app.route('/tooloop/api/v1.0/presentation/stop', methods=['GET'])
def stop_presentation():
    return_code = presentation.stop()
    try:
        return jsonify({ 'message' : 'Called stop script with return code '+str(return_code) })
    except Exception as e:
        abort(500, e)

@app.route('/tooloop/api/v1.0/presentation/reset', methods=['GET'])
def reset_presentation():
    try:
        return_code = presentation.reset()
        return jsonify({ 'message' : 'Called reset script with return code '+str(return_code) })
    except Exception as e:
        abort(500, e)


# appcenter

@app.route('/tooloop/api/v1.0/appcenter/installed', methods=['GET'])
def get_installed_app():
    return jsonify(appcenter.get_installed_presentation())

@app.route('/tooloop/api/v1.0/appcenter/available', methods=['GET'])
def get_available_packages():
    packages = appcenter.get_available_packages()
    return jsonify(packages)

@app.route('/tooloop/api/v1.0/appcenter/refresh', methods=['GET'])
def update_packages():
    appcenter.update_packages()
    return get_available_packages()



@app.route('/tooloop/api/v1.0/appcenter/install/<string:name>', methods=['GET'])
def install_package(name):
    try:
        appcenter.install(name)
        return jsonify({ 'message' : name+' installed successfully' })
    except InvalidUsage as e:
        return make_response(jsonify({'message':e.message}), e.status_code)
    except Exception as e:
        abort(500, e)



@app.route('/tooloop/api/v1.0/appcenter/uninstall/<string:name>', methods=['GET'])
def uninstall_package(name):
    try:
        appcenter.uninstall(name)
        return jsonify({ 'message' : name+' uninstalled successfully' })
    except InvalidUsage as e:
        return make_response(jsonify({'message':e.message}), e.status_code)
    except Exception as e:
        abort(500, e)

@app.route('/tooloop/api/v1.0/appcenter/progress')
def appcenter_progress():
    def progress():
        progress = appcenter.get_progress()
        while True:
            yield 'data: '+json.dumps(progress)+'\n\n'
            if progress['status'] != 'ok':
                break
            time.sleep(0.1)

        # lines = [
        #     'Reading package lists… Done',
        #     'Building dependency tree       ',
        #     'Reading state information… Done',
        #     'The following NEW packages will be installed:',
        #     '  tooloop-video-player',
        #     '0 upgraded, 1 newly installed, 0 to remove and 68 not upgraded.',
        #     'Need to get 0 B/5,911 kB of archives.',
        #     'After this operation, 0 B of additional disk space will be used.',
        #     'WARNING: The following packages cannot be authenticated!',
        #     '  tooloop-video-player',
        #     'Authentication warning overridden.',
        #     'Get:1 file:/assets/packages ./ tooloop-video-player 0.1.0 [5,911 kB]',
        #     'Selecting previously unselected package tooloop-video-player.',
        #     '(Reading database ... 168126 files and directories currently installed.)',
        #     'Preparing to unpack .../tooloop-video-player_0.1.0_all.deb ...',
        #     'Unpacking tooloop-video-player (0.1.0) ...',
        #     'Setting up tooloop-video-player (0.1.0) ...'
        # ]
        # percent = 0.0
        # task = 'installing'
        
        # for index, line in enumerate(lines):
        #     percent = min(100, percent + 100.0/len(lines))
        #     if index == len(lines)-1:
        #         task = 'finished'
        #     progress = {'percent':percent, 'status':line, 'task': task}
        #     yield 'data: '+json.dumps(progress)+'\n\n'
        #     time.sleep(0.1)

    return Response(progress(), mimetype= 'text/event-stream')








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
        abort(500, e)


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    app.json_encoder = PackageJSONEncoder
    app.run(
        debug=True,
        host=app.config['HOST'],
        port=80
    )