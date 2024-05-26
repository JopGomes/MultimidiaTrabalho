#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <sstream>
#include <cmath>
#include <map>
#include <iomanip>

using namespace std;

struct PGMImage {
    int width;
    int height;
    int max_val;
    vector<vector<int>> pixels;
};

PGMImage readPGM(const string& filename) {
    ifstream file(filename, ios::in);
    if (!file.is_open()) {
        cerr << "Erro ao abrir o arquivo: " << filename << endl;
        exit(1);
    }

    string line;
    PGMImage img;

    // Ler o identificador
    getline(file, line);
    if (line != "P2") {
        cerr << "Formato inválido: " << line << endl;
        exit(1);
    }

    // Ignorar comentários
    while (getline(file, line) && line[0] == '#');

    // Ler dimensões
    stringstream ss(line);
    ss >> img.width >> img.height;

    // Ler valor máximo
    file >> img.max_val;

    // Ler pixels
    img.pixels.resize(img.height, vector<int>(img.width));
    for (int i = 0; i < img.height; ++i) {
        for (int j = 0; j < img.width; ++j) {
            file >> img.pixels[i][j];
        }
    }

    file.close();
    return img;
}

void writePGM(const string& filename, const PGMImage& img) {
    ofstream file(filename, ios::out);
    if (!file.is_open()) {
        cerr << "Erro ao abrir o arquivo: " << filename << endl;
        exit(1);
    }

    // Escrever cabeçalho
    file << "P2\n";
    file << img.width << " " << img.height << "\n";
    file << img.max_val << "\n";

    // Escrever pixels
    for (int i = 0; i < img.height; ++i) {
        for (int j = 0; j < img.width; ++j) {
            file << img.pixels[i][j] << " ";
        }
        file << "\n";
    }

    file.close();
}

struct Symbol {
    double low;
    double high;
    double range;
};

map<int, Symbol> createProbabilityTable(const vector<int>& data, int max_val) {
    map<int, int> freq;
    for (int value : data) {
        freq[value]++;
    }

    map<int, Symbol> probTable;
    double cumulative = 0.0;
    for (int i = 0; i <= max_val; ++i) {
        if (freq.find(i) != freq.end()) {
            double probability = static_cast<double>(freq[i]) / data.size();
            probTable[i] = { cumulative, cumulative + probability, probability };
            cumulative += probability;
        }
    }
    return probTable;
}

string encodeArithmetic(const vector<int>& data, int max_val) {
    auto probTable = createProbabilityTable(data, max_val);
    double low = 0.0;
    double high = 1.0;

    for (int value : data) {
        double range = high - low;
        high = low + range * probTable[value].high;
        low = low + range * probTable[value].low;
    }

    double code = (low + high) / 2.0;
    stringstream ss;
    ss << fixed << setprecision(15) << code;
    return ss.str();
}

vector<int> decodeArithmetic(const string& codeStr, int size, const map<int, Symbol>& probTable) {
    double code;
    stringstream ss(codeStr);
    ss >> code;

    vector<int> data(size);
    for (int i = 0; i < size; ++i) {
        for (const auto& [value, sym] : probTable) {
            if (code >= sym.low && code < sym.high) {
                data[i] = value;
                double range = sym.high - sym.low;
                code = (code - sym.low) / range;
                break;
            }
        }
    }
    return data;
}

int main() {
    vector<string> filenames = { "lena.ascii.pgm", "baboon_ascii.pgm", "quadrado_ascii.pgm" };
    vector<string> rec_filenames = { "./output/lena_ascii-rec.pgm", "./output/baboon_ascii-rec.pgm", "./output/quadrado_ascii-rec.pgm" };

    for (size_t i = 0; i < filenames.size(); ++i) {
        PGMImage img = readPGM(filenames[i]);

        // Transformar a imagem em um vetor de dados
        vector<int> data;
        for (const auto& row : img.pixels) {
            data.insert(data.end(), row.begin(), row.end());
        }

        // Codificar
        string code = encodeArithmetic(data, img.max_val);

        // Salvar o codestream
        ofstream codeStream("./output/"+filenames[i] + ".arithmetic");
        codeStream << code;
        codeStream.close();

        // Decodificar
        map<int, Symbol> probTable = createProbabilityTable(data, img.max_val);
        vector<int> decodedData = decodeArithmetic(code, data.size(), probTable);

        // Reconstituir a imagem
        PGMImage decodedImg = img;
        int index = 0;
        for (int r = 0; r < decodedImg.height; ++r) {
            for (int c = 0; c < decodedImg.width; ++c) {
                decodedImg.pixels[r][c] = decodedData[index];
                index++;
            }
        }

        // Escrever a imagem decodificada
        writePGM(rec_filenames[i], decodedImg);

        // Calcular a taxa de compressão
        streampos originalSize = ifstream(filenames[i], ios::binary | ios::ate).tellg();
        streampos compressedSize = ifstream("./output/"+filenames[i] + ".arithmetic", ios::binary | ios::ate).tellg();
        double compressionRate = static_cast<double>(originalSize) / compressedSize;

        cout << "Taxa de compressão para " << filenames[i] << ": " << compressionRate << endl;
    }

    return 0;
}
