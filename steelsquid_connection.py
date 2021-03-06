#!/usr/bin/python -OO


'''
A simple module that i use to sen async command to and from client/server.
Override this class and use for client and server.
A request can be made from server to client or from client to server

The server (Using default host='localhost', port=22222):
aserver = SteelsquiConnectionClass(True)
aserver.start()

The client (Using default host='localhost', port=22222):
aclient = SteelsquiConnectionClass(False)
aclient.start()

The client will try to connect to the server every 1 second.

The server or the client can send a request:
But if the server and client sends a request at the sam etime a problem may occur, so for this use two connections.
aserver.send_request("thecommand", ["A", "test"])
or
aclient.send_request("thecommand", ["A", "test"])

Communication takes place in the following way (may also be the other way (client to server))
1. aserver.send_request("thecommand", ["A test para 1", "A test para 2"])
2. The function thecommand_request execute on the client with ["A test para 1", "A test para 2"] as paramters
   def thecommand_request(self, remote_address, parameters):
        return ["A answer 1", "A answer 2"]
3. The function thecommand_response execute on the server with ["A answer 1", "A answer 2"] as paramters
   def thecommand_response(self, remote_address, parameters):
        ...
3. If exception in thecommand_error will execute on the server with [error message] as paramters
   def thecommand_error(self, remote_address, parameters):
        ...

remote_address is the other sides address, example IP number

This is what is send on the socket when a client send a request to the server:

1. Server listen forconnections.
2. Client connect to server.
3. Both server and client is listening on there input stream.
4. Client send the request 'acommand' with the paramaters 'aparamater1' and 'aparamater2' on the output stream.
   request|acommand|aparamater1|aparamater2
5. The server reads the string and try to execute a function named acommand_request with two paramaters remote_address and ['aparamater1', 'aparamater2']
6. The function  acommand_request return ['answer1', 'answer2']
7. The server send the answer to the client
   response|acommand|answer1|answer2
8. The client read the answer and execute the method acommand_response with two paramaters remote_address and ['answer1', 'answer2']
9. If the execution on the server has error the response would have looked like this:
   error|acommand|error string
10. The client read the answer (error) and execute the method acommand_error with two paramaters remote_address and ['error string']


@organization: Steelsquid
@author: Andreas Nilsson
@contact: steelsquid@gmail.com
@license: GNU Lesser General Public License v2.1
@change: 2013-10-25 Created
'''

import subprocess
from subprocess import Popen, PIPE, STDOUT
import threading
import thread
import time
import steelsquid_utils


