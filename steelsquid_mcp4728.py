#!/usr/bin/python -OO


'''
Write analog out from MCP4728 (0 to 5v)

@organization: Steelsquid
@author: Andreas Nilsson
@contact: steelsquid@gmail.com
@license: GNU Lesser General Public License v2.1
@change: 2013-10-25 Created
'''


import sys
import steelsquid_pi

if len(sys.argv)==1:
    from steelsquid_utils import printb
    print("")
    printb("mcp4728 <address> <value>")
    print("Write analog out from MCP4728 (0 to 5v)")
    print("address= 62")
    print("pin = 1 to 4")
    print("value = 0 and 4095")
    print("")
else:
    try:
        steelsquid_pi.mcp4728(sys.argv[1], sys.argv[2], sys.argv[3])
    except KeyboardInterrupt:
        pass
