import os  # os module is required to manipulate directories and files
import json  # JSON module helps to manipulate json data
import platform # Platform information
import re  # RegExp support for our app
import shutil  # This module helps to delete databases

banner = """\n\n  \
██████╗  ██╗   ██╗ ███╗   ███╗ ██████╗  ██╗  ██╗ ██╗ ███╗   ██╗ \n  \
██╔══██╗ ██║   ██║ ████╗ ████║ ██╔══██╗ ██║ ██╔╝ ██║ ████╗  ██║ \n  \
██████╔╝ ██║   ██║ ██╔████╔██║ ██████╔╝ █████╔╝  ██║ ██╔██╗ ██║ \n  \
██╔═══╝  ██║   ██║ ██║╚██╔╝██║ ██╔═══╝  ██╔═██╗  ██║ ██║╚██╗██║ \n  \
██║      ╚██████╔╝ ██║ ╚═╝ ██║ ██║      ██║  ██╗ ██║ ██║ ╚████║ \n  \
╚═╝       ╚═════╝  ╚═╝     ╚═╝ ╚═╝      ╚═╝  ╚═╝ ╚═╝ ╚═╝  ╚═══╝ \n  \
                                                                \n  \
         ██████╗  ██████╗                                       \n  \
    ██╗  ██╔══██╗ ██╔══██╗        ██╗                           \n  \
    ╚═╝  ██║  ██║ ██████╔╝     ██╗╚═╝████████████╗  ██╗         \n  \
    ██╗  ██║  ██║ ██╔══██╗     ╚═╝██╗╚═══════════╝  ╚═╝         \n  \
    ╚═╝  ██████╔╝ ██████╔╝        ╚═╝                           \n  \
         ╚═════╝  ╚═════╝                                       \n\n\
"""

print(banner)

mydb = ""

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

''' Module group for PumpkinDB.
    Use it to access data tables in your database.
    This module is supposed to be a child of the
    utils.database.db module. Not to be used as a
    standalone module.
    This modules defines:
        1. TableNotFound
        2. GroupExistsError
        3. group
'''
# Function for recursively sorting array
def merge(left, right, param):

    # If the first array is empty, then nothing needs
    # to be merged, and you can return the second array as the result
    if len(left) == 0:
        return right

    # If the second array is empty, then nothing needs
    # to be merged, and you can return the first array as the result
    if len(right) == 0:
        return left

    result = []
    index_left = index_right = 0

    try:
        # Now go through both arrays until all the elements make it into the resultant array
        while len(result) < len(left) + len(right):

            # The elements need to be sorted to add them to the
            # resultant array, so you need to decide whether to get the next element from the first or the second array
            if left[index_left][param] <= right[index_right][param]:
                result.append(left[index_left])
                index_left += 1
            else:
                result.append(right[index_right])
                index_right += 1

            # If you reach the end of either array, then you can add the remaining elements from the other array to the result and break the loop
            if index_right == len(right):
                result += left[index_left:]
                break

            if index_left == len(left):
                result += right[index_right:]
                break

    # Probably sort parameter is not there in some docs So, raise an error in such cases
    except KeyError:
        raise ValueError(
            f"The sort parameter `{param}` is not present in all documents. \
            Please make sure that you use a correct sort parameter."
        )
    return result

  # This function implements a merge sort
def merge_sort(array, param):
    # If the input array contains fewer than two elements, then return it as the result of the function
    if len(array) < 2:
        return array

    midpoint = len(array) // 2

    # Sort the array by recursively splitting the input
    # into two equal halves, sorting each half and merging them together into the final result
    return merge(
        param=param,
        left=merge_sort(array[:midpoint], param),
        right=merge_sort(array[midpoint:], param),
    )

  # This function implements binary search on an array of docs, finding the
# one that matches the filters
def binary_search(arr, key, value):
    l = 0
    u = len(arr) - 1

    while l < u:
        mid = (l + u) // 2
        if arr[mid][key] == value:
            return arr[mid]
        else:
            if arr[mid][key] < value:
                l = mid + 1
            else:
                u = mid
    return False

