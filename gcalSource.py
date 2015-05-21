# -*- coding: utf-8 -*-

import requests
from urllib import urlencode, quote_plus
import json
from subprocess import Popen

client_id = "871810524450-rle77t9mrhoob7ab3aq67gsfjqvf9fea.apps.googleusercontent.com"
client_secret = "22AZcKwoLratSWsduL_piarS"
redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
base_url = r"https://accounts.google.com/o/oauth2/"
authorization_code = ""
access_token = ""

"""
Retrieving authorization_code from authorization API.
"""
def retrieve_authorization_code():
  authorization_code_req = {
    "response_type": "code",
    "client_id": client_id,
    "redirect_uri": redirect_uri,
    "scope": (r"https://www.googleapis.com/auth/userinfo.profile" +
              r" https://www.googleapis.com/auth/userinfo.email" +
              r" https://www.googleapis.com/auth/calendar.readonly")
    }

  r = requests.get(base_url + "auth?%s" % urlencode(authorization_code_req),
                   allow_redirects=False)
  print "Something gibberish"
  url = r.headers.get('location')
  Popen(["firefox", url])

  authorization_code = raw_input("\nAuthorization Code >>> ")
  return authorization_code


"""
Retrieving access_token and refresh_token from Token API.
"""
def retrieve_tokens(authorization_code):
  access_token_req = {
    "code" : authorization_code,
    "client_id" : client_id,
    "client_secret" : client_secret,
    "redirect_uri" : redirect_uri,
    "grant_type": "authorization_code",
    }
  content_length=len(urlencode(access_token_req))
  access_token_req['content-length'] = str(content_length)

  r = requests.post(base_url + "token", data=access_token_req)
  data = json.loads(r.text)
  return data



"""
Sample code of fetching user information from userinfo API.
"""
def get_userinfo():
  global authorization_code
  authorization_code = retrieve_authorization_code()
  tokens = retrieve_tokens(authorization_code)
  access_token = tokens['access_token']
  authorization_header = {"Authorization": "OAuth %s" % access_token}
  r = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", 
                   headers=authorization_header)
  print r.text



def get_calendar_list():
  global authorization_code
  global access_token

  authorization_code = retrieve_authorization_code()
  tokens = retrieve_tokens(authorization_code)
  access_token = tokens['access_token']
  authorization_header = {"Authorization": "OAuth %s" % access_token}

  r = requests.get("https://www.googleapis.com/calendar/v3/users/me/calendarList",
                   headers=authorization_header)
  return r.text


def _get_start_end_time(event):
  try:
    if event['start'].has_key('date'):
      start = event['start']['date']
    elif event['start'].has_key('dateTime'):
      start = event['start']['dateTime']
    else:
      start = 'N/A'

    if event['end'].has_key('date'):
      end = event['end']['date']
    elif event['end'].has_key('dateTime'):
      end = event['end']['dateTime']
    else:
      end = 'N/A'
    return start, end

  except:
    return event['etag'], event['status']


def get_events_list():
  global authorization_code
  global access_token

  data = json.loads(get_calendar_list())
  for calendar in data['items']:
    calendar_id = calendar['id']
    print calendar['summary']

    if authorization_code == "" or access_token == "":
      authorization_code = retrieve_authorization_code()
      tokens = retrieve_tokens(authorization_code)
      access_token = tokens['access_token']
    
    authorization_header = {"Authorization": "OAuth %s" % access_token}
    url = ("https://www.googleapis.com/calendar/v3/calendars/%s/events" % 
           (quote_plus(calendar_id), ))
    r = requests.get(url, headers=authorization_header)

    events = json.loads(r.text)
    for event in events['items']:
      print event.get('summary', '(Event title not set)')
      if event['status'] != 'cancelled':
        start, end = _get_start_end_time(event)
        print "   start : ", start, "  end : ", end


def main():
  get_events_list()


if __name__ == '__main__':
  main()
