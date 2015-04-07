import json
import datetime
import logging

log = logging.getLogger(__name__)


def parse_boolean(b_value):
    """
    Args: is a string representing a boolean value or None or the empty string.
    This function returns the boolean value that b_value represents. 
    It returns False if b_value is None or the empty string. """
    if b_value and b_value.lower() == 'true':
        return True
    return False


class Log(object):
    def __init__(self, key=None, name=None, filename=None, ntype=None, retention=None, nobject=None, created=None,
                 port=None, follow=None, token=None):
        self._key = key
        self._name = name
        self._filename = filename
        self._type = ntype
        self._retention = retention
        self._object = nobject
        self._follow = follow
        self._created = created
        self._port = port
        self._token = token

    def __repr__(self):
        return 'Log:%s' % self._name

    def load_data(self, log_data):
        # TODO: make it more robust in case keys don't belong to the dictionary
        self._key = log_data['key']
        self._name = log_data['name']
        # TODO: check if filename can be modified by the user.
        # It is something that the user shouldn't be able to manually modify.
        if log_data['filename']:
            self._filename = log_data['filename']
        else:
            self._filename = log_data['name']
        self._type = log_data['type']
        self._retention = log_data['retention']
        self._object = log_data['object']
        self._follow = parse_boolean(log_data['follow'])
        created = log_data['created']
        if created is not None:
            try:
                self.set_created(created)
            except TypeError:
                log.error('Cannot convert created field into epoch time. created=%s', created)
        self._port = log_data['port'] if 'port' in log_data else None
        self._token = log_data['token'] if 'token' in log_data else None

    def get_key(self):
        return self._key

    def set_value(self, attr, value):
        attr = value

    def get_value(self, attr):
        return attr

    def set_token(self, token):
        self._token = token

    def set_source(self, ntype):
        self._type = ntype

    def set_port(self, port):
        self._port = port

    def set_name(self, name):
        self._name = name

    def set_filename(self, filename):
        self._filename = filename

    def set_key(self, log_key):
        self._key = log_key

    def set_retention(self, retention):
        self._retention = retention

    def set_object(self, nobject):
        self._object = nobject

    def set_follow(self, follow):
        self._follow = follow

    def set_created(self, created):
        """

        :param created: an int representing an epoch timestamp in millisecond
        :return:
        """
        self._created = datetime.datetime.fromtimestamp(created / 1000)

    def get_name(self):
        return self._name

    def get_filename(self):
        return self._filename

    def get_token(self):
        return self._token

    def get_type(self):
        return self._type

    def get_port(self):
        return self._port

    def get_retention(self):
        return self._retention

    def get_object(self):
        return self._object

    def get_follow(self):
        return self._follow

    def get_created(self):
        return self._created

    def to_json(self):
        """
        Returns a dictionnary representing the attribute values of this log.
        """
        log_repr = {'key': self._key, 'name': self._name, 'filename': self._filename, 'type': self._type,
                    'retention': self._retention, 'object': self._object, 'follow': self._follow,
                    'created': self._created}
        if self._port is not None:
            log_repr['port'] = self._port
        elif self._token is not None:
            log_repr['token'] = self._token

        return log_repr

    def __unicode__(self):
        return json.dumps(self.to_json())


