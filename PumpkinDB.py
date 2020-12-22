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
