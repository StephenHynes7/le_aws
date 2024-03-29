from fabric.api import *
from fabric.contrib import files
from paramiko.config import SSHConfig

import logentriessdk.client as logclient 
from logentriesprovisioning import configfile
from logentriesprovisioning import constants
from logentriesprovisioning import utils
import os
import sys
import json
import logging

# get global logger
logger = logging.getLogger('sync')

_GROUP_HOST_LIST = []

def get_instance_log_paths(instance_id, log_filter):
    """
    Args:
    instance_id is an instance identifier.
    ssh_config is the ssh configuration associated to the instance with id 'instance_id'.
    Returns the list of log paths for the instance with id 'instance_id'.
    Returns an empty list if no log file paths could be retrieved from the instance.
    """
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)
    log_paths = []

    # Retrieve log file paths that match the log filter
    command = "find / -type f -regex '%s'"%(log_filter)
    try:
        output = sudo(command, warn_only=True)
    except:
        logger.warning('Could not retrieve log paths. hostname=%s, log_filter=%s, command=%s', host_name, log_filter, command)
        return []

    if not output.succeeded:
        logger.warning('Could not retrieve log paths. hostname=%s, log_filter=%s, message=%s', host_name, log_filter, output.stdout.replace('\n',' \\ '))
        return log_paths
    # Clean output
    log_paths.extend([logpath.replace('\r','') for logpath in output.stdout.split('\n')])
    logger.info('Log Paths: %s',log_paths)
    return log_paths


def get_instance_log_conf_file(instance_id):
    """
    Args:
    instance_id is an instance identifier.
    Returns the Logentries-RSyslog configuration file deployed on the instance or None if the configuration does not exist or could not be retrieved. 
    """
    # Retrieve current log config file
    log_conf_file = None
    host_name='%s_%s'%(constants.get_group_name(), instance_id)
    filename = 'logentries_%s.conf'%host_name
    rsyslog_conf_name = '/etc/rsyslog.d/%s'%filename
    local_conf_name = '/tmp/%s'%filename
    
    # Remove local version of the file if already present as it may be obsolete
    try:
        local('rm %s'%local_conf_name, capture=True)
    except:
        logger.debug('No version of the file present locally. host_name=%s, remote_filename=%s, local_filename=%s', host_name, rsyslog_conf_name, local_conf_name)
    # Get remote conf file or return None if it cannot be retrieved
    if not files.exists(rsyslog_conf_name, use_sudo=True):
        return None
    try:
        get(rsyslog_conf_name,local_conf_name)
    except:
        logger.debug('No version of the file present remotely. host_name=%s, remote_filename=%s, local_filename=%s', host_name, rsyslog_conf_name, local_conf_name)
        return None
    # Open conf file or return None if it cannot be opened
    try:
        log_conf_file = open(local_conf_name,'r')
    except:
        logger.error('Cannot open Logentries-Rsyslog configuration file. host_name=%s, local_filename=%s', host_name, local_conf_name)
        return None
    logger.debug('Remote Logentries-Rsyslog configuration file successfully retrieved and opened. filename=%s, hostname=%s', rsyslog_conf_name, host_name)
    return log_conf_file


def load_conf_file(log_conf_file,instance_id):
    """
    Args:
    log_conf_file is a file object
    instance_id is an instance identifier.
    Returns a Logentries-RSyslog configuration object representing the content of log_conf_file or None if log_conf_file is None.
    log_conf_file is closed by this function as a side effect and is therefore no longer accessible.
    """
    log_conf = None
    # conf file or return None if it cannot be opened
    if log_conf_file != None:
        log_conf = configfile.LoggingConfFile.load_file(log_conf_file,instance_id)
        log_conf_file.close()
    return log_conf


def get_logentries_host(log_client,conf_host):
    """
    Args:
    log_client is a client object to manage a Logentries account.
    conf_host is a Logentries-Rsyslog configuration object.
    Returns the logentries host corresponding to conf_host or None if no such host is present in the Logentries account.
    """
    account = log_client.get_account()
    if account is not None:
        for host in account.get_hosts():
            if host.get_key() == conf_host.get_key():
                return host
    return None

