# -*- coding: utf-8 -*-
import base64
from uuid import uuid4

import pytest
import requests
from tests.dummy import OPEN_ROSA_SUCCESS_RESPONSE, dummy_user, dummy_restore_xml

from tests.mock import CaseFactory, CaseStructure, post_case_blocks, CaseRelationship, CaseBlock
from tests.utils import post_form_xml, get_restore_payload, synclog_id_from_restore_payload, check_xml_line_by_line

DOMAIN = 'test_domain'

class TestReceiver(object):

    def test_vanilla_form(self):
        user_id = str(uuid4())
        form_id = str(uuid4())
        result = post_form_xml('http://localhost:5000/ota/receiver/', DOMAIN, form_id=form_id,
                user_id=user_id
        )

        assert result.status_code == 201
        assert result.text == OPEN_ROSA_SUCCESS_RESPONSE

    def test_create_case(self):
        user_id = str(uuid4())
        form_id = str(uuid4())
        case_id = str(uuid4())
        synclog_id = synclog_id_from_restore_payload(
            get_restore_payload('http://localhost:5000/ota/restore/', DOMAIN, dummy_user(user_id))
        )
        case_attrs = {
            'create': True,
            'user_id': user_id,
            'owner_id': user_id,
            'case_type': 'duck',
            'update': {'identity': 'mallard'}
        }
        factory = CaseFactory(
            'http://localhost:5000/ota/receiver/',
            domain=DOMAIN,
            form_extras={
                'user_id': user_id,
                'headers': {
                    'last_sync_token': synclog_id
                }
            }
        )
        [case_block] = factory.create_or_update_cases([
            CaseStructure(case_id, attrs=case_attrs),
        ], form_extras={
            'form_id': form_id,
        })

        restore_payload = get_restore_payload('http://localhost:5000/ota/restore/', DOMAIN, dummy_user(user_id))
        new_synclog_id = synclog_id_from_restore_payload(restore_payload)
        case_xml = case_block.as_string()
        # case block should come back
        check_xml_line_by_line(
            dummy_restore_xml(dummy_user(user_id), new_synclog_id, case_xml=case_xml, items=4),
            restore_payload,
        )
    #
    # def test_update_case(self, testapp, client):
    #     user_id = str(uuid4())
    #     case_id = str(uuid4())
    #     synclog_id = create_synclog(DOMAIN, user_id)
    #     with testapp.app_context():
    #         factory = CaseFactory(
    #             client,
    #             domain=DOMAIN,
    #             case_defaults={
    #                 'user_id': user_id,
    #                 'owner_id': user_id,
    #                 'case_type': 'duck',
    #             },
    #             form_extras={
    #                 'headers': {
    #                     'last_sync_token': synclog_id
    #                 }
    #             }
    #         )
    #         factory.create_or_update_cases([
    #             CaseStructure(case_id, attrs={'create': True}),
    #         ])
    #
    #         self._assert_case(case_id, user_id)
    #         self._assert_synclog(synclog_id, case_ids=[case_id])
    #
    #         updated_case, = factory.create_or_update_case(
    #             CaseStructure(case_id, attrs={'update': {'identity': 'mallard'}, 'close': True})
    #         )
    #
    #         assert updated_case.identity == 'mallard'
    #         assert updated_case.closed is True
    #         self._assert_case(case_id, user_id, num_forms=2, closed=True)
    #         self._assert_synclog(synclog_id, case_ids=[])
    #
    # def test_case_index(self, testapp, client):
    #     user_id = str(uuid4())
    #     owner_id = str(uuid4())
    #     with testapp.app_context():
    #         factory = CaseFactory(client, domain=DOMAIN, case_defaults={
    #             'user_id': user_id,
    #             'owner_id': owner_id,
    #             'case_type': 'duck',
    #         })
    #         child, parent = factory.create_or_update_case(
    #             CaseStructure(
    #                 attrs={'create': True, 'case_type': 'duckling'},
    #                 relationships=[
    #                     CaseRelationship(
    #                         CaseStructure(attrs={'case_type': 'duck'})
    #                     ),
    #                 ])
    #         )
    #
    #         self._assert_case(parent.id, owner_id)
    #         self._assert_case(child.id, owner_id, indices={
    #             'parent': {
    #                 'referenced_type': 'duck',
    #                 'referenced_id': parent.id,
    #             }
    #         })

