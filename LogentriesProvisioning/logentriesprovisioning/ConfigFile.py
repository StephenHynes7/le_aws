import paramiko
import boto.ec2
import boto.manage.cmdshell

import os.path
import json
import instance
from logentriessdk.models import Log
from logentriessdk.models import Host
from logentriessdk.client import Client
from logentriessdk.models import Account


class InstancesConf:
   """
   This class represents a list of instances with information about connecting to these instances: username, ip address, ssh key location as well as the logentries account key related to this list of instances. It also contains filter regarding log file locations on those instances.
   """
   def __init__(self,account_key,instances=[]):
      self._account_key = account_key
      self._instances = instances

   def load_conf_data(self,conf_json):
      # Specify the logentries account key related to these instances
      if 'account_key' in conf_json:
         self._account_key = conf_json['account_key']
      else:
         print '%s missing in configuration'%('account_key')
         logger.error('%s missing in configuration','account_key')
         self._account_key = None
         
      if 'log_filters' in conf_json:
         self._log_filters = [LogFilter.load_json(log_filter_raw) for log_filter_raw in conf_json['log_filters']]
      else:
         print '%s missing in configuration'%('log_filters')
         logger.error('%s missing in configuration','log_filters')
         self._log_filters = {}

      if 'instances' in conf_json:
         self._instances = []
         for instance_data in conf_json['instances']:
            instance = instance.Instance.load_instance_data(instance_data)
            self._instances.append(instance)
      else:
         print 'instances missing in configuration'
         logger.error('instances missing in configuration')
         self._instances = None


   def load_conf_file(self,filename):
      try:
         conf_file = open(filename,'r')
      except IOError:
         print 'Cannot open file %s'%filename
         logger.error('Cannot open file %s',filename)
      else:
         conf_json = json.load(conf_file)
         conf_file.close()
         self.load_conf_data(conf_json)

   def set_log_filters(self,log_filters):
      self._log_filters = log_filters

   def get_log_filters(self):
      return self._log_filters

   def set_account_key(self,account_key):
      self._account_key = account_key

   def get_account_key(self):
      return self._account_key

   def set_instances(self,instances):
      self._instances = instances

   def add_instance(self,instance):
      if self.get_instances() is None:
         self._instances = [instance]
      elif instance not in self.get_instances():
         self._instances.append(instance)
      else:
         for i in range(0,len(self.get_instances())):
            if self.get_instances()[i] == instance:
               self._instances[i] = instance.load_aws_data(instance.to_json())
               break

   def add_instances(self,instances):
      for instance in instances:
         self.add_instance(instance)

   def get_instance_with_id(self,instance_id):
      for i in self.get_instances():
         if i.get_instance_id() == instance_id:
            return i
      return None

   def set_instance(self,instance_id,instance):
      for k in range(0,len(self.get_instances())):
         i = self.get_instances()[k]
         if i is None:
             print 'Error. Instance is None, id=%s'%instance_id
             logger.error('Error. Instance is None, id=%s',instance_id)
         if i.get_instance_id() == instance_id:
            self._instances[k] = instance
            return
      self.add_instance(instance)
      return

   def get_instances(self):
      return self._instances


   def save(self,filename):
      conf_file = open(filename,'w')
      conf_file.write(json.dumps(self.to_json(),indent=2))
      conf_file.close()

   def to_json(self):
      instance_list = []
      for instance in self.get_instances():
         instance_list.append(instance.to_json())
      return {"account_key":self.get_account_key(),"instances":instance_list}

   def __unicode__(self):
      return json.dumps(self.to_json())



