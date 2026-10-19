"""
Integration example for P01/P02 work showing how to use the bounded capability runtime.

This demonstrates how the capability runtime would be integrated into the broader system
for processing capability requests in the language matrix project.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from language_matrix.capabilities import validate_capability_request, is_request_expired, get_granted_permissions

def example_worker_integration():
    """
    Example of how a worker might integrate with the capability runtime.
    
    This shows the typical workflow for processing capability requests:
    1. Receive capability request
    2. Validate using bounded runtime
    3. Execute capability with proper permissions
    4. Return validated output
    """
    
    # Sample capability request (similar to what would come from P01/P02 harness)
    sample_request = {
        "schema_version": "1.0",
        "request_id": "example-request-123",
        "capability": "phonology.check",
        "provider": "local",
        "input": {
            "text": "안녕하세요.",
            "language": "ko"
        },
        "policy": {
            "max_cost_usd": 0,
            "allow_network": False,
            "max_attempts": 1,
            "timeout_seconds": 30
        },
        "rationale": "Check the pronunciation explanation before presenting it as reviewed.",
        "output_schema": "phonology-report.v1",
        "permissions": [
            "cache.read",
            "local.generate"
        ],
        "deadline_utc": "2026-10-20T00:00:00Z"
    }
    
    print("Processing capability request through bounded runtime...")
    
    try:
        # 1. Validate the capability request
        errors = validate_capability_request(sample_request)
        if errors:
            raise ValueError(f"Capability request validation failed: {', '.join(errors)}")
        
        # 2. Check if request has expired
        if is_request_expired(sample_request):
            raise ValueError("Capability request has expired")
            
        # 3. Get granted permissions
        granted_permissions = get_granted_permissions(sample_request)
        print(f"Granted permissions: {granted_permissions}")
        
        # 4. Simulate capability execution (in real system, this would call actual handlers)
        result = {
            "request_id": sample_request["request_id"],
            "capability": sample_request["capability"],
            "output_schema": sample_request["output_schema"],
            "result": {
                "phonology_report": "Sample phonology report for 안녕하세요.",
                "confidence": 0.95,
                "analysis": [
                    {"syllable": "안", "pronunciation": "an"},
                    {"syllable": "녕", "pronunciation": "nyeong"},
                    {"syllable": "하", "pronunciation": "ha"},
                    {"syllable": "세", "pronunciation": "se"},
                    {"syllable": "요", "pronunciation": "yo"}
                ]
            }
        }
        
        print("✓ Capability request validated and executed successfully")
        print(f"Result type: {result['output_schema']}")
        print(f"Output keys: {list(result.keys())}")
        
        return result
        
    except Exception as e:
        print(f"✗ Capability request failed: {e}")
        raise

def example_batch_processing():
    """
    Example of batch processing multiple capability requests.
    """
    requests = [
        {
            "schema_version": "1.0",
            "request_id": "batch-request-1",
            "capability": "phonology.check",
            "provider": "local",
            "input": {
                "text": "안녕하세요.",
                "language": "ko"
            },
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 1,
                "timeout_seconds": 30
            },
            "rationale": "Check pronunciation",
            "output_schema": "phonology-report.v1",
            "permissions": [
                "cache.read"
            ],
            "deadline_utc": "2026-10-20T00:00:00Z"
        },
        {
            "schema_version": "1.0",
            "request_id": "batch-request-2",
            "capability": "tts.synthesize",
            "provider": "local",
            "input": {
                "text": "안녕하세요.",
                "language": "ko",
                "voice_id": "default"
            },
            "policy": {
                "max_cost_usd": 0,
                "allow_network": False,
                "max_attempts": 1,
                "timeout_seconds": 30
            },
            "rationale": "Generate audio for lesson",
            "output_schema": "audio-asset.v1",
            "permissions": [
                "cache.read",
                "local.generate"
            ],
            "deadline_utc": "2026-10-20T00:00:00Z"
        }
    ]
    
    results = []
    for i, request in enumerate(requests):
        print(f"Processing batch request {i+1}...")
        try:
            # Validate the capability request
            errors = validate_capability_request(request)
            if errors:
                raise ValueError(f"Capability request validation failed: {', '.join(errors)}")
            
            # Check if request has expired
            if is_request_expired(request):
                raise ValueError("Capability request has expired")
                
            # Get granted permissions
            granted_permissions = get_granted_permissions(request)
            print(f"Granted permissions for request {i+1}: {granted_permissions}")
            
            # Simulate capability execution (in real system, this would call actual handlers)
            result = {
                "request_id": request["request_id"],
                "capability": request["capability"],
                "output_schema": request["output_schema"],
                "result": {
                    "audio_asset_id": f"audio-{i}",
                    "duration_seconds": 2.5,
                    "format": "wav"
                }
            }
            
            results.append(result)
            print(f"✓ Batch request {i+1} completed successfully")
        except Exception as e:
            print(f"✗ Batch request {i+1} failed: {e}")
            raise
    
    return results

if __name__ == "__main__":
    print("=== Capability Runtime Integration Example ===")
    
    # Test single capability execution
    result = example_worker_integration()
    
    print("\n=== Batch Processing Example ===")
    # Test batch processing
    batch_results = example_batch_processing()
    
    print("\n=== Integration Complete ===")