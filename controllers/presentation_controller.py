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

    def get_start_script(self):
        return open("/assets/presentation/start-presentation.sh", "r").read()

    def get_stop_script(self):
        return open("/assets/presentation/stop-presentation.sh", "r").read()