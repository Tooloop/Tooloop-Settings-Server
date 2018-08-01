import time

def gmtime_from_string(time_string, format_string):
    return time.gmtime(time.mktime(time.strptime(time_string, format_string)))

# ISO 8601 Extended Format
# YYYY-MM-DDTHH:mm:ss.sssZ
def time_to_ISO_string(gmtime):
    return time.strftime('%Y-%m-%dT%H:%M:%S.000Z', gmtime)

def time_to_unix_epoch_time(gmtime):
    return 0
