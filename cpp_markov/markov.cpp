/**
 * Markov Chain Text Generator Backend
 *
 * This implements a Markov chain algorithm to generate pseudo-random text
 * based on input training data. It analyzes the statistical patterns of words
 * in the training text and uses these patterns to generate new, similar-sounding text.
 *
 * The program is designed to be called as a subprocess by other applications
 * and outputs the generated text to stdout.
 */

#include <iostream>
#include <map>
#include <vector>
#include <fstream>
#include <sstream>
#include <random>
#include <filesystem>

class Markov
{
public:
    enum class SplitStrategy
    {
        SplitByWord,
        SplitByCharacter,
    };

public:
    Markov() {};

    // Opens specified file and reads it to 'source_text'
    void ReadSourceFromFile(const std::string &source_path)
    {
        std::ifstream input(source_path);
        if (!input.is_open())
        {
            std::cout << "Could not open file: " << source_path << std::endl
                      << std::flush;
        }

        std::stringstream buffer;
        buffer << input.rdbuf();
        source_text = buffer.str();
    }

    // Builds Ngrams from text currently held within 'source_text'
    // 'character_count' only matters when splitting by characters
    void BuildNgrams(SplitStrategy split_strategy, int character_count = 1, const std::string *optional_text = nullptr)
    {
        const std::string &text_to_use = optional_text ? *optional_text : source_text;

        std::vector<std::string> words;

        switch (split_strategy)
        {
        case SplitStrategy::SplitByWord:
            words = SplitKeepSpaces(text_to_use);
            break;
        case SplitStrategy::SplitByCharacter:
            words = SplitByNCharacters(text_to_use, character_count);
            break;
        default:
            std::cout << "Unknown split strategy to build Ngrams." << std::endl
                      << std::flush;
            break;
        }

        for (size_t i = 0; i < words.size() - 1; i++)
        {
            const std::string &current_word = words[i];
            const std::string &next_word = words[i + 1];
            ngrams[current_word].push_back(next_word);
        }
    }

    std::string GenerateText(size_t length)
    {
        if (ngrams.empty())
        {
            return "No ngrams available - call BuildNgrams first";
        }

        std::random_device rd;
        std::mt19937 gen(rd());

        std::string current_word = GetRandomKey();
        std::string generated_text = current_word;

        for (size_t i = 0; i < length; i++)
        {
            const auto &values = ngrams[current_word];
            if (values.empty())
            {
                break;
            }

            std::uniform_int_distribution<> dis(0, values.size() - 1);
            current_word = values[dis(gen)];
            generated_text += current_word;
        }

        return generated_text;
    }

    void SaveNgramsToBinary(const std::string &filename)
    {
        std::ofstream out(filename, std::ios::binary);
        for (const auto &[key, values] : ngrams)
        {
            size_t key_len = key.size();
            out.write(reinterpret_cast<const char *>(&key_len), sizeof(size_t));
            out.write(key.data(), key_len);

            size_t vec_size = values.size();
            out.write(reinterpret_cast<const char *>(&vec_size), sizeof(size_t));

            for (const auto &val : values)
            {
                size_t str_len = val.size();
                out.write(reinterpret_cast<const char *>(&str_len), sizeof(size_t));
                out.write(val.data(), str_len);
            }
        }
    }

    void LoadNgramsFromBinary(const std::string &filename)
    {
        if (!std::filesystem::exists(filename))
        {
            std::ofstream out(filename, std::ios::binary); // creates empty file
            out.close();
            return;
        }

        std::ifstream in(filename, std::ios::binary);
        if (!in)
        {
            std::cout << "Could not open file for reading: " << filename << std::endl;
            return;
        }

        ngrams.clear();
        while (in.peek() != EOF)
        {
            size_t key_len = 0;
            in.read(reinterpret_cast<char *>(&key_len), sizeof(size_t));
            if (in.eof())
                break;

            std::string key(key_len, '\0');
            in.read(&key[0], key_len);

            size_t vec_size = 0;
            in.read(reinterpret_cast<char *>(&vec_size), sizeof(size_t));

            std::vector<std::string> values;
            for (size_t i = 0; i < vec_size; ++i)
            {
                size_t str_len = 0;
                in.read(reinterpret_cast<char *>(&str_len), sizeof(size_t));

                std::string val(str_len, '\0');
                in.read(&val[0], str_len);

                values.push_back(std::move(val));
            }

            ngrams[std::move(key)] = std::move(values);
        }
    }

private:
    using Ngrams = std::map<std::string, std::vector<std::string>>;
    Ngrams ngrams;
    std::string source_text;

private:
    // Helper function to split text keeping spaces
    std::vector<std::string> SplitKeepSpaces(const std::string &text)
    {
        std::vector<std::string> result;
        std::string current;

        for (char c : text)
        {
            if (std::isspace(c))
            {
                if (!current.empty())
                {
                    result.push_back(current);
                    current.clear();
                }
                result.push_back(std::string(1, c));
            }
            else
            {
                current += c;
            }
        }
        if (!current.empty())
        {
            result.push_back(current);
        }
        return result;
    }

