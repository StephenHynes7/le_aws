import paramiko
import boto.ec2
# TODO: the following dependency seems to no longer be necessary
import boto.manage.cmdshell

import json
import os
import sys
import socket

from logentriesprovisioning import instance
from logentriesprovisioning import sshkeys
from logentriesprovisioning import configfile
from logentriesprovisioning import constants

import logging
logger = logging.getLogger('sync')

class AWSConfFile(object):

   def __init__(self,filename='aws.json',instances=[]):
      try:
         conf_file = open(filename,'r')
      except IOError:
         print 'Cannot open file %s'%filename
         logger.error('Cannot open file %s',filename)
      else:
         conf_json = json.load(conf_file)
         conf_file.close()
         self._name = filename
         key_id = 'aws_access_key_id'
         secret_key = 'aws_secret_access_key'

         if key_id in conf_json:
            self._aws_access_key_id = conf_json[key_id]
         else:
            print '%s missing in %s'%(key_id,filename)
            logger.error('%s missing in %s',key_id,filename)
            self._aws_access_key_id = None

         if 'filters' in conf_json:
            self._filters = conf_json['filters']
         else:
            print '%s missing in %s'%('filters',filename)
            logger.error('%s missing in %s','filters',filename)
            self._filters = []

         if secret_key in conf_json:
            self._aws_secret_access_key = conf_json[secret_key]
         else:
            print '%s missing in %s'%(secret_key,filename)
            logger.error('%s missing in %s',secret_key,filename)
            self._aws_secret_access_key = None

         if 'usernames' in conf_json:
            self._usernames = conf_json['usernames']
         else:
            print 'usernames missing in %s'%(filename)
            logger.error('usernames missing in %s',filename)
            self._usernames = None

         if 'ssh_key_paths' in conf_json:
            self._ssh_key_paths = conf_json['ssh_key_paths']
         else:
            print 'ssh key paths missing in %s'%(filename)
            logger.error('ssh_key_paths missing in %s',filename)
            self._ssh_key_paths = None


   def set_name(self,name):
      self._name = name

   def get_name(self):
      return self._name

   def get_ec2_filter(self,_filter):
      if 'ec2_filter' not in _filter:
         return None
      return _filter['ec2_filter']

   def set_filters(self,filters):
      self._filters = filters

   def get_filters(self):
      return self._filters

   def get_log_filter(self,_filter):
      if 'log_filter' not in _filter:
         return None
      return _filter['log_filter']

   def set_aws_access_key_id(self,aws_access_key_id):
      self._aws_access_key_id = aws_access_key_id

   def get_aws_access_key_id(self):
      return self._aws_access_key_id

   def set_aws_secret_access_key(self,aws_secret_access_key):
      self._aws_secret_access_key = aws_secret_access_key

   def get_aws_secret_access_key(self):
      return self._aws_secret_access_key

   def set_usernames(self,usernames):
      self._usernames = usernames

   def add_username(self,username):
      if username not in self._usernames:
         self._usernames.append(username)

   def add_usernames(self,usernames):
      for username in usernames:
         add_username(username)

   def get_usernames(self):
      return self._usernames

   def set_ssh_key_paths(self,ssh_key_paths):
      self._ssh_key_paths = ssh_key_paths

   def get_ssh_key_paths(self):
      return self._ssh_key_paths

   def add_ssh_key_path(self,ssh_key_path):
      if self.get_ssh_key_paths() is None:
         self.set_ssh_key_paths([ssh_key_path])
      elif ssh_key_path not in _ssh_key_paths:
         self.get_ssh_key_paths().append(ssh_key_path)


   @staticmethod
   def open(filename):
      try:
         return AWSConfFile(filename=filename)
      except IOError:
         print 'Cannot open file %s'%filename
         logger.error('Cannot open file %s',filename)
         return None

   def save(self):
      conf_file = open(self.get_name(),'w')
      conf_file.write(json.dumps(self.to_json(),indent=2))
      conf_file.close()

   def to_json(self):
      return {"account_key":self.get_account_key(),"aws_access_key_id":self.get_aws_access_key_id(),"aws_secret_access_key":self.get_aws_secret_access_key(),"usernames":self.get_usernames,"ssh_key_paths":self.get_ssh_key_paths(),"usernames":self.get_usernames(),"filters": self.get_filters()}

   def __unicode__(self):
      return json.dumps(self.to_json())



