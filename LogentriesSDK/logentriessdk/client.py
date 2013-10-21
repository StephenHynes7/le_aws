#!/usr/bin/python

#
# Logentries agent <https://logentries.com/>.
# This work is licensed under a <http://creativecommons.org/licenses/by/3.0/> Creative Commons Attribution 3.0 Unported License
#
# Mark Lacomber <mark@logentries.com>

"""The **LogentriesSDK.client.LogentriesClient** class provides a Python interface to the Logentries API,
allowing you to programmatically access Logentries resources.

You can instantiate this class as follows:    client = LogentriesClient('my_account_key'), where you would provide your Logentries
Account Key as the only parameter, if you don't provide it as a parameter, you must set an environment variable called 
LOGENTRIES_ACCOUNT_KEY contaning your account key.

Once created, you have the following methods at your disposal.  * indicates a parameter is optional

client.get_account()
client.create_host( name )
client.update_host( host, *name, *location )
client.remove_host( host )
client.get_host(hostkey,name)
client.get_log(logkey,hostkey,logname)
client.create_log_token( host, logname )
client.create_log_http( host, logname )
client.create_log_agent( host, logname, filename )
client.create_log_syslog( host, logname )
client.remove_log( host, log )
client.get_events()
client.get_event(eventname,_id)
client.delete_event(_id)
client.create_event(eventname,color)
client.get_tags(logkey)
client.get_tag( host, logname, tagname, _id)
client.create_tag( host, logname, tagname, eventid, pattern)
client.remove_tag( tagname, host, logname)

See individual calls for more information
"""

#
# Constants
#

VERSION="0.1"

#
# Modules
#
import os
import sys

#
# Le Modules
#
from logentriessdk.connection import LogentriesConnection 
from logentriessdk.exception import InvalidParametersException, InvalidLogSourceException
import logentriessdk.constants as constants
import logentriessdk.helpers as helpers
import logentriessdk.models as models
import inspect


