import socket, httplib, urllib
from logentriessdk.exception import InvalidServerResponse, MissingModuleException
import logentriessdk.constants as constants

import socket

try:
	import ssl
        wrap_socket = ssl.wrap_socket
        CERT_REQUIRED = ssl.CERT_REQUIRED
except ImportError:
	raise MissingModuleException("Please install the python SSL module to use this SDK.")

try:
	import json
except ImportError:
	try:
		import simplejson
	except ImportError:
		raise MissingModuleException("Please install the python JSON module to use this SDK.")


def create_connection( host, port):
        """
        A simplified version of socket.create_connection from Python 2.6.
        """
        for addr_info in socket.getaddrinfo( host, port, 0, socket.SOCK_STREAM):
                af, stype, proto, cn, sa = addr_info
                soc = None
                try:
                        soc = socket.socket( af, stype, proto)
                        soc.connect( sa)
                        return soc
                except socket.error:
                        if socket:
                                soc.close()

        raise socket.error, "Cannot make connection to %s:%s"%(host,port)

class ServerHTTPSConnection(httplib.HTTPSConnection):
        """
        A slight modification of HTTPSConnection to verify the certificate
        """

        def __init__(self, server, port, cert_file):
                self.cert_file = cert_file
                httplib.HTTPSConnection.__init__( self, server, port, cert_file=cert_file)

        def connect(self):
                sock = create_connection( self.host, self.port)
                try:
                        if self._tunnel_host:
                                self.sock = sock
                                self._tunnel()
                except AttributeError: pass
                self.sock = wrap_socket( sock, ca_certs=self.cert_file, cert_reqs=CERT_REQUIRED)


class LogentriesConnection:
	def __init__(self):
		pass

	def _make_api_call( self, request ):
		try:
                        cert_full_path = os.path.dirname(__file__)+'/cert.pem'
			http = httplib.ServerHTTPSConnection( constants.LE_SERVER_API, constants.LE_SERVER_API_PORT, cert_file=cert_full_path)
			params = urllib.urlencode(request)
			http.request( "POST", "/", params)
			resp = http.getresponse()
		except socket.sslerror, msg:
			raise InvalidServerResponse(msg)
		except socket.error, msg:
			raise InvalidServerResponse(msg)
		except httplib.BadStatusLine:
			raise InvalidServerResponse("Unrecognised status code returned from Logentries server.")

		try:
			data = json.loads( resp.read() )
		except AttributeError:
			data = simplejson.loads( resp.read() )

		http.close()

		if data[ 'response'] != constants.RESP_OK:
			return data, False

		return data, True

	def request( self, request ):
		return self._make_api_call( request )
