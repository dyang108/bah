#!/bin/zsh

# Capture the output of your Python CLI script.
TMP_COMMAND_FILE="/tmp/bah.sh"

# Run the Python script
python3 /Users/dyang/strava/bah/bah.py "$@"

# If the temp file exists and is non-empty, execute its contents
if [ -s "$TMP_COMMAND_FILE" ]; then
    cmd=$(cat "$TMP_COMMAND_FILE")
    # Add command to history
    print -s -- "$cmd"      # Adds to in-memory history (Ctrl+R recallable)
    echo "$cmd" >> ~/.zsh_history  # Manually append to history file
    echo "$cmd"
    fc -R  
    # Execute command in current shell context
    eval "$cmd"
    # Cleanup
    rm -f "$TMP_COMMAND_FILE"
fi
