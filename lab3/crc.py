import random

polynomial = [1, 1, 0, 0, 0, 1, 0, 1, 1]


def bits_to_string(bits):
    chars = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        byte_str = ''.join(str(bit) for bit in byte_bits)
        char = chr(int(byte_str, 2))
        chars.append(char)
    return ''.join(chars)


def corrupt_bit_with_probability(data):
    if isinstance(data, str):
        data_bytes = bytearray(data.encode('utf-8'))
    else:
        data_bytes = bytearray(data) 
    
    if len(data_bytes) == 0:
        return data

    byte_index = random.randint(0, len(data_bytes) - 1)
    bit_index = random.randint(0, 7)

    if random.random() < 0.7:
        data_bytes[byte_index] ^= (1 << bit_index)

    return data_bytes.decode('utf-8')



def poly_division_mod2(dividend, divisor):
    deg_dividend = len(dividend) - 1
    deg_divisor = len(divisor) - 1
    if deg_dividend < deg_divisor:
        return [0], dividend
    quotient = [0] * (deg_dividend - deg_divisor + 1)
    remainder = dividend[:]
    for i in range(deg_dividend - deg_divisor + 1):
        if remainder[i] == 1:
            quotient[i] = 1
            for j in range(len(divisor)):
                remainder[i + j] ^= divisor[j]
    while len(remainder) > 8 and remainder[0] == 0:
        remainder.pop(0)
    return quotient, remainder


def calculate_crc(data):
    global polynomial
    bits = []
    for char in data:
        bin_representation = bin(ord(char))[2:].zfill(8)
        bits.extend([int(bit) for bit in bin_representation])
    bits.extend([0, 0, 0, 0, 0, 0, 0, 0])
    quotient, remainder = poly_division_mod2(bits, polynomial)
    byte = 0
    for bit in remainder:
        byte = (byte << 1) | bit
    return chr(byte)


def generate_syndrome_map(polynomial, data_length):
    syndrome_map = {}
    for i in range(data_length):
        bits = [0] * data_length
        bits[i] = 1
        _, remainder = poly_division_mod2(bits, polynomial)
        bits[i] = 0
        syndrome_map[tuple(remainder)] = i
    return syndrome_map


def check_crc_with_syndrome(data_with_crc, fcs):
    global polynomial
    bits = []
    
    for byte in data_with_crc:
        if isinstance(byte, str):
            byte = ord(byte)
        bin_representation = format(byte, '08b')
        bits.extend([int(bit) for bit in bin_representation])
    
    if isinstance(fcs, str):
        fcs = ord(fcs)
    fcs_bits = [int(bit) for bit in format(fcs, '08b')]
    
    bits.extend(fcs_bits)
    
    total_bits = len(bits)
    
    syndrome_map = generate_syndrome_map(polynomial, total_bits)
    
    quotient, remainder = poly_division_mod2(bits, polynomial)
    
    if remainder == [0] * len(remainder):
        return data_with_crc
    else:
        syndrome = tuple(remainder)
        if syndrome in syndrome_map:
            error_bit_position = syndrome_map[syndrome]
            print(f"Обнаружена ошибка в бите {error_bit_position}, исправляем")
            bits[error_bit_position] ^= 1
            print(bits_to_string(bits[:len(bits) - 8]))
            return bits_to_string(bits[:len(bits) - 8])
        return data_with_crc
