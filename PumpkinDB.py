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