class LoggingConfFile:
   """ """

   def __init__(self,name='logentries.conf',conf_format='rsyslog',host=None,instance_logs=[],polling_period=10):
      self._name = name
      self._conf_format = conf_format
      # _instance_logs is a list of mapping between paths and log keys, i.e. _instance_logs=[{'path':path,'log_key':key},...]
      self._instance_logs = instance_logs
      self._host=host
      self._polling_period = polling_period

   def set_format(self,conf_format):
      self._conf_format = conf_format

   def set_name(self,name):
      self._name = name

   def set_host(self,host):
      self._host = host

   def set_polling_period(polling_period):
      self._polling_period = polling_period

   def get_instance_logs(self):
      return self._instance_logs

   def set_instance_logs(instance_logs):
      self._instance_logs = instance_logs

   def get_instance_log_map(self):
      return self._instance_log_map

   def get_format(self):
      return self._conf_format

   def get_name(self):
      return self._name

   def get_host(self):
      return self._host

   def get_polling_period(self):
      return self._polling_period

   def add_instance_log(self,instance_log):
      self._instance_logs.append(instance_log)

   def to_model_rep(self):
      model_rep = '#LOGENTRIES_MODEL:'+unicode(self.get_host().get_key())+'\n'
      for instance_log in self.get_instance_logs():
         log = self.get_host().get_log(instance_log.get_logentries_log().get_key())
         # the logentries log associated to instance log is updated.
         instance_log = instance.InstanceLog(instance_log.get_path(),log)
         model_rep = model_rep + '#' + unicode(instance_log.to_json()) + '\n' 
      return model_rep

   def open(self):
      conf_file = open(self.get_name(),'r')
      conf_json = json.load(conf_file)
      conf_file.close()
      return create(conf_json)

   def save(self):
      """ """
      if self.get_format() == 'rsyslog':
         return self.save_rsyslog_conf()
      else:
         print '%s is not a valid output type'%(self.get_format())
         return None

   def save_rsyslog_conf(self):
      """ """
      if self.get_host() is None:
         print 'No configuration file saved for %s as host is None'%self.get_name()
         return
      # Open configuration file
      conf_file = open(self.get_name(),'w')
      # Set the rsyslog mode to follow files
      conf_file.write(self.get_start_rsyslog_conf())

      templates = ""
      for index in range(0,len(self.get_host().get_logs())):
         log = self.get_host().get_logs()[index]
         rsyslog_entry,template = self.create_rsyslog_entry(log,index)
         conf_file.write(rsyslog_entry)
         templates = templates + template + "\n"
      # Set the rsyslog polling policy 
      conf_file.write(self.get_poll_rsyslog_conf())
      conf_file.write(templates)
      conf_file.write(self.to_model_rep())
      return conf_file


   # Check if this is called and add code for instance_logs if it is
   def load_data(self,conf_data):
      if 'name' in conf_data:
         self._name = conf_data['name']
      if 'conf_format' in conf_data:
         self._conf_format = conf_data['conf_format']
      if 'host' in conf_data:
         host = Host()
         host.load_data(conf_data['host'])
         self._host = host
      if 'polling_period' in conf_data:
         self._polling_period = conf_data['polling_period']

   @staticmethod
   def load_file(conf_file,instance_id):
      """
      """
      filename = conf_file.name
      log_conf = LoggingConfFile(name=filename)
      host = Host(name=instance_id)
      logs = []
      for line in conf_file.readlines():
         if line.startswith('#LOGENTRIES_MODEL:'):
            host_key_array = line.split(':',1)
            if len(host_key_array) > 1:
               host.set_key(host_key_array[1])
            else:
               print 'Wrong format for Logentries Model in %s'%log_conf.get_name()
               return None
         elif line.startswith('#LOG:'):
            log_conf_array = line.split(':',1)
            if len(log_conf_array) > 1:
               instance_log = InstanceLog()
               instance_log.load_data(json.load(log_conf_array[1]))
               host.add_log(instance_log.get_logentries_log())
               log_conf.add_instance_log(instance_log)
            else:
               print 'Wrong log format for Logentries Model in %s'%log_conf.get_name()
               return None
      log_conf.set_host(host)
      return log_conf

   @staticmethod
   def load_rsyslog_conf(self, filename):
      """ 
      Returns the configuration loaded from filename
      """
      # Open configuration file
      conf_file = open(filename,'r')
      return load_file(conf_file)

   def create_rsyslog_entry(self,log,index):
      """ 
      Args: log is a log instance.
      Returns the strings representing an rsyslog template as well as an rsyslog entry for the log data provided
      """
      if not log.get_token():
         return "","";
      file_path = log.get_filename()
      file_id = 'tag%s'%str(index)
      format_name = 'format_%s'%file_id
      return """# FILE
            $InputFileName """+file_path+"""
            $InputFileTag """+file_id+"""
            $InputFileStateFile """+file_id+"""
            $InputFileSeverity info
            $InputFileFacility logentries0
            $InputRunFileMonitor\n\n
            ""","""$template """+format_name+""",\""""+log.get_token()+""" %HOSTNAME% %msg%\\n\"
            if $programname == '"""+file_id+"""' then @@api.logentries.com:10000;"""+format_name+"""\n& ~\n
            """


   def get_start_rsyslog_conf(self):
      return """$Modload imfile\n\n"""

   def get_poll_rsyslog_conf(self):
      return """
            # check for new lines every 10 seconds
            # Only entered once in case of following multiple files
            $InputFilePollInterval """+unicode(self.get_polling_period())+"""\n\n"""


   def to_json(self):
      """ """
      return {"name":self.get_name(),"conf_format":self.get_format(),"instance_logs": [instance_log.to_json() for instance_log in self.get_instance_logs()],"host":(None if self.get_host() is None else self.get_host().to_json()),"polling_period":self.get_polling_period()}

      
#if __name__ == '__main__':
   # Open the updated version of the aws config file
   #aws_conf = AWSConfFile('aws.json')
   #aws_client = AWS_Client(aws_conf)
   #aws_client.aws_refresh()

   # Update logentries account and create rsyslog config files
   #for instance in aws_client.get_aws_conf().get_instances():
   #   log_conf = aws_client.update_instance_conf(instance)
   #   if log_conf is not None:
   #      instance.set_log_conf(log_conf)
   #      instance.get_log_conf().save()
   #      aws_client.deploy_log_conf(instance)

   #client = Client(aws_client.get_aws_conf().get_account_key())
   #account = client.get_account()

   #for host in account.get_hosts():
      #log_str = "["
      #for log in host.get_logs():
      #   log_str = log_str + ", " + log.get_name()
      #print host.get_name() + " - " + log_str + "]"
      #print host.get_name() + " - " + str(len(host._logs))
   #for instance in aws_client.get_aws_conf().get_instances():
   #   print str(instance.get_instance_id()) + " - " + str(instance.get_ip_address())
