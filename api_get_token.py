import requests
import json
import logging
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

_LOGGER = logging.getLogger(__name__)


AUTH_API_URL = 'https://api.authentication.husqvarnagroup.dev/v1/oauth2/token'
AUTH_HEADERS = {'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'}

MOWER_API_BASE_URL = 'https://api.amc.husqvarna.dev/v1/mowers/'

class GetAccessToken:
    """Class to communicate with the ExampleHub API."""

    def __init__(self, api_key, username, password):
        """Initialize the API and store the auth so we can make requests."""
        self.username = username
        self.password = password
        self.api_key= api_key
        self.auth_data= 'client_id={0}&grant_type=password&username={1}&password={2}'.format(self.api_key,self.username,self.password)

    async def async_get_access_token(self):
        """Return the token"""
        # self.resp = requests.post(url=AUTH_API_URL, headers=AUTH_HEADERS, data=self.auth_data)
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        # return self.resp_raw_dict
        oauth = OAuth2Session(client=LegacyApplicationClient(client_id=self.api_key))
        token = oauth.fetch_token(token_url=AUTH_API_URL, username=self.username, password=self.password, client_id=self.api_key)
        _LOGGER.info(f"{token}")
        return token

class GetMowerData:
    """Class to communicate with the ExampleHub API."""

    def __init__(self, api_key, access_token, provider, token_type):
        """Initialize the API and store the auth so we can make requests."""
        self.api_key= api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_headers = {'Authorization': '{0} {1}'.format(self.token_type,self.access_token),
                        'Authorization-Provider': '{0}'.format(self.provider),
                        'Content-Type': 'application/vnd.api+json',
                        'X-Api-Key': '{0}'.format(self.api_key)}             

    async def async_mower_state(self):
        """Return the token"""
        self.resp = requests.get(MOWER_API_BASE_URL, headers=self.mower_headers)
        self.resp.raise_for_status()
        self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp_raw_dict['data'][0]

class Return:
    """Class to communicate with the ExampleHub API."""

#   mower_parkuntilfurthernotice:
#     url: https://api.amc.husqvarna.dev/v1/mowers/b2bc3443-b31a-4c7f-834e-d6e408c53f1b/actions
#     method: POST
#     headers:
#       authorization: !secret automower_access_token
#       Authorization-Provider: 'husqvarna'
#       Content-Type: 'application/vnd.api+json'
#       X-Api-Key: !secret husqvarna_x_api_key
#     payload: '{"data": {"type": "ParkUntilFurtherNotice"}}'


    def __init__(self, api_key, access_token, provider, token_type, mower_id):
        """Initialize the API and store the auth so we can make requests."""
        self.api_key= api_key
        self.access_token = access_token
        self.provider = provider
        self.token_type = token_type
        self.mower_id = mower_id
        self.mower_headers = {'Authorization': '{0} {1}'.format(self.token_type,self.access_token),
                        'Authorization-Provider': '{0}'.format(self.provider),
                        'Content-Type': 'application/vnd.api+json',
                        'accept': '*/*',
                        'X-Api-Key': '{0}'.format(self.api_key)}             
        self.mower_action_url = f"{MOWER_API_BASE_URL}{self.mower_id}/actions"


    def mower_parkuntilfurthernotice(self):
        """Return the token"""
        self.payload = '{"data": {"type": "ParkUntilFurtherNotice"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code

    def mower_pause(self):
        """Return the token"""
        self.payload = '{"data": {"type": "Pause"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code

    def mower_parkuntilnextschedule(self):
        """Return the token"""
        self.payload = '{"data": {"type": "ParkUntilNextSchedule"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code

    def mower_resumeschedule(self):
        """Resume Scheudele"""
        self.payload = '{"data": {"type": "ResumeSchedule"}}'
        self.resp = requests.post(self.mower_action_url, headers=self.mower_headers, data=self.payload)
        _LOGGER.info("befehl wurde gesendet")
        _LOGGER.info('action_url: {0} \n mower_headers: {1} \n Payload: {2} \n payload_json: {3} \n'.format(self.mower_action_url,self.mower_headers,self.payload,json.dumps(self.payload)))
        _LOGGER.info(f"{self.resp}")
        # self.resp.raise_for_status()
        # self.resp_raw_dict = json.loads(self.resp.content.decode('utf-8'))
        return self.resp.status_code