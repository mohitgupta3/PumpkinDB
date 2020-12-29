import Exceptions
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
