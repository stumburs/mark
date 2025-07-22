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
            throw std::runtime_error("Could not open file: " + source_path);
        }

        std::stringstream buffer;
        buffer << input.rdbuf();
        source_text = buffer.str();
    }

    // Builds Ngrams from text currently held within 'source_text'
    // 'character_count' only matters when splitting by characters
    void BuildNgrams(SplitStrategy split_strategy, int character_count = 1)
    {
        std::vector<std::string> words;

        switch (split_strategy)
        {
        case SplitStrategy::SplitByWord:
            words = SplitKeepSpaces(source_text);
            break;
        case SplitStrategy::SplitByCharacter:
            words = SplitByNCharacters(source_text, character_count);
            break;
        default:
            std::cerr << "Unknown split strategy to build Ngrams." << std::endl;
            break;
        }

        for (size_t i = 0; i <= words.size() - 1; i++)
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
            throw std::runtime_error("No ngrams available - call BuildNgrams first");
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
            result.push_back(text.substr(i, n));
        }
        return result;
    }

    // Helper function to get a random key from ngrams
    std::string GetRandomKey()
    {
        if (ngrams.empty())
        {
            throw std::runtime_error("Ngrams is empty");
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

    std::cout << "Backend awaiting commands..." << std::endl;

    // I have no clue how to make this better.
    while (std::getline(std::cin, line))
    {
        if (line == "load_source")
        {
            std::getline(std::cin, line);
            m.ReadSourceFromFile(line);
            std::cout << "Loaded " << line << std::endl;
            std::cout << "__END__" << std::endl
                      << std::flush;
        }
        else if (line == "build_ngrams")
        {
            std::getline(std::cin, line);
            if (line == "word")
            {
                m.BuildNgrams(Markov::SplitStrategy::SplitByWord);
                std::cout << "Ngrams built" << std::endl;
                std::cout << "__END__" << std::endl
                          << std::flush;
            }
            else
            {
                try
                {
                    size_t char_count = std::stoull(line);
                    m.BuildNgrams(Markov::SplitStrategy::SplitByCharacter, char_count);
                    std::cout << "Ngrams built" << std::endl;
                    std::cout << "__END__" << std::endl
                              << std::flush;
                }
                catch (const std::exception &e)
                {
                    std::cerr << "Invalid split strategy or count: " << line << std::endl;
                }
            }
        }
        else if (line == "generate")
        {
            std::getline(std::cin, line); // Ignored for now
            std::cout << m.GenerateText(100) << std::endl;
            std::cout << "__END__" << std::endl;
        }
    }
}