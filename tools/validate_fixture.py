#!/usr/bin/env python3
"""Offline fixture validation CLI for Language Matrix contracts."""

import sys
import json
import os
from pathlib import Path
from jsonschema import Draft202012Validator

def validate_fixture(schema_name, file_path):
    """Validate a fixture against the specified schema."""
    
    # Enforce whitelist at library boundary - only allow known schemas
    if schema_name not in ('lesson', 'capability-request'):
        print(f"Error: Unknown schema '{schema_name}'. Must be 'lesson' or 'capability-request'", file=sys.stderr)
        return 2
    
    # Resolve schema path relative to repository root
    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / 'docs' / 'contracts' / f'{schema_name}-v1.schema.json'
    
    if not schema_path.exists():
        print(f"Error: Schema '{schema_name}' not found at {schema_path}", file=sys.stderr)
        return 2
    
    # Read and parse the schema
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
    except Exception as e:
        print(f"Error reading schema: {e}", file=sys.stderr)
        return 2
    
    # Validate that schema doesn't contain external $ref references (only fragment refs allowed)
    def check_refs(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    # Reject any $ref that doesn't start with '#'
                    if not value.startswith('#'):
                        print(f"Error: External $ref reference found at {path}: {value}", file=sys.stderr)
                        return False
                else:
                    # Recursively check nested objects
                    if not check_refs(value, f"{path}.{key}" if path else key):
                        return False
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if not check_refs(item, f"{path}[{i}]"):
                    return False
        return True
    
    # Validate schema structure and check for external references
    try:
        if not check_refs(schema):
            return 2
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        print(f"Error in schema definition: {e}", file=sys.stderr)
        return 2
    
    # Read and parse the fixture file
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"Error: Malformed JSON in '{file_path}': {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
        return 2
    
    # Validate the data against schema
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    
    if errors:
        print("Schema validation failed:")
        for error in errors:
            print(f"  Error: {error.message}", file=sys.stderr)
        return 1
    
    # If we get here, the fixture is valid
    return 0

def main():
    """Main CLI entry point."""
    
    # Check number of arguments first
    if len(sys.argv) != 3:
        print("Usage: python3 tools/validate_fixture.py SCHEMA FILE", file=sys.stderr)
        print("SCHEMA must be 'lesson' or 'capability-request'", file=sys.stderr)
        sys.exit(2)
    
    schema_name = sys.argv[1]
    file_path = sys.argv[2]
    
    # Validate schema name
    if schema_name not in ('lesson', 'capability-request'):
        print(f"Error: Unknown schema '{schema_name}'. Must be 'lesson' or 'capability-request'", file=sys.stderr)
        sys.exit(2)
    
    # Run validation
    exit_code = validate_fixture(schema_name, file_path)
    sys.exit(exit_code)

if __name__ == '__main__':
    main()