from crc import calculate_crc, check_crc_with_syndrome, corrupt_bit_with_probability

group_number = 21
escape_char = '\\'
symbol_to_change = "#w"


class Package:
    def __init__(self, source_address, data):
        self.flag = generate_flag()
        self.destination_address = 0
        self.source_address = source_address
        self.data = self._format_data(data)  # Вызываем метод для форматирования данных
        self.fcs = calculate_crc(self.data)

    def _format_data(self, data):
        """Дополняет или обрезает сегмент данных до фиксированной длины 22 символа."""
        if len(data) < 22:
            # Дополняем пробелами до 22 символов
            return data.ljust(22)
        else:
            # Обрезаем данные до 22 символов
            return data[:22]

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


def byte_unstuffing(stuffed_data):
    global escape_char, symbol_to_change

    # Убедимся, что stuffed_data - это байты
    if isinstance(stuffed_data, str):
        stuffed_data = stuffed_data.encode('utf-8')  # Преобразуем строку в байты

    unstuffed_data = bytearray()  # Хранит "распакованные" байты
    i = 0

    while i < len(stuffed_data):
        # Проверяем, является ли текущий сегмент escape-последовательностью
        if stuffed_data[i:i + len(escape_char)] == escape_char.encode('utf-8'):
            # Проверяем следующий байт после escape-последовательности
            if (i + len(escape_char)) < len(stuffed_data) and stuffed_data[i + len(escape_char):i + len(escape_char) + len(symbol_to_change)] == symbol_to_change.encode('utf-8'):
                # Восстанавливаем заменённый символ
                unstuffed_data.extend(generate_flag().encode('utf-8'))
                i += len(escape_char) + len(symbol_to_change)
            else:
                unstuffed_data.append(stuffed_data[i])
                i += 1
        else:
            unstuffed_data.append(stuffed_data[i])
            i += 1

    return unstuffed_data  # Возвращаем результат в байтах


def unpack_string_packages(packages_string):
    all_data = ""
    package_size = 27  # размер каждого пакета
    print(f"Received package string: {packages_string}")

    i = 0
    while i + package_size <= len(packages_string):
        package = packages_string[i:i + package_size]  # Извлекаем пакет фиксированного размера
        print("Package received:")
        print(package)

        fcs = package[-1]  # FCS находится в последнем байте пакета
        print(f"FCS: {fcs}")

        # Извлекаем сегмент данных
        data_segment = check_crc_with_syndrome(package[4:26], fcs)  # Данные от 4-го до 26-го байта
        print(f"Data Segment: {data_segment}")

        # Если сегмент данных - это байты, преобразуем их в строку
        if isinstance(data_segment, bytes):
            data_segment = data_segment.decode('utf-8', errors='ignore')  # Игнорируем недопустимые символы

        all_data += data_segment
        i += package_size  # Переходим к следующему пакету

    if i < len(packages_string):
        print("Недостаточно данных для нового пакета.")

    print(f"Combined Data: {all_data}")
    
    # Применение байтового разуплотнения
    original_data = byte_unstuffing(all_data)

    return original_data
