#!/usr/bin/env python3
import sys
import requests
import json
import re
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: {} <prompt>".format(sys.argv[0]))
        sys.exit(1)

    # Combine all arguments into one prompt string.
    prompt = " ".join(sys.argv[1:])

    # URL of the Ollama endpoint.
    url = "http://10.0.0.1:11434/api/generate"

    subprompt = """I want you to give me a series of options for a bash/zsh command, given what I want to do. Give them to me in a format where there is one per line, with numbers leading the line. Above each cli command, add a very short (max 10 words) comment disambiguating it from the others. Add extra newline in between options. It's very important that there is consistent formatting. For example, if I say "find string in files", you say:
1) grep "your_string" file.txt
    ↳ searches for "your_string" in file.txt.

2) grep "your_string" /path/to/directory/*
    ↳ searches all files in directory
        
        Here's what I want to do: 
    """
    # JSON payload for the request
    payload = {
        "model": "deepseek-coder-v2",
        "prompt": subprompt + prompt,
        "stream": True
    }

    options_text = []
    try:
        # Make the POST request with streaming enabled.
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()  # Raise an error on bad status
            # Stream the output line by line.
            first = True
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if first:
                            first = False
                            continue
                        if "response" in data:
                            print(data["response"], end="", flush=True)
                            options_text.append(data["response"])
                    except json.JSONDecodeError:
                        continue  # Ignore malformed JSON
    except requests.exceptions.RequestException as e:
        print("Request failed: {}".format(e))
        sys.exit(1)
    options = parse_commands("".join(options_text))

    run_command(options, input("\n\nSelect a command (#/n): "))

def run_command(options, choice):
    if choice == 'n':
        sys.exit(0)
    # Validate choice
    if choice not in options:
        print(f"Invalid choice. Available options: {', '.join(options.keys())}")
        sys.exit(1)

    # Execute the selected command
    try:
        result = subprocess.run(options[choice], shell=True, text=True, capture_output=True)
        print(result.stdout)
    except Exception as e:
        print(f"Error executing command: {e}")
    sys.exit(result.returncode)

def parse_commands(input_string):
    """
    Parses the input string and creates a dictionary mapping numbers to commands.
    """
    command_map = {}
    lines = input_string.split("\n")
    
    for line in lines:
        match = re.match(r"(\d+)\)\s(.+)", line.strip())  # Extract number and command
        if match:
            key, command = match.groups()
            command_map[key] = command  # Map number to command

    return command_map

if __name__ == '__main__':
    main()