def update_instance_conf(instance_id, log_paths, log_conf):
    """
    Args:
    instance_id is an instance identifier.
    log_paths is a not None list of log file paths.
    log_conf is a not None Logentries-RSyslog configuration object.
    Returns the updated log_conf, taking into account new log files present on the instance as well as modifications made to the corresponding logentries host.
    
    """
    log_client = logclient.Client(constants.ACCOUNT_KEY)
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)

    # Creation of a host if no configuration file exists
    if log_conf is None and len(log_paths)>0:
        host = utils.create_host_and_logs(log_client,instance_id,log_paths)
        log_conf = configfile.LoggingConfFile(name='logentries_%s.conf'%host.get_name(),host=host)
    # if a configuration file exists for the instance, look for the differences between the log lists
    elif log_conf is not None:
        conf_host = log_conf.get_host()
        if conf_host is None:
            logger.error('This instance configuration is missing the corresponding model!! hostname=%s', host_name)
            host = utils.create_host_and_logs(log_client,instance_id,log_paths)
            log_conf = configfile.LoggingConfFile(name='logentries_%s.conf'%host.get_name(),host=host)
            return log_conf

        if conf_host.get_key() is None:
            logger.warning('Instance has a logentries-rsyslog config file but no account key!! hostname=%s', host.get_name())
            logger.warning('Instance is re-provisioned. hostname=%s', host.get_name())
            host = utils.create_host_and_logs(log_client,instance_id,log_paths)
            log_conf = configfile.LoggingConfFile(name='logentries_%s.conf'%host.get_name(),host=host)
            return log_conf
        
        logentries_host = get_logentries_host(log_client,conf_host)
        # If there is no matching host, then it is assumed that it was deleted from Logentries and that no configuration should be associated to this instance.
        if logentries_host is None:
            logger.info('Instance has an logentries-rsyslog config file but no matching host in logentries!! hostname=%s', host_name)
            logger.info('Instance will be deprovisioned hostname=%s', host_name)            
            #host = utils.create_host_and_logs(log_client,instance_id,log_paths)
            #log_conf = configfile.LoggingConfFile(name='logentries_%s.conf'%host.get_name(),host=host)
            return None

        logentries_logs = logentries_host.get_logs()
        logentries_log_paths = [log.get_filename() for log in logentries_logs]
        logger.info('Logs are already followed on this instance. hostname=%s, log_paths=%s',log_conf.get_host().get_name(), logentries_log_paths)
        new_log_paths = [log_path for log_path in log_paths if log_path not in logentries_log_paths]
        logger.info('New logs detected. hostname=%s, new_log_paths=%s',log_conf.get_host().get_name(), new_log_paths)


        for new_log_name in new_log_paths:
            logentries_host, log_key = log_client.create_log_token(host=logentries_host, log_name=new_log_name)
            logger.info('Log Created. hostname=%s, log_path=%s, key=%s', logentries_host.get_name(), new_log_name, log_key)

        removed_logs = [removed_log for removed_log in logentries_logs if removed_log.get_filename() not in log_paths]
        for removed_log in removed_logs:
            if removed_log is not None and log_client.remove_log(host=logentries_host, log=removed_log):
                logger.info('Log Removed. hostname=%s, log=%s', logentries_host.get_name(), removed_log)
        log_conf.set_host(logentries_host)
    return log_conf


def restart_rsyslog(instance_id):
    """
    Restarts RSyslog service.
    Args:
    instance_id is an instance identifier.
    Returns True if and only if RSyslog was successfully restarted. 
    """
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)
    output = None

    if files.exists('/etc/rsyslog.d/', use_sudo=True):
        command = 'service rsyslog restart'
        try:
            output = sudo(command, warn_only=True)
            logger.warning('Could not restart syslog. hostname=%s, command=\'%s\'', host_name, command)
        except:
            command = '/etc/init.d/rsyslog restart'
            try:
                sudo(command, warn_only=True)
            except:
                logger.error('Rsyslog could not be restarted. hostname=%s, command=\'%s\'', host_name, command)
    else:
        logger.warning('Instance does not support RSyslog. hostname=%s', host_name)
        return False

    if output is None:
        return False
    
    if output.succeeded:
        logger.info('RSyslog restarted successfully. hostname=%s', host_name)
    else:
        logger.error('Error restarting RSyslog. hostname=%s, message=%s', host_name, output.stdout)
    return output.succeeded


