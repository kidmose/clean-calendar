import requests
from urllib import urlencode, quote_plus
import json
from subprocess import Popen

#TODO: Include usage instructions

"""
Client id for use against google OAUTH2 API. 

The identity of this application authorised to the google API.
TODO: Load from JSON file, rather than hard code. 
"""
class ClientId:
  def __init__(self):
    self.client_id = "871810524450-rle77t9mrhoob7ab3aq67gsfjqvf9fea.apps.googleusercontent.com"
    self.client_secret = "22AZcKwoLratSWsduL_piarS"
    self.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    self.base_url = r"https://accounts.google.com/o/oauth2/"

""" 
Authorization code.

Authorisation code from google oauth2 api, retrieved on initialisation. 
TODO: Store result in file
TODO: Load result from file
TODO: Don't depend in firefox
"""
class AuthorizationCode:
  def __init__(self, localfile, clientid, scope):
    req = {
      "response_type": "code",
      "client_id": clientid.client_id,
      "redirect_uri": clientid.redirect_uri,
      "scope": (" ".join(scope))
    }
    r = requests.get(clientid.base_url + "auth?%s" % urlencode(req),
                     allow_redirects=False)

    url = r.headers.get('location')
    Popen(["firefox", url])

    self.code = raw_input("\nAuthorization Code >>> ")
    self.clientid = clientid

"""
Access Token
"""
class AccessToken:
  def __init__(self, authcode): 
    req = {
      "code" : authcode.code,
      "client_id" : authcode.clientid.client_id,
      "client_secret" : authcode.clientid.client_secret,
      "redirect_uri" : authcode.clientid.redirect_uri,
      "grant_type": "authorization_code",
    }
    content_length=len(urlencode(req))
    req['content-length'] = str(content_length)

    r = requests.post(authcode.clientid.base_url + "token", data=req)
    data = json.loads(r.text)

    self.access_token = data['access_token']

  """
  Quthentification header dict
  """
  def getHeader(self):
    return {"Authorization": "OAuth %s" % self.access_token}

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
  cid = ClientId()
  ac = AuthorizationCode(
    None, 
    cid, 
    ['https://www.googleapis.com/auth/userinfo.profile',
     'https://www.googleapis.com/auth/userinfo.email',
     'https://www.googleapis.com/auth/calendar.readonly'],
  )
  at = AccessToken(ac)
  
  r = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", 
                   headers=at.getHeader())
  print r.text
  


if __name__ == '__main__':
  main()
