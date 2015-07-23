import ConfigParser
import os
import pytest
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth


class ConfigWrapper(object):
    def __init__(self, config):
        self.config = config

        if self.auth_type == 'basic':
            self.auth = HTTPBasicAuth(self.username, self.password)
        elif self.auth_type == 'digest':
            self.auth = HTTPDigestAuth(self.username, self.password)

    def __getattr__(self, item):
        return self.config.get('main', item)


@pytest.fixture(scope="session")
def config():
    config_file = os.environ['CONFIG']

    config = ConfigParser.ConfigParser()
    config.read(config_file)
    return ConfigWrapper(config)


@pytest.fixture(scope="module")
def test_setup_teardown(request, config):
    def _do_setup_request(start_or_end):
        response = requests.get('{}/{}'.format(config.test_setup_url, start_or_end), auth=config.auth, params={
            'domain': config.domain
        })
        assert response.status_code == 200, response.text

    _do_setup_request('setup')

    def teardown():
        _do_setup_request('tear_down')

    request.addfinalizer(teardown)
