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
