# (c) Copyright IBM Corp. 2021
# (c) Copyright Instana Inc. 2021

"""
The Instana agent (for GCR) that manages
monitoring state and reporting that data.
"""
import time
from instana.options import GCROptions
from instana.collector.google_cloud_run import GCRCollector
from instana.log import logger
from instana.util import to_json
from instana.agent.base import BaseAgent
from instana.version import VERSION


class GCRAgent(BaseAgent):
    """ In-process agent for Google Cloud Run """

    def __init__(self, service, configuration, revision):
        super(GCRAgent, self).__init__()

        self.options = GCROptions()
        self.collector = None
        self.report_headers = None
        self._can_send = False

        # Update log level (if INSTANA_LOG_LEVEL was set)
        self.update_log_level()

        logger.info("Stan is on the AWS Fargate scene.  Starting Instana instrumentation version: %s", VERSION)

        if self._validate_options():
            self._can_send = True
            self.collector = GCRCollector(self, service, configuration, revision)
            self.collector.start()
        else:
            logger.warning("Required INSTANA_AGENT_KEY and/or INSTANA_ENDPOINT_URL environment variables not set.  "
                           "We will not be able monitor this GCR cluster.")

    def can_send(self):
        """
        Are we in a state where we can send data?
        @return: Boolean
        """
        return self._can_send

    def get_from_structure(self):
        """
        Retrieves the From data that is reported alongside monitoring data.
        @return: dict()
        """
        return {'hl': True, 'cp': 'gcp', 'e': self.collector.get_instance_id()}

    def report_data_payload(self, payload):
        """
        Used to report metrics and span data to the endpoint URL in self.options.endpoint_url
        """
        response = None
        try:
            if self.report_headers is None:
                # Prepare request headers
                self.report_headers = {
                    "Content-Type": "application/json",
                    "X-Instana-Host": "gcp:cloud-run:revision:{revision}".format(
                        revision=self.collector.revision),
                    "X-Instana-Key": self.options.agent_key
                }

            self.report_headers["X-Instana-Time"] = str(round(time.time() * 1000))

            response = self.client.post(self.__data_bundle_url(),
                                        data=to_json(payload),
                                        headers=self.report_headers,
                                        timeout=self.options.timeout,
                                        verify=self.options.ssl_verify,
                                        proxies=self.options.endpoint_proxy)

            if response.status_code >= 400:
                logger.info("report_data_payload: Instana responded with status code %s", response.status_code)
        except Exception as exc:
            logger.debug("report_data_payload: connection error (%s)", type(exc))
        return response

    def _validate_options(self):
        """
        Validate that the options used by this Agent are valid.  e.g. can we report data?
        """
        return self.options.endpoint_url is not None and self.options.agent_key is not None

    def __data_bundle_url(self):
        """
        URL for posting metrics to the host agent.  Only valid when announced.
        """
        return "{endpoint_url}/bundle".format(endpoint_url=self.options.endpoint_url)