import sys
from collections import Counter
from decimal import Decimal, getcontext

getcontext().prec = 10000000000

def read_pgm(filename):
    with open(filename, 'r') as f:
        assert f.readline() == 'P2\n'
        # Ignora comentários
        line = f.readline()
        while line.startswith('#'):
            line = f.readline()
        width, height = [int(i) for i in line.split()]
        max_val = int(f.readline())
        data = []
        for line in f:
            if not line.startswith('#'):
                data.extend([int(i) for i in line.split()])
        return (width, height, max_val, data)

def write_pgm(filename, width, height, max_val, data):
    with open(filename, 'w') as f:
        f.write('P2\n')
        f.write(f'{width} {height}\n')
        f.write(f'{max_val}\n')
        line_len = 0
        for pixel in data:
            f.write(f'{pixel} ')
            line_len += 1
            if line_len >= 17:
                f.write('\n')
                line_len = 0

def calculate_frequency(data):
    freq = Counter(data)
    max_val = max(data)
    return [freq[i] if i in freq else 0 for i in range(max_val + 1)]

def arithmetic_encode(data, freq):
    cumulative_freq = [0] * (len(freq) + 1)
    for i in range(1, len(freq) + 1):
        cumulative_freq[i] = cumulative_freq[i-1] + freq[i-1]
    
    total = cumulative_freq[-1]
    low, high = Decimal(0), Decimal(1)
    for symbol in data:
        range_ = high - low
        high = low + range_ * cumulative_freq[symbol+1] / total
        low = low + range_ * cumulative_freq[symbol] / total
    
    return (low + high) /2

def arithmetic_decode(encoded_value, freq, length):
    cumulative_freq = [0] * (len(freq) + 1)
    for i in range(1, len(freq) + 1):
        cumulative_freq[i] = cumulative_freq[i-1] + freq[i-1]
    
    total = cumulative_freq[-1]
    data = []
    low, high = Decimal(0), Decimal(1)
    for _ in range(length):
        value = (encoded_value - low) / (high - low) if high != low else 0.0
        for symbol in range(len(freq)):
            if cumulative_freq[symbol] / total <= value < cumulative_freq[symbol+1] / total:
                data.append(symbol)
                range_ = high - low
                high = low + range_ * cumulative_freq[symbol+1] / total
                low = low + range_ * cumulative_freq[symbol] / total
                break
    return data

def main():
    input_files = ['lena.ascii.pgm', 'baboon_ascii.pgm', 'quadrado_ascii.pgm']
    output_files = ['./output/lena_ascii-rec.pgm', './output/baboon_ascii-rec.pgm', './output/quadrado_ascii-rec.pgm']

    for input_file, output_file in zip(input_files, output_files):
        width, height, max_val, data = read_pgm(input_file)
        freq = calculate_frequency(data)

        # Encoding
        encoded_value = arithmetic_encode(data, freq)
        with open(input_file.replace('.pgm', '.encoded'), 'w') as f:
            f.write(str(encoded_value))

        # Read encoded value for decoding
        with open(input_file.replace('.pgm', '.encoded'), 'r') as f:
            encoded_value = float(f.read())
            encoded_value = Decimal(encoded_value)

        # Decoding
        decoded_data = arithmetic_decode(encoded_value, freq, len(data))
        write_pgm(output_file, width, height, max_val, decoded_data)

        # Compression Ratio
        original_size = len(data) * 8  # in bits
        compressed_size = len(str(encoded_value)) * 8  # in bits
        compression_ratio = original_size / compressed_size
        print(f'{input_file} compression ratio: {compression_ratio:.2f}')

if __name__ == '__main__':
    main()
