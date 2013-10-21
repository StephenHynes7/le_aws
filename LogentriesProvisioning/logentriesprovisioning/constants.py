import logging
import json

from logentriessdk import *

ACCOUNT_KEY = None
WORKING_DIR = None
AWS_SECRET_ACCESS_KEY = None
AWS_ACCESS_KEY_ID = None

GROUP_NAME = 'AWS'

_LOGENTRIES_LOGGING_HANDLER = None

from logentries import LogentriesHandler
logger = logging.getLogger('sync')

def set_group_name(name):
    global GROUP_NAME
    GROUP_NAME = name

def get_group_name():
    return GROUP_NAME

def set_working_dir(working_dir):
    global WORKING_DIR
    WORKING_DIR = working_dir

def set_account_key(conf_file_name):
    """
    """
    global ACCOUNT_KEY
    global WORKING_DIR
    if conf_file_name is None:
        conf_file_name='%slogentries.json'%(WORKING_DIR+'/' if WORKING_DIR is not None else '')

    try:
        account_key_file = open(conf_file_name,'r')
    except:
        logger.error('Could not open %s',conf_file_name)
        account_key_file = None

    # Retrieve account key from file
    global ACCOUNT_KEY
    if account_key_file is None:
        ACCOUNT_KEY = None
        return

    try:
        account_key_json = json.load(account_key_file)
    except:
        logger.error('Could not load json structure from %s'%conf_file_name)
        account_key_json = None

    if account_key_json is not None and 'account_key' in account_key_json.keys():
        ACCOUNT_KEY = account_key_json['account_key']
    else:
        ACCOUNT_KEY = None
        print 'Could not retrieve logentries account key from json in logentries.json'
        logger.error('Could not retrieve logentries account key from json in logentries.json')

def set_aws_credentials(conf_file_name):
    """
    """
    global AWS_SECRET_ACCESS_KEY
    global AWS_ACCESS_KEY_ID
    global WORKING_DIR
    if conf_file_name is None:
        conf_file_name='%saws.json'%(WORKING_DIR+'/' if WORKING_DIR is not None else '')
    try:
        aws_conf_file = open(conf_file_name,'r')
    except:
        logger.error('Could not open %s',conf_file_name)
        aws_conf_file = None
    # Retrieve account key from file
    if aws_conf_file is None:
        AWS_SECRET_ACCESS_KEY = None
        AWS_ACCESS_KEY_ID = None
        return

    try:
        aws_conf_json = json.load(aws_conf_file)
    except:
        logger.error('Could not load json structure from %s'%conf_file_name)
        aws_conf_json = None

    if aws_conf_json is not None:
        if 'aws_secret_access_key' in aws_conf_json.keys():
            AWS_SECRET_ACCESS_KEY = aws_conf_json['aws_secret_access_key']
        if 'aws_access_key_id' in aws_conf_json.keys():
            AWS_ACCESS_KEY_ID = aws_conf_json['aws_access_key_id']
    else:
        AWS_SECRET_ACCESS_KEY = None
        AWS_ACCESS_KEY_ID = None
        print 'Could not retrieve AWS credentials from json in %s'%conf_file_name
        logger.error('Could not retrieve AWS credentials from json in %s',conf_file_name)

def get_account_key():
    global ACCOUNT_KEY
    return ACCOUNT_KEY

def get_aws_secret_access_key():
    global AWS_SECRET_ACCESS_KEY
    return AWS_SECRET_ACCESS_KEY

def get_aws_access_key_id():
    global AWS_ACCESS_KEY_ID
    return AWS_ACCESS_KEY_ID

def set_logentries_logging(logger_name='sync'):
    global _LOGENTRIES_LOGGING_HANDLER
    if get_account_key() is not None and _LOGENTRIES_LOGGING_HANDLER is None:
        logger = logging.getLogger(logger_name)
        log = get_log_setup()
        if log is not None and log.get_token() is not None:
            _LOGENTRIES_LOGGING_HANDLER = LogentriesHandler(log.get_token())
            logger.addHandler(_LOGENTRIES_LOGGING_HANDLER)
        else:
            logger.warning('Could not retrieve a token for the setup log')

def get_log_setup():
    client = Client(account_key=ACCOUNT_KEY)
    host = client.get_host(hostkey=None,name='AutoProvisioning')
    if host is None:
        host = client.create_host(name='AutoProvisioning')
    if host is None:
        return None
    log = client.get_log(logkey=None, hostkey=host.get_key(), logname='Setup')
    if log is not None:
        return log
    host, logkey = client.create_log_token(host=host, log_name='Setup')
    if host is not None:
        return host.get_log(logkey)
