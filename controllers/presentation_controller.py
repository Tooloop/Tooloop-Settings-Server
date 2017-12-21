# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE, call
import os

class Presentation(object):
    """Holds information of the installed presentation."""
    def __init__(self):
        super(Presentation, self).__init__()

    def start(self):
        return call(['/bin/bash', '/assets/presentation/start-presentation.sh'])

    def stop(self):
        return call(['/bin/bash', '/assets/presentation/stop-presentation.sh'])

    def reset(self):
        self.stop()
        self.start()

    def display_on(self):
        call(['xset', 'dpms', 'force', 'on'])
        return self.check_display_state()

    def display_off(self):
        call(['xset', 'dpms', 'force', 'off'])
        return self.check_display_state()

    def check_display_state(self):
        # check result
        ps = Popen('xset q | grep Monitor', shell=True, stdout=PIPE)
        output = ps.stdout.read()
        ps.stdout.close()
        ps.wait()
        return output.split()[-1]

    def get_start_script(self):
        return open("/assets/presentation/start-presentation.sh", "r").read()

    def get_stop_script(self):
        return open("/assets/presentation/stop-presentation.sh", "r").read()