class Host(object):
    def __init__(self, name=None, key=None, created=None, location=None, logs=[], platform=None):
        self._name = name
        self._location = location
        self._key = key
        self._created = created
        self._logs = logs
        self._platform = platform

    def __repr__(self):
        return 'Host:%s' % self._name

    def load_data(self, host_data):
        """
        Args: host_data is a dictionary containing host object information. It is assumed that host key, name and
        platform are provided in this dictionary, i.e. 'key', 'name' and 'platform' are keys of this dictionary.
        Sets this host attributes to the ones provided in host_data.
        """
        name = host_data['name'] if 'name' in host_data else None
        location = host_data['hostname'] if 'hostname' in host_data else None
        key = host_data['key'] if 'key' in host_data else None
        created = host_data['created'] if 'created' in host_data else None
        platform = host_data['platform'] if 'platform' in host_data else None
        logs_data = host_data['logs'] if 'logs' in host_data else None
        if name is not None:
            self.set_name(name)
        else:
            self.set_name('n/a')
        if created is not None:
            try:
                self.set_created(created)
            except TypeError:
                log.error('Cannot convert created field into epoch time. created=%s', created)
        if location is not None:
            self.set_location(location)
        if platform is not None:
            self.set_platform(platform)
        if key is not None:
            self.set_key(key)
        if logs_data is not None:
            self.add_logs(logs_data)

    def rm_log(self, log_key):
        self._logs = [x for x in self._logs if log.get_key() != log_key]

    def set_name(self, name):
        """
        Args: name is a string.
        Sets this host name to name.
        """
        self._name = name

    def set_created(self, created):
        """
        Args: created is an int representing an epoch time in ms.
        Sets this host creation date to created.
        """
        self._created = datetime.datetime.fromtimestamp(created/1000)

    def set_platform(self, platform_name):
        """
        Args: platform is a string.
        Sets this host platform name to platform_name.
        """
        self._platform = platform_name

    def set_key(self, key):
        """
        Args: key is a string.
        Sets this host key to key.
        """
        self._key = key

    def set_location(self, location):
        """
        Args: location is a string.
        Sets this host location to location.
        """
        self._location = location

    def get_location(self):
        """
        Returns this host location.
        """
        return self._location

    def add_log(self, log_data):
        """
        Args: log_data is a dictionary containing a log attributes.
        Create a log with attributes from log_data and adds log to the list of logs associated to this account.
        """
        log = Log()
        log.load_data(log_data)
        if self._logs is None:
            self._logs = [log]
        else:
            self._logs.append(log)

    def add_logs(self, logs_data):
        """
        Args: logs_data is a list of dictionary containing log attributes.
        Create logs with attributes from logs_data and adds logs to the list of logs associated to this account.
        """
        for log_data in logs_data:
            self.add_log(log_data)

    def add_log2(self, log):
        """
        Args: log is not None Log object.
        Adds log to the list of logs associated to this account.
        """
        if self._logs is None:
            self._logs = [log]
        else:
            self._logs.append(log)

    def add_logs2(self, logs):
        """
        Args: logs is a list of Log objects that are not None.
        Adds all item in logs to the list of logs associated to this account.
        """
        for log in logs:
            self.add_log(log)

    def get_name(self):
        """
        Returns this host name.
        """
        return self._name

    def get_created(self):
        """
        Returns this host creation date.
        """
        return self._created

    def get_platform(self):
        """
        Returns this host name or None if it has no name.
        """
        return self._platform

    def get_key(self):
        """
        Returns the Logentries key associated to this host or None if it is not associated to any key.
        """
        return self._key

    def get_log(self, log_key):
        """
        Args: log_key is a string.
        Returns the Log object associated with key log_key in Logentries or None if no log
        with key log_key is associated to this host.
        """
        for log in self._logs:
            if log.get_key() == log_key:
                return log
        return None

    def get_logs(self):
        """
        Returns the list of log objects associated with this host.
        """
        return self._logs

    def set_logs(self, logs):
        """
        Args: logs is a list of logs that are not None.
        Sets the list of log objects associated with this host to logs.
        """
        self._logs = logs

    def to_json(self):
        host_repr = {'key': self._key, 'name': self._name, 'hostname': self._location, 'logs': []}
        for log in self._logs:
            host_repr['logs'].append(log.to_json())
        return host_repr

    def __unicode__(self):
        return json.dumps(self.to_json())


class Account(object):
    def __init__(self, account_key=None, name='n/a/', created=None):
        self._account_key = account_key
        self._name = name
        self._created = created
        self._hosts = []

    def add_host2(self, host):
        """ Args: host is not None """
        if self.get_hosts() is None:
            self.set_hosts([host])
        else:
            self._hosts.append(host)

    def add_host(self, host_data):
        host = Host(logs=[])
        host.load_data(host_data)
        self.add_host2(host)

    def add_hosts(self, hosts_data):
        for host_data in hosts_data:
            self.add_host(host_data)

    def edit_host(self, host_data):
        pass

    def rm_host(self, host_key):
        self._hosts = [x for x in self._hosts if x.key != host_key]

    def add_log_to_host(self, host_key, log_data):
        log = Log()
        log.load_data(log_data['log'])
        for host in self._hosts:
            if host.get_key() == host_key:
                host.add_log(log)
        return log

    def rm_log_from_host(self, host_key, log_key):
        for host in self._hosts:
            if host.get_key() == host_key:
                host.rm_log(log_key)

    def set_account_key(self, account_key):
        self._account_key = account_key

    def set_name(self, name):
        self._name = name

    def set_created(self, created):
        """

        :param created: int representing an epoch timestamp in millisecond
        :return:
        """
        self._created = datetime.datetime.fromtimestamp(created / 1000)

    def get_name(self):
        return self._name

    def get_created(self):
        return self._created

    def get_account_key(self):
        return self._account_key

    def get_host(self, hostkey):
        for host in self.get_hosts():
            if host.get_key() == hostkey:
                return host
        return None

    def get_hosts(self):
        return self._hosts

    def to_json2(self):
        account_repr = {'account_key': self._account_key, 'hosts': []}
        for host in self._hosts:
            account_repr['hosts'].append(host.to_json())
        return str(account_repr)

    def to_json(self):
        """
        Returns a dictionnary representing the attribute values of this account.
        """
        result = {"account_key": self.get_account_key()}
        hosts_json = []
        for host in self.get_hosts():
            hosts_json.append(host.to_json())
        result["hosts"] = hosts_json
        return result

    def load_data(self, account_data):
        """
        Args: account_data is a json object containing some account attributes
        Returns an account object with attributes provided in account_data
        """
        if 'user_key' in account_data:
            acc_key = account_data['user_key']
            self.set_account_key(acc_key)
        else:
            log.error('Account_data does not contain an account key!!')
        if 'name' in account_data:
            name = account_data['name']
            self.set_name(name)
        if 'created' in account_data:
            created = account_data['created']
            try:
                self.set_created(created)
            except TypeError:
                log.error('Cannot convert created field to datetime. Default to None. created=%s', created)

        if 'hosts' in account_data:
            self.add_hosts(account_data['hosts'])
        else:
            log.error('Account_data does not contain a list of hosts!!')

    def __unicode__(self):
        return json.dumps(self.to_json())
