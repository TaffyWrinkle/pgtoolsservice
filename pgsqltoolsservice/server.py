# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Listen for JSON RPC inputs on stdin and dispatch them to the appropriate methods"""

from __future__ import print_function, unicode_literals
import json
import logging
import sys

import utils

from connection_service import ConnectionService
from contracts.capabilities_service import (
    CapabilitiesResult,
    CategoryValue,
    ConnectionProviderOptions,
    ConnectionOption,
    DMPServerCapabilities)
from contracts.initialization import (
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind)
from jsonrpc import JSONRPCResponseManager, dispatcher


class Server(object):
    """Class representing a server for JSON RPC requests"""

    def __init__(self, input_stream, output_stream):
        logging.debug('creating server object')
        self.connection_service = ConnectionService(self)
        self.is_shutdown = False
        self.should_exit = False
        self.threads = set()
        self.input_stream = input_stream
        self.output_stream = output_stream
        dispatcher['initialize'] = self.initialize

    def initialize(
            self,
            processId=None,
            rootPath=None,
            rootUri=None,
            initializationOptions=None,
            capabilities=None,
            trace=None):
        """Initialize the service"""
        logging.debug('initialize method')
        self.initialize_dispatcher()
        initialize_result = InitializeResult(ServerCapabilities(
            textDocumentSync=TextDocumentSyncKind.INCREMENTAL,
            definitionProvider=False,
            referencesProvider=False,
            documentFormattingProvider=False,
            documentRangeFormattingProvider=False,
            documentHighlightProvider=False,
            hoverProvider=False,
            completionProvider=None
        ))
        # Since jsonrpc expects a serializable object, convert it to a
        # dictionary
        return utils.object_to_dictionary(initialize_result)

    def initialize_dispatcher(self):
        """Initialize the JSON RPC dispatcher"""
        logging.debug('initialize_dispatcher method')
        dispatcher['connection/connect'] = self.connection_service.handle_connect_request
        dispatcher['connection/disconnect'] = self.connection_service.handle_disconnect_request
        dispatcher['shutdown'] = self.shutdown
        dispatcher['exit'] = self.exit
        dispatcher['echo'] = self.echo
        dispatcher['version'] = version
        dispatcher['capabilities/list'] = capabilities
        dispatcher['wait'] = self.wait

    def shutdown(self):
        """Shutdown the service"""
        logging.debug('shutdown method')
        self.is_shutdown = True

    def exit(self):
        """Exit the process"""
        logging.debug('exit method')
        self.should_exit = True

    def wait(self):
        """
        Wait for all threads to finish executing

        Used for manual testing of the server
        """
        for thread in self.threads:
            thread.join()

    def register_thread(self, thread):
        """Add a thread to the set of known threads for tracking"""
        self.threads.add(thread)

    def echo(self, arg):
        """Method used for manually testing the JSON RPC server"""
        self.output_stream.write(arg)

    def send_event(self, event_name, event_params):
        """Send a JSON RPC event with the given name and parameters"""
        output_string = '{"jsonrpc":"2.0","method":"%s","params":%s}' % (event_name, json.dumps(
            utils.object_to_dictionary(event_params)))
        self.handle_output(output_string)

    def handle_output(self, output_string):
        """Add the content-length header and output the given string"""
        newlines = '\n\n' if sys.platform == 'win32' else '\r\n\r\n'
        full_output = 'Content-Length: {}{}'.format(
            len(output_string), newlines) + output_string
        logging.debug('sending message: %s', full_output)
        self.output_stream.write(full_output)
        self.output_stream.flush()

    def read_headers(self):
        """Read the VSCode Language Server Protocol message headers"""
        headers = {}
        while True:
            line = self.input_stream.readline().strip()
            if line == '':
                return headers
            parts = line.split(': ')
            headers[parts[0]] = parts[1]

    def read_content(self, length):
        """Read the number of bytes of content specified"""
        return self.input_stream.read(length)

    def handle_input(self):
        """
        Loop to process input and dispatch the requests.

        Input is formatted according to the VSCode language server protocol at
        https://github.com/Microsoft/language-server-protocol/. For example
        a single request might look like the following (see more examples in README.md):

        'Content-Length: 57

        {"jsonrpc":"2.0","id":0,"method":"connection/disconnect"}'
        """
        while True:
            headers = self.read_headers()
            somestring = self.read_content(int(headers['Content-Length']))
            logging.debug('read string: %s', somestring)
            response = JSONRPCResponseManager.handle(somestring, dispatcher)
            if self.should_exit:
                sys.exit(0 if self.is_shutdown else 1)
            if response is None:
                continue
            self.handle_output(response.json)


def version():
    """Get the version of the tools service"""
    return "0"


def capabilities(hostName, hostVersion):
    """Get the server capabilities response"""
    server_capabilities = CapabilitiesResult(DMPServerCapabilities(
        protocolVersion='1.0',
        providerName='PGSQL',
        providerDisplayName='PostgreSQL',
        connectionProvider=ConnectionProviderOptions(options=[
            ConnectionOption(
                name='connectionString',
                displayName='Connection String',
                description='PostgreSQL-format connection string',
                valueType=ConnectionOption.VALUE_TYPE_STRING,
                isIdentity=True,
                isRequired=False,
                groupName='Source'
            ),
            ConnectionOption(
                name='server',
                displayName='Server Name',
                description='Name of the PostgreSQL instance',
                valueType=ConnectionOption.VALUE_TYPE_STRING,
                specialValueType=ConnectionOption.SPECIAL_VALUE_SERVER_NAME,
                isIdentity=True,
                isRequired=True,
                groupName='Source'
            ),
            ConnectionOption(
                name='database',
                displayName='Database Name',
                description='The name of the initial catalog or database in the data source',
                valueType=ConnectionOption.VALUE_TYPE_STRING,
                specialValueType=ConnectionOption.SPECIAL_VALUE_DATABASE_NAME,
                isIdentity=True,
                isRequired=False,
                groupName='Source'
            ),
            ConnectionOption(
                name='user',
                displayName='User Name',
                description='Indicates the user ID to be used when connecting to the data source',
                valueType=ConnectionOption.VALUE_TYPE_STRING,
                specialValueType=ConnectionOption.SPECIAL_VALUE_USER_NAME,
                isIdentity=True,
                isRequired=True,
                groupName='Security'
            ),
            ConnectionOption(
                name='password',
                displayName='Password',
                description='Indicates the password to be used when connecting to the data source',
                valueType=ConnectionOption.VALUE_TYPE_PASSWORD,
                specialValueType=ConnectionOption.SPECIAL_VALUE_PASSWORD_NAME,
                isIdentity=True,
                isRequired=True,
                groupName='Security'
            ),
            ConnectionOption(
                name='authenticationType',
                displayName='Authentication Type',
                description='Specifies the method of authenticating with SQL Server',
                valueType=ConnectionOption.VALUE_TYPE_CATEGORY,
                specialValueType=ConnectionOption.SPECIAL_VALUE_AUTH_TYPE,
                isIdentity=True,
                isRequired=True,
                groupName='Security',
                categoryValues=[
                    CategoryValue('SQL Login', 'SqlLogin')
                ]
            )
        ])
    ))
    # Since jsonrpc expects a serializable object, convert it to a dictionary
    return utils.object_to_dictionary(server_capabilities)


if __name__ == '__main__':
    logging.basicConfig(filename='server.log', level=logging.DEBUG)
    logging.debug('initializing server')
    SERVER = Server(sys.stdin, sys.stdout)
    SERVER.handle_input()