class SteelsquidConnection(object):
    '''
    The server
    '''

    #Execute the command on this objects as well
    external_objects=[]
    
    lock = threading.Lock()

    def __init__(self, is_server):
        '''
        Constructor.
        '''
        self.is_server = is_server


    def is_server(self):
        '''
        Is this a server
        '''
        return self.is_server


    def is_client(self):
        '''
        Is this a client
        '''
        return not self.is_server
        

    def on_setup_client(self):
        '''
        Override this to setup the client.
        Example setup socket
        Will loop until server is stopped.
        @return: Connection object (example socket)
        '''
        pass


    def on_setup_server(self):
        '''
        Override this to setup the server.
        Example setup the serversocket
        Will loop until server is stopped.
        @return: Listener object (example serversocket)
        '''
        pass


    def on_connect(self, connection_object):
        '''
        Override this to connect to a server.
        Example connect to a socket.
        Will loop until server is stopped.
        @param connection_object: The object from on_setup_client
        @return: connection_object (the connection_object object)
        '''
        time.sleep(1)
        return connection_object
        

    def on_listen(self, listener_object):
        '''
        Override this to start the server listen for connection functionality.
        Example listen for clients on a socket.
        Will loop until server is stopped.
        @param listener_object: The object from on_setup_server
        @return: connection_object (None = do nothing)
        '''
        time.sleep(1)
        return None


    def on_read(self, connection_object):
        '''
        Override this to listen for data.
        Example listen for requests on socket
        @param connection_object: Read from this client
        @return: (type, command, parameters) 
                 (type = request, response, error)
                 command = None (do nothing)
        '''
        return None, None, None


    def on_write(self, the_type, connection_object, command, parameters):
        '''
        Override this to send data to host.
        Example write request on socket
        @param the_type: "request", "response", "error"
        @param connection_object: Write to this client
        @param command: The command
        @param answer_list: parameters
        @return: True = Continue
                 False = Close connection
        '''
        return False


    def on_close_connection(self, connection_object, error_message):
        '''
        Override this to close the connection.
        Will also execute on connection lost or no connection
        @param server_object: The connection (Can be None)
        @param error_message: I a error (Can be None)
        '''
        steelsquid_utils.shout("Connection: Connection closed", debug=True)

    
    def on_close_listener(self, listener_object, error_message):
        '''
        Override this to close the listener.
        Will also execute on unable to listen
        @param listener_object: The listener (Can be None)
        @param error_message: I a error (Can be None)
        '''
        steelsquid_utils.shout("Connection: Listener closed", debug=True)


    def on_start(self):
        '''
        Override this to do things when the server/client starts
        '''
        pass


    def on_stop(self):
        '''
        Override this to do things when the server/client stops
        '''
        pass


    def on_get_remote_address(self, connection_object):
        '''
        Override this to do and return the adress of the remote address (IP)
        @param connection_object: The listener object to read adress from (Can be None)
        '''
        return None


    def start(self):
        '''
        Start server/client
        '''
        self.listen_thread = ListenThread(self)
        self.listen_thread.start()
        try:
            self.on_start()
        except:
            steelsquid_utils.shout()


    def stop(self):
        '''
        Stop server/client
        '''
        try:
            self.listen_thread.stop_thread()
        except:
            pass
        try:
            self.on_stop()
        except:
            steelsquid_utils.shout()
            
            
    def send_request(self, command, parameters, remote_address=None):
        '''
        Send request remote server or clients
        command = Command to send
        parameters = Paramater list to send
        remote_address = If this is a server with multipple clients, only send to thisclient address (IP)
                         None send to all clients
        '''
        count = 0
        for string in parameters:
            parameters[count] = steelsquid_utils.decode_string(str(string))
            count = count + 1
        if remote_address == None:
            for cli in self.listen_thread.clients:
                with self.lock:
                    self.on_write("request", cli, command, parameters)
        else:
            for cli in self.listen_thread.clients:
                this_remote_add = self.on_get_remote_address(cli)
                if this_remote_add==remote_address:
                    with self.lock:
                        self.on_write("request", cli, command, parameters)
           

    def execute(self, connection_object, command, parameters=None):
        '''
        Execute the command (method with same name as the command)
        Will raise a RuntimeError on error
        The parameters will be convertet to a list of strings before sent to command.
        String => [String]
        int => [String]
        bool => [True/False]
        @param connection_object: To read remote adress from (IP)
        @param command: Command to execute
        @param paramaters: Paramaters (list of bool, int, float, string or a single bool, int, float, string)
        @return: Answer list
        '''
        try:
            remote_add = self.on_get_remote_address(connection_object)
            if not parameters == None:
                if isinstance(parameters, (list)):
                    count = 0
                    for string in parameters:
                        parameters[count] = steelsquid_utils.decode_string(str(string))
                        count = count + 1
                else:
                    parameters = [steelsquid_utils.decode_string(str(parameters))]
            else:
                parameters = []

            the_answer = None
            is_found=False
            if hasattr(self, command):
                is_found=True
                fn = getattr(self, command)
                the_answer = fn(remote_add, parameters)
            else:
                for o in self.external_objects:
                    if hasattr(o, command):
                        is_found=True
                        fn = getattr(o, command)
                        the_answer = fn(remote_add, parameters)
            if not is_found:
                raise RuntimeError("Command "+command+" not found!")
            if the_answer != None:
                if isinstance(the_answer, (list)):
                    count = 0
                    for string in the_answer:
                        the_answer[count] = steelsquid_utils.encode_string(str(string))
                        count = count + 1
                    return the_answer
                else:
                    return [steelsquid_utils.encode_string(str(the_answer))]
        except RuntimeError, err:
            steelsquid_utils.shout()
            raise err
        except:
            steelsquid_utils.shout()
            import traceback                
            import sys
            exc_type, exc_value, exc_traceback = sys.exc_info()
            raise RuntimeError, (exc_value), exc_traceback

    def get_connection_objects(self):
        '''
        Get all connection objects in this client or server.
        On the client it will always be one (or 0 if no connection).
        But the server may have several.
        @return: List with all Connection objects (example socket)
        '''
        return self.listen_thread.clients


