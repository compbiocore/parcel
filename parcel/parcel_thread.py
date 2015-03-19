from ctypes import create_string_buffer
from utils import state_method, vec
import json
from math import ceil
import urlparse
from log import get_logger

from const import (
    # Lengths
    LEN_CONTROL, LEN_PAYLOAD_SIZE,
    # Control messages
    CNTL_EXIT,
    # States
    STATE_IDLE,
)
from utils import (
    distribute, construct_header, check_status_code, parse_file_header
)
from lib import lib
import requests

# Logging
log = get_logger('parcel')


class ParcelThread(object):

    def __init__(self, instance, socket, close_func):
        """
        Creates a new udpipeClient instance from shared object library
        """

        self.state = STATE_IDLE
        self.encryptor = None
        self.decryptor = None
        self.instance = instance
        self.socket = socket
        self.close_func = close_func
        self.uri = None
        self.token = None
        log.debug('New instance {}'.format(self))

    def __repr__(self):
        return '<{}({}, {})>'.format(
            type(self).__name__, self.instance, self.socket)

    def assert_encryption(self):
        assert self.encryptor, 'Encryptor not initialized'
        assert self.decryptor, 'Decryptor not initialized'

    ############################################################
    #                     Library Wrappers
    ############################################################

    def read_size(self, size, encryption=True):
        buff = create_string_buffer(size)
        if encryption:
            self.assert_encryption()
            rs = lib.read_size(self.decryptor, self.socket, buff, size)
        else:
            rs = lib.read_size_no_encryption(self.socket, buff, size)
        if (rs == -1):
            raise Exception('Unable to read from socket.')
        return buff.value

    def send(self, data, size=None, encryption=True, encrypt_inplace=False):
        if encrypt_inplace and encryption:
            assert isinstance(data, str)
            to_send = (data+'\0')[:-1]
        else:
            to_send = data
        if size is None:
            size = len(data)
        if encryption:
            self.assert_encryption()
            ss = lib.send_data(self.encryptor, self.socket, to_send, size)
        else:
            ss = lib.send_data_no_encryption(self.socket, to_send, size)
        if ss != size:
            raise RuntimeError('Unable to write to socket.')

    ############################################################
    #                     Transfer Functions
    ############################################################

    def send_payload_size(self, size, **send_args):
        buff = create_string_buffer(LEN_PAYLOAD_SIZE)
        buff.value = str(size)
        self.send(buff, LEN_PAYLOAD_SIZE, **send_args)

    def read_payload_size(self, **read_args):
        payload_size = int(self.read_size(LEN_PAYLOAD_SIZE, **read_args))
        return payload_size

    def next_payload(self, **read_args):
        payload_size = self.read_payload_size(**read_args)
        return self.read_size(payload_size, **read_args)

    def send_payload(self, payload, size=None, **send_args):
        if size is None:
            size = len(payload)
        self.send_payload_size(size, **send_args)
        self.send(payload, size, **send_args)

    def send_control(self, cntl, **send_args):
        cntl_buff = create_string_buffer(LEN_CONTROL)
        cntl_buff.raw = cntl
        self.send(cntl_buff, LEN_CONTROL, **send_args)

    def recv_control(self, expected=None, **read_args):
        cntl = self.read_size(LEN_CONTROL, **read_args)
        log.debug('CONTROL: {}'.format(ord(cntl)))
        if expected is not None and cntl not in vec(expected):
            raise RuntimeError('Unexpected control msg: {} != {}'.format(
                ord(cntl), ord(expected)))
        return cntl

    def send_json(self, doc, **send_args):
        payload = json.dumps(doc)
        self.send_payload(payload, size=len(payload), **send_args)

    def read_json(self, **read_args):
        return json.loads(self.next_payload(**read_args))

    ############################################################
    #                     State Functions
    ############################################################

    def close(self):
        self.close_func(self.instance)

    @state_method(STATE_IDLE)
    def handshake(self, *args, **kwargs):
        raise NotImplementedError()

    @state_method('handshake')
    def authenticate(self, *args, **kwargs):
        raise NotImplementedError()

    ############################################################
    #                          Util
    ############################################################

    def split_file(self, size, blocks):
        block_size = int(ceil(float(size)/blocks))
        segments = distribute(0, size, block_size)
        return segments, block_size

    ############################################################
    #                   REST API Functions
    ############################################################

    def request_file_information(self):
        url = urlparse.urljoin(self.uri, self.file_id)
        headers = construct_header(self.token)
        log.info('Request to {}'.format(url))
        size, name = self.make_file_request(url, headers)
        return name, size

    def make_file_request(self, url, headers, verify=False):
        """Make request for file, just get the header.

        """
        r = requests.get(url, headers=headers, verify=verify, stream=True)
        check_status_code(r, url)
        size, file_name = parse_file_header(r, url)
        r.close()
        return size, file_name
