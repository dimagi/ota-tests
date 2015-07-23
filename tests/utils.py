import base64
from datetime import datetime
from uuid import uuid4
from xml.etree import ElementTree
import requests
from lxml import etree

ISO_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
ISO_DATE_FORMAT = '%Y-%m-%d'
SYNC_XMLNS = "http://commcarehq.org/sync"


def json_format_datetime(dt):
    """
    includes microseconds (always)
    >>> json_format_datetime(datetime.datetime(2015, 4, 8, 12, 0, 1))
    '2015-04-08T12:00:01.000000Z'
    """
    return dt.strftime(ISO_DATETIME_FORMAT)


def json_format_date(date_):
    return date_.strftime(ISO_DATE_FORMAT)


def synclog_id_from_restore_payload(restore_payload):
    element = ElementTree.fromstring(restore_payload)
    return element.findall('{%s}Sync' % SYNC_XMLNS)[0].findall('{%s}restore_id' % SYNC_XMLNS)[0].text


def get_restore_payload(endpoint_url, domain, user, since=None):
    if endpoint_url[-1] == '/':
        endpoint_url = endpoint_url[:-1]

    headers = {'Authorization': 'Basic ' + base64.b64encode('{}:{}'.format(user.username, user.password))}
    result = requests.get(
        '{endpoint_url}/{domain}?version=2.0&items=true&user_id={user_id}{since}'.format(
            endpoint_url=endpoint_url,
            domain=domain,
            user_id=user.user_id,
            since='&since={}'.format(since) if since else ''),
        headers=headers
    )
    assert result.status_code == 200
    return result.text


MOCK_FORM = """<?xml version='1.0' ?>
<system version="1" uiVersion="1" xmlns="http://commcarehq.org/case">
    <meta xmlns="http://openrosa.org/jr/xforms">
        <deviceID />
        <timeStart>{time}</timeStart>
        <timeEnd>{time}</timeEnd>
        <username>{username}</username>
        <userID>{user_id}</userID>
        <instanceID>{uid}</instanceID>
    </meta>
    {case_block}
</system>"""


def post_form_xml(endpoint_url, domain, case_blocks=None, form_id=None, username=None, user_id=None, headers=None):
    """
    Post form to endpoint URL.
    """
    if endpoint_url[-1] == '/':
        endpoint_url = endpoint_url[:-1]

    now = json_format_datetime(datetime.utcnow())
    case_blocks = case_blocks or ''
    if not isinstance(case_blocks, basestring):
        case_blocks = ''.join([ElementTree.tostring(cb) for cb in case_blocks])

    form_xml = MOCK_FORM.format(**{
        'case_block': case_blocks,
        'time': now,
        'uid': form_id or str(uuid4()),
        'username': username or 'bob',
        'user_id': user_id or str(uuid4()),
    })

    headers = {'Authorization': 'Basic ' + base64.b64encode('admin:secret')}
    headers.update(headers or {})
    result = requests.post(
        '{}/{}'.format(endpoint_url, domain),
        headers=headers,
        data=form_xml
    )
    return result


def check_xml_line_by_line(expected, actual):
    """Does what it's called, hopefully parameters are self-explanatory"""
    # this is totally wacky, but elementtree strips needless
    # whitespace that mindom will preserve in the original string
    parser = etree.XMLParser(remove_blank_text=True)
    parsed_expected = etree.tostring(etree.XML(expected, parser), pretty_print=True)
    parsed_actual = etree.tostring(etree.XML(actual, parser), pretty_print=True)

    if parsed_expected == parsed_actual:
        return

    try:
        expected_lines = parsed_expected.split("\n")
        actual_lines = parsed_actual.split("\n")
        assert len(expected_lines) == len(actual_lines), ("Parsed xml files are different lengths\n" +
            "Expected: \n%s\nActual:\n%s" % (parsed_expected, parsed_actual))

        for i in range(len(expected_lines)):
            assert expected_lines[i] == actual_lines[i]

    except AssertionError:
        import logging
        logging.error("Failure in xml comparison\nExpected:\n%s\nActual:\n%s" % (parsed_expected, parsed_actual))
        raise