    // Helper function to split text by N characters
    std::vector<std::string> SplitByNCharacters(const std::string &text, size_t n)
    {
        std::vector<std::string> result;
        for (size_t i = 0; i < text.length(); i += n)
        {
            size_t remaining = std::min(n, text.length() - i);
            result.push_back(text.substr(i, remaining));
        }
        return result;
    }

    // Helper function to get a random key from ngrams
    std::string GetRandomKey()
    {
        if (ngrams.empty())
        {
            std::cout << "Ngrams is empty" << std::endl
                      << std::flush;
        }

        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, ngrams.size() - 1);

        auto it = ngrams.begin();
        std::advance(it, dis(gen));
        return it->first;
    }
};

int main()
{
    Markov m;
    std::string line;

    // I have no clue how to make this better.
    while (std::getline(std::cin, line))
    {
        if (line == "load_source")
        {
            std::getline(std::cin, line);
            m.ReadSourceFromFile(line);
            std::cout << "Loaded " << line << std::endl
                      << std::flush;
            std::cout << "__END__" << std::endl
                      << std::flush;
        }
        else if (line == "build_ngrams")
        {
            std::getline(std::cin, line);
            std::string strategy_line = line;
            std::string input_buffer = "";

            while (std::getline(std::cin, line))
            {
                if (line == "__END__INPUT__")
                {
                    break;
                }
                input_buffer += line + "\n";
            }

            bool has_input_text = !input_buffer.empty();

            if (strategy_line == "word")
            {
                if (has_input_text)
                {
                    m.BuildNgrams(Markov::SplitStrategy::SplitByWord, 1, &input_buffer);
                }
                else
                {
                    m.BuildNgrams(Markov::SplitStrategy::SplitByWord);
                }
                std::cout << "Ngrams built by word" << (has_input_text ? " (chat)" : "") << std::endl;
            }
            else
            {
                try
                {
                    size_t char_count = std::stoull(strategy_line);
                    if (has_input_text)
                    {
                        m.BuildNgrams(Markov::SplitStrategy::SplitByCharacter, char_count, &input_buffer);
                    }
                    else
                    {
                        m.BuildNgrams(Markov::SplitStrategy::SplitByCharacter, char_count);
                    }
                    std::cout << "Ngrams built by " << char_count << " characters" << (has_input_text ? " (chat)" : "") << std::endl;
                }
                catch (const std::exception &e)
                {
                    std::cout << "Invalid split strategy: " << strategy_line << std::endl;
                }
            }

            std::cout << "__END__" << std::endl
                      << std::flush;
        }
        else if (line == "generate")
        {
            std::getline(std::cin, line); // Ignored for now
            std::cout << m.GenerateText(std::stoull(line)) << std::endl
                      << std::flush;
            std::cout << "__END__" << std::endl
                      << std::flush;
        }
        else if (line == "save")
        {
            std::getline(std::cin, line);
            std::cout << "Saving ngrams to " << line << std::endl;
            m.SaveNgramsToBinary(line);
            std::cout << "Ngrams successfully saved to " << line << std::endl;
            std::cout << "__END__" << std::endl
                      << std::flush;
        }
        else if (line == "load")
        {
            std::getline(std::cin, line);
            std::cout << "Loading ngrams from " << line << std::endl;
            m.LoadNgramsFromBinary(line);
            std::cout << "Ngrams successfully loaded from " << line << std::endl;
            std::cout << "__END__" << std::endl
                      << std::flush;
        }
    }
}