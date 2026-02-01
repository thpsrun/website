VARIABLES_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "5lygdn8q",
                        "name": "Platform",
                        "slug": "platform",
                        "scope": "full-game",
                        "all_cats": True,
                        "hidden": False,
                        "values": [
                            {
                                "value": "pc",
                                "name": "PC",
                                "slug": "pc",
                                "hidden": False,
                                "rules": "PC version of the game",
                            },
                            {
                                "value": "ps2",
                                "name": "PlayStation 2",
                                "slug": "ps2",
                                "hidden": False,
                                "rules": "PlayStation 2 version of the game",
                            },
                        ],
                        "game": {
                            "id": "n2680o1p",
                            "name": "Tony Hawk's Pro Skater 4",
                            "slug": "thps4",
                            "release": "2002-10-23",
                            "boxart": "https://example.com/boxart.jpg",
                            "twitch": "Tony Hawk's Pro Skater 4",
                            "defaulttime": "realtime",
                            "idefaulttime": "realtime",
                            "pointsmax": 1000,
                            "ipointsmax": 100,
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Variable could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "5lygdn8q",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Variable ID",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,category,level",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: game, category, level",
        },
    ],
}

VARIABLES_POST = {
    "responses": {
        201: {
            "description": "Variable created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "5lygdn8q",
                        "name": "Platform",
                        "slug": "platform",
                        "scope": "full-game",
                        "all_cats": True,
                        "hidden": False,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data, validation failed, or resource does not exist."
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["name", "game_id", "scope"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "example": "Platform",
                            "description": "VARIABLE NAME",
                        },
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "GAME ID THIS VARIABLE BELONGS TO",
                        },
                        "category_id": {
                            "type": "string",
                            "example": "rklge08d",
                            "description": "CATEGORY ID (REQUIRED IF all_cats IS FALSE)",
                        },
                        "level_id": {
                            "type": "string",
                            "example": "592pxj8d",
                            "description": "LEVEL ID (REQUIRED IF scope IS single-level)",
                        },
                        "scope": {
                            "type": "string",
                            "enum": [
                                "global",
                                "full-game",
                                "all-levels",
                                "single-level",
                            ],
                            "example": "full-game",
                            "description": "VARIABLE SCOPE",
                        },
                        "all_cats": {
                            "type": "boolean",
                            "example": True,
                            "description": "WHETHER VARIABLE APPLIES TO ALL CATEGORIES",
                        },
                        "hidden": {
                            "type": "boolean",
                            "example": False,
                            "description": "WHETHER VARIABLE IS HIDDEN",
                        },
                    },
                },
                "example": {
                    "name": "Platform",
                    "game_id": "n2680o1p",
                    "scope": "full-game",
                    "all_cats": True,
                    "hidden": False,
                },
            }
        },
    },
}

VARIABLES_PUT = {
    "responses": {
        200: {
            "description": "Variable updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "id": "5lygdn8q",
                        "name": "Platform",
                        "slug": "platform",
                        "scope": "full-game",
                        "all_cats": True,
                        "hidden": False,
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data, validation failed, or resource does not exist."
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Variable does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "5lygdn8q",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Variable ID to update",
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
                            "example": "Platform",
                            "description": "UPDATED VARIABLE NAME",
                        },
                        "game_id": {
                            "type": "string",
                            "example": "n2680o1p",
                            "description": "UPDATED GAME ID",
                        },
                        "category_id": {
                            "type": "string",
                            "example": "rklge08d",
                            "description": "UPDATED CATEGORY ID",
                        },
                        "level_id": {
                            "type": "string",
                            "example": "592pxj8d",
                            "description": "UPDATED LEVEL ID",
                        },
                        "scope": {
                            "type": "string",
                            "enum": [
                                "global",
                                "full-game",
                                "all-levels",
                                "single-level",
                            ],
                            "example": "full-game",
                            "description": "UPDATED VARIABLE SCOPE",
                        },
                        "all_cats": {
                            "type": "boolean",
                            "example": True,
                            "description": "UPDATED ALL CATEGORIES FLAG",
                        },
                        "hidden": {
                            "type": "boolean",
                            "example": False,
                            "description": "UPDATED HIDDEN STATUS",
                        },
                    },
                },
                "example": {"name": "Platform Updated", "hidden": True},
            }
        },
    },
}

