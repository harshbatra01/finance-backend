"""
Standardized API response helpers.

Provides consistent response formatting across all endpoints. Every API
response follows the same structure, making it predictable for frontend
consumers.

Success format:
    {
        "success": true,
        "data": <payload>,
        "message": "Human-readable message"
    }

Error format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": { ... }  // optional field-level errors
        }
    }
"""

from flask import jsonify


def success_response(data=None, message="Success", status_code=200):
    """
    Create a standardized success response.

    Args:
        data: The response payload (dict, list, or None).
        message: A human-readable success message.
        status_code: HTTP status code (default 200).

    Returns:
        A Flask JSON response tuple (response, status_code).
    """
    response = {
        "success": True,
        "data": data,
        "message": message,
    }
    return jsonify(response), status_code


def created_response(data=None, message="Resource created successfully"):
    """
    Create a 201 Created response for POST operations.

    Args:
        data: The created resource data.
        message: A human-readable success message.

    Returns:
        A Flask JSON response tuple with 201 status.
    """
    return success_response(data=data, message=message, status_code=201)


def no_content_response():
    """
    Create a 204 No Content response for DELETE operations.

    Returns:
        An empty Flask response with 204 status.
    """
    return "", 204


def error_response(error_code, message, details=None, status_code=400):
    """
    Create a standardized error response.

    Args:
        error_code: A machine-readable error code string (e.g. "VALIDATION_ERROR").
        message: A human-readable error description.
        details: Optional dict with field-level error details.
        status_code: HTTP status code (default 400).

    Returns:
        A Flask JSON response tuple (response, status_code).
    """
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
        },
    }
    if details:
        response["error"]["details"] = details

    return jsonify(response), status_code