# This function matches the documents according to the criteria defined in the filters
# Not only '== matching' but different kinds like !=, >, <, <=, >=
def matchDocs(doc, filters):
    # We should apply special match only if
    # the filter is a dictionary
    if "dict" in str(type(filters)):

        # Loop through all the defined filters
        for i in filters.keys():
            # Check each filter one by one
            # The not equals filter
            if i == "__ne":
                if doc == filters[i]:
                    return False
            # The greater than filter
            elif i == "__gt":
                if doc <= filters[i]:
                    return False
            # The less than filter
            elif i == "__lt":
                if doc >= filters[i]:
                    return False
            # The less than or equals filter
            elif i == "__lte":
                if doc > filters[i]:
                    return False
            # The greater than or equals filter
            elif i == "__gte":
                if doc < filters[i]:
                    return False
            # The Regular Expression filter
            elif i == "__re":
                try:
                    if re.match(filters[i], str(doc)) == None:
                        return False
                except:
                    raise InvalidRegExpError(
                        f"The given RegExp `{filters[i]}` is not valid. \
                        Please refer to docs of the `re` module to see\
                        what a valid Regular Expression is."
                    )
            # Custom function filter
            elif i == "__cf":
                try:
                    if not filters[i](doc):
                        return False
                except Exception as e:
                    raise InvalidFilterError(
                        f"The provided custom filter `{str(filters[i])}`\
                        raised an unhandled exception: {str(e)}`"
                    )

            # Filter does not match any provided filters. Raise Excepion
            else:
                raise InvalidFilterError(
                    f"The provided filter `{i}` is not valid.\
                     Must be one of __ne, __lt, __gt, __lte, \
                    __gte, __re, __cf"
                )

        # The doc passed all the specified filters
        # It passed the test!
        return True

    # No custom filter specified, return simple equality check
    else:
        return filters == doc

