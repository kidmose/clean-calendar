#!/usr/bin/python

import sys, os
from icalendar import Calendar, Event
import requests

class HttpSources:
    def __init__(self, url):
        self._url = url
    def get(self):
        r = requests.get(url)
        cal = Calendar.from_ical(r.content)
        return cal

class Cleaner:
    def __init__(self, outputable, override):
        self._outputable = outputable
        self._override = override
    def clean(self, cal):
        events = [ e for e in cal.subcomponents if isinstance(e, Event) ]
        out = Calendar()

        for e in events:
            items = [ (k,v) for (k,v) in e.items() if k in outputable ]
            for k,v in override.items():
                items.append((k, v))
                out.add_component(Event(items))
        return out

class FilePublisher:
    def __init__(self, filename):
        self._filename = filename
    def publish(self, cal):
        with open(filename, 'wb') as f:
            f.write(cal.to_ical())

url = sys.argv[1]
orig_cal = HttpSources(url).get()

outputable = ( 
    "STATUS", 
    "DTSTART", 
    "DTEND", 
    "DURATION", 
    "TRANSP",
    "STATUS",
)
override = {
    "SUMMARY": "Private",
}
clean_cal = Cleaner(outputable, override).clean(orig_cal)
    
filename = os.path.join(os.path.dirname(sys.argv[0]), "clean-calendar.ics")
FilePublisher(filename).publish(clean_cal)
