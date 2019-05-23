# -*- coding: utf-8 -*-
from subprocess import check_output, check_call, Popen, PIPE, call
import os
import time
import pexpect
import fileinput
import json
import datetime
from utils.time_utils import *
from utils.cpu_load import CpuLoad
from crontab import CronTab


class System(object):
    """Holds information of the tooloop box."""
    def __init__(self, app):
        super(System, self).__init__()
        self.app = app
        self.cpu_load = CpuLoad()
        self.needs_reboot = False
        # read runtime schedule from disk
        try:
            with open(self.app.root_path+'/data/runtime-schedule.json') as json_data:
                self.runtime_schedule = json.load(json_data)
        except Exception as e:
            self.runtime_schedule = {
                'startup': {
                    'enabled': False, 
                    'weekdays': [], 
                    'time': {
                        'hours': 8, 
                        'minutes': 0
                    }
                },
                'shutdown': {
                    'enabled': False, 
                    'type': 'poweroff', 
                    'weekdays': [], 
                    'time': {
                        'hours': 20, 
                        'minutes': 0
                    }
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
            return check_output(['hostname', '-i']).rstrip('\n').split()[0]
        except IndexError as e:
            return ''
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
        packages = int(os.popen('du -s -B1 /assets/packages').readline().split()[0])
        data = int(os.popen('du -s -B1 /assets/data').readline().split()[0])
        logs = int(os.popen('du -s -B1 /assets/logs').readline().split()[0])
        presentation = int(os.popen('du -s -B1 /assets/presentation').readline().split()[0])
        screenshots = int(os.popen('du -s -B1 /assets/screenshots').readline().split()[0])

        return {
            'unit': 'Byte',
            'size': size,
            'data': data,
            'logs': logs,
            'packages': packages,
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


    def get_runtime_schedule(self):
        return self.runtime_schedule

    def set_runtime_schedule(self, schedule):
        # update data
        self.set_single_schedule('startup', schedule)
        self.set_single_schedule('shutdown', schedule)
        # write changes to disk
        try:
            with open(self.app.root_path+'/data/runtime-schedule.json', 'w') as json_file:
                json.dump(self.runtime_schedule, json_file, indent=4)
        except Exception as e:
            raise e
        # set up the rtc wakealarm and cron jobs
        self.setup_runtime_schedule()

    def set_single_schedule(self, which, schedule):
        if which in schedule:
            if 'enabled' in schedule[which]:
                self.runtime_schedule[which]['enabled'] = schedule[which]['enabled']
            if 'type' in schedule[which]:
                if schedule[which]['type'] in ['blackout', 'poweroff']:
                    self.runtime_schedule[which]['type'] = schedule[which]['type']
            if 'weekdays' in schedule[which]:
                self.runtime_schedule[which]['weekdays'] = schedule[which]['weekdays']
            if 'time' in schedule[which]:
                if 'hours' in schedule[which]['time']:
                    self.runtime_schedule[which]['time']['hours'] = int(schedule[which]['time']['hours'])
                if 'minutes' in schedule[which]['time']:
                    self.runtime_schedule[which]['time']['minutes'] = int(schedule[which]['time']['minutes'])
        

    def setup_runtime_schedule(self):
        crontab = CronTab(user='tooloop')
        
        # empty wakealarm
        call('echo 0 > /sys/class/rtc/rtc0/wakealarm', shell=True)

        # remove cron jobs
        crontab.remove_all('display-on')
        crontab.remove_all('poweroff')
        crontab.remove_all('blackout')
        crontab.write()

        # start up
        if self.runtime_schedule['startup']['enabled'] and len(self.runtime_schedule['startup']['weekdays']) > 0:
            if self.runtime_schedule['shutdown']['type'] == 'poweroff':
                # set rtc wake alarm
                call('echo '+str(self.get_next_startup_time())+' > /sys/class/rtc/rtc0/wakealarm', shell=True)
            elif self.runtime_schedule['shutdown']['type'] == 'blackout':
                # set startup cron job
                job = crontab.new(command='env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-display-on && env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-presentation-reset')
                job.hour.on(self.runtime_schedule['startup']['time']['hours'])
                job.minute.on(self.runtime_schedule['startup']['time']['minutes'])
                job.dow.on(*self.runtime_schedule['startup']['weekdays'])
                crontab.write()

        # shutdown
        if self.runtime_schedule['shutdown']['enabled'] and len(self.runtime_schedule['shutdown']['weekdays']) > 0:
            if self.runtime_schedule['shutdown']['type'] == 'poweroff':
                job = crontab.new(command='sudo poweroff')
            elif self.runtime_schedule['shutdown']['type'] == 'blackout':
                job = crontab.new(command='env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-blackout')
            job.hour.on(self.runtime_schedule['shutdown']['time']['hours'])
            job.minute.on(self.runtime_schedule['shutdown']['time']['minutes'])
            job.dow.on(*self.runtime_schedule['shutdown']['weekdays'])
            crontab.write()



    def get_next_startup_time(self):
        # What weeday is today?
        weekday = get_iso_weekday()

        # What’s the next weekday to start up?
        next_weekday = min(self.runtime_schedule['startup']['weekdays'])
        for day in sorted(self.runtime_schedule['startup']['weekdays']):
            if day > weekday:
                next_weekday = day
                break

        # Create a date of today at start up time
        next_startup = datetime.datetime.today().replace(
            hour=self.runtime_schedule['startup']['time']['hours'],
            minute=self.runtime_schedule['startup']['time']['minutes'],
            second=0, 
            microsecond=0
        )

        # If it is after the daily startup time,
        # add the days between today and the next startup day
        now = datetime.datetime.now().time()
        startup_time = datetime.time(
            hour=self.runtime_schedule['startup']['time']['hours'],
            minute=self.runtime_schedule['startup']['time']['minutes']
        )
        if now > startup_time:
            delta_days = ((next_weekday + 7) - weekday) % 7
            next_startup += datetime.timedelta(days=delta_days)

        # Convert time to unix epoch time (in time utils)
        return datetime_to_unix_time_millis(next_startup)