class table:
    def __init__(self, name, parent, safeMode: bool = True, preLoad: bool = False):
        """
            The class represents a single data table of the name 'name'.
            @param name <str>: Name of the current table
            @param parent <utis.database.db.db>: Instance of the parent database.
            @param safeMode <bool> [Optional]: Whether to use safeMode or not. Default: True.
            @param preLoad <bool>. [Optional]: Whether to preLoad table data or not.
                                                This speeds up query speeds by loading data into
                                                memory. Default: False.
            WARNING: Using preLoad setting loads data into memory, so if your table is big, then it
            is recommended NOT to use this option. Don't use this also if you are low on memory.
        """

        # Save the data
        self.name = name
        self.safeMode = safeMode
        self.preLoad = preLoad

        # Inherit some things from the parent databse
        self.parent = parent
        self.path = f"{parent.dbPath}/db/{self.parent.name}/{self.name}.tables"
        self.key = parent.key

        # If the preLoad method is enabled
        if preLoad:
            self.fetch_data()

    # Method used to load/refresh data into memory if preload is enabled
    def fetch_data(self):
        # open the table
        with open(self.path, "rb") as f:
            # Read, Decrypt and save the data
            self.data = json.loads(Fernet(self.key.encode()).decrypt(f.read()))

    # Method to insert data into the current table
    def insert(self, data: dict = {}, **moreData):
        """
            This method inserts the given data into the current table.
            This can be done in two ways:
                1. table.insert({'key1': 'value1', 'key2': 'value2'})
                2. table.insert(key1 = value1, key2 = value2)
            @param data: The data to be inserted into the table
            @returns <bool>: True if insertion was succesfull, False otherwise
        """
        # Make sure the data is correct
        data = dict(data)
        # Merge the two types of data provided
        data.update(moreData)
        # If preLoad is enabled
        if self.preLoad:
            # Change data inplace if preLoad is enabled
            self.data.append(data)

        # Save the data in file
        with open(self.path, "rb+") as grp:
            # load the older data
            d = json.loads(Fernet(self.key).decrypt(grp.read()).decode("utf-8"))
            # Insert this data
            d.append(data)
            # Empty the file now
            grp.truncate(0)
            # Get the cursor at zero position
            grp.seek(0)
            # Write the new data
            grp.write(Fernet(self.key.encode()).encrypt(json.dumps(d).encode()))

        # Success!
        return True
    # Multiple data node insertion.
    def insert_many(self, *data):
        """
            This method inserts the given data dictionaries into the current table.
            This can be done in this way:
                table.insert_many(dict1, dict2, dict3, ...)
            @param data: The data dictionaries to be inserted into the table
            @returns <bool>: True if insertion was succesfull, False otherwise
        """
        # Make sure the data is correct
        data = [dict(d) for d in data]

        # If preLoad is enabled
        if self.preLoad:
            # Change data inplace if preLoad is enabled
            self.data.extend(data)

        # Save the data in file
        with open(self.path, "rb+") as grp:
            # load the older data
            d = json.loads(Fernet(self.key).decrypt(grp.read()).decode("utf-8"))
            # Insert this data
            d.extend(data)
            # Empty the file now
            grp.truncate(0)
            # Get the cursor at zero position
            grp.seek(0)
            # Write the new data
            grp.write(Fernet(self.key.encode()).encrypt(json.dumps(d).encode()))

        return True

    # Function to get back prevously saved data
    def get_one(self, filters: dict, sortby: str = None):
        """
            This functions returns the first document that match the filters
            defined by the 'filters' dict.
            @param filters <dict>: This dictionary defines all the filters. All the documents in the
            table that match these filters are returned.
            @param sortby <str> [Optional]: The parameter to sort the documents
            with, before matching.
            @returns <dict>: The document that matched the given filters
        """

        # Make sure that filters are correct
        filters = dict(filters)

        # load data from memory if preLoad is enabled
        if self.preLoad:
            docs = self.data

        # Get them from the drive otherwise
        else:
            with open(self.path, "rb") as d:
                docs = json.loads(Fernet(self.key.encode()).decrypt(d.read()))

        # If there is just one filter and it
        # does not require a special search
        if (
            len(filters) == 1
            and not sortby
            and "dict" not in str(type(filters[list(filters.keys())[0]]))
        ):

            # We have an advantage here, we can sort the documents accroding to the only filter
            # and then implement a Binary search algorithm for faster response

            # This shortens our filters dict into one single variabe rather than a dictionary
            key = list(filters.keys())[0]
            value = filters[key]

            # Sort the docs accroding to the filter
            docs = merge_sort(docs, key)

            # Implement a binary search algorithm on the sorted docs
            return binary_search(docs, key, value)

        else:
            # Implement a sort if the user wants it
            docs = merge_sort(docs, sortby) if sortby else docs

            # Implement a linear search algorithm because we can't sort the list according to all the filter parameters at once
            for i in docs:

                # Let us assume it matches
                matches = True

                # Loop through all the filters
                for j in filters:

                    try:
                        # If one of the filters does not match the doc's value
                        if not matchDocs(i[j], filters[j]):

                            # Mark it unmatched
                            matches = False

                            # And break from the loop
                            break

                    # Its posiible that all documents don't have the keys given
                    # in filter, in which case we'll have a KeyError
                    except KeyError:
                        matches = False
                        break

                # If the match is found then return this doc to the user
                if matches:
                    return i

    # Function to get back prevously saved data
    # Same as previous but it returns all occurences of the documents instead of the first one
    def get(self, filters: dict, sortby: str = None):
        """
            This functions returns a list of all documents that match the filters
            defined by the 'filters' dict.
            @param filters <dict>: This dictionary defines all the filters. All the documents in the
            table that match these filters are returned
            @param sortby <str>[Optional]: The parameter, whose value should be used to sort the result.
            @returns <List>: Of all the documents that match the given filters
        """

        # Make sure that filters are correct
        filters = dict(filters)

        # load data from memory if preLoad is enabled
        if self.preLoad:
            docs = self.data

        # Get them from the drive otherwise
        else:
            with open(self.path, "rb") as d:
                docs = json.loads(Fernet(self.key.encode()).decrypt(d.read()))

        # Implement a linear search algorithm because we can't sort the list according to all the filter parameters at once
        output = []
        for i in docs:
            # Let us assme it matches
            matches = True

            # Loop through all the filters
            for j in filters:
                try:
                    # If one of the filters does not match the doc's value
                    if not matchDocs(i[j], filters[j]):
                        # Mark it unmatched
                        matches = False
                        # And break from the loop
                        break

                # Its posiible that all documents don't have the keys given in filter, in which case we'll have a KeyError
                except KeyError:
                    matches = False
                    break

            # If the match is found then return this doc to the user
            if matches:
                output.append(i)

        if sortby:
            # If there's a need to sort the result then do it
            return merge_sort(output, sortby)
        else:
            return output
    
    # Function to update the values
    def update_one(self, filters: dict, nValues: dict):
        """
            This function is used to update the values in the data table.
            It updates the first occurence of the document found to be matching
            the filters.
            @param filters <dict> : The dictionary of filters.
            @param nValues <dict>: The dictionary to get the new values from.
            @returns None.
        """

        # First up get the data document
        doc = self.get_one(filters)
        # Create a copy of the document
        nDoc = doc.copy()
        # Update the new document
        nDoc.update(nValues)

        # Then delete this document and add the new one

        # First from the in-mem cache
        if self.preLoad:
            self.data.remove(doc)
            self.data.append(nDoc)

        # Then form the data files
        with open(self.path, "rb+") as f:
            docs = json.loads(
                Fernet(self.key.encode()).decrypt(f.read()).decode("utf-8")
            )
            # Remove the current document and add the new one
            docs.remove(doc)
            docs.append(nDoc)
            # Empty the file now
            f.truncate(0)
            # Get the cursor at zero position
            f.seek(0)
            # Write the new data
            f.write(Fernet(self.key.encode()).encrypt(json.dumps(docs).encode()))

        # Done!

    # Function to update many documents in the table
    def update(self, filters: dict, nValues: dict):
        """
            This function is used to update the values in the data table.
            It updates all occurences of the document found to be matching
            the filters.
            @param filters <dict> : The dictionary of filters.
            @param nValues <dict>: The dictionary to get the new values from.
            @returns <int>: The number of documents updated.
        """

        # First up get the data documents
        doc = self.get(filters)
        # Create copies of the documents
        nDoc = [i.copy() for i in doc]
        # Update the new documents
        [i.update(nValues) for i in nDoc]
        # Then delete this document and add the new one
        # First from the in-mem cache
        if self.preLoad:
            [self.data.remove(i) for i in doc]
            self.data.extend(nDoc)

        # Then form the data files
        with open(self.path, "rb+") as f:
            docs = json.loads(
                Fernet(self.key.encode()).decrypt(f.read()).decode("utf-8")
            )
            # Remove the current document and add the new one
            [docs.remove(j) for j in doc]
            docs.extend(nDoc)
            # Empty the file now
            f.truncate(0)
            # Get the cursor at zero position
            f.seek(0)
            # Write the new data
            f.write(Fernet(self.key.encode()).encrypt(json.dumps(docs).encode()))

        # Done!

        return len(nDoc)

    # Function to delete a single data document
    def remove_one(self, filters: dict):
        """
            This function deletes the first occurence of the document tha matches
            the filters.
            WARNING: This task is irreversible
            @param filters <dict>: The filters, using which the document to be deleted is decided.
            @returns None
        """

        # First up get the data document
        doc = self.get_one(filters)
        # Then delete this document
        # First from the in-mem cache
        if self.preLoad:
            self.data.remove(doc)

        # Then form the data files
        with open(self.path, "rb+") as f:
            docs = json.loads(
                Fernet(self.key.encode()).decrypt(f.read()).decode("utf-8")
            )
            # Remove the current document
            docs.remove(doc)
            # Empty the file now
            f.truncate(0)
            # Get the cursor at zero position
            f.seek(0)
            # Write the new data
            f.write(Fernet(self.key.encode()).encrypt(json.dumps(docs).encode()))

    # Function to delete all documents that match a criteria
    def remove(self, filters: dict):
        """
            This function deletes all the occurences of the documents that match
            the filters.
            WARNING: This task is irreversible
            @param filters <dict>: The filters, using which the documents to be deleted are decided.
            @returns <int>: The number of documents deleted
        """

        # First up get the data documents
        doc = self.get(filters)
        # Then delete these documents
        # First from the in-mem cache
        if self.preLoad:
            [self.data.remove(i) for i in doc]

        # Then form the data files
        with open(self.path, "rb+") as f:
            docs = json.loads(
                Fernet(self.key.encode()).decrypt(f.read()).decode("utf-8")
            )

            # Remove these documents
            [docs.remove(j) for j in doc]

            # Empty the file now
            f.truncate(0)

            # Get the cursor at zero position
            f.seek(0)

            # Write the new data
            f.write(Fernet(self.key.encode()).encrypt(json.dumps(docs).encode()))

        # Done!

        return len(doc)

    # Function to delete this whole table
    def drop(self):
        """
            Delete this whole data table.
            WARNING: This task is irreversible.
        """
        # Delete the table file
        os.remove(self.path)

        # Update the parent database
        self.parent.tables.remove(self.name)

        # Update the metadata file
        with open(
            f"{self.parent.dbPath}/db/{self.parent.name}/metadata.json", "r+"
        ) as f:
            # Load the file
            d = json.loads(f.read())
            # Remove the current table
            d["tables"].remove(self.name)
            # Empty the file now
            f.truncate(0)
            # Get the cursor at zero position
            f.seek(0)
            # Write the new data
            f.write(json.dumps(d))