VARIABLES_DELETE = {
    "responses": {
        200: {
            "description": "Variable deleted successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Variable 'Platform' and its values deleted successfully"
                    }
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Variable does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "id",
            "in": "path",
            "required": True,
            "example": "5lygdn8q",
            "schema": {"type": "string", "maxLength": 15},
            "description": "Variable ID to delete",
        },
    ],
}

VARIABLES_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "5lygdn8q",
                            "name": "Platform",
                            "slug": "platform",
                            "scope": "full-game",
                            "all_cats": True,
                            "hidden": False,
                        },
                        {
                            "id": "9k2xfl7m",
                            "name": "Difficulty",
                            "slug": "difficulty",
                            "scope": "single-level",
                            "all_cats": False,
                            "hidden": False,
                        },
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "game_id",
            "in": "query",
            "example": "thps4",
            "schema": {"type": "string"},
            "description": "Filter by game ID",
        },
        {
            "name": "category_id",
            "in": "query",
            "example": "rklge08d",
            "schema": {"type": "string"},
            "description": "Filter by category ID",
        },
        {
            "name": "level_id",
            "in": "query",
            "example": "592pxj8d",
            "schema": {"type": "string"},
            "description": "Filter by level ID",
        },
        {
            "name": "scope",
            "in": "query",
            "example": "full-game",
            "schema": {
                "type": "string",
                "pattern": "^(global|full-game|all-levels|single-level)$",
            },
            "description": "Filter by scope",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "game,category",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds",
        },
        {
            "name": "limit",
            "in": "query",
            "example": 50,
            "schema": {"type": "integer", "minimum": 1, "maximum": 100},
            "description": "Results per page (default 50, max 100)",
        },
        {
            "name": "offset",
            "in": "query",
            "example": 0,
            "schema": {"type": "integer", "minimum": 0},
            "description": "Results to skip (default 0)",
        },
    ],
}


# ============================================================================
# Variable Values OpenAPI Documentation
# ============================================================================

VALUES_GET = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": {
                        "value": "pc",
                        "name": "PC",
                        "slug": "pc",
                        "archive": False,
                        "rules": "PC version of the game",
                        "variable": {
                            "id": "5lygdn8q",
                            "name": "Platform",
                            "slug": "platform",
                            "scope": "full-game",
                            "archive": False,
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        404: {"description": "Variable value could not be found."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "value_id",
            "in": "path",
            "required": True,
            "example": "pc",
            "schema": {"type": "string", "maxLength": 10},
            "description": "Variable Value ID",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "variable",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: variable",
        },
    ],
}

VALUES_ALL = {
    "responses": {
        200: {
            "description": "Success!",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "value": "pc",
                            "name": "PC",
                            "slug": "pc",
                            "archive": False,
                            "rules": "PC version",
                        },
                        {
                            "value": "ps2",
                            "name": "PlayStation 2",
                            "slug": "ps2",
                            "archive": False,
                            "rules": "PS2 version",
                        },
                    ]
                }
            },
        },
        400: {"description": "Invalid response sent to server."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "variable_id",
            "in": "query",
            "example": "5lygdn8q",
            "schema": {"type": "string"},
            "description": "Filter by variable ID (required)",
        },
        {
            "name": "embed",
            "in": "query",
            "example": "variable",
            "schema": {"type": "string"},
            "description": "Comma-separated embeds: variable",
        },
        {
            "name": "limit",
            "in": "query",
            "example": 50,
            "schema": {"type": "integer", "minimum": 1, "maximum": 100},
            "description": "Results per page (default 50, max 100)",
        },
        {
            "name": "offset",
            "in": "query",
            "example": 0,
            "schema": {"type": "integer", "minimum": 0},
            "description": "Results to skip (default 0)",
        },
    ],
}

