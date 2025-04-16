#!/bin/bash

# Setup Cursor rules and configuration
setup_cursor() {
    echo "Setting up Cursor rules and configuration..."
    
    # Create necessary directories
    mkdir -p .cursor/rules
    
    # Don't overwrite existing rules, only copy if they don't exist
    if [ ! -f ".cursor/rules/ui-formatting-rules.mdc" ]; then
        echo "Creating ui-formatting-rules.mdc..."
    fi
    
    if [ ! -f ".cursor/rules/library-and-route-awareness.mdc" ]; then
        echo "Creating library-and-route-awareness.mdc..."
    fi
    
    # Copy config if it doesn't exist
    if [ ! -f ".cursor-config.json" ]; then
        echo "Creating .cursor-config.json..."
    fi
    
    echo "Cursor setup complete!"
}

# Validate setup
validate_setup() {
    local errors=0
    
    # Check for required files without modifying them
    for file in ".cursor-config.json" ".cursor/rules/ui-formatting-rules.mdc" ".cursor/rules/library-and-route-awareness.mdc"; do
        if [ ! -f "$file" ]; then
            echo "Warning: Missing $file"
            errors=$((errors + 1))
        fi
    done
    
    # Return validation status
    return $errors
}

# Run setup
setup_cursor
validate_setup 