def deploy_log_conf(instance_id, log_conf):
    """
    Args:
    instance_id is an not None instance identifier.
    log_conf is a Logentries-RSyslog configuration.
    Deploys Logentries-RSyslog configuration file 'log_conf' and restart RSyslog so that this file is taken into account.
    Returns True if and only if log_conf was successfully deployed and RSyslog was successfully restarted. 
    """
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)
    if log_conf is None:
        logger.warning('No RSyslog Configuration file is provided. hostname=%s', host_name)
        return False

    # Get current instance information
    local_conf_name = log_conf.get_name()

    # Save configuration in a file
    log_conf_file = log_conf.save()

    filename = os.path.basename(log_conf_file.name)
    log_conf_file.close()

    remote_conf_name = '/etc/rsyslog.d/%s'%filename
    
    try:
        put(local_conf_name,remote_conf_name,use_sudo=True)
    except:
        logger.error('File could not be transfer to instance. local_filename=%s, remote_filename=%s, hostname=%s',local_conf_name, remote_conf_name, host_name)
        return False
    logger.debug('Configuration file successfully deployed. local_filename=%s, remote_filename=%s, hostanme=%s', local_conf_name, remote_conf_name, host_name)
    return True


def get_instance_log_conf(instance_id):
    """
    Args:
    instance_id is an not None instance identifier.
    Returns the Logentries-RSyslog configuration deployed on the instance or None if no such configuration is deployed.
    """
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)
    log_conf_file = get_instance_log_conf_file(instance_id)
    if log_conf_file is None:
        logger.debug('No existing logentries rsyslog configuration file was found. hostname=%s', host_name)

    log_conf = load_conf_file(log_conf_file,instance_id)

    if log_conf is None:
        logger.info('Logentries rsyslog configuration file could not be read. hostname=%s', host_name)

    return log_conf

#@parallel
def sync():
    """
    Syncs the logentries account with each instance and logs defined in the ssh config file.
    """
    # Get current instance information
    instance_id, log_filter = utils.get_log_filter(env.host)
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)

    log_paths = get_instance_log_paths(instance_id, log_filter)
    if not files.exists('/etc/rsyslog.d/', use_sudo=True):
        logger.info('Instance does not support rsyslog. hostname=%s', host_name)
        return
    log_conf = get_instance_log_conf(instance_id)
    log_conf = update_instance_conf(instance_id, log_paths, log_conf)
    if log_conf is None:
        logger.info('No new rsyslog configuration was detected. hostname=%s', host_name)
        return

    deploy_log_conf(instance_id, log_conf)
    # Restart RSyslog
    restart_rsyslog(instance_id)  
    return


def remove_log_conf(instance_id):
    """
    Args:
    instance_id is an instance identifier.
    Returns True if and only if the Logentries-RSyslog configuration file is no longer present on the remote the instance.
    """
    host_name='%s_%s'%(constants.get_group_name(), instance_id)
    remote_conf_filename = '/etc/rsyslog.d/logentries_%s.conf'%host_name


    try:
        # Remove logentries rsyslog conf file
        command = 'rm %s'%remote_conf_filename
        output = sudo(command, warn_only=True)
        if output.succeeded:
            logger.debug('File successfully removed. remote_filename=%s, hostname=%s.', remote_conf_filename, host_name)
        else:
            logger.warning('Could not remove file.  remote_filename=%s, hostname=%s.', remote_conf_filename, host_name)
    except:
        logger.error('Could not remove file. remote_filename=%s, hostname=%s.', remote_conf_filename, host_name)

    present = files.exists(remote_conf_filename)
    if not present:
            logger.debug('File is not present on the system. remote_filename=%s, hostname=%s.', remote_conf_filename, host_name)
    return present
        

