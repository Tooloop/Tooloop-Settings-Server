# -*- coding: utf-8 -*-
from subprocess import check_output, check_call, Popen, PIPE
    
import time
import pexpect
from utils.time_utils import *
from utils.cpu_load import CpuLoad


class System(object):
    """Holds information of the tooloop box."""
    def __init__(self, augtool):
        super(System, self).__init__()
        self.augtool = augtool
        self.cpu_load = CpuLoad()
        self.needs_reboot = False

    def get_hostname(self):
        try:
            return self.augtool.get("/files/etc/hostname/hostname")
        except Exception as e:
            raise

    def set_hostname(self, hostname):
        old_hostname = self.get_hostname()

        # nothing to do
        if hostname == old_hostname: return

        try:
            # change /etc/hostname
            self.augtool.set("/files/etc/hostname/hostname", hostname)
            self.augtool.save()
        except Exception as e:
            raise

        try:
            # change /etc/hosts
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
