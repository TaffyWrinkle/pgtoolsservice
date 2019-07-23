# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import List, Mapping, Tuple
from abc import ABC, abstractmethod

class ServerConnection(ABC):
    """Abstract base class that outlines methods and properties that connections must implement"""

    ###################### PROPERTIES ##################################
    @property
    @abstractmethod
    def autocommit(self) -> bool:
        """Returns the current autocommit status for this connection"""
        pass

    @property
    @abstractmethod
    def host_name(self) -> str:
        """Returns the hostname for the current connection"""
        pass
    
    @property
    @abstractmethod
    def port_num(self) -> int:
        """Returns the port number used for the current connection"""
        pass
    
    @property
    @abstractmethod
    def user_name(self) -> str:
        """Returns the port number used for the current connection"""
        pass
        
    @property
    @abstractmethod
    def database_name(self) -> str:
        """Return the name of the current connection's database"""
        pass

    @property
    @abstractmethod
    def server_version(self) -> Tuple[int, int, int]:
        """Tuple that splits version string into sensible values"""
        pass

    @property
    def database_error(self):
        """ Returns the type of database error this connection throws"""
        pass

    @property
    @abstractmethod
    def transaction_in_error(self) -> bool:
        pass

    @property
    @abstractmethod
    def cancellation_query(self) -> str:
        pass
    
    ############################# METHODS ##################################
    @autocommit.setter
    @abstractmethod
    def autocommit(self, mode: bool):
        """
        Sets the connection's autocommit setting to the specified mode
        :param mode: True or False
        """
        pass
    
    @abstractmethod
    def execute_query(self, query: str, all=True):
        """
        Execute a simple query without arguments for the given connection
        :raises an error: if there was no result set when executing the query
        """
        pass

    @abstractmethod
    def execute_dict(self, query: str, params=None):
        """
        Executes a query and returns the results as an ordered list of dictionaries that map column
        name to value. Columns are returned, as well.
        :param conn: The connection to use to execute the query
        :param query: The text of the query to execute
        :param params: Optional parameters to inject into the query
        :return: A list of column objects and a list of rows, which are formatted as dicts.
        """
        pass
    
    @abstractmethod
    def list_databases(self):
        """
        List the databases accessible by the current connection.
        """
        pass
    
    @abstractmethod
    def get_database_owner(self):
        """
        List the owner(s) of the current database
        """
    pass
    
    @abstractmethod
    def close(self):
        """
        Closes this current connection.
        """
        pass