from fabric.api import *

import os
import sys
import json
import logging

# get global logger
logger = logging.getLogger('sync')


def get_log_filter(host_name):
    """
    Args:
    host_name is the name of a host in the current ssh_config_file.
    Returns the host name and the log filter of the host matching host_name.
    Returns None and an empty dictionary if no host matches host_name.
    """
    for host_config in env._ssh_config._config:
        if host_config['host'][0] != '*' and host_config['config']['hostname'] == host_name:
            if 'logfilter' in host_config['config']:
                log_filter = host_config['config']['logfilter']
            else:
                log_filter = '^/var/log/.*log'
            return host_config['host'][0], log_filter
    return None,{}



def create_host(log_client, instance_id):
    """
    Creates a host in logentries.
    Args: 
    log_client is a not None Logentries client object.
    instance_id is a not None the identifier of the remote instance.
    Returns the Host object or None if the host creation fails.
    """
    host_name='AWS_%s'%instance_id
    host = log_client.create_host(name=host_name,location='AWS')
    if host is None:
        logger.error('Host could not be created. hostname=%s',host_name)
        return None
    logger.info('Host Created. hostname=%s, location=%s', host.get_name(), host.get_location())
    return host

def create_logs(log_client, host, log_paths):
    """
    Args:
    log_client is a not None Logentries client object.
    host is a not None Logentries Host object.
    log_paths is a not None list of log file paths.
    Creates token based logs in logentries for each log file paths.
    Returns the Logentries Host object updated by the log creations.
    """
    for log_name in log_paths:
        host, logkey = log_client.create_log_token(host=host,log_name=log_name)
        if logkey is None:
            logger.warning('Could not create log. hostname=%s, logname=%s', host.get_name(), log_name)
        else:
            logger.info('Log created. hostname=%s, logname=%s', host.get_name(), log_name)
    return host


def create_host_and_logs(log_client, instance_id, log_paths):
    """
    Args:
    log_client is a not None Logentries client object.
    instance_id is a not None identifier of an instance.
    log_paths is a not None list of log file paths.
    Creates a Logentries host corresponding to the instance as well as logs for this host in logentries for each log file paths.
    Returns the created Logentries Host object.
    """
    host = create_host(log_client,instance_id)
    host = create_logs(log_client,host,log_paths)
    return host
