# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE, call
from crontab import CronTab

class Services(object):
    """Holds information of the tooloop box."""
    def __init__(self):
        super(Services, self).__init__()
        # self.augtool = augtool

    def is_vnc_running(self):
        ps = Popen('systemctl status x11vnc | grep "active (running)"', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        return output != ""

    def enable_vnc(self):
        call(['systemctl','enable','x11vnc'])
        call(['systemctl','start','x11vnc'])
        pass

    def disable_vnc(self):
        call(['systemctl','disable','x11vnc'])
        call(['systemctl','stop','x11vnc'])
        pass

    def is_ssh_running(self):
        ps = Popen('systemctl status ssh | grep "active (running)"', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        return output != ""

    def enable_ssh(self):
        call(['systemctl','enable','ssh'])
        call(['systemctl','start','ssh'])

    def disable_ssh(self):
        call(['systemctl','disable','ssh'])
        call(['systemctl','stop','ssh'])

    def is_avahi_running(self):
        return False

    def enable_avahi(self):
        pass

    def disable_avahi(self):
        pass

    def is_remote_configuration_running(self):
        return True

    def enable_remote_configuration(self):
        pass

    def disable_remote_configuration(self):
        pass

    def is_screenshot_service_running(self):
        crontab = CronTab(user='tooloop')
        for job in crontab:
            if job.command == 'env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-screenshot' and job.is_enabled():
                return True
        return False

    def enable_screenshot_service(self):
        crontab = CronTab(user='tooloop')
        for job in crontab:
            if job.command == 'env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-screenshot' and not job.is_enabled():
                job.enable()
        crontab.write()

    def disable_screenshot_service(self):
        crontab = CronTab(user='tooloop')
        for job in crontab:
            if job.command == 'env DISPLAY=:0.0 /opt/tooloop/scripts/tooloop-screenshot' and job.is_enabled():
                job.enable(False)
        crontab.write()

    def get_status(self):
        return {
            'vnc': self.is_vnc_running(),
            'ssh': self.is_ssh_running(),
            'avahi': self.is_avahi_running(),
            'remote_configuration': self.is_remote_configuration_running(),
            'screenshot_service': self.is_screenshot_service_running()
            }