def create(name: str, dbPath: str = ".", safeMode: bool = True):
    """
        This method creates a database by the name of 'name'.
        If safeMode is not set to True, it raises DBExistsError
        if the requested database already exists.
        @param name <str> [Required]: Name of the db.
        @param safeMode <bool> [Optional]: Whether to use safeMode.
                                        Enabled by default
        @param dbPath <str> [Optional]: The relative path the directory
                                        where the 'db' directory is located.
                                        Default: Current directory.
        @returns: utils.database.db.db instance of the newly created
                database
    """

    # Be sure of the data types of the params
    name, safeMode, dbPath = str(name), bool(safeMode), str(dbPath)

    # Check if the given path is correct
    if "db" not in os.listdir(dbPath):
        raise ValueError(
            f"The given path {dbPath}, is not a\
             valid database directory.\n(Could \
            not find `db` subdirectory in `{dbPath}`)"
        )

    # Check if the name is correct
    if re.match(r".*[+/\\,.^%!@#$&*(){}\[\]'\"<>\?\|= ].*", name):
        raise ValueError(
            f"The name `{name}` is not a vaid name\
             for a database.\nA valid name is one \
            with just alphanumeric characters(0-9, \
            a-z, A-Z), hyphens(-) and underscores(_)"
        )

    if name in os.listdir(f"{dbPath}/db"):  # If the database already exists

        if not safeMode:  # And safe mode is disabled

            # Raise an error
            raise DBExistsError(f"The requested database '{name}' already exists.")
        else:

            # Or if safeMode is enabled give them the database
            return db(name, dbPath=dbPath, safeMode=safeMode)

    # Otherwise create the database
    else:

        # Create a directory for our new db
        os.mkdir(f"{dbPath}/db/{name}")

        # Add some metadata to it for faster table-access
        with open(f"{dbPath}/db/{name}/metadata.json", "x") as mdata:
            key = Fernet.generate_key().decode("utf-8")
            mdata.write(
                json.dumps(
                    {
                        "name": name,  # Name of the db
                        "tables": [],  # New databases are empty
                        "key": key,  # The encryption key for this db
                    }
                )
            )

        # Return the newly created database
        return db(name, dbPath=dbPath, safeMode=safeMode)


