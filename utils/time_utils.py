import time
import datetime

def gmtime_from_string(time_string, format_string):
    return time.gmtime(time.mktime(time.strptime(time_string, format_string)))

# ISO 8601 Extended Format
# YYYY-MM-DDTHH:mm:ss.sssZ
def time_to_ISO_string(gmtime):
    return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', gmtime)

def get_iso_weekday():
    return datetime.datetime.today().isoweekday()

def datetime_to_unix_time_millis(d):
    return int(d.strftime("%s"))