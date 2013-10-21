import json
import fabric

import logentriessdk.models

import logging
logging.basicConfig(filename='logentries_setup.log',level=logging.DEBUG)
# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Instance(object):
   """
   Instance class representing physical EC2 instances. Instance objects contain information about connecting to the corresponding EC2 instance, e.g. ip address, ssh key filename, username, etc, as well as information about the logging configuration associated to them. This logging configuration must comply to filters that are also attribute of this class. 
   """

   def __init__(self,instance_id,ssh_key_name=None,ip_address=None,port=None,logs=[],filters=['/var/log/'],log_filter='/var/log/.*log',log_conf=None,platform=None, username=None, name=None):
      """
      Args:
      instance_id represents a unique identifier for this instance
      ssh_key_name represents the name of the ssh key associated to this instance
      ip_address represents this instance ip address
      port represents the port on which to connect to this instance
      filters represents a list of path filters where log files under interest are located on the instance.
      logs represents the list of paths where .log files are present and that comply with filters
      log_conf represents the currently deployed Logentries log forwarding configuration on the instance.
      platform represents the os type that runs on the instance
      username represents the username with which to connect to the instance
      name is the name of the instance as defined in the ec2 tags.
      """
      self._instance_id = instance_id
      self._ssh_key_name = ssh_key_name
      self._ip_address = ip_address
      self._username = username
      self._port = port
      self._name = name if name else instance_id
      self._logs = logs
      self._log_conf = log_conf
      self._log_filter = log_filter
      self._filters = filters
      self._platform = platform


   def set_instance_id(self,instance_id):
      """
      Args: instance_id is a string. It represents the associated instance id.
      Sets the id of this instance to instance_id.
      """
      if self.get_name()== self.get_instance_id():
         self._name = instance_id
      self._instance_id = instance_id

   def set_name(self,name):
      """
      Args: name is a string. It represents the name of the instance.
      Sets the name of this instance to name.
      """
      self._name = name

   def set_ssh_key_name(self,ssh_key_name):
      """
      Args: ssh_key_name is a string. It represents the location of a file containing an ssh key.
      Sets the path of the file containing the ssh key of allowing to connect to this instance to ssh_key_name.
      """
      self._ssh_key_name = ssh_key_name

   def set_logs(self,logs):
      """
      Args: logs is a list of strings. Each string represents the location of a log file present on the instance.
      Sets list of log file paths for log files present on the instance.
      """
      self._logs = logs

   def set_log_conf(self,log_conf):
      """
      Args: log_conf is a configuration file to follow logs on the instance
      Sets the configuration file to follow log files on the instance to log_conf
      """
      self._log_conf = log_conf

   def set_filters(self,filters):
      """
      Args: filters is a list of path where to consider log files.
      Sets the log file path filters to filters
      """
      self._filters = filters

   def set_log_filter(self,log_filter):
      """
      Args: log_filter is a regular expression on the path where to consider log files.
      Sets the log file path filter to log_filter
      """
      self._log_filter = log_filter

   def set_ip_address(self,ip_address):
      """
      Args: ip_address is a string. It represents the ip_address of this instance.
      Sets the ip address of this instance to ip_address.
      """
      self._ip_address = ip_address

   def set_username(self,username):
      """
      Args: username is a string. It represents the user name with which to log on to this instance.
      Sets the user name of this instance to username.
      """
      self._username = username

   def get_instance_id(self):
      """
      Returns the instance id of this instance.
      """
      return self._instance_id

   def set_port(self,port):
      """
      Args: port is an integer. It represents the port on which this instance can be sshed.
      Sets the port on which to shh this instance to port.
      """
      self._port = port

   def get_port(self):
      """
      Returns the port on which to ssh this instance.
      """
      return self._port

   def get_name(self):
      """
      Returns the name of this instance.
      """
      return self._name


   def get_ssh_key_name(self):
      """
      Returns the location of a file containing an ssh key with which to connect to this instance.
      """
      return self._ssh_key_name

   def get_ip_address(self):
      """
      Returns this instance ip address.
      """
      return self._ip_address

   def get_username(self):
      """
      Returns the user name with which to connect to this instance.
      """
      return self._username

   def get_logs(self):
      """
      Returns the list of paths to log files present on the instance.
      """
      return self._logs

   def get_log_conf(self):
      """
      Returns the configuration file to follow log files on the instance
      """
      return self._log_conf

   def get_filters(self):
      """
      Returns the log file path filters
      """
      return self._filters

   def get_log_filter(self):
      """
      Returns the log file path filter
      """
      return self._log_filter


   def get_ssh_config_entry(self):
      result = 'Host %s\n'%self.get_instance_id()
      result = result + '\tHostName %s\n'%self.get_ip_address()
      if self.get_username() is not None:
         result = result + '\tUser %s\n'%self.get_username()
      result = result + '\tIdentityFile %s\n'%self.get_ssh_key_name()
      result = result + '\tLogFilter %s\n'%self.get_log_filter()
      result = result + '\n'
      return result

   @staticmethod
   def load_instance_data(i):
      """ 
      Args: i is a dict object containing an instance attributes.
      """
      if 'instance_id' in i:
         ssh_key_name = i['ssh_key_name'] if 'ssh_key_name' in i else None
         ip_address = i['ip_address'] if 'ip_address' in i else None
         name = i['name'] if 'name' in i else None

         log_conf = None
         log_conf_data = i['log_conf'] if 'log_conf' in i else None
         if log_conf_data is not None:
            log_conf = LoggingConfFile()
            log_conf.load_data(log_conf_data)
         
         host_data = i['host'] if 'host' in i else None
         if host_data is not None:
            host = Host()
            host.load_data(host_data)

         filters = i['filters'] if 'filters' in i else []
         logs =  i['logs'] if 'logs' in i else []

         platform = i['platform'] if 'platform' in i else None
         username = i['username'] if 'username' in i else None
         port = i['port'] if 'port' in i else None
         return Instance(instance_id=i['instance_id'],ssh_key_name=ssh_key_name,ip_address=ip_address,name=name,logs=logs,platform=platform,log_conf=log_conf,username=username,port=port)
      else:
         return None


   def remove_logs_from_conf(self):
      """
      Removes from the instance logentries conf the logs whose paths are not in the instance log paths list.
      """
      log_conf = self.get_log_conf()
      host = log_conf.get_host()
      if host is None:
         return
      updated_logs = []
      for log in host.get_logs():
         if log.get_filename() in self.get_logs():
            updated_logs.append(log)
      host.set_logs(updated_log)
      log_conf.set_host(host)
      self.set_log_conf(log_conf)

   def get_new_logs(self):
      """
      Returns the list of log paths that are not known by the log configuration associated to this instance
      """
      log_conf = self.get_log_conf()
      if log_conf is None or log_conf.get_host() is None:
         return self.get_logs()
      conf_logs = log_conf.get_host().get_logs()
      conf_log_names = [log.get_filename() for log in conf_logs]
      new_logs = [log_path for log_path in self.get_logs() if log_path not in conf_log_names]
      return new_logs
      

   def to_json(self):
      """
      Returns a dictionnary representing the attribute values of this instance.
      """
      result = {"instance_id":self.get_instance_id(),"ssh_key_name":self.get_ssh_key_name(),"ip_address":self.get_ip_address(), "username": self.get_username(),"port":self.get_port(),"filters":self.get_filters(),"logs":self.get_logs()}
      if self.get_log_conf() is not None:
         result['log_conf'] = self.get_log_conf().to_json()
      else:
         result['log_conf'] = None
      return result

   def __unicode__(self):
      return json.dumps(self.to_json())

   def __eq__(self, other):
      return (isinstance(other, self.__class__) and self.get_instance_id() == other.get_instance_id())

   def __ne__(self, other):
      return not self.__eq__(other)