#@parallel
def deprovision():
    """
    Deprovisions the instance by removing the logentries rsyslog config file from it, restarting rsyslog and removing the corresponding host from the logentries system.
    """
    instance_id, log_filter = utils.get_log_filter(env.host)
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)

    log_conf_file = get_instance_log_conf_file(instance_id)
    if log_conf_file is None:
        logger.debug('Cannot deprovision instance as it has not been provisioned. hostname=%s', host_name)
        return
    log_conf = load_conf_file(log_conf_file, instance_id)

    if log_conf is None:
        logger.info('No existing logentries rsyslog configuration file was found on instance %s',instance_id)
        return

    if remove_log_conf(instance_id):
        restart_rsyslog(instance_id)

    conf_host = log_conf.get_host()
    if conf_host is None:
        logger.error('Error. This instance configuration is missing the corresponding model!! instance_id=%s',instance_id)
        return
    
    if conf_host.get_key() is None:
        logger.error('Host has a logentries-rsyslog config file but no account key, host=%s!!',host.to_json())
    else:
        log_client = logclient.Client(constants.get_account_key())
        logentries_host = get_logentries_host(log_client,conf_host)

        # If there is no matching host, then it is assumed that it was deleted from Logentries and that no configuration should be associated to this instance.
        if logentries_host is not None:
                succeeded = log_client.remove_host(logentries_host)
                if succeeded:
                    logger.warning('Host removed from Logentries. host=%s', logentries_host.to_json())
                else:
                    logger.error('Could not remove host from Logentries. host=%s', logentries_host.to_json())
        else:
            logger.error('Could not remove host from Logentries. hostname=%s', host_name)
    return


def set_instance_host_keys():
    """
    Args:
    Collects host keys associated to instance in fabric host_list.
    """
    instance_id, log_filter = utils.get_log_filter(env.host)
    host_name = '%s_%s'%(constants.get_group_name(), instance_id)
    log_client = logclient.Client(constants.get_account_key())

    global _GROUP_HOST_LIST
    log_conf = get_instance_log_conf(instance_id)
    if log_conf is None:
        return
    conf_host = log_conf.get_host()
    logger.debug('Checking if host should be kept. host=%s', conf_host)
    if conf_host is not None:
        logger.info('Host found in ssh configuration. host=%s', conf_host.to_json())
        _GROUP_HOST_LIST.append(conf_host.get_key())


def remove_hosts(group_name,exclude=[]):
    """
    Args:
    group_name is a string representing the name of a group of hosts.
    exclude is a list of string representing host keys.
    Removes, from Logentries, hosts that belong to group with name 'group_name' except for the one whose key belong to 'exclude'.
    """
    global _GROUP_HOST_LIST
    log_client = logclient.Client(constants.get_account_key())
    if log_client is None or constants.get_account_key() is None:
        logger.error('Could not retrieve account information. account_key=%s','%s-xxxx-xxxx-xxxx-xxxxxxxxxxxx'%constants.get_account_key().split('-')[0])
        return
    hosts = log_client.get_hosts()
    for host in hosts:
        if host.get_key() not in _GROUP_HOST_LIST and host.get_location() == group_name:
            logger.debug('Removing Logentries host. host=%s', host)
            log_client.remove_host(host)
    return


def main(working_dir=None, cmd='', group_name='AWS'):
    """
    Main function for the module. Calls other functions according to the parameters provided.
    """
    constants.set_working_dir(working_dir)
    constants.set_account_key(None)
    constants.set_logentries_logging()
      
    if working_dir is None:
        ssh_config_name = 'ssh_config'
    else:
        ssh_config_name = '%s/ssh_config'%working_dir

    env.use_ssh_config = True
    try:
        config_file = file(ssh_config_name)
    except IOError:
        pass
    else:
        config = SSHConfig()
        config.parse(config_file)
        env._ssh_config = config

    list_hosts = []
    for host_config in env._ssh_config._config:
        host_name = host_config['host'][0]
        if host_config['host'][0]!='*':
            ssh_config = host_config['config']['hostname']
            logger.info('Found instance ssh config. instance=%s, ssh_config=%s', host_name, ssh_config)
            list_hosts.extend(host_config['host'])

    if cmd == 'deprovision':
        execute(deprovision,hosts=list_hosts)
    elif cmd == 'clean':
        execute(set_instance_host_keys,hosts=list_hosts)
        execute(remove_hosts,group_name,hosts=list_hosts)
    elif cmd == '':
        execute(sync,hosts=list_hosts)



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'You must specify the path to your ssh config file.'
    else:
        constants.set_working_dir(sys.argv[1])
        constants.set_account_key(None)
        constants.set_logentries_logging()
        main('%s/ssh_config'%sys.argv[1])