class ListenThread(threading.Thread):
    '''
    Thread that listens 
    '''

    __slots__ = ['running', 'server', 'listener', 'clients']

    def __init__(self, server):
        '''
        Constructor.
        '''
        self.running = True
        self.server = server
        self.clients = []
        threading.Thread.__init__(self)

    def run(self):
        '''
        Thread main method
        '''
        if self.server.is_server:
            while self.running:
                self.listener = None
                error = None
                try:
                    self.listener = self.server.on_setup_server()
                    while self.running:
                        client = self.server.on_listen(self.listener)
                        if client != None:
                            thread.start_new_thread(self.handle, (client,))
                except Exception, err:
                    error = str(err)
                    time.sleep(1)
                try:
                    self.server.on_close_listener(self.listener, error)
                except Exception, e:
                    pass
            for cli in self.clients:
                try:
                    self.server.on_close_connection(cli, None)
                except:
                    pass
        else:
            while self.running:
                try:
                    client = self.server.on_setup_client()
                    while self.running:
                        client = self.server.on_connect(client)
                        self.handle(client)
                except Exception, err:
                    error = str(err)
                    time.sleep(1)
                try:
                    self.server.on_close_connection(client, error)
                except Exception, e:
                    pass
            

    def handle(self, client):
        '''
        Handle a client.
        '''
        self.clients.append(client)
        execute = True
        error = None
        try:
            remote_add = self.server.on_get_remote_address(client)
            try:
                for o in self.server.external_objects:
                    if hasattr(o, "is_server"):
                        o.is_server=self.server.is_server
                    if hasattr(o, "on_connect"):
                        fn = getattr(o, "on_connect")
                        fn(remote_add)
            except:
                steelsquid_utils.shout()
            while execute:
                the_type, command, parameters = self.server.on_read(client)
                if not self.running:
                    execute = False
                if command != None:
                    if the_type == "request":
                        answer_list = None
                        try:
                            answer_list = self.server.execute(client, command+"_request", parameters)
                        except:
                            import traceback
                            import sys
                            exc_type, exc_var, exc_traceback = sys.exc_info()            
                            answer_list = [str(exc_var)]
                            del exc_traceback
                            with self.server.lock:
                                execute = self.server.on_write("error", client, command, answer_list)
                        else:
                            if answer_list != None:
                                with self.server.lock:
                                    execute = self.server.on_write("response", client, command, answer_list)
                    elif the_type == "response":
                        try:
                            self.server.execute(command+"_response", parameters)
                        except:
                            steelsquid_utils.shout()
                    elif the_type == "error":
                        try:
                            self.server.execute(client, command+"_error", parameters)
                        except:
                            steelsquid_utils.shout()
        except Exception, err:
            error = str(err)
        self.clients.remove(client)
        try:
            for o in self.server.external_objects:
                if hasattr(o, "on_disconnect"):
                    fn = getattr(o, "on_disconnect")
                    fn(error)
        except:
            steelsquid_utils.shout()
        try:
            self.server.on_close_connection(client, error)
        except Exception, e:
            pass
            

    def stop_thread(self):
        '''
        Stop this thread.
        '''
        self.running = False
            

