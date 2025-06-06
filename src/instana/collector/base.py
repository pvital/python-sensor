# (c) Copyright IBM Corp. 2021
# (c) Copyright Instana Inc. 2020

"""
A Collector launches a background thread and continually collects & reports data.
The data can be any combination of metrics, snapshot data and spans.
"""

import queue  # pylint: disable=import-error
import threading
import time
from typing import TYPE_CHECKING, Any, DefaultDict, Dict, List, Type

from instana.log import logger
from instana.util import DictionaryOfStan

if TYPE_CHECKING:
    from instana.agent.base import BaseAgent
    from instana.span.readable_span import ReadableSpan


class BaseCollector(object):
    """
    Base class to handle the collection & reporting of snapshot and metric data
    This class launches a background thread to do this work.
    """

    def __init__(self, agent: Type["BaseAgent"]) -> None:
        # The agent for this process.  Can be Standard, AWSLambda or Fargate
        self.agent = agent

        # The name assigned to the spawned thread
        self.THREAD_NAME = "Instana Collector"

        # The Queue where we store finished spans before they are sent
        self.span_queue = queue.Queue()

        # The Queue where we store finished profiles before they are sent
        self.profile_queue = queue.Queue()

        # The background thread that reports data in a loop every self.report_interval seconds
        self.reporting_thread = None

        # Signal for background thread(s) to shutdown
        self.thread_shutdown = threading.Event()

        # Timestamp in seconds of the last time we sent snapshot data
        self.snapshot_data_last_sent = 0
        # How often to report snapshot data (in seconds)
        self.snapshot_data_interval = 300

        # List of helpers that help out in data collection
        self.helpers = []

        # Lock used synchronize reporting - no updates when sending
        # Used by the background reporting thread.  Used to synchronize report attempts and so
        # that we never have two in progress at once.
        self.background_report_lock = threading.Lock()

        # Reporting interval for the background thread(s)
        self.report_interval = 1

        # Flag to indicate if start/shutdown state
        self.started = False

        # Start time of fetching metadata
        self.fetching_start_time = 0

    def is_reporting_thread_running(self) -> bool:
        """
        Indicates if there is a thread running with the name self.THREAD_NAME
        """
        for thread in threading.enumerate():
            if thread.name == self.THREAD_NAME:
                return True
        return False

    def start(self) -> None:
        """
        Starts the collector and starts reporting as long as the agent is in a ready state.
        @return: None
        """
        if self.is_reporting_thread_running():
            if self.thread_shutdown.is_set():
                # Force a restart.
                self.thread_shutdown.clear()
                # Reschedule this start in 5 seconds from now
                timer = threading.Timer(5, self.start)
                timer.daemon = True
                timer.name = "Collector Timed Start"
                timer.start()
                return
            logger.debug(
                f"BaseCollector.start non-fatal: call but thread already running (started: {self.started})"
            )

        if self.agent.can_send():
            logger.debug("BaseCollector.start: launching collection thread")
            self.thread_shutdown.clear()
            self.reporting_thread = threading.Thread(
                target=self.background_report, args=()
            )
            self.reporting_thread.daemon = True
            self.reporting_thread.name = self.THREAD_NAME
            self.reporting_thread.start()
            self.started = True
        else:
            logger.warning(
                "BaseCollector.start: the agent tells us we can't send anything out"
            )

    def shutdown(self, report_final: bool = True) -> None:
        """
        Shuts down the collector and reports any final data (if possible).
        e.g. If the host agent disappeared, we won't be able to report final data.
        @return: None
        """
        self.thread_shutdown.set()
        if report_final is True:
            logger.debug("Collector.shutdown: Reporting final data.")
            self.prepare_and_report_data()
        self.started = False

    def background_report(self) -> None:
        """
        The main work-horse method to report data in the background thread.

        This method runs indefinitely, preparing and reporting data at regular
        intervals.
        It checks for a shutdown signal and stops execution if it's set.

        @return: None
        """
        while True:  # pragma: no cover
            if self.thread_shutdown.is_set():
                logger.debug(
                    "Thread shutdown signal is active: Shutting down reporting thread"
                )
                break

            self.prepare_and_report_data()
            time.sleep(self.report_interval)

    def prepare_and_report_data(self) -> bool:
        """
        Prepare and report the data payload.
        @return: Boolean
        """
        with self.background_report_lock:
            payload = self.prepare_payload()
            self.agent.report_data_payload(payload)
        return True

    def prepare_payload(self) -> DefaultDict[str, Any]:
        """
        Method to prepare the data to be reported.
        @return: DictionaryOfStan()
        """
        logger.debug("BaseCollector: prepare_payload needs to be overridden")
        return DictionaryOfStan()

    def should_send_snapshot_data(self) -> bool:
        """
        Determines if snapshot data should be sent
        @return: Boolean
        """
        logger.debug("BaseCollector: should_send_snapshot_data needs to be overridden")
        return False

    def collect_snapshot(self, *argv, **kwargs) -> None:
        logger.debug("BaseCollector: collect_snapshot needs to be overridden")

    def queued_spans(self) -> List["ReadableSpan"]:
        """
        Get all of the queued spans
        @return: list
        """
        spans = []
        while True:
            try:
                span = self.span_queue.get(False)
            except queue.Empty:
                break
            else:
                spans.append(span)
        return spans

    def queued_profiles(self) -> List[Dict[str, Any]]:
        """
        Get all of the queued profiles
        @return: list
        """
        profiles = []
        while True:
            try:
                profile = self.profile_queue.get(False)
            except queue.Empty:
                break
            else:
                profiles.append(profile)
        return profiles