class AWS_Client(object):

   def __init__(self,aws_conf=None,ec2_instances=[]):    
       self._aws_conf = aws_conf
       self._ec2_instances = ec2_instances

   def get_aws_conf(self):
       return self._aws_conf

   def set_aws_conf(self,aws_conf):
       self._aws_conf = aws_conf

   def get_ec2_instances(self):
       return self._ec2_instances

   def set_ec2_instances(self,ec2_instances):
       self._ec2_instances = ec2_instances

   def add_ec2_instance(self,ec2_instance):
       ec2_instances = self.get_ec2_instances()
       if ec2_instance in ec2_instances:
           return
       ec2_instances.append(ec2_instance)
       self.set_ec2_instances(ec2_instances)

   def remove_ec2_instance(self,ec2_instance):
       ec2_instances = self.get_ec2_instances()
       ec2_instances.remove(ec2_instance)
       self.set_ec2_instances(ec2_instances)


   def get_ec2_instance(self,ec2_instance_id):
       for ec2_instance in self.get_ec2_instances():
           if ec2_instance.id == ec2_instance_id:
               return ec2_instance
       return None

   def get_instance(self,local_keys,ec2_instance):
      """
      Args:
      local_keys is a dictionnary mapping ssh key names to their location.
      ec2_instance is a Boto instance object.
      """
      if ec2_instance.key_name is not None and ec2_instance.key_name in local_keys:
         if ec2_instance.platform is None:
            logger.info('Platform is Linux for instance with id=%s and can be ssh-ed!',ec2_instance.id)
            platf = 'linux'
         else:
            platf = ec2_instance.platform
            logger.info('Platform is %s for instance with id=%s',platf,ec2_instance.id)
            return None
         if 'Name' in ec2_instance.tags:
            name = ec2_instance.tags['Name']
         else:
            name = ec2_instance.id+'_'+ec2_instance.ip_address
         if 'user' in ec2_instance.tags:
            username = ec2_instance.tags['user']
         else:
            username = None
         return instance.RemoteInstance(instance_id=ec2_instance.id,ssh_key_name=local_keys[ec2_instance.key_name],ip_address=ec2_instance.ip_address,name=name,platform=platf,username=username)
      return None


   def load_instance_ssh_attributes(self,local_keys,ec2_instance,log_filter='/var/log/.*log'):
      """
      """
      sudo_user = None
      if ec2_instance.platform == 'windows':
         logger.info('No attempt to ssh instance %s as its platform is %s',ec2_instance.id,ec2_instance.platform)
         return None

      instance = self.get_instance(local_keys,ec2_instance)
      
      if instance is None:
         return None

      instance.set_log_filter(log_filter)
      if instance.get_username() is None:
         usernames = self.get_aws_conf().get_usernames()
      else:
         usernames = [instance.get_username()]
      for username in usernames:
         logger.debug('Checking if %s has sudo privileges on %s ',username,instance.get_instance_id())
         key_filename = os.path.expanduser(instance.get_ssh_key_name())
         try:
             ssh = paramiko.SSHClient()
             ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
             ssh.connect(ec2_instance.ip_address, username=username, key_filename=key_filename)
             stdin, stdout, stderr = ssh.exec_command('sudo whoami',get_pty=True)
         except paramiko.SSHException as e:
            logger.warning('Connection to %s with user %s and ssh key %s failed. %s',instance.get_ip_address(),username,key_filename,e)
            continue
         except socket.error as e1:
            logger.warning('Connection to %s with user %s and ssh key %s failed. %s',instance.get_ip_address(),username,key_filename,e1)
            continue

         logger.debug('Checking if %s has sudo privileges on %s ',username,instance.get_instance_id())
         for line in stdout:
            if line.startswith('root'):
               sudo_user = username
               logger.debug('sudo found, username=%s, instance=%s',username,instance.get_instance_id())
               break
         if sudo_user is not None:
            break
      # Update instance information with username, log paths and current log config
      instance.set_username(sudo_user)
      return instance


   def aws_create_ssh_config(self,filename='ssh_config'):
      """
      This function generates an ssh_config file saved at 'filename' with information about running ec2 instances that can be ssh-ed.
      """
      try:
         ssh_config = open(filename, 'w')
      except IOError as e:
         logger.info('Could not open aws configuration file, filename=%s, error=%s',filename,e.message)
         return None
      regions_info = boto.ec2.regions()
      for region in [boto.ec2.get_region(region_info.name) for region_info in regions_info]:
          logger.info('Region=%s',region)
          con = boto.ec2.connection.EC2Connection(aws_access_key_id=self.get_aws_conf().get_aws_access_key_id(), aws_secret_access_key=self.get_aws_conf().get_aws_secret_access_key(),region=region)
          if con is not None:
              try:
                  key_pairs = con.get_all_key_pairs()
              except boto.exception.EC2ResponseError as e:
                  print e.message
                  logger.error('Exception raised, message=%s',e.message)
              else:
                  key_names = [key_pair.name for key_pair in key_pairs]
                  ssh_k = sshkeys.SSHKeys(paths=self.get_aws_conf().get_ssh_key_paths(),names=key_names)
                  local_keys = ssh_k.get_keys_onpaths(ssh_k.get_paths(),ssh_k.get_names())

                  for _filter in self.get_aws_conf().get_filters():
                     ec2_filter = self.get_aws_conf().get_ec2_filter(_filter)
                     if ec2_filter is None:
                        ec2_filter = {}
                     log_filter = self.get_aws_conf().get_log_filter(_filter)
                     if log_filter is None:
                        log_filter = '/var/log/.*log' 
                     ec2_instances = con.get_only_instances(filters=ec2_filter)
                     for ec2_instance in ec2_instances:
                        if ec2_instance.state != 'running':
                           logger.info('Instance %s is not running, state=%s',ec2_instance.id,ec2_instance.state)
                           continue
                        instance = self.load_instance_ssh_attributes(local_keys,ec2_instance,log_filter)
                        if instance is not None:
                           ssh_config.write(instance.get_ssh_config_entry())
                  con.close()
      ssh_config.close()
      return ssh_config


def create_ssh_config(working_dir=None):
   if working_dir is None:
      return      

   constants.set_working_dir(working_dir)
   constants.set_aws_credentials(None)
   constants.set_account_key(None)
   constants.set_logentries_logging()

   if working_dir is None:
      aws_conf_filename = 'aws.json'
   else:
      aws_conf_filename = '%s/aws.json'%working_dir

   # Open the updated version of the aws config file
   aws_conf = AWSConfFile(aws_conf_filename)
   aws_client = AWS_Client(aws_conf)
   aws_client.aws_create_ssh_config()
   

if __name__ == '__main__':
   if len(sys.argv) < 2:
      print 'You must specify the path to the AWS configuration file containing your AWS credentials'
   else:
      constants.set_working_dir(sys.argv[1])
      constants.set_aws_credentials(None)
      constants.set_account_key(None)
      constants.set_logentries_logging()
      main('%s/aws.json'%constants.WORKING_DIR)
