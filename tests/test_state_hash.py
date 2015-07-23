# -*- coding: utf-8 -*-
import pytest
from uuid import uuid4
from tests.dummy import dummy_user

from tests.mock import CaseBlock, post_case_blocks
from tests.utils import get_restore_payload, synclog_id_from_restore_payload, \
    get_restore_response, message_nature_from_restore_payload, NATURE_OTA_RESTORE_ERROR


@pytest.mark.usefixtures("config", "test_setup_teardown")
class TestStateHash(object):

    def test_wrong_state_hash(self, config):
        user_id = str(uuid4())
        response = get_restore_response(config.restore_url, config.domain, dummy_user(user_id))
        assert response.status_code == 200

        synclog_id = synclog_id_from_restore_payload(
            response.text
        )

        response = get_restore_response(config.restore_url, config.domain, dummy_user(user_id),
                                        since=synclog_id, state_hash='ccsh:wrong')
        assert response.status_code == 412
        assert message_nature_from_restore_payload(response.text) == NATURE_OTA_RESTORE_ERROR

    def test_mismatch(self, config):
        user_id = str(uuid4())
        synclog_id = synclog_id_from_restore_payload(
            get_restore_payload(config.restore_url, config.domain, dummy_user(user_id))
        )

        c1 = CaseBlock(case_id="690ad3bd49ba4eef9ca839681dbd86b9", create=True, user_id=user_id,
                       owner_id=user_id)
        c2 = CaseBlock(case_id="e66c36c673a24319832c62ed806096e4", create=True, user_id=user_id,
                       owner_id=user_id)
        result = post_case_blocks(config.receiver_url, [c1, c2], domain=config.domain,
                         form_extras={'headers': {"last_sync_token": synclog_id}})
        assert result.status_code == 201

        # check correct hash
        response = get_restore_response(config.restore_url, config.domain, dummy_user(user_id),
                                        since=synclog_id, state_hash="ccsh:21f8a4fb891affbcf51eaa9ba7da22ef")
        assert response.status_code == 200

        # check incorrect hash
        response = get_restore_response(config.restore_url, config.domain, dummy_user(user_id),
                                        since=synclog_id, state_hash="ccsh:badhash")
        assert response.status_code == 412
