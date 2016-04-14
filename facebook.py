import requests
import time

at = REDACTED!

nxt = 'https://graph.facebook.com/v2.6/me?fields=events.order(chronological){name, description, start_time, end_time, place}&access_token='+at
#nxt = 'https://graph.facebook.com/v2.6/me?fields=events{start_time}&access_token='+at

data = list();

r = requests.get(nxt)
data += r.json()['events']['data']
nxt = r.json()['events']['paging'].get('next',None)

while nxt is not None:
    time.sleep(0.1)
    r = requests.get(nxt)
    data += r.json()['data']
    nxt = r.json()['paging'].get('next',None)

from icalendar import Event, Calendar

cal = Calendar()
for d in data:
    cal.add_component(Event({
        'UID':d['id'],
        'SUMMARY':d['name'],
        'DESCRIPTION':d.get('description', None),
        'DTSTART':d['start_time'],
        'DTEND':d.get('end_time', None),
    }))

with open("dummyfile.ical", 'w') as f:
    f.write(cal.to_ical().decode('UTF-8'))