# Function to get all the databases
def getAllDbs(dbPath="."):
    """
        This function returns a list containing the names of all the databases in
        the /db subdirectory of the directory 'dbPath'
    """

    # Check if the given path is correct
    if "db" not in os.listdir(dbPath):
        raise ValueError(
            f"The given path {dbPath}, is not a valid \
            database directory.\n(Could not find `db` \
            subdirectory in `{dbPath}`)"
        )

    return os.listdir(dbPath + "/db")

# The main thing comes here, the db class
class db:
    """
        Get a database instance.
        @param name <str>: Name of the database.\n
        @param safeMode <bool> [Opional]: Whether to get tables in safeMode or not. Defaults to True.\n
        @param preLoad <bool>  [Optional]: Whether to preload table names for faster table access. Defaults to True.\n
        @param dbPath <str> [Optional]: The path to the directory where the 'db' directory is located.
                                        Default: Current directory
    """

    # Initiation of our database
    def __init__(
        self, name: str, dbPath: str = ".", safeMode: bool = True, preLoad: bool = True
    ):

        # Store the dbPath
        self.dbPath = str(dbPath)

        # Check if the given path is correct
        if "db" not in os.listdir(self.dbPath):
            raise ValueError(
                f"The given path {self.dbPath}, is not a valid database directory. \
                \n(Could not find `db` subdirectory in `{self.dbPath}`"
            )

        # Check if the name is correct
        if re.match(r".*[+/\\\\,.^%!@#$&*(){}\[\]'\"<>\?\|= ].*", name):
            raise ValueError(
                f"The name `{name}` is not a vaid name for\
                 a database.\nA valid name is one with just\
                 alphanumeric characters(0-9, a-z, A-Z), \
                hyphens(-) and underscores(_)"
            )

        # Check if the asked database is availabe:
        if name not in os.listdir(f"{self.dbPath}/db/"):

            # Create the db if safeMode is enabled
            if safeMode:
                create(name, dbPath=dbPath)

            # Otherwise display an error
            else:
                raise DBNotFoundError(
                    f"The requested db {name} has not been\
                    created yet. Either create it using create\
                    method or enable safeMode."
                )

        # Save the data otherwise
        self.name = name
        self.safeMode = safeMode
        self.key = None  # These are just there till we
        self.tables = []  # load the metadata.

        # Get the preload data if it is enabled
        if preLoad:
            self.get_meta()

    def __getitem__(self, name):
        return self.loadTable(name)

    # This function loads the metadata about the database. For internal
    # use only. Not to be used by users.
    def get_meta(self):
        # Open the metadata file
        with open(f"{self.dbPath}/db/{self.name}/metadata.json", "r") as mdata:
            # Load the data
            d = json.loads(mdata.read())

            # Save the data
            self.key = d["key"]
            self.tables = d["tables"]

    # Function to drop this database
    def drop(self):
        """
            Delete this database.
            Warning: This method deletes ALL the data stored inside it and it is NOT reversible.
        """

        # Delete the database folder
        shutil.rmtree(f"{self.dbPath}/db/{self.name}")
        # And we're done!

    # Function to create a new table
    def createTable(self, name: str, safeMode: bool = True, preLoad: bool = False):
        """
            Create a new data table in the current database.
            Raises GroupExistsError if table already exists and database is not in safe mode.
            @param name <str>: Name of the new table.
            @param safeMode <bool> [Optional]: Whether to use safeMode or not
            @param preLoad <bool> [Optional]: Whether to preLoad data or not
            @returns utils.database.tables.tables instance of the new table.
        """

        # Check if the name is correct
        if re.match(r".*[+/\\\\,.^%!@#$&*(){}\[\]'\"<>\?\|= ].*", name):
            raise ValueError(
                f"The name `{name}` is not a vaid name\
                for a database.\nA valid name is one wi\
                th just alphanumeric characters(0-9, a-z\
                , A-Z), hyphens(-) and underscores(_)"
            )

        # If the table already exists
        if name + ".tables" in os.listdir(f"{self.dbPath}/db/{self.name}"):

            # If the safeMode is enabled
            if safeMode:

                # Return the normal instance
                return self.loadTable(name, preLoad=preLoad)

            # Otherwise raise an error
            else:
                raise table.GroupExistsError(f"The table {name} already exists.")

        # Create it if its not there
        else:
            # If key is not there then get it
            if self.key is None:
                self.get_meta()

            # Create our file
            with open(f"{self.dbPath}/db/{self.name}/{name}.tables", "x") as grp:
                # Write an empty list into it for now
                grp.write(Fernet(self.key).encrypt(b"[]").decode("utf-8"))

            # Add the table to our in-memory list of tables
            self.tables.append(name)

            # Now update our metadata file
            f = open(f"{self.dbPath}/db/{self.name}/metadata.json", "w")
            f.write(
                json.dumps({"name": self.name, "key": self.key, "tables": self.tables})
            )

            return self.loadTable(name, safeMode=safeMode, preLoad=preLoad)

    # This function is used to access a table
    def loadTable(self, name: str, safeMode: bool = True, preLoad: bool = False):
        """
            Access a data table in the database.
            Raises GroupNotFoundError if the table is not found and safeMode is disabled. If safeMode is enabled, it creates the table.
            @param name <str>: Name of the table you want to access.
            @param safeMode <bool> [Optional]: Whether to open the table in safeMode or not. Default: True.
            @param preLoad <bool> [Optional]: Whether to pre-load the table for faster data access.
            WARNING: Setting pre-load to True makes a copy of the data in the memory (RAM) of the machine. So, using this setting is not recommended for large tables or if you are low on memory.
            @returns utils.database.tables.tables instance of the table.
        """

        # If the table does not exist
        if name not in self.tables:
            # If safe mode is enabled
            if safeMode:
                # Create the requested table
                return self.createTable(name, preLoad=preLoad)
            # Otherwise
            else:
                # Throw an error that it does not exist
                raise table.TableNotFoundError(
                    f"The requested table {name} has no been created."
                )

        # The table exists
        else:
            # Get the user the requested table
            return table(name, preLoad=preLoad, parent=self)

    # Function to export our database for sharing
    def export(self, path):
        """
            This function packages the current database into a single file and saves the
            file in the path provided as the param. This function can be used to create
            encrypted backups for the database.
            @param path <path>: This should be a relative or absolute path to the directory
            where the output package should be saved.
            @returns key: The output file is encrypted. To use it again you should provide
            the key returned by this function
        """

        # Get the absolute path of the required directory
        path = os.path.abspath(path)

        # If the given path is not a valid path
        if not os.path.isdir(path):

            # Raise a value error
            raise ValueError("The provided path %s is invalid" % path)

        # If the given path is not writable
        if not os.access(path, os.W_OK):
            # Raise a value error
            raise ValueError("The provided path %s is not writable" % path)

        # A skeleton json for the export package
        d = {
            "name": self.name,  # Name
            "key": self.key,  # Encryption key of the tables
            "tables": [],  # The tables
        }

        # Loop through all the tables
        for i in self.tables:
            # Open the table
            with open(f"{self.dbPath}/db/{self.name}/{i}.tables", "r") as f:
                # Add the table data to our export package
                d["tables"].append({"name": i, "data": f.read().encode()})

        # Generate a key for export package
        out_key = Fernet.generate_key()

        # Generate and then write to the output file
        with open(f"{path}/{self.name}.amazedb", "x") as out:
            # Encrypt the data before writing
            out.write(Fernet(out_key).encrypt(json.dumps(d).encode()).decode("utf-8"))

        # Return the encryption key
        return out_key

    # Function to import data from a package
    def import_data(self, path, key):
        """
            Function to import data to this database from an export package generated
            by the util.database.db.db.export metod.
            WARNING: This function will delete all the tables (and thus data) in the database.
            @param path <path>: This should be a valid path to the file which needs to be imported.
            @param key <bytes>: This should be a vaid encryption/decryption key of the file
        """

        # Handle some exceptions:
        try:

            # Open the file
            with open(path, "r") as f:

                # Try to read the file
                d = f.read().encode("utf-8")

                # Decrypt the file
                d = Fernet(key).decrypt(d)

                # Load the data
                d = json.loads(d)

                # Delete all existing tables
                [table.tables(self, i).drop() for i in self.tables]
                self.tables = []

                # Create new tables
                for i in d["tables"]:

                    # Create a new file
                    gr = open(f'{self.dbPath}/db/{self.name}/{i["name"]}.tables', "x")
                    # Save the data
                    gr.write(i["data"])
                    # close
                    gr.close()
                    # Update the self.tables list
                    self.tables.append(i["name"])

                # Edit the current encryption key
                self.key = d["key"]
                # Update our metadata
                md = open(f"{self.dbPath}/db/{self.name}/metadata.json", "w")
                md.write(json.dumps({"name": self.name, "tables": self.tables}))
                md.close()

        # The provided file was not found
        except FileNotFoundError:
            raise FileNotFoundError("The provided file %s was not found" % path)

        # The provided key is not the correct key
        except InvalidToken:
            raise ValueError("The provided key %s is not a vaild key" % key)

        # Some other exception
        except Exception as exc:
            raise Exception(
                "Encountered a problem while importing {}: \n\t\t{}".format(path, exc)
            )

