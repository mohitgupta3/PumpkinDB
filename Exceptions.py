''' Some exceptions we may face
'''
class DBNotFoundError(Exception):
    # This exception is raised when you try to open a database that has not been created yet
    pass

class DBExistsError(Exception):
    # This exception is raised when you try to create a database that already exists
    pass

class DecryptionFailedError(Exception):
    # This exception is raised when the module fails to decrypt a metadata file.
    # This generally happens when you manually manipulate the encrypted metadata
    # file or if you make changes to the encryption key
    pass

class GroupExistsError(Exception):
    # This exception is raised if you create a group that already exists
    pass

# Exceptions related to Groups
class TableNotFound(Exception):
    # This error is raised if you access a group that
    # does not exist
    pass

class InvalidFilterError(Exception):
    # This error is raised if you try to use
    # a filter that is not defined.
    pass

class InvalidRegExpError(Exception):
    # This error is raised if you pass
    # in an invaid re into the filters
    pass
