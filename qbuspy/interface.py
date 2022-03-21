from __future__ import annotations
import dataclasses
from enum import Enum
from typing import Dict, Optional
import random
import json
import requests

from .exceptions import QBusResponseException, QbusCredentialException


class Commands(Enum):
    ERROR = 0
    LOGIN = 1
    LOGIN_RESPONSE = 2
    GET_GROUPS = 10
    GET_GROUPS_RESPONSE = 11
    SET_STATUS = 12
    SET_STATUS_RESPONSE = 13
    GET_STATUS = 14
    GET_STATUS_RESPONSE = 15
    GET_MENU_STATUS = 16
    GET_MENU_STATUS_RESPONSE = 17


class ChannelType(Enum):
    TOGGLE = 0
    DIMMER = 1
    SET_TEMP = 2
    PROG_TEMP = 3
    SHUTTERS = 4
    AUDIO = 5
    SCENES = 7
    RENSON = 8


@dataclasses.dataclass
class QbusChannel():
    name: str
    id: int
    channel_type: int
    group_name: str
    value: Optional[int] = None

    @classmethod
    def from_response(cls, response: dict, group_name: str):
        # legacy support for older eqo-web versions
        value = response['Val']
        if isinstance(value, list):
            value = value[0]
        return cls(response['Nme'], response['Chnl'], response['Ico'],
                   group_name, value)

    def __repr__(self):
        return f'<QbusChannel type={ChannelType(self.channel_type)} id= {self.id} name={self.name} value={self.value}>'


class QbusInterface:
    """
    This class is used to interact with the Qbus EQOWeb API.
    """

    def __init__(self,
                 url: str,
                 user: str = "QBUS",
                 password: str = "",
                 timeout: int = 1):
        """
        Initialize the QbusInterface.

        :param url: The url of the Qbus API.
        :param user: The user name to use for authentication.
        :param password: The password to use for authentication.
        :param timeout: The timeout for the request in seconds.
        """
        self.url = url
        self.user = user
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"})
        self._channels = None

        # self.login()

    def login(self) -> str:
        message = {
            'Type': Commands.LOGIN.value,
            'Value': {
                'Usr': self.user,
                'Psw': self.password
            }
        }
        data = self._request(message)
        if not data['Value']['rsp']:
            raise QbusCredentialException('Login or password is wrong')
        # return data['Value']['id']

    def get_channels(self, refresh: bool = True) -> Dict[int, QbusChannel]:
        if self._channels is None or refresh:
            message = {'Type': Commands.GET_GROUPS.value, 'Value': None}
            data = self._request(message)
            channels = {}
            for group in data['Value']['Groups']:
                group_name = group['Nme']
                for channel_resp in group['Itms']:
                    channel = QbusChannel.from_response(
                        channel_resp, group_name)
                    channels[channel.id] = channel
            self._channels = channels
        return list(self._channels.values())

    def set_channel(self, channel: QbusChannel, value: int):
        message = {'Type': 12, 'Value': {'Chnl': channel.id, 'Val': [value]}}
        self._request(message)
        channel.value = value

    def get_events(self) -> Dict[QbusChannel]:
        """
        Check if a channel changed its value.

        :return: The channels that changed their value.
        """
        old_channels = self._channels
        new_channels = self.get_channels(refresh=True)
        events = {}
        for channel in new_channels:
            if old_channels[channel.id].value != new_channels[
                    channel.id].value:
                events[channel.id] = channel
        return events

    def _request(self, message: dict) -> requests.Response:
        """
        Make a request to the Qbus API.

        :param message: The request data.
        :return: The response from the request.
        """

        data = {'strJSON': json.dumps(message, separators=(',', ':'))}
        params = (('r', random.random()), )

        r = self.session.post(f'{self.url}/default.aspx',
                              data=data,
                              params=params,
                              timeout=self.timeout)
        json_respons = r.json()
        if 'Value' not in json_respons:
            raise ValueError(f'Bad response: {data}')

        if 'Error' in json_respons['Value']:
            raise QBusResponseException(data["Value"]['Error'])

        return json_respons
