# -*- coding: utf-8 -*-
from subprocess import check_output, check_call, Popen, PIPE, call
import os
import time
import pexpect
import fileinput
import json
from utils.time_utils import *
from utils.cpu_load import CpuLoad


class System(object):
    """Holds information of the tooloop box."""
    def __init__(self, app):
        super(System, self).__init__()
        self.app = app
        self.cpu_load = CpuLoad()
        self.needs_reboot = False
        # read runtime schedule from disk
        try:
            with open(self.app.root_path+'/data/startup-schedule.json') as json_data:
                self.startup_schedule = json.load(json_data)
        except Exception as e:
            self.startup_schedule = {
                'enabled' : False,
                'weekdays' : [],
                'time' : {
                    'hours':8,
                    'minutes':0
                }
            }
        try:
            with open(self.app.root_path+'/data/shutdown-schedule.json') as json_data:
                self.shutdown_schedule = json.load(json_data)
        except Exception as e:
            self.shutdown_schedule = {
                'enabled' : False,
                'type': 'poweroff',
                'weekdays' : [],
                'time' : {
                    'hours':20,
                    'minutes':0
                }
            }

        self.setup_runtime_schedule()



    def get_hostname(self):
        try:
            file = open("/etc/hostname", "r") 
            hostname = file.read().rstrip()
            return hostname
        except Exception as e:
            raise

    def set_hostname(self, hostname):
        old_hostname = self.get_hostname()

        # nothing to do
        if hostname == old_hostname: return

        # change /etc/hostname
        try:
            file = open("/etc/hostname", "w")
            file.write(hostname)
            file.close()
        except Exception as e:
            raise

        # change /etc/hosts
        try:
            with open('/etc/hosts', 'r') as file :
              filedata = file.read()

            # Replace the target string
            filedata = filedata.replace(old_hostname, hostname)

            # Write the file out again
            with open('/etc/hosts', 'w') as file:
              file.write(filedata)
        except Exception as e:
            raise e

        self.needs_reboot = True


    def get_ip(self):
        try:
            return check_output(['hostname', '-I']).rstrip('\n').split()[0]
        except Exception as e:
            raise

    def get_uptime(self):
        uptime_string = check_output(['uptime', '-s']).rstrip('\n')
        uptime = gmtime_from_string(uptime_string, '%Y-%m-%d %H:%M:%S')
        return uptime

    def get_hd(self):
        # get hd information
        # /dev/root        7541056 2210616   4994300  31% /

        hd_info = os.popen('df -B1 | grep assets').readline()
        # if no /assets partition is available, get the whole disk
        if hd_info == '':
            hd_info = os.popen('df -B1 | pcregrep -M "/\n"').readline()

        # split string in tokens
        # ['/dev/root', '7541056', '2210616', '4994300', '31%', '/']
        size = int(hd_info.split()[1])

        # assets directory
        apps = int(os.popen('du -s -B1 /assets/apps').readline().split()[0])
        data = int(os.popen('du -s -B1 /assets/data').readline().split()[0])
        logs = int(os.popen('du -s -B1 /assets/logs').readline().split()[0])
        presentation = int(os.popen('du -s -B1 /assets/presentation').readline().split()[0])
        screenshots = int(os.popen('du -s -B1 /assets/screenshots').readline().split()[0])

        return {
            'unit': 'Byte',
            'size': size,
            'apps': apps,
            'data': data,
            'logs': logs,
            'presentation': presentation,
            'screenshots': screenshots
        }

    def get_cpu(self):
        # get all thermal zones, of the cpu
        thermal_zones = []
        for name in os.listdir('/sys/class/thermal'):
            if 'thermal_zone' in name:
                full_path = os.path.join('/sys/class/thermal', name)
                if os.path.isdir(full_path):
                    thermal_zones.append(full_path)

        temperature = 0
        if thermal_zones:
            # get the temperatures and sum them up
            for zone in thermal_zones:
                temperature += float(os.popen('cat '+zone+'/temp').readline().strip())/1000
            # calculate the average
            temperature /= len(thermal_zones)

        usage = self.cpu_load.get_cpu_load()
        return {
            'timestamp': time_to_ISO_string(time.gmtime()),
            'temperature': temperature,
            'usage_percent': usage
        }

    def get_gpu(self):
        # temperature = os.popen('vcgencmd measure_temp').readline()
        # temperature = float(temperature.lstrip('temp=').rstrip("'C\n"))
        # return {
        #     'timestamp': time_to_ISO_string(time.gmtime()),
        #     'temperature': temperature
        # }
        return {
            'timestamp': time_to_ISO_string(time.gmtime()),
            'temperature': 0
        }

    def get_memory(self):
        with open('/proc/meminfo', 'r') as mem:
            tmp = 0
            for i in mem:
                sline = i.split()
                if str(sline[0]) == 'MemTotal:':
                    total = int(sline[1])
                elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                    tmp += int(sline[1])
        total = total / 1024
        free = tmp / 1024
        used = total - free
        usage_percent = (float(used) * 100) / float(total)
        return {
            'timestamp': time_to_ISO_string(time.gmtime()),
            'unit': 'MB',
            'total': total,
            'free': free,
            'used': used,
            'usage_percent': usage_percent
        }


    def reboot(self):
        try:
            check_call(["reboot"])
        except Exception as e:
            raise

    def poweroff(self):
        try:
            check_call(["poweroff"])
        except Exception as e:
            raise

    def set_password(self, old_password, new_password):        
        # test if current password is correct
        child = pexpect.spawn('/usr/bin/sudo -u tooloop /usr/bin/passwd tooloop')
        child.expect('.*current.*')
        child.sendline(old_password)
        child.expect('.*password.*')

        if ('new' in child.after):
            # set new password
            child = pexpect.spawn('/usr/bin/passwd tooloop')
            # repeat it 2 times
            for x in xrange(2):
                child.expect('.*')
                child.sendline(new_password)
                time.sleep(0.1)

        else:
            raise Exception('The old password was not correct.')

    def to_dict(self):
        return {
            'needs_reboot': self.needs_reboot,
            'hostname': self.get_hostname()
            }

    def get_audio_volume(self):
        try:
            for line in check_output('su tooloop -c "pactl --server=/run/user/1000/pulse/native list sinks"', shell=True).split('\n'):
                # find the output lint with the volume
                if 'Volume' in line and not 'Base' in line:
                    # find the first channels’ volume as we are ignoring separate channels
                    for token in line.split():
                        if '%' in token:
                            return int(token.rstrip('%'))
        except Exception as e:
            return 0

    def set_audio_volume(self, volume):
        call('su tooloop -c "pactl --server=/run/user/1000/pulse/native set-sink-volume 0 '+str(volume)+'%"', shell=True)

    def set_audio_mute(self, mute):
        mute_param = '1' if mute else '0'
        call('su tooloop -c "pactl --server=/run/user/1000/pulse/native set-sink-mute 0 '+mute_param+'"', shell=True)

    def get_audio_mute(self):
        try:
            for line in check_output('su tooloop -c "pactl --server=/run/user/1000/pulse/native list sinks"', shell=True).split('\n'):
                if 'Mute' in line:
                    return 'yes' in line
        except Exception as e:
            raise




    def get_display_state(self):
        # check result
        ps = Popen('xset q | grep Monitor', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        try:
            state = output.split()[-1]
        except IndexError as e:
            state = 'unknown'
        return state

    def set_display_state(self, state):
        if not state.lower() in ['on', 'off', 'standby']:
            raise ValueError("Display state can only be one of 'on', 'off' or 'standby'")
        call(['xset', 'dpms', 'force', state.lower()])
        return self.get_display_state()


    def get_startup_schedule(self):
        return self.startup_schedule

    def set_startup_schedule(self, schedule):
        # update data
        if 'enabled' in schedule:
            self.startup_schedule['enabled'] = schedule['enabled']
        if 'weekdays' in schedule:
            self.startup_schedule['weekdays'] = schedule['weekdays']
        if 'time' in schedule:
            if 'hours' in schedule['time']:
                self.startup_schedule['time']['hours'] = int(schedule['time']['hours'])
            if 'minutes' in schedule['time']:
                self.startup_schedule['time']['minutes'] = int(schedule['time']['minutes'])
        # write changes to disk
        try:
            with open(self.app.root_path+'/data/startup-schedule.json', 'w') as json_file:
                json.dump(self.startup_schedule, json_file, indent=4)
        except Exception as e:
            raise e

    def get_shutdown_schedule(self):
        return self.shutdown_schedule

    def set_shutdown_schedule(self, schedule):
        # update data
        if 'enabled' in schedule:
            self.shutdown_schedule['enabled'] = schedule['enabled']
        if 'weekdays' in schedule:
            self.shutdown_schedule['weekdays'] = schedule['weekdays']
        if 'time' in schedule:
            if 'hours' in schedule['time']:
                self.shutdown_schedule['time']['hours'] = int(schedule['time']['hours'])
            if 'minutes' in schedule['time']:
                self.shutdown_schedule['time']['minutes'] = int(schedule['time']['minutes'])
        if 'type' in schedule:
            if schedule['type'] in ['blackout', 'poweroff']:
                self.shutdown_schedule['type'] = schedule['type']
        # write changes to disk
        try:
            with open(self.app.root_path+'/data/shutdown-schedule.json', 'w') as json_file:
                json.dump(self.shutdown_schedule, json_file, indent=4)
        except Exception as e:
            raise e

    def setup_runtime_schedule(self):
        # clear old wake_alarm
        # call('echo 0 > /sys/class/rtc/rtc0/wakealarm', shell=True)
        # clear start_app_and_display cron
        # clear shutdown cron
        # clear blackout cron

        # startup_time = get_next_startup_time

        # if start_up_enabled:
        #     if blackout_enabled:
        #         true:
        #             set_start_app_and_display_cron
        #         false:
        #             set_wakealarm
        
        # if blackout_enabled:
        #     set_blackout_cron

        # if shutdown_enabled:
        #     set_poweroff_cron
        pass



    def get_next_startup_time(self):
        pass