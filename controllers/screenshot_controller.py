# -*- coding: utf-8 -*-
from os import listdir
from os.path import isdir
from subprocess import check_call, call

class Screenshots(object):
    """Holds information of the tooloop box."""
    def __init__(self):
        super(Screenshots, self).__init__()
        self.screenshots = []
        self.screenshot_path = '/assets/screenshots/'
        self.scan_screenshots()

    def scan_screenshots(self):
        self.screenshots = []
        directory = listdir(self.screenshot_path)
        for file in directory:
            if not isdir(self.screenshot_path + file) and "thumb" not in file:
                self.screenshots.append({
                    'url': '/screenshots/'+file,
                    'thumbnail_url': '/screenshots/'+file.rstrip('.jpg')+'-thumb.jpg',
                    'date': file.rstrip('.jpg')
                    })
        self.screenshots.sort(key=lambda x : x['date'], reverse=True)

    def get_latest_screenshot(self):
        self.scan_screenshots();
        return self.get_screenshot(0);

    def get_screenshot(self, index):
        self.scan_screenshots();
        return self.screenshots[index];

    def get_screenshot_at_date(self, date):
        self.scan_screenshots();
        return self.get_screenshot(0);

    def grab_screenshot(self):
        try:
            call('su tooloop -c "/opt/tooloop/scripts/tooloop-screenshot"', shell=True)
            return self.get_latest_screenshot()
        except Exception as e:
            raise
