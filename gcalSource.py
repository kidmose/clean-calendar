import requests
from urllib import urlencode, quote_plus
import json
from subprocess import Popen

CLIENT_ID_FILE = "app-oauth.json"
REFRESH_TOKEN_FILE = "auth.json"

#TODO: Include usage instructions
#TODO: Logging


class Authenticator:
  """
  Implements authentification against googles OAuth 2.0 API

  Usage: 
  >>> scope = ['https://www.googleapis.com/auth/userinfo.profile',
  >>>          'https://www.googleapis.com/auth/userinfo.email',
  >>>          'https://www.googleapis.com/auth/calendar.readonly']
  >>> auth = Authenticator(client_id_file, refresh_token_file, scope)
  >>> access_token = auth.getAccessToken()
  """
  def __init__(self, client_id_file, refresh_token_file, scope):
    """
    Loads relevant data, if available
    """

    client_id = self._loadClientId(client_id_file)
    refresh_token = self._loadRefreshToken(refresh_token_file)
    if refresh_token is None:
      print "Getting tokens through authorization code"
      ac = self._getAuthorizationCode(client_id, scope)
      (access_token, refresh_token) = self._redeemAuthorizationCode(ac, client_id)
      with open(refresh_token_file, 'w+') as f:
        json.dump({'refresh_token': refresh_token}, f)
        
    self.client_id = client_id 
    self.refresh_token = refresh_token
    
  def getAccessToken(self):
    """
    Returns an Access Token and takes care of house keeping. 

    If refresh token is available it is used, 
    if not the user authorization process is followed. 
    """
    print "Getting access tokens with refresh token"
    access_token = self._redeemRefreshToken(self.refresh_token, self.client_id)
    return access_token    

  def _loadClientId(self, client_id_file):
    """ 
    Loads client id and corresponding values from json file. 

    The json file can be downloaded from googles developer console.
    """
    print "Loading client id from %s" % client_id_file 
    try:
      with open(client_id_file, 'r') as f:
        json_data = json.load(f)
      return json_data['installed']
    except:
      print "Failed to load client id"
      raise
    print "Loaded client id"

  def _loadRefreshToken(self, refresh_token_file):
    """
    Loads refresh token from file. 
    """
    print "Loading refresh token from file %s" % refresh_token_file 
    try:
      with open(refresh_token_file, 'r') as f:
        json_data = json.load(f)
        token = json_data['refresh_token']
        print "Refresh token loaded"
        return token
    except:
      print "No refresh token loaded"
      return None

  def _getAuthorizationCode(self, client_id, scope):
    """ Retrieves authorization code. 
    
    TODO: Don't depend in firefox
    """
    print "Getting authorization token"
    req = {
      "response_type": "code",
      "client_id": client_id['client_id'],
      "redirect_uri": client_id['redirect_uris'][0], # Need to pick one from the list
      "scope": (" ".join(scope))
    }
    r = requests.get(client_id['auth_uri'] + "?%s" % urlencode(req),
                     allow_redirects=False, 
    )
    if r.status_code != 302:
      raise Exception("Invalid HTTP status code (%s), response: \n%s)" % (r.status_code, r.text)) 
      
    url = r.headers.get('location')
    Popen(["firefox", url])
    code = raw_input("\nAuthorization Code >>> ")
    print "Authorization Code obtained"
    return code

  def _redeemAuthorizationCode(self, authorization_code, client_id):
    """
    Redeems an authorization code for access and refresh tokens.
    """
    req = {
      "code" : authorization_code,
      "client_id" : client_id['client_id'],
      "client_secret" : client_id['client_secret'],
      "redirect_uri": client_id['redirect_uris'][0], # Need to pick one from the list
      "grant_type": "authorization_code",
    }
    content_length=len(urlencode(req))
    req['content-length'] = str(content_length) #TODO: Investigate if this makes any sense(goes into body...)

    r = requests.post(client_id['token_uri'], 
                      data=req,
    )
    if r.status_code != 200:
      raise Exception("Invalid HTTP status code (%s), response: \n%s)" % (r.status_code, r.text))
    data = r.json()
    print "Tokens obtained from Authorization Code"
    return (data['access_token'], data['refresh_token'])

  def _redeemRefreshToken(self, refresh_token, client_id):
    """
    Redeems a refresh token for a access token and a new refresh token
    """
    req = {
      "refresh_token" : refresh_token,
      "client_id" : client_id['client_id'],
      "client_secret" : client_id['client_secret'],
      "grant_type": "refresh_token",
    }
    content_length=len(urlencode(req))
    req['content-length'] = str(content_length) #TODO: Investigate if this makes any sense(goes into body...)

    r = requests.post(client_id['token_uri'], 
                      data=req,
    )
    if r.status_code != 200:
      raise Exception("Invalid HTTP status code (%s), response: \n%s)" % (r.status_code, r.text))
    data = r.json()
    print "Access token obtained from Refresh Token"
    return data['access_token']

  """
  Authentification header dict
  """
  def getAuthHeader(self):
    return {"Authorization": "OAuth %s" % self.getAccessToken()}


def get_calendar_list():
  global authorization_code
  global access_token

  authorization_code = retrieve_authorization_code()
  tokens = retrieve_tokens(authorization_code)
  access_token = tokens['access_token']
  authorization_header = {"Authorization": "OAuth %s" % access_token}

  r = requests.get("https://www.googleapis.com/calendar/v3/users/me/calendarList",
                   headers=authorization_header,
                 )
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
    r = requests.get(url, 
                     headers=authorization_header,
    )

    events = json.loads(r.text)
    for event in events['items']:
      print event.get('summary', '(Event title not set)')
      if event['status'] != 'cancelled':
        start, end = _get_start_end_time(event)
        print "   start : ", start, "  end : ", end


def main():
  scope = ['https://www.googleapis.com/auth/userinfo.profile',
           'https://www.googleapis.com/auth/userinfo.email',
           'https://www.googleapis.com/auth/calendar.readonly']
  auth = Authenticator(CLIENT_ID_FILE, REFRESH_TOKEN_FILE, scope)
  access_token = auth.getAccessToken()
  
  r = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", 
                   headers=auth.getAuthHeader())
  print r.text

  r = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", 
                   headers=auth.getAuthHeader())
  print r.text

if __name__ == '__main__':
  main()
