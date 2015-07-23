from collections import namedtuple
from datetime import datetime

DUMMY_USERNAME = "admin"
DUMMY_PASSWORD = "secret"

User = namedtuple('User', 'username, password, user_id')

def dummy_user(user_id, username=None, password=None):
    return User(user_id=user_id,
                username=username or DUMMY_USERNAME,
                password=password or DUMMY_PASSWORD)


def dummy_user_xml(user):
        return """
    <Registration xmlns="http://openrosa.org/user/registration">
        <username>{u.username}</username>
        <password>{u.password}</password>
        <uuid>{u.user_id}</uuid>
        <date>2011-06-09</date>
        <user_data>
            <data key="commcare_first_name"/>
            <data key="commcare_last_name"/>
            <data key="something">arbitrary</data>
            <data key="commcare_phone_number"/>
        </user_data>
    </Registration>""".format(u=user)


DUMMY_RESTORE_XML_TEMPLATE = ("""
<OpenRosaResponse xmlns="http://openrosa.org/http/response"%(items_xml)s>
    <message nature="ota_restore_success">%(message)s</message>
    <Sync xmlns="http://commcarehq.org/sync">
        <restore_id>%(restore_id)s</restore_id>
    </Sync>
    %(user_xml)s
    %(case_xml)s
</OpenRosaResponse>
""")


OPEN_ROSA_SUCCESS_RESPONSE = (
    '<OpenRosaResponse xmlns="http://openrosa.org/http/response">'
    '<message nature="submit_success">Thanks for submitting!</message>'
    '</OpenRosaResponse>'
)


def dummy_restore_xml(user, restore_id, case_xml="", items=None):
    return DUMMY_RESTORE_XML_TEMPLATE % {
        "restore_id": restore_id,
        "items_xml": '' if items is None else (' items="%s"' % items),
        "user_xml": dummy_user_xml(user),
        "case_xml": case_xml,
        "message": "Successfully restored account {}!".format(user.username)
    }