class Client(object):

	def __init__(self, account_key=None):
		acc_key = helpers.check_user_key(account_key)
		self._account_key = acc_key
		self._conn = LogentriesConnection()

	def get_account_key(self):
		return self._account_key

	def get_account(self):
		request = {
			'request': constants.API_GET_ACCOUNT,
			'user_key': self._account_key,
			'load_hosts': 'true',
			'load_logs': 'true'
		}
		account_data, success = self._conn.request( request )

		if not success:
			print 'Error retrieving account with key %s'%self.get_account_key()
			return None

		account = models.Account()
		account.load_data(account_data)
		return account

	def _create_log( self, host, log_name, source, filename=None):

		host_key = helpers.inspect_host( host )

		if not helpers.is_valid_log_source( source ):
			raise InvalidLogSourceException

		request = {
			'request': constants.API_NEW_LOG,
			'user_key': self._account_key,
			'host_key': host_key,
			'name': log_name,
			'type': '',
			'retention': constants.DEFAULT_RETENTION,
			'source': source
		}

		request['filename'] = filename if filename is not None else ''

		log_data, success = self._conn.request( request )

		if success:
			if 'log' in log_data and 'key' in log_data['log']:
				host.add_log(log_data['log'] )
				return host, log_data['log']['key']
			else:
				print 'Log information was missing when creating log, log_name=%s, host_name=%s'%(str(log_name),str(host.get_name()))
				return host, None
		else:
			return host, None


	def create_host( self, name, **optionals ):
		""" Creates a new host on Logentries. 
		Required Parameters:
			name     (This is the name of the host)
		Optional Parameters:
			location (This is the name of the server)

		Successful response returns object as follows:
		{
			"response": "ok",
			"host": { "logs"    : [],    # List of logs inside host, not applicable for creation
					  "c"       : 123445678,  #Creation date in Unix Epoch
					  "name"    : "name you provided",
					  "distver" : "",  
					  "hostname": "location you provided, else 'nolocation'",
					  "object"  : "host",
					  "distname": "",
					  "key"     : "12345678-1234-1234-1234-123456789123",
					},
			"user_key":"12345678-1234-1234-1234-123456789123",
			"agent_key":"12345678-1234-1234-1234-123456789123"
		}"""

		location = optionals.get( 'location','' )

		request = {
			'request': constants.API_NEW_HOST,
			'user_key': self._account_key,
			'name': name,
			'hostname': location,
			'distver': '',
			'system': '',
			'distname': ''
		}

		host_data, success = self._conn.request( request )

		if success:
			host = models.Host()
			if 'host' in host_data:
				host.load_data(host_data['host'])
				return host
			else:
				print 'Host is missing from Response.'
				return None
		else:
			print 'Response for host creation with name %s is not OK.'%str(name)
			return None

	def update_host( self, host, **optionals ): 
		""" Updates an existing host on Logentries.
			Required Parameters:
				host (Host object returned by the create_host method or the host_key UUID for it)
			Optional Parameters:
				name	 (The new name you would like to give the host)
				location (The new name of the server you would like to give the host

			Successful response returns object as follows:
			{	
				"response":"ok",
				"host": { "logs"    : [],    # List of logs inside host, not applicable for creation
						  "c"       : 123445678,  #Creation date in Unix Epoch
						  "name"    : "name you provided",
						  "distver" : "",  
						  "hostname": "location you provided, else 'nolocation'",
						  "object"  : "host",
						  "distname": "",
						  "key"     : "12345678-1234-1234-1234-123456789123",
						},
				"user_key":"12345678-1234-1234-1234-123456789123"
			}"""

		host_key = helpers.inspect_host( host )

		name = optionals.get( 'name', '' )
		location = optionals.get( 'location', '' )

		if helpers.parameters_are_empty( name, location ):
			raise InvalidParametersException("You must provide either 'name' or 'hostname' values to update a host")
			
		request = {
			'request': constants.API_SET_HOST,
			'user_key': self._account_key,
			'host_key': host_key,
		}

		if name != '':
			request['name'] = name

		if location != '':
			request['hostname'] = location

		host_data, success = self._conn.request( request )

	def remove_host( self, host, **optionals ):
		""" Removes an existing host on Logentries.
			Required Parameters:
				host (host object returned by the create_host method)			
			
			Successful response returns object as follows:
			{
				"response":"ok",
				"host_key":"12345678-1234-1234-1234-123456789123",
				"user_key":"12345678-1234-1234-1234-123456789123",
				"reason": "Host 'host_name' removed."
			}"""

		host_key = helpers.inspect_host( host )

		request = {
			'request': constants.API_RM_HOST,
			'user_key': self._account_key,
			'host_key': host_key
		}

		removed_host, success = self._conn.request( request )

		if success:
			return True
		else:
			return False

	def create_log_token( self, host, log_name, **optionals ):
		""" Creates a log of source type Token TCP. 
			Required Parameters:
				host (The host object returned by create_host you wish to create the log in)
				log_name (The name you would like to give the new log)

			Successful response returns object as follows:
			{
				"response":"ok",
				"log_key" :"12345678-1234-1234-123456789123",
				"log":{
						"token"  :"12345678-1234-1234-123456789123",#Use this Token to send events
						"created":12345678910, 						#Unix Epoch creation
						"name"   :"log_name",
						"retention":-1,  							#Default retention
						"filename":"", 							#Only used for agent logs
						"object" :"log",
						"type"   :"token",
						"key"	 :"12345678-1234-1234-1234-123456789123",
						"follow" :"false" 
					  }
			}"""

		return self._create_log( host, log_name, constants.LOG_TOKEN )

	def create_log_http( self, host, log_name, **optionals ):
		""" Creates a log of source type HTTP PUT. 
			Required Parameters:
				host (The host object returned by create_host you wish to create the log in)
				log_name (The name you would like to give the new log)
			Optional Parameters:
				account_key (Logentries Account Key, can be environment variable or passed to method)	

			Successful response returns object as follows:
			{
				"response":"ok",
				"log_key" :"12345678-1234-1234-123456789123",
				"log":{
						"created":12345678910, 					#Unix Epoch creation
						"name"   :"log_name",
						"retention":-1,  						#Default retention
						"filename":"", 							#Only used for agent logs
						"object" :"log",
						"type"   :"api",
						"key"	 :"12345678-1234-1234-1234-123456789123",
						"follow" :"false" 
					  }
			}"""

		return self._create_log( host, log_name, constants.LOG_HTTP )

	def create_log_agent( self, host, log_name, filename, **optionals ):
		""" Creates a log of source type 'agent'. To be used in conjunction with logentries agent.
			Required Parameters:
				host (The host object returned by create_host you wish to create the log in)
				log_name (The name you would like to give the new log)
				filename (The full location of the file on your machine)

			Successful response returns object as follows:
			{
				"response":"ok",
				"log_key" :"12345678-1234-1234-123456789123",
				"log":{
						"created":12345678910, 						#Unix Epoch creation
						"name"   :"log_name",
						"retention":-1,  							#Default retention
						"filename":"filename", 
						"object" :"log",
						"type"   :"agent",
						"key"	 :"12345678-1234-1234-1234-123456789123",
						"follow" :"true" 
					  }
			}"""

		return self._create_log( host, log_name, constants.LOG_AGENT, filename )

	def create_log_syslog( self, host, log_name, **optionals ):
		""" Creates a log of source type Syslog.
			Required Parameters:
				host (The host object returned by create_host you wish to create the log in)
				log_name (The name you would like to give the new log)

			Successful response returns object as follows:
			{
				"response":"ok",
				"log_key" :"12345678-1234-1234-123456789123",
				"log":{
						"port":12345 					#Use this port to send events
						"created":12345678910, 			#Unix Epoch creation
						"name"   :"log_name",
						"retention":-1,  				#Default retention
						"filename":"", 					#Not used for token logs
						"object" :"log",
						"type"   :"token",
						"key"	 :"12345678-1234-1234-1234-123456789123",
						"follow" :"false" 
					  }
			}"""

		return self._create_log( host_key, log_name, constants.LOG_SYSLOG )

	def remove_log( self, host, log, **optionals ):
		""" Deletes an existing logfile on Logentries.
			Required Parameters:
				host_key (The UUID key of the host containing the log)
				log_key (The UUID key of the log you would like to remove)
			Optional Parameters:
				account_key (Logentries Account Key, can be environment variable or passed to method)

			Successful response returns the following object:
			{
				"response":"ok",
				"host_key":"12345678-1234-1234-1234-123456789123",
				"reason"  :"Log 'log_name' removed",
				"user_key":"12345678-1234-1234-1234-123456789123",
				"log_key" :"12345678-1234-1234-1234-123456789123"
			}"""

		host_key = helpers.inspect_host( host )
		log_key = helpers.inspect_log( log )

		request = {
			'request': constants.API_RM_LOG,
			'user_key': self._account_key,
			'host_key': host_key,
			'log_key': log_key
		}

		removed_log, success = self._conn.request( request )

		if success:
			return True
		else:
			return False


        def get_hosts(self):
		""" 
		Retrieves the hosts of the client account.
                Returns a not None list of host objects.
                """
                account = self.get_account()
                if account is None:
                        return []
		return account.get_hosts()


        def get_host(self, hostkey, name=None):
		""" Retrieves the host with the specified logkey. If logkey is None, then this method returns the first encountered host with name 'name'.
                Returns None if no host with key 'hostkey' or name 'name' could be retrieved.
                """
                account = self.get_account()
                if account is None:
                        return None
                if hostkey is not None:
                        return account.get_host(hostkey)
                if name is not None:
                        for host in account.get_hosts():
                                if host.get_name() == name:
                                        return host
                return None


        def get_log(self, logkey, hostkey=None, logname=None):
		""" Retrieves the log with the specified logkey. If logkey is None, then this method returns the first encountered log with name 'logname' that is part of host with key 'hostkey'. 
                Returns None if no log with key 'logkey' or name 'logname' (within host with key 'hostkey') could be retrieved.
                """
                account = self.get_account()
                if account is None:
                        return None
                for host in account.get_hosts():
                        if logkey is not None:
                                return host.get_log(logkey)
                        
                        for log in host.get_logs():
                                if log.get_name() == logname:
                                        return log
                return None

        def get_events(self):
		""" Retrieves all the events for a Logentries account.
                Returns a list of events where each event is a json structure with keys:
                {
                'vtype',
                'name',
                'title',
                'color',
                'active',
                'id',
                'desc'.
                }
                Returns None if no events could be retrieved.
                """
		request = {
                        'request':'list_tags',
                        'user_key':self.get_account_key(),
                        'id':'init_menu'
		}

		events, success = self._conn.request( request )

		if success and 'tags' in events:
			return events['tags']
                else:
                        return None

        def get_event(self,eventname,_id=None):
		""" Retrieves Event with id '_id' if it is specified or the first event whose name matches eventname from a Logentries account. _id has precedence over name. So if _id is specified, then eventname is discarded.
                Returns Event as a json structure with keys:
                {
                'vtype',
                'name',
                'title',
                'color',
                'active',
                'id',
                'desc'.
                }
                Returns None if no event with name eventname exist or if it could not be retrieved.
                """
                key = '_id'
                if _id is None:
                        key = 'name'
                events = self.get_events()
                if events is not None:
                        for event in events:
                                if key in event and event[key] == eventname:
                                        return event
                return None

        def create_event(self,eventname,color):
		""" Returns the id of the event with name eventname and color 'color' for a Logentries account. If an event with name eventname already exist for the logentries account, then it is returned and no new event is created (In particular, color is discarded in this case). If no event with name eventname already exists then one is created and returned.
                Returns None if no event could be created or if its id could not be retrieved.
                """
                event = self.get_event(eventname)
                if event is None:
                        request = {
                                'request':'set_tag',
                                'user_key': self.get_account_key(),
                                'tag_id': '',
                                'name': eventname,
                                'title': eventname,
                                'desc': eventname,
                                'color': color,
                                'vtype': 'bar'
                        }

                        resp, success = self._conn.request( request )

                        if success and 'tag_id' in resp:
                                return resp['tag_id']
                if 'id' in event:
                        return event['id']
                return None

        def remove_event(self,_id):
		""" Removes the event of with id '_id' from a Logentries account.
                Returns True if and only if event with id _id has been removed (whether such an event exists or not). False is returned if the attempt for removal failed.
                """
                request = {
                        'request':'rm_tag',
                        'user_key': self.get_account_key(),
                        'tag_id': _id,
                }
                
                _, success = self._conn.request( request )
                return success



        def get_tags(self, logkey):
		""" Retrieves all the tags for a Logentries log.
                Returns a list of tags associated with log with key 'logkeys' where each tag is a json structure with keys:
                {
                'object',
                'name',
                'key',
                'pattern',
                'tags', (representing a list of event ids associated to the tag)
                }
                Returns None if no events could be retrieved.
                """
		request = {
                        'request': 'list_tagfilters',
                        'user_key': self.get_account_key(),
                        'log_key': logkey,
                        'id': 'init_menu'
		}

		response, success = self._conn.request( request )

		if success and 'list' in response:
			return response['list']
                else:
                        return None


        def get_tag(self, host, logname, tagname, _id=None):
		""" Retrieves the first tag encountered with name 'tagname' from the log with name logname in host. The tag is a json structure with keys:
                {
                'object',
                'name',
                'key',
                'pattern',
                'tags', (representing a list of event ids associated to the tag)
                }
                Returns None if no tag could be retrieved with name tagname, for log with name logname in host.
                """
                log = self.get_log(host,logname)
                if log is None:
                        return None
                tag_list = self.get_tags(log.get_key())
                if tag_list is None:
                        return None
                for tag in tag_list:
                        if tag.get_name() == tagname:
                                return tag
                return None


        def create_tag(self, host, logname, tagname, eventid, pattern=''):
		""" creates a tag with name 'tagname' for the log with name logname in host. The tag is associated event with id 'eventid' and to pattern pattern. name a json structure with keys:
                {
                'object',
                'name',
                'key',
                'pattern',
                'tags', (representing a list of event ids associated to the tag)
                }
                Returns None if no tag could be retrieved with name tagname, for log with name logname in host.
                """
		log = client.get_log(host,logname)
		if log is None:
			return None
		request = {
			'request': 'set_tagfilter',
			'user_key': self.get_account_key(),
			'name': tagname,
			'pattern': pattern,
			'tags': eventid,
			'tagfilter_key':'',
			'log_key': log.get_key()
			}
		response, success = self._conn.request( request )

		if success and 'tag_filter' in response:
			return response['tag_filter']
                else:
                        return None


        def remove_tag(self, tagname, host, logname):
		""" Removes the tag encountered with name 'tagname' from the log with name logname in host. The tag is a json structure with keys:
                {
                'object',
                'name',
                'key',
                'pattern',
                'tags', (representing a list of event ids associated to the tag)
                }
                Returns the deleted tag or None if no tag could be retrieved with name tagname, for log with name logname in host.
                """
		log = client.get_log(host,logname)
		if log is None:
			return None
		tag_data = get_tag(host, logname, tagname)
		if tag_data is None or 'tagfilter_key' not in tag_data:
			return None
		request = {
			'request': 'rm_tagfilter',
			'user_key': self.get_account_key(),
			'name': tagname,
			'pattern': pattern,
			'tags': eventid,
			'tagfilter_key': tag_data['tagfilter_key'],
			'log_key': log.get_key()
			}
		response, success = self._conn.request( request )

		if success and 'tag_filter' in response:
			return response['tag_filter']
                else:
                        return None



if __name__ == '__main__':
        client = Client(account_key='9d1d1f88-eb3a-4522-8196-f45414530ef7')
        print unicode(client.get_events())
        print unicode(client.get_event('Rsyslog Restarted'))
        print unicode(client.get_event('RsyslogRestarted'))
        event_id = client.create_event('RsyslogRestarted',constants.COLORS[0])
        print unicode(client.get_account())
        print unicode(event_id)
        if event_id is not None:
                print unicode(client.remove_event(event_id))
                print unicode(client.remove_event(event_id))
        host = client.get_host(hostkey=None,name='AutoProvisionning')
        if host is None:
                print None
        else:
                print unicode(host.to_json())
                log = client.get_log(logkey=None,hostkey=host.get_key(),logname='Setup')
                if log is None:
                        print None
                else:
                        print unicode(client.get_tags(log.get_key()))
                        tag = client.create_tag()

        
                        