VALUES_POST = {
    "responses": {
        201: {
            "description": "Variable value created successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "value": "pc",
                        "name": "PC",
                        "slug": "pc",
                        "archive": False,
                        "rules": "PC version of the game",
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data, validation failed, or resource does not exist."
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "required": ["variable_id", "name"],
                    "properties": {
                        "value": {
                            "type": "string",
                            "maxLength": 10,
                            "example": "pc",
                            "description": "VALUE ID (AUTO-GENERATED IF NOT PROVIDED)",
                        },
                        "variable_id": {
                            "type": "string",
                            "example": "5lygdn8q",
                            "description": "VARIABLE ID THIS VALUE BELONGS TO",
                        },
                        "name": {
                            "type": "string",
                            "maxLength": 50,
                            "example": "PC",
                            "description": "VALUE NAME",
                        },
                        "slug": {
                            "type": "string",
                            "maxLength": 50,
                            "example": "pc",
                            "description": "URL-FRIENDLY SLUG (AUTO-GENERATED IF NOT PROVIDED)",
                        },
                        "archive": {
                            "type": "boolean",
                            "example": False,
                            "description": "WHETHER VALUE IS ARCHIVED/HIDDEN",
                        },
                        "rules": {
                            "type": "string",
                            "maxLength": 1000,
                            "example": "PC version of the game",
                            "description": "RULES SPECIFIC TO THIS VALUE CHOICE",
                        },
                    },
                },
                "example": {
                    "variable_id": "5lygdn8q",
                    "name": "PC",
                    "slug": "pc",
                    "archive": False,
                    "rules": "PC version of the game",
                },
            }
        },
    },
}

VALUES_PUT = {
    "responses": {
        200: {
            "description": "Variable value updated successfully!",
            "content": {
                "application/json": {
                    "example": {
                        "value": "pc",
                        "name": "PC Updated",
                        "slug": "pc-updated",
                        "archive": False,
                        "rules": "Updated rules for PC",
                    }
                }
            },
        },
        400: {
            "description": "Invalid request data, validation failed, or resource does not exist."
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Variable value does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "value_id",
            "in": "path",
            "required": True,
            "example": "pc",
            "schema": {"type": "string", "maxLength": 10},
            "description": "Variable value ID to update",
        },
    ],
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "variable_id": {
                            "type": "string",
                            "example": "5lygdn8q",
                            "description": "UPDATED VARIABLE ID",
                        },
                        "name": {
                            "type": "string",
                            "maxLength": 50,
                            "example": "PC Updated",
                            "description": "UPDATED VALUE NAME",
                        },
                        "slug": {
                            "type": "string",
                            "maxLength": 50,
                            "example": "pc-updated",
                            "description": "UPDATED URL-FRIENDLY SLUG",
                        },
                        "archive": {
                            "type": "boolean",
                            "example": True,
                            "description": "UPDATED ARCHIVE STATUS",
                        },
                        "rules": {
                            "type": "string",
                            "maxLength": 1000,
                            "example": "Updated rules",
                            "description": "UPDATED RULES",
                        },
                    },
                },
                "example": {"name": "PC Updated", "rules": "Updated rules for PC"},
            }
        },
    },
}

VALUES_DELETE = {
    "responses": {
        200: {
            "description": "Variable value deleted successfully!",
            "content": {
                "application/json": {
                    "example": {"message": "Variable value 'PC' deleted successfully"}
                }
            },
        },
        401: {"description": "API key required for this operation."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "Variable value does not exist."},
        429: {"description": "Rate limit exceeded, calm your horses."},
        500: {"description": "Server Error. Error is logged."},
    },
    "parameters": [
        {
            "name": "value_id",
            "in": "path",
            "required": True,
            "example": "pc",
            "schema": {"type": "string", "maxLength": 10},
            "description": "Variable value ID to delete",
        },
    ],
}
