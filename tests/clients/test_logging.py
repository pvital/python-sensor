# (c) Copyright IBM Corp. 2021
# (c) Copyright Instana Inc. 2020

import logging
import unittest
from instana.singletons import agent, tracer


class TestLogging(unittest.TestCase):
    def setUp(self):
        """ Clear all spans before a test run """
        self.recorder = tracer.recorder
        self.recorder.clear_spans()
        self.logger = logging.getLogger('unit test')

    def tearDown(self):
        """ Ensure that allow_exit_as_root has the default value """
        agent.options.allow_exit_as_root = False

    def test_no_span(self):
        with tracer.start_active_span('test'):
            self.logger.info('info message')

        spans = self.recorder.queued_spans()
        self.assertEqual(1, len(spans))

    def test_extra_span(self):
        with tracer.start_active_span('test'):
            self.logger.warning('foo %s', 'bar')

        spans = self.recorder.queued_spans()
        self.assertEqual(2, len(spans))
        self.assertEqual(2, spans[0].k)

        self.assertEqual('foo bar', spans[0].data["log"].get('message'))

    def test_log_with_tuple(self):
        with tracer.start_active_span('test'):
            self.logger.warning('foo %s', ("bar",))

        spans = self.recorder.queued_spans()
        self.assertEqual(2, len(spans))
        self.assertEqual(2, spans[0].k)

        self.assertEqual("foo ('bar',)", spans[0].data["log"].get('message'))

    def test_parameters(self):
        with tracer.start_active_span('test'):
            try:
                a = 42
                b = 0
                c = a / b
            except Exception as e:
                self.logger.exception('Exception: %s', str(e))

        spans = self.recorder.queued_spans()
        self.assertEqual(2, len(spans))

        self.assertIsNotNone(spans[0].data["log"].get('parameters'))

    def test_no_root_exit_span(self):
        agent.options.allow_exit_as_root = True
        self.logger.info('info message')

        spans = self.recorder.queued_spans()
        self.assertEqual(0, len(spans))

    def test_root_exit_span(self):
        agent.options.allow_exit_as_root = True
        self.logger.warning('foo %s', 'bar')

        spans = self.recorder.queued_spans()
        self.assertEqual(1, len(spans))
        self.assertEqual(2, spans[0].k)

        self.assertEqual('foo bar', spans[0].data["log"].get('message'))
