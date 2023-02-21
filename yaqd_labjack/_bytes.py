"""
Helpful functions for converting register data to numbers and vice versa.

"""

import struct


def float2int(num):
    return struct.unpack("=i", struct.pack("=f", num))[0]


def concatData(data):
    tVal = 0
    upper = True
    for reg in data:
        if upper:
            tVal = (reg & 0xFFFF) << 16
            upper = False
        else:
            tVal = tVal | (reg & 0xFFFF)
            upper = True
    return tVal


"""
Converting numbers to 16-bit data arrays
"""


def uint16_to_data(num):
    return struct.unpack("=H", struct.pack("=H", num & 0xFFFF))[0]


def uint32_to_data(num):
    data = [0, 0]
    data[0] = struct.unpack("=H", struct.pack("=H", (num >> 16) & 0xFFFF))[0]
    data[1] = struct.unpack("=H", struct.pack("=H", num & 0xFFFF))[0]
    return data


def int32_to_data(num):
    data = [0, 0]
    data[0] = struct.unpack("=H", struct.pack("=H", (num >> 16) & 0xFFFF))[0]
    data[1] = struct.unpack("=H", struct.pack("=H", num & 0xFFFF))[0]
    return data


def float32_to_data(num):
    intNum = float2int(num)
    data = [0, 0]
    data[0] = (intNum >> 16) & 0xFFFF
    data[1] = intNum & 0xFFFF
    return data


def type_to_data(type, num):
    if type == "uint16":
        return uint16_to_data(int(num))
    elif type == "uint32":
        return uint32_to_data(int(num))
    elif type == "int32":
        return int32_to_data(num)
    elif type == "float32":
        return float32_to_data(num)
    else:
        raise KeyError(f"type {type} not recognized in type_to_data")


"""
Converting data arrays to numbers
"""


def data_to_uint16(data):
    return data[0]


def data_to_uint32(data):
    return concatData(data)


def data_to_int32(data):
    return struct.unpack(">i", struct.pack(">I", concatData(data)))[0]


def data_to_float32(data):
    return struct.unpack(">f", struct.pack(">I", concatData(data)))[0]


def data_to_type(data, type):
    if type == "unit16":
        return data_to_uint16(data)
    elif type == "uint32":
        return data_to_uint32(data)
    elif type == "int32":
        return data_to_int32(data)
    elif type == "float32":
        return data_to_float32(data)
    else:
        raise KeyError(f"type {type} not recognized in data_to_type")