class RemoteInstance(Instance):


   def run_instance_update(self,func,use_sudo):
      """
      Args:
      func is a function that runs on the physical instance and updates the remote instance object with the information retrieved.
      use_sudo is a boolean value that indicates if sudo is required to execute func.
      Updates the remote instance object with information retrieve by func
      """
      if self.get_username() is None:
         usernames = self.get_aws_conf().get_usernames()
      else:
         usernames = [self.get_username()]
      root_privileges = False
      for username in usernames:
         key_filename = os.path.expanduser(self.get_ssh_key_name())
         try:
             ssh = paramiko.SSHClient()
             ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
             ssh.connect(self.get_ip_address(), username=username, key_filename=key_filename)
         except paramiko.SSHException as e:
             logger.warning('Connection to %s with user %s and ssh key %s failed. %s',self.get_ip_address(),username,key_filename,e)
             continue
         except socket.error as e1:
             logger.warning('Connection to %s with user %s and ssh key %s failed. %s',self.get_ip_address(),username,key_filename,e1)
             continue
         try:
            func(self,use_sudo,ssh)
         except SudoException as e:
            continue
         root_privileges = True
         break
      # update instance information with username if found
      if root_privileges:
         self.set_username(username)
      return self


   def get_instance_log_path(self,ssh):
      # Retrieve log file paths
      log_paths = []
      for path in self.get_filters():
         tmp_file_name = '/tmp/log_list.txt'
         chan = ssh.get_transport().open_session()
         chan.get_pty()
         chan.exec_command("sudo find %s -type f -regex '%s' > %s"%(path,self.get_log_filter(),tmp_file_name))
         if chan.recv_stderr_ready():
            error_msg = chan.recv_stderr(1024)
            print error_msg
            logger.error('Could not retrieve log file locations, error=%s',error_msg)
         #stdin, stdout, stderr = 
         try:
            f = ssh.open_sftp().open(tmp_file_name)
         except IOError as e:
            print 'Could not open %s. %s'%(tmp_file_name,e.message)
            logger.error('Could not open %s. %s',tmp_file_name,e.message)
         log_paths.extend([logpath.split('\n')[0] for logpath in f.readlines()])
      logger.info('Log Paths: %s',log_paths)
      # Remove the remote tmp file
      _, _, stderr = ssh.exec_command('rm %s'%tmp_file_name)
      if stderr != '':
         logger.error('Error while removing temporary file /tmp/log_list.txt on %s. %s',self.get_ip_address(),stderr.read())
      # set instance information
      self.set_logs([log_path for log_path in log_paths])
      return


   def get_instance_log_conf(self,ssh):
      # Retrieve current log config
      filename = 'logentries_%s.conf'%self.get_instance_id()
      log_conf = None
      log_conf_file = None
      rsyslog_conf_name = '/etc/rsyslog.d/%s'%filename
      try:
         log_conf_file = ssh.open_sftp().open(rsyslog_conf_name)
      except:
         logger.warning('Cannot open %s on remote instance %s',rsyslog_conf_name,self.get_instance_id())
      if log_conf_file != None:
         log_conf = configfile.LoggingConfFile.load_file(log_conf_file,filename)
         # Set the configuration file name
         log_conf.set_name(filename)

      # Update instance information with current log config
      self.set_log_conf(log_conf)
      return


   def deploy_log_conf(self):
       # Save log config in a file and retrieve its name
       self.get_log_conf().save()
       filename = self.get_log_conf().get_name()
       
       if self.get_username() is None:
           usernames = self.get_aws_conf().get_usernames()
       else:
           usernames = [self.get_username()]
       for username in usernames:
           key_filename = os.path.expanduser(self.get_ssh_key_name())
           try:
               ssh = paramiko.SSHClient()
               ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
               ssh.connect(self.get_ip_address, username=username, key_filename=key_filename)

           except paramiko.SSHException as e:
               logger.error('Connection to %s with user %s and ssh key %s failed. %s',self.get_ip_address(),username,key_filename,e)
               continue
           # Copy the file previously saved onto the instance
           try:
               ssh.open_sftp().put(filename,'/tmp/%s'%filename)
           except:
               logger.error('Transfering %s to remote /tmp/%s Failed',filename,filename)
           # Restart syslogd
           # TODO: Capture errors and report them
           chan = ssh.get_transport().open_session()
           chan.get_pty()
           try:
               chan.exec_command('sudo mv /tmp/%s /etc/rsyslog.d/.'%filename)

               chan = ssh.get_transport().open_session()
               chan.get_pty()
               chan.exec_command('sudo service rsyslog restart > /tmp/output.txt')
           except paramiko.SSHException as e:
               logger.error('Connection to %s with user %s and ssh key %s failed. %s',self.get_ip_address(),username,key_filename,e)
           except:
               logger.error('Connection to %s with user %s and ssh key %s failed. %s',self.get_ip_address(),username,key_filename)

           try:
               f = ssh.open_sftp().open('/tmp/output.txt')
           except IOError as e:
               logger.error('Could not open %s. %s','/tmp/output.txt',e.message)
           for line in f.readlines():
               logger.info(line)

           if chan.recv_stderr_ready():
               logger.error('Error when restarting rsyslog. %s',chan.recv_stderr(1024))
               return
           logger.info('Rsyslog restarted successfully on %s',self.get_instance_id())

   def update_instance_conf(self):
       """
       Returns the updated log_conf, taking into account new log files present on the instance as well as modifications made to the corresponding logentries host.
       """
       log_conf = None
       log_client = LogClient.Client(self.get_aws_conf().get_account_key()) 
       if self.get_log_conf() is None and len(self.get_logs())>0:
           host = log_client.create_host(name='AWS_%s'%self.get_instance_id(),location='AWS')
           logger.info('Created Host: %s',str(host.get_name()))
           if host is None:
               logger.error('Error when creating host for instance %s',self.get_instance_id())
               return
           for log_name in self.get_logs():
               host,_ = log_client.create_log_token(host=host,log_name=log_name)
           log_conf = configfile.LoggingConfFile(name='logentries_%s.conf'%self.get_instance_id(),host=host)
       
       elif self.get_log_conf() is not None:
           log_conf = self.get_log_conf()
           conf_host = log_conf.get_host()
           if conf_host is None:
               logger.error('Error. This instance configuration is missing the corresponding model!! instance_id=%s',self.get_instance_id())
               return None

           account = log_client.get_account()
           matching_host = None
           for host in account.get_hosts():
               if host.get_key() == conf_host.get_key():
                   matching_host = host
                   break
           # If there is no matching host, then it is assumed that it was deleted from Logentries and that no configuration should be associated to this instance.
           if matching_host is None:
               return None
           # Addition to the matching host on Logentries are not taken into account (they may not make sense on the instance). Only log removal from Logentries are taken into account
           #for conf_log in conf_host.get_logs():
           #    matching_log = None
           #    for log in matching_host.get_logs():
           #        if log.get_key() == conf_log.get_key():
           #            matching_log = log.get_key()
           #            break
               # Remove conf_log from the current configuration if it no longer exsist on Logentries
           #    if matching_log is None:
           #        conf_host.remove_log(conf_log)
           # Finally add new logs if any. TODO: would it be better to do this at the beginning of this function?
           new_logs = self.get_new_logs()
           for new_log in new_logs:
               matching_host,_ = log_client.create_log_token(host=matching_host,log_name=new_log)
           log_conf.set_host(matching_host)
       return log_conf



class InstanceLog(logentriessdk.models.Log):
   """
   This class represents an instance log file with a representation in logentries.com.
   It encodes the relationship between a path on an instance and a logentries log object.
   """
   def __init_(self, path=None, log=None):
      self._logentries_log = log
      self._path = path

   def set_path(self, path):
      self._path = path

   def get_path(self):
      return self._path

   def set_logentries_log(self, log):
      self._logentries_log = log

   def get_logentries_log(self):
      return self._logentries_log

   def load_data(self, log_data):
      # TODO: make it more robust in case keys don't belong to the dictionary
      self.set_path(log_data['path'])
      self.set_logentries_log(log_data['log'])


   def to_json(self):
      """
      Returns a dictionnary representing the attribute values of this log instance.
      """
      log_repr = {'path': self.get_path(),'log': self.get_logentries_log()}
      return log_repr

   def __unicode__(self):
      return json.dumps(self.to_json())