def sysInfo():
    sysinfo = PrettyTable(field_names=["KEY", "VALUE"])
    sysinfo.add_row(["Operating system", platform.platform()])
    sysinfo.add_row(["Machine type", platform.machine()])
    sysinfo.add_row(["Machine architecture", platform.architecture()[1]+", "+platform.architecture()[0]])
    sysinfo.add_row(["Platform processor", platform.platform()])
    sysinfo.add_row(["Systems network name", platform.node()])
    sysinfo.add_row(["Python build no.", platform.python_build()[0]])
    sysinfo.add_row(["Python build date", platform.python_build()[1]])
    sysinfo.add_row(["Python compiler", platform.python_compiler()])
    sysinfo.add_row(["Python implementation", platform.python_implementation()])
    sysinfo.add_row(["Python version", platform.python_version()])
    sysinfo.align["KEY"] = "l"
    sysinfo.align["VALUE"] = "l"
    print(sysinfo.get_string(title="-:SYSTEM INFO:-"))

def queryProcessor(QUERY : str):
    global mydb

    query_tokens = QUERY.split()
    # Get the primary operation...
    operationPrimary = query_tokens[0].upper()

    # Create or Use a database
    if operationPrimary == "USE":
        if query_tokens[1].upper() == "DATABASE":
            try:
                mydb = db(query_tokens[2])
                print("\t[INFO] Connected to",  query_tokens[2])
            except: print("\t[EXCEPTION] Failed to create/connect to", query_tokens[2])
        else: print("\t[EXCEPTION] Malformed query!")
    
    # Create a table
    elif operationPrimary == "CREATE":
        if mydb != "":    
            if query_tokens[1].upper() == "TABLE":
                table_name = query_tokens[2]
                table = mydb.createTable(table_name)
                table = mydb.loadTable(table_name)
                if len(query_tokens) <= 5: print("\t[EXCEPTION] Empty query data!")
                
                if len(query_tokens) > 5 and query_tokens[3] == "(" and query_tokens[-1] == ")":
                    table_headers = [qt.upper() for qt in query_tokens[4:-2]]
                    table_meta = [tuple(table_headers[x:x+2]) for x in range(0, len(table_headers), 2)]
                    
                    # Get header names
                    header_dict = {}
                    for tm in table_meta:
                        header_dict.update({tm[0] : tm[1]})
                    table.insert(header_dict)
                    return True
                else: print("\t[EXCEPTION] Malformed query!")
            else: print("\t[EXCEPTION] Invalid option! \n\t(only thing we create is table.)")
        else: print("\t[EXCEPTION] No database defined! \n\t(you can't live in a house which doesn't exist)")

    elif operationPrimary == "INSERT":
        if query_tokens[1].upper() == "INTO" and len(query_tokens) > 5:
            table_name = query_tokens[2]
            table = mydb.loadTable(table_name)
            table.insert({})
        result = None
        return result
    
    elif operationPrimary == "SELECT":
        result = None
        return result
    
    elif operationPrimary == "UPDATE":
        result = None
        return result
    
    elif operationPrimary == "DELETE":
        result = None
        return result
    
    elif operationPrimary == "DROP":
        result = None
        return result
    
    # return result

def CLI():
    QUERY = "None"
    print(banner)
    sysInfo()
    while(QUERY.upper() != "EXIT"):
        try:
            QUERY = input("\n [QUERY]>> ")
            if QUERY.strip() != "":
                queryProcessor(QUERY)
            else: pass
        except(KeyboardInterrupt):
            print('\n\n[WARNING] Force close attempt!')
            exit()

if __name__ == "__main__":
    CLI()
