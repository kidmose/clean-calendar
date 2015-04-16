#!/usr/bin/python

import sys, os
from icalendar import Calendar, Event
import requests

url = sys.argv[1]
r = requests.get(url)
ical = Calendar.from_ical(r.content)
events = [ e for e in ical.subcomponents if isinstance(e, Event) ]

out = Calendar()
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
    
for e in events:
    items = [ (k,v) for (k,v) in e.items() if k in outputable ]
    for (k,v) in override:
        items.append((k, v))
    out.add_component(Event(items))

filename = os.path.join(os.path.dirname(sys.argv[0]), "clean-calendar.ics")
with open(filename, 'wb') as f:
    f.write(out.to_ical())


