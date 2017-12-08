# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE, call
import os

class Presentation(object):
    """Holds information of the installed presentation."""
    def __init__(self):
        super(Presentation, self).__init__()

    def start(self):
        # try:
        # call(['export', 'DISPLAY=:0'])
        # call(['export', 'XAUTHORITY=~/.Xauthority'])

        return call(['/bin/sh', '/assets/presentation/start-presentation.sh'])
        # except Exception as e:
        #     raise

    def stop(self):
        try:
            return call(['/bin/sh', '/assets/presentation/stop-presentation.sh'])
        except Exception as e:
            raise

    def reset(self):
        try:
            self.stop()
            self.start()
        except Exception as e:
            raise

    def display_on(self):
        try:
            call(['xset', 'dpms', 'force', 'on'])
            return self.check_display_state()
        except Exception as e:
            raise

    def display_off(self):
        try:
            call(['xset', 'dpms', 'force', 'off'])
            return self.check_display_state()
        except Exception as e:
            raise

    def check_display_state(self):
        # check result
        ps = Popen('xset q | grep Monitor', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        return output.split()[-1]

    def get_start_script(self):
        try:
            return open("/assets/presentation/start-presentation.sh", "r").read()
        except Exception as e:
            raise

    def get_stop_script(self):
        try:
            return open("/assets/presentation/stop-presentation.sh", "r").read()
        except Exception as e:
            raise
