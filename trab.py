import os
from decimal import Decimal, getcontext

# Configura a precisão desejada
getcontext().prec = 1000


def read_pgm(filename):
    with open(filename, 'r') as f:
        assert f.readline().strip() == 'P2' 
        # Skip comments
        line = f.readline().strip()
        while line.startswith('#'):
            line = f.readline().strip()
        width, height = map(int, line.split())
        max_gray = int(f.readline().strip())
        pixels = []
        for _ in range(height):
            row = list(map(int, f.readline().strip().split()))
            pixels.append(row)
    return width, height, max_gray, pixels

def write_pgm(filename, width, height, max_gray, pixels):
    with open(filename, 'w') as f:
        f.write("P2\n")
        f.write(f"{width} {height}\n")
        f.write(f"{max_gray}\n")
        for row in pixels:
            f.write(" ".join(map(str, row)) + "\n")

class ArithmeticEncoder:
    def __init__(self, freq_table):
        self.low = Decimal(0.0)
        self.high = Decimal(1.0)
        self.freq_table = freq_table
        self.total_freq = sum(freq_table.values())

    def encode_symbol(self, symbol):
        range_ = self.high - self.low
        print(f"high: {self.high:.3f}",f"low:{self.low:.3f}")
        self.high = self.low + range_ * self.cumulative_freq(symbol, True)
        self.low = self.low + range_ * self.cumulative_freq(symbol, False)

    def cumulative_freq(self, symbol, high):
        cum_freq = 0
        for key, freq in self.freq_table.items():
            if key == symbol:
                return Decimal ( (cum_freq + freq) / self.total_freq if high else cum_freq / self.total_freq) # x(n) ou x(n-1)
            cum_freq += freq
        return Decimal(1.0)

    def get_encoded_value(self):
        return (self.low + self.high) / 2

def encode_image(pixels):
    freq_table = {i: 0 for i in range(256)}
    for row in pixels:
        for pixel in row:
            freq_table[pixel] += 1

    encoder = ArithmeticEncoder(freq_table)
    for row in pixels:
        for pixel in row:
            encoder.encode_symbol(pixel)
    return encoder.get_encoded_value(), freq_table

def save_codestream(filename, value, freq_table):
    with open(filename, 'w') as f:
        f.write(f"{value}\n")
        for key, freq in freq_table.items():
            f.write(f"{key} {freq}\n")

class ArithmeticDecoder:
    def __init__(self, encoded_value, freq_table):
        self.value = encoded_value
        self.low = Decimal(0.0)
        self.high = Decimal(1.0)
        self.freq_table = freq_table
        self.total_freq = sum(freq_table.values())

    def decode_symbol(self):
        range_ = self.high - self.low
        if(range_ != 0):
            scaled_value = (self.value - self.low) / range_
            for symbol in range(256):
                if self.cumulative_freq(symbol, False) <= scaled_value < self.cumulative_freq(symbol, True):
                    self.high = self.low + range_ * self.cumulative_freq(symbol, True)
                    self.low = self.low + range_ * self.cumulative_freq(symbol, False)
                    return symbol
        return 255  # In case something goes wrong

    def cumulative_freq(self, symbol, high):
        cum_freq = 0
        for key, freq in self.freq_table.items():
            if key == symbol:
                return Decimal( (cum_freq + freq) / self.total_freq if high else cum_freq / self.total_freq)
            cum_freq += freq
        return Decimal(1.0)

def decode_image(encoded_value, freq_table, width, height):
    decoder = ArithmeticDecoder(encoded_value, freq_table)
    pixels = []
    for _ in range(height):
        row = []
        for _ in range(width):
            row.append(decoder.decode_symbol())
        pixels.append(row)
    return pixels

def load_codestream(filename):
    with open(filename, 'r') as f:
        encoded_value = Decimal(f.readline().strip())
        freq_table = {}
        for line in f:
            key, freq = map(int, line.strip().split())
            freq_table[key] = freq
    return encoded_value, freq_table


def compress_image(input_filename, output_codestream_filename):
    width, height, max_gray, pixels = read_pgm(input_filename)
    encoded_value, freq_table = encode_image(pixels)
    save_codestream(output_codestream_filename, encoded_value, freq_table)

def decompress_image(input_codestream_filename, output_filename, width, height, max_gray):
    encoded_value, freq_table = load_codestream(input_codestream_filename)
    pixels = decode_image(encoded_value, freq_table, width, height)
    write_pgm(output_filename, width, height, max_gray, pixels)

def calculate_compression_ratio(original_file, codestream_file):
    original_size = os.path.getsize(original_file)
    codestream_size = os.path.getsize(codestream_file)
    return original_size / codestream_size

# Exemplo de uso:
images = ["lena.ascii.pgm", "baboon_ascii.pgm", "quadrado_ascii.pgm"]
for image in images:
    codestream_file = "./output/"+image.replace(".pgm", "_codestream.txt")
    rec_file = "./output/"+image.replace(".pgm", "-rec.pgm")

    # Compressão
    compress_image(image, codestream_file)

    # Leitura da largura, altura e max_gray para descompressão
    width, height, max_gray, _ = read_pgm(image)

    # Descompressão
    decompress_image(codestream_file, rec_file, width, height, max_gray)

    # Cálculo da taxa de compressão
    compression_ratio = calculate_compression_ratio(image, codestream_file)
    print(f"Taxa de compressão para {image}: {compression_ratio:.2f}")
