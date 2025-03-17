# Bah CLI Prompt Generator

A CLI tool that generates bash/zsh command options based on a natural language prompt using Ollama for generation.

## Features
- Generates multiple command-line options from a natural language prompt.
- Each option is numbered with a brief description.
- Allows selection of the desired command via number input or exit with 'n'.
- Supports execution of the selected command.

## Usage

```bash
bah <prompt>
```

### Example

```bash
$ bah "find string in files"
```

The tool will generate options like:
```
1) grep "your_string" file.txt
    ↳ searches for "your_string" in file.txt.
2) grep "your_string" /path/to/directory/*
    ↳ searches all files in directory

Select a command (#/n):
```

## Installation

```bash
git clone https://github.com/dyang108/bah.git
cd bah
pip install -r requirements.txt
chmod +x bah.py
ln -sf bah.py /usr/local/bin/bah
```

## Configuration

- Ensure you have [Ollama](https://ollama.ai/) installed and running locally.
- Set the `OLLAMA_API` environment variable if necessary.

## Limitations
- Requires Ollama to be running locally on port 11434.
- Formatting of generated commands may vary occasionally.
- Limited to basic bash/zsh command generation.
- Response time depends on Ollama's availability and response speed.

## License
MIT License
