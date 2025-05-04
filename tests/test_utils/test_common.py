import os
import logging.config
from unittest import mock
from app.utils import common

def test_setup_logging_reads_config_correctly():
    # Patch os.path methods and logging.config.fileConfig
    with mock.patch("os.path.dirname", return_value="/app/utils"), \
         mock.patch("os.path.normpath", return_value="/app/logging.conf") as norm_mock, \
         mock.patch("logging.config.fileConfig") as log_mock:

        common.setup_logging()

        # Assert normpath was called with the constructed path
        norm_mock.assert_called_once_with("/app/utils/../../logging.conf")

        # Assert fileConfig was called with the normalized path
        log_mock.assert_called_once_with("/app/logging.conf", disable_existing_loggers=False)
