"""Confluence API response fixtures for mocking."""

# Successful page search response with results
PAGE_FOUND_RESPONSE = {
    "results": [
        {
            "id": "123456",
            "type": "page",
            "title": "Test Page",
            "version": {
                "number": 5,
                "message": "Updated content",
            },
        }
    ],
    "size": 1,
}

# Empty search response (page not found)
PAGE_NOT_FOUND_RESPONSE = {
    "results": [],
    "size": 0,
}

# Page with version info
PAGE_WITH_VERSION_RESPONSE = {
    "results": [
        {
            "id": "123456",
            "type": "page",
            "title": "Test Page",
            "version": {
                "number": 10,
                "message": "Latest update",
            },
        }
    ],
    "size": 1,
}

# Page with ancestors (parent info)
PAGE_WITH_ANCESTORS_RESPONSE = {
    "id": "123456",
    "type": "page",
    "title": "Child Page",
    "ancestors": [
        {
            "id": "111111",
            "title": "Root Page",
        },
        {
            "id": "222222",
            "title": "Parent Page",
        },
    ],
}

# Page with no ancestors (root page)
PAGE_NO_ANCESTORS_RESPONSE = {
    "id": "123456",
    "type": "page",
    "title": "Root Page",
    "ancestors": [],
}

# Attachment found response
ATTACHMENT_FOUND_RESPONSE = {
    "results": [
        {
            "id": "att123",
            "type": "attachment",
            "title": "test_image.png",
            "version": {
                "number": 1,
                "message": "MKDocsWithConfluence [vabc123def456]",
            },
        }
    ],
    "size": 1,
}

# Attachment not found response
ATTACHMENT_NOT_FOUND_RESPONSE = {
    "results": [],
    "size": 0,
}

# Successful page creation response
PAGE_CREATED_RESPONSE = {
    "id": "789012",
    "type": "page",
    "title": "New Page",
    "version": {
        "number": 1,
    },
}

# Successful page update response
PAGE_UPDATED_RESPONSE = {
    "id": "123456",
    "type": "page",
    "title": "Updated Page",
    "version": {
        "number": 11,
    },
}

# Successful attachment upload response
ATTACHMENT_UPLOADED_RESPONSE = {
    "results": [
        {
            "id": "att456",
            "type": "attachment",
            "title": "uploaded_file.png",
            "version": {
                "number": 1,
            },
        }
    ],
}


def get_page_response(page_id: str, title: str, version: int = 1) -> dict:
    """Generate a page response with custom values."""
    return {
        "results": [
            {
                "id": page_id,
                "type": "page",
                "title": title,
                "version": {
                    "number": version,
                    "message": f"Version {version}",
                },
            }
        ],
        "size": 1,
    }


def get_attachment_response(
    attachment_id: str, filename: str, version: int = 1, file_hash: str | None = None
) -> dict:
    """Generate an attachment response with custom values."""
    message = f"MKDocsWithConfluence [v{file_hash}]" if file_hash else f"Version {version}"
    return {
        "results": [
            {
                "id": attachment_id,
                "type": "attachment",
                "title": filename,
                "version": {
                    "number": version,
                    "message": message,
                },
            }
        ],
        "size": 1,
    }
