#!/usr/bin/env python3
import sys
import requests
import json
import re
import subprocess
import select
import pyperclip

def main():
    if len(sys.argv) < 2:
        print("Usage: {} <prompt>".format(sys.argv[0]))
        sys.exit(1)

    # Combine all arguments into one prompt string.
    prompt = " ".join(sys.argv[1:])

    # URL of the Ollama endpoint.
    url = "http://10.0.0.1:11434/api/generate"
    awk_example = "awk -F, '{print $2,$3}' input.csv > output.csv"

    subprompt = f"""Here's what I want: "{prompt}"

Given the task above, provide multiple bash/zsh commands that accomplish the task, numbered and separated by newlines. Give one command per line, with numbers leading the line. Below each command, add a very short comment (max 10 words) disambiguating it from the others. Add newline in between options. Ensure consistency in formatting. No extra quotes or backticks. Do not introduce your response with any preamble. Give at least one response. For example:
If I say "find abc in foo", you respond with:
1) grep "abc" foo.txt
    ↳ searches for text "abc" in foo.txt

2) find foo -name abc
    ↳ finds a file named "abc" in foo

3) grep "abc" foo/*
    ↳ searches all files in directory "foo"

If I say "choose the second and third columns of a csv and write it to a new csv", you respond with:
1) {awk_example}
    ↳ selects the second and third columns from a CSV file named "input.csv" and writes to a new file named "output.csv"

2) cut -d',' -f2-3 input.csv > output.csv
    ↳ extracts the second and third fields (columns) delimited by commas from "input.csv" and writes to "output.csv"

3) tail -n +1 input.csv | head -n 1 | cut -d',' -f2-3 > output.csv
    ↳ reads the first line of a CSV file, extracts columns 2 and 3, and writes them to "output.csv"
    """
    context = "\n\n Here is some context for the development environment: " + build_dev_context()

    full_prompt = subprompt + prompt + context
    # JSON payload for the request
    payload = {
        "model": "deepseek-coder-v2",
        "prompt": full_prompt,
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
                        if "response" in data and data["response"] != '```':
                            print(data["response"], end="", flush=True)
                            options_text.append(data["response"])
                    except json.JSONDecodeError:
                        continue  # Ignore malformed JSON
    except requests.exceptions.RequestException as e:
        print("Request failed: {}".format(e))
        sys.exit(1)
    options = parse_commands("".join(options_text))
    try:
        selected = input("\n\nSelect a command # | [q]uit | [#c]opy: ")
        run_command(options, selected)
    except KeyboardInterrupt:
        print("\n")
        sys.exit(1)

def run_command(options, choice):
    if choice == 'q':
        sys.exit(0)
    if 'c' in choice:
        print(choice[0])
        if choice[0] not in options:
            print(f"Invalid choice. Available options: {', '.join(map(lambda x: x + 'c', options.keys()))}")
            sys.exit(1)
        pyperclip.copy(options[choice[0]])

        sys.exit(0)

    # Validate choice
    if choice not in options:
        print(f"Invalid choice. Available options: {', '.join(options.keys())}")
        sys.exit(1)

    # Execute the selected command
    try:
        result = process_output(options[choice])
    except Exception as e:
        print(f"Error executing command: {e}")
    sys.exit(result)


def process_output(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Use select to read stdout and stderr as they are produced
    while True:
        reads = [process.stdout.fileno(), process.stderr.fileno()]
        ready, _, _ = select.select(reads, [], [])

        for r in ready:
            if r == process.stdout.fileno():
                output = process.stdout.readline()
                if output:
                    sys.stdout.write(output)
                    sys.stdout.flush()
            if r == process.stderr.fileno():
                error = process.stderr.readline()
                if error:
                    sys.stderr.write(error)
                    sys.stderr.flush()

        # Break when process is done
        if process.poll() is not None and process.stdout.read() == '' and process.stderr.read() == '':
            break

    return process.wait()

def get_command_output(cmd):
    """Run a shell command and return its output as a string."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def build_dev_context():
    """Gathers relevant development environment details into a string."""
    context = {
        "Shell History": get_command_output("HISTTIMEFORMAT='%F %T ' history 10"),
        "Current Directory (pwd)": get_command_output("pwd"),
        "Directory Listing (ls -lhA)": get_command_output("ls -lhA | head 10"),
        "OS Information": get_command_output("uname -a"),
        "Path": get_command_output("echo $PATH"),
        "Running Processes": get_command_output("ps -u $(whoami) -o pid,command --sort=-%cpu | head -10"),
        "Git Status": get_command_output("git status --short"),
        "Git Branch": get_command_output("git rev-parse --abbrev-ref HEAD"),
        "Git Commit Hash": get_command_output("git rev-parse HEAD"),
        "Python Version": get_command_output("python --version"),
        "Virtual Environment": get_command_output("echo $VIRTUAL_ENV"),
        # "Environment Variables": get_command_output("env | sort"),
    }

    context_str = "\n".join(f"{key}:\n{value}\n" for key, value in context.items())
    return context_str

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
