group_number = 21
escape_char = '\\'
symbol_to_change = "#w"


class Package:
    def __init__(self, source_address, data):
        self.flag = generate_flag()
        self.destination_address = 0
        self.source_address = source_address
        self.data = data
        self.fcs = 0

    def create_string(self):
        flag_bytes = self.flag.encode('utf-8')
        destination_address_bytes = str(self.destination_address).encode('utf-8')
        source_address_bytes = str(self.source_address).encode('utf-8')
        stuffed_data_bytes = self.data.encode('utf-8')
        fcs_bytes = str(self.fcs).encode('utf-8')

        package_bytes = (
            flag_bytes +
            destination_address_bytes +
            source_address_bytes +
            stuffed_data_bytes +
            fcs_bytes
        )

        return package_bytes


def generate_flag():
    global group_number
    return f"${chr(ord('a') + group_number)}"


def byte_stuffing(data):
    global escape_char

    stuffed_data = ""
    flag = generate_flag()

    i = 0
    while i < len(data):
        if data[i:i + len(flag)] == flag:
            stuffed_data += escape_char + symbol_to_change
            i += len(flag)
        else:
            stuffed_data += data[i]
            i += 1
    return stuffed_data


def string_by_packages(s, source_address):
    global group_number
    packages = []
    s = byte_stuffing(s)

    for i in range(0, len(s), group_number + 1):
        data = s[i:i + group_number + 1]
        package = Package(source_address, data)

        packages.append(package.create_string())

    return packages


def bits_to_string(bytes_array):
    byte_data = bytes(bytes_array).decode('utf-8', errors='ignore')
    original_data = []
    flag = generate_flag()
    escape_char_len = len(escape_char)

    i = 0
    while i < len(byte_data) - 1:
        if byte_data[i:i + len(flag)] == flag:
            if i == 0 or byte_data[i - escape_char_len:i] != escape_char:
                end_of_package = byte_data.find(flag, i + len(flag))
                while True:
                    index_of_symbol_to_change = byte_data.find(escape_char + symbol_to_change, i + len(flag))
                    if index_of_symbol_to_change == -1:
                        break
                    else:
                        byte_data_list = list(byte_data)
                        byte_data_list[index_of_symbol_to_change:index_of_symbol_to_change+2] = flag
                        byte_data = ''.join(byte_data_list)
                if end_of_package == -1:
                    original_data.append(byte_data[i+4:-1])
                    break

                package = byte_data[i:end_of_package]
                data_start = 4
                data_end = len(package) - 1

                data_segment = package[data_start:data_end]
                original_data.append(data_segment)

                i += len(package)
            else:
                tmp = original_data.pop()
                tmp = tmp[:-2]
                original_data.append(tmp)
                original_data.append(byte_data[i])
                i += 1
        else:
            if (byte_data[i+1:i+len(flag)+1] != flag and i != 0):
                original_data.append(byte_data[i])
            i += 1

    return ''.join(original_data)
