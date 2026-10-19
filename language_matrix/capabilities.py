"""
Capability request validation and execution runtime for P03.

This module implements structural validation, deadline checks, 
permission validation, and output schema validation for capability requests.
"""
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from jsonschema import Draft202012Validator, ValidationError
from pathlib import Path

# Registry of supported capabilities and their output schemas
CAPABILITY_REGISTRY = {
    "lesson.generate": ["lesson.v1"],
    "phonology.check": ["phonology-report.v1"],
    "tts.synthesize": ["audio-asset.v1"],
    "asr.transcribe": ["transcript.v1"],
    "image.generate": ["image-asset.v1"]
}

# Registry of supported permissions
PERMISSION_REGISTRY = {
    "cache.read",
    "cache.write", 
    "local.generate"
}

# Output schema registry (only lesson.v1 is currently defined)
OUTPUT_SCHEMA_REGISTRY = {
    "lesson.v1": "lesson-v1.schema.json",
    "phonology-report.v1": "phonology-report-v1.schema.json",
    "audio-asset.v1": "audio-asset-v1.schema.json", 
    "transcript.v1": "transcript-v1.schema.json",
    "image-asset.v1": "image-asset-v1.schema.json"
}

# Schema validator for capability requests
CAPABILITY_REQUEST_SCHEMA = None
SCHEMA_ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'contracts'

def _load_schema(schema_file: str) -> Dict[str, Any]:
    """Load a JSON schema from the contracts directory."""
    schema_path = SCHEMA_ROOT / schema_file
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file {schema_file} not found")
    return json.loads(schema_path.read_text())

def _get_validator() -> Draft202012Validator:
    """Get or create the capability request validator."""
    global CAPABILITY_REQUEST_SCHEMA
    if CAPABILITY_REQUEST_SCHEMA is None:
        schema = _load_schema("capability-request-v1.schema.json")
        CAPABILITY_REQUEST_SCHEMA = Draft202012Validator(schema)
    return CAPABILITY_REQUEST_SCHEMA

def validate_capability_request(request: Dict[str, Any]) -> List[str]:
    """
    Validate a capability request according to P03 requirements.
    
    Returns list of validation errors. Empty list means valid request.
    """
    errors = []
    
    # 1. Structural validation using JSON Schema
    validator = _get_validator()
    schema_errors = list(validator.iter_errors(request))
    
    for error in schema_errors:
        errors.append(f"Schema validation failed: {error.message}")
    
    # 2. Deadline validation (must be in the future)
    if "deadline_utc" in request:
        try:
            deadline = datetime.strptime(request["deadline_utc"], "%Y-%m-%dT%H:%M:%SZ")
            # Make the deadline timezone-aware to match current_time
            deadline = deadline.replace(tzinfo=timezone.utc)
            current_time = datetime.now(timezone.utc)
            if deadline <= current_time:
                errors.append("Deadline has expired")
        except ValueError:
            errors.append("Invalid deadline format")
    
    # 3. Capability validation (must be in registry)
    if "capability" in request:
        capability = request["capability"]
        if capability not in CAPABILITY_REGISTRY:
            errors.append(f"Unknown capability: {capability}")
    
    # 4. Output schema validation
    if "output_schema" in request:
        output_schema = request["output_schema"]
        if output_schema not in OUTPUT_SCHEMA_REGISTRY:
            errors.append(f"Unknown output schema: {output_schema}")
    
    # 5. Permission validation (must be in registry)
    if "permissions" in request:
        permissions = request["permissions"]
        for perm in permissions:
            if perm not in PERMISSION_REGISTRY:
                errors.append(f"Unknown permission: {perm}")
    
    # 6. Policy validation
    if "policy" in request:
        policy = request["policy"]
        
        # Validate max_cost_usd is 0
        if "max_cost_usd" in policy and policy["max_cost_usd"] != 0:
            errors.append("Policy must have max_cost_usd = 0")
            
        # Validate allow_network is false
        if "allow_network" in policy and policy["allow_network"] is not False:
            errors.append("Policy must have allow_network = false")
    
    return errors

def validate_output_schema(output: Dict[str, Any], schema_name: str) -> List[str]:
    """
    Validate output against the specified schema.
    
    Returns list of validation errors. Empty list means valid output.
    """
    errors = []
    
    if schema_name not in OUTPUT_SCHEMA_REGISTRY:
        return [f"Unknown output schema: {schema_name}"]
    
    # Load the appropriate schema
    try:
        schema_file = OUTPUT_SCHEMA_REGISTRY[schema_name]
        schema = _load_schema(schema_file)
        validator = Draft202012Validator(schema)
        schema_errors = list(validator.iter_errors(output))
        
        for error in schema_errors:
            errors.append(f"Output validation failed: {error.message}")
    except Exception as e:
        errors.append(f"Failed to validate output against {schema_name}: {str(e)}")
    
    return errors

def is_request_expired(request: Dict[str, Any]) -> bool:
    """
    Check if a request has expired based on its deadline.
    
    Returns True if expired, False otherwise.
    """
    if "deadline_utc" not in request:
        return True  # No deadline means expired
        
    try:
        deadline = datetime.strptime(request["deadline_utc"], "%Y-%m-%dT%H:%M:%SZ")
        # Make the deadline timezone-aware to match current_time
        deadline = deadline.replace(tzinfo=timezone.utc)
        current_time = datetime.now(timezone.utc)
        return deadline <= current_time
    except ValueError:
        return True  # Invalid date format is considered expired

def get_granted_permissions(request: Dict[str, Any]) -> List[str]:
    """
    Get the list of granted permissions for a request.
    
    For now, this just returns what's in the request (no actual granting logic).
    """
    if "permissions" not in request:
        return []
    return request["permissions"]

def get_supported_capabilities() -> Dict[str, List[str]]:
    """
    Get the registry of supported capabilities and their output schemas.
    """
    return CAPABILITY_REGISTRY.copy()

def get_supported_permissions() -> set:
    """
    Get the registry of supported permissions.
    """
    return PERMISSION_REGISTRY.copy()