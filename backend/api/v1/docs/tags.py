"""OpenAPI documentation for Tags endpoints."""

TAGS_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Tricks",
                        "slug": "tricks",
                        "description": "Guides related to performing tricks and combos",
                    }
                }
            },
        },
        404: {"description": "Tag not found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "slug",
            "in": "path",
            "required": True,
            "example": "tricks",
            "schema": {"type": "string", "maxLength": 200},
            "description": "Tag slug",
        },
    ],
}

TAGS_POST = {
    "responses": {
        201: {
            "description": "Tag created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Tricks",
                        "slug": "tricks",
                        "description": "Guides related to performing tricks and combos",
                    }
                }
            },
        },
        400: {"description": "Invalid request data or tag with slug already exists."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions (contributor required)."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["name", "description"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Tricks",
                            "description": "TAG NAME",
                        },
                        "description": {
                            "type": "string",
                            "example": "Guides related to performing tricks and combos",
                            "description": "TAG DESCRIPTION",
                        },
                    },
                },
                "example": {
                    "name": "Tricks",
                    "description": "Guides related to performing tricks and combos",
                },
            }
        },
    },
}

TAGS_PUT = {
    "responses": {
        200: {
            "description": "Tag updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Advanced Tricks",
                        "slug": "advanced-tricks",
                        "description": "Guides for advanced tricks and combos",
                    }
                }
            },
        },
        400: {"description": "Invalid request data."},
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions (contributor required)."},
        404: {"description": "Tag does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "slug",
            "in": "path",
            "required": True,
            "example": "tricks",
            "schema": {"type": "string", "maxLength": 200},
            "description": "Tag slug to update",
        },
    ],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Advanced Tricks",
                            "description": "UPDATED TAG NAME",
                        },
                        "slug": {
                            "type": "string",
                            "example": "advanced-tricks",
                            "description": "UPDATED TAG SLUG",
                        },
                        "description": {
                            "type": "string",
                            "example": "Guides for advanced tricks and combos",
                            "description": "UPDATED TAG DESCRIPTION",
                        },
                    },
                },
                "example": {
                    "name": "Advanced Tricks",
                    "description": "Guides for advanced tricks and combos",
                },
            }
        },
    },
}

TAGS_DELETE = {
    "responses": {
        200: {
            "description": "Tag deleted successfully!",
            "content": {
                "application/json": {
                    "example": {"message": "Tag 'Tricks' deleted successfully"}
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions (contributor required)."},
        404: {"description": "Tag does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "slug",
            "in": "path",
            "required": True,
            "example": "tricks",
            "schema": {"type": "string", "maxLength": 200},
            "description": "Tag slug to delete",
        },
    ],
}

TAGS_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "Tricks",
                            "slug": "tricks",
                            "description": "Guides related to performing tricks and combos",
                        },
                        {
                            "name": "Glitches",
                            "slug": "glitches",
                            "description": "Guides for exploiting glitches",
                        },
                    ]
                }
            },
        },
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
}
