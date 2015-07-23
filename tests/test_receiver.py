# -*- coding: utf-8 -*-
import pytest
from uuid import uuid4
from datetime import datetime
from tests.dummy import OPEN_ROSA_SUCCESS_RESPONSE, dummy_user, dummy_restore_xml

from tests.mock import CaseFactory, CaseStructure, CaseBlock
from tests.utils import post_form_xml, get_restore_payload, synclog_id_from_restore_payload, check_xml_line_by_line

@pytest.mark.usefixtures("config", "test_setup_teardown")
class TestReceiver(object):

    def test_vanilla_form(self, config):
        user_id = str(uuid4())
        form_id = str(uuid4())
        result = post_form_xml(config.receiver_url, config.domain, form_id=form_id,
                user_id=user_id
        )

        assert result.status_code == 201
        assert result.text == OPEN_ROSA_SUCCESS_RESPONSE

    def test_initial_restore(self, config):
        user_id = str(uuid4())
        case_attrs = {
            'create': True,
            'user_id': user_id,
            'owner_id': user_id,
            'case_type': 'duck',
            'update': {'identity': 'mallard'}
        }
        factory = CaseFactory(
            config.receiver_url,
            domain=config.domain,
            form_extras={
                'user_id': user_id,
            }
        )
        [case_block] = factory.create_or_update_cases([
            CaseStructure(attrs=case_attrs),
        ])

        restore_payload = get_restore_payload(config.restore_url, config.domain, dummy_user(user_id))
        synclog_id = synclog_id_from_restore_payload(restore_payload)
        case_xml = case_block.as_string()
        check_xml_line_by_line(
            dummy_restore_xml(dummy_user(user_id), synclog_id, case_xml=case_xml, items=4),
            restore_payload,
        )

    def test_basic_workflow(self, config):
        """
        Sync, create a case
        Verify sync doesn't contain case
        Update case by another user
        Verify sync contains updated case
        """
        user_id = str(uuid4())
        case_id = str(uuid4())
        user = dummy_user(user_id)

        initial_payload = get_restore_payload(config.restore_url, config.domain, user)
        synclog_id = synclog_id_from_restore_payload(
            initial_payload
        )

        # payload should not contain any cases
        check_xml_line_by_line(
            dummy_restore_xml(user, synclog_id, items=3),
            initial_payload,
        )

        factory = CaseFactory(
            config.receiver_url,
            domain=config.domain,
            form_extras={
                'user_id': user_id,
            }
        )
        case_attrs = {
            'create': True,
            'user_id': user_id,
            'owner_id': user_id,
            'case_type': 'gangster',
            'case_name': 'Fish',
            'update': {'last_name': 'Mooney'}
        }
        factory.create_or_update_case(
            CaseStructure(case_id, attrs=case_attrs),
            form_extras={'headers': {'last_sync_token': synclog_id}}
        )

        restore_payload = get_restore_payload(config.restore_url, config.domain, user, since=synclog_id)
        new_synclog_id = synclog_id_from_restore_payload(restore_payload)
        # restore still does not contain case
        check_xml_line_by_line(
            dummy_restore_xml(user, new_synclog_id, items=3),
            restore_payload,
        )

        # update the case
        case_updates = {'cover_job': 'restaurant owner'}
        date_modified = datetime.utcnow()
        factory.create_or_update_case(
            CaseStructure(case_id, attrs={'update': case_updates, 'date_modified': date_modified}),
            form_extras={
                'user_id': user_id,
                # 'headers': {
                #     'last_sync_token': new_synclog_id
                }#}
        )

        restore_payload = get_restore_payload(config.restore_url, config.domain, user, since=new_synclog_id)
        new_new_synclog_id = synclog_id_from_restore_payload(restore_payload)

        case_attrs['create'] = False
        case_attrs['update'].update(case_updates)
        case_block = CaseBlock(case_id, date_modified=date_modified, **case_attrs)
        # restore contain case
        check_xml_line_by_line(
            dummy_restore_xml(user, new_new_synclog_id, case_xml=case_block.as_string(), items=4),
            restore_payload,
        )
