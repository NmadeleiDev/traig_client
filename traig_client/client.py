import logging
import os
from enum import Enum

import requests
from traig_client.exceptions import ClientNotInitialized


class MetricTypeEnum(str, Enum):
    value = "value"  # simply store latest value assigned
    max = "max"  # return maximum
    min = "min"  # return minimum
    sum = "sum"  # return sum
    mean = "mean"  # return mean
    mode = "mode"  # return mode
    median = "median"  # return mode
    count = "count"  # return number of updates of the metric (actual update values does not matter)


class TraigStubClient:
    def __init__(self):
        pass

    def init_metrics(self, **metrics):
        pass

    def update_metrics(self, **metric_values):
        pass


class TraigClient:
    def __init__(self):
        self.traig_server_url = 'http://traigserver.io'
        self.metrics = {}
        self.is_initialized = False

    def init_metrics(self, **metrics):
        metric_types = [m.value for m in MetricTypeEnum]
        metrics_validated = {k: v for k, v in metrics.items() if v in metric_types}

        for ignored_metric in set(metrics.keys()) - set(metrics_validated.keys()):
            logging.debug(f'metric type {metrics[ignored_metric]} for metric {ignored_metric} is not understood '
                          f'and will be ignored. '
                          f'Use one of: {metric_types}')

        if len(metrics) == 0:
            logging.warning('No metrics to initialize, ignoring')
            return

        self.metrics = metrics

        resp = requests.post(f'{self.traig_server_url}/metric/init', json={'data': metrics})
        if resp.status_code == 200:
            self.is_initialized = True
        else:
            logging.error('failed to initialize metrics, client is not usable')

    def update_metrics(self, **metric_values):
        if len(self.metrics) == 0 or not self.is_initialized:
            raise ClientNotInitialized(f'is_initialized={self.is_initialized}, '
                                       f'len(self.metrics) == {len(self.metrics)}')

        for k, v in metric_values.items():
            if k not in self.metrics:
                logging.warning(f'metric "{k}" was not initialized, will ignore it. '
                                f'Your initialized metrics are: {self.metrics}')
                metric_values.pop(k)
        metric_values_validated = {k: v for k, v in metric_values.items() if k in self.metrics}

        for ignored_metric in set(metric_values.keys()) - set(metric_values_validated.keys()):
            logging.warning(f'metric "{ignored_metric}" was not initialized, will ignore it. '
                            f'Your initialized metrics are: {self.metrics}')

        if len(metric_values) == 0:
            logging.warning('No metrics to update, ignoring')
            return

        requests.post(f'{self.traig_server_url}/metric/update', json={'data': metric_values})


def get_client() -> TraigClient | TraigStubClient:
    if not hasattr(get_client, 'traig_client'):
        if os.getenv('TRAIG_SESSION', '0') == '1':
            get_client.traig_client = TraigClient()
        else:
            get_client.traig_client = TraigStubClient()

    return get_client.traig_client
