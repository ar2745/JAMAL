"""
API Documentation specifications for the Responsive Chat application.
This file contains the Swagger/OpenAPI documentation for all endpoints.
"""

# Document Management
list_documents_spec = {
    'tags': ['Documents'],
    'description': 'Get a list of all uploaded documents',
    'responses': {
        200: {
            'description': 'List of all documents',
            'schema': {
                'type': 'object',
                'properties': {
                    'documents': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'filename': {'type': 'string'},
                                'metadata': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        }
    }
}

document_upload_spec = {
    'tags': ['Documents'],
    'description': 'Upload a new document',
    'parameters': [
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': True,
            'description': 'Document file to upload (PDF, TXT, JSON, DOCX)'
        }
    ],
    'responses': {
        200: {
            'description': 'Document uploaded successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'filename': {'type': 'string'},
                    'content': {'type': 'string'}
                }
            }
        },
        400: {
            'description': 'Invalid file or no file provided'
        }
    }
}

document_delete_spec = {
    'tags': ['Documents'],
    'description': 'Delete an uploaded document',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'filename': {'type': 'string'}
                },
                'required': ['filename']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Document deleted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Document not found'
        }
    }
}

# Link Management
list_links_spec = {
    'tags': ['Links'],
    'description': 'Get a list of all processed links',
    'responses': {
        200: {
            'description': 'List of all links',
            'schema': {
                'type': 'object',
                'properties': {
                    'links': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'url': {'type': 'string'},
                                'metadata': {'type': 'object'}
                            }
                        }
                    }
                }
            }
        }
    }
}

link_upload_spec = {
    'tags': ['Links'],
    'description': 'Process and store a new link',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'url': {'type': 'string'}
                },
                'required': ['url']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Link processed successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'link_id': {'type': 'string'},
                    'content': {'type': 'string'},
                    'metadata': {'type': 'object'}
                }
            }
        },
        400: {
            'description': 'Invalid URL or crawling failed'
        }
    }
}

link_delete_spec = {
    'tags': ['Links'],
    'description': 'Delete a processed link',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'link_id': {'type': 'string'}
                },
                'required': ['link_id']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Link deleted successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'message': {'type': 'string'}
                }
            }
        },
        404: {
            'description': 'Link not found'
        }
    }
}

# Chat and Memory
chat_spec = {
    'tags': ['Chat'],
    'description': 'Send a message and get a response from the chatbot',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'conversation_id': {'type': 'string'},
                    'documents': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    },
                    'links': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                },
                'required': ['message']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Chat response',
            'schema': {
                'type': 'object',
                'properties': {
                    'response': {'type': 'string'},
                    'conversation_id': {'type': 'string'}
                }
            }
        }
    }
}

store_memory_spec = {
    'tags': ['Memory'],
    'description': 'Store a conversation in memory',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'conversation_id': {'type': 'string'},
                    'user_message': {'type': 'string'},
                    'bot_message': {'type': 'string'},
                    'documents': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    },
                    'links': {
                        'type': 'array',
                        'items': {'type': 'string'}
                    }
                },
                'required': ['conversation_id', 'user_message', 'bot_message']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Memory stored successfully',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean'},
                    'memory_id': {'type': 'string'}
                }
            }
        }
    }
}

retrieve_memory_spec = {
    'tags': ['Memory'],
    'description': 'Retrieve relevant memories for a conversation',
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'conversation_id': {'type': 'string'},
                    'query': {'type': 'string'},
                    'limit': {'type': 'integer', 'default': 5}
                },
                'required': ['conversation_id', 'query']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Retrieved memories',
            'schema': {
                'type': 'object',
                'properties': {
                    'memories': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'user_message': {'type': 'string'},
                                'bot_message': {'type': 'string'},
                                'timestamp': {'type': 'string'},
                                'relevance_score': {'type': 'number'}
                            }
                        }
                    }
                }
            }
        }
    }
}

# Analytics
chat_analytics_spec = {
    'tags': ['Analytics'],
    'description': 'Get chat analytics data',
    'parameters': [
        {
            'name': 'chat_id',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Optional chat ID to get specific chat statistics'
        }
    ],
    'responses': {
        200: {
            'description': 'Chat analytics data',
            'schema': {
                'type': 'object',
                'properties': {
                    'total_chats': {'type': 'integer'},
                    'total_messages': {'type': 'integer'},
                    'active_chats': {'type': 'integer'},
                    'total_active_users': {'type': 'integer'}
                }
            }
        }
    }
}

document_analytics_spec = {
    'tags': ['Analytics'],
    'description': 'Get document analytics data',
    'parameters': [
        {
            'name': 'chat_id',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Optional chat ID to get specific document statistics'
        }
    ],
    'responses': {
        200: {
            'description': 'Document analytics data',
            'schema': {
                'type': 'object',
                'properties': {
                    'total_documents': {'type': 'integer'},
                    'total_size': {'type': 'integer'},
                    'types': {'type': 'object'},
                    'recent_uploads': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'timestamp': {'type': 'string'},
                                'file_type': {'type': 'string'},
                                'file_size': {'type': 'integer'}
                            }
                        }
                    }
                }
            }
        }
    }
}

link_analytics_spec = {
    'tags': ['Analytics'],
    'description': 'Get link analytics data',
    'parameters': [
        {
            'name': 'chat_id',
            'in': 'query',
            'type': 'string',
            'required': False,
            'description': 'Optional chat ID to get specific link statistics'
        }
    ],
    'responses': {
        200: {
            'description': 'Link analytics data',
            'schema': {
                'type': 'object',
                'properties': {
                    'total_links': {'type': 'integer'},
                    'domains': {'type': 'object'},
                    'recent_shares': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'timestamp': {'type': 'string'},
                                'domain': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    }
}

usage_analytics_spec = {
    'tags': ['Analytics'],
    'description': 'Get usage analytics data',
    'responses': {
        200: {
            'description': 'Usage analytics data',
            'schema': {
                'type': 'object',
                'properties': {
                    'daily_active_users': {'type': 'integer'},
                    'weekly_active_users': {'type': 'integer'},
                    'monthly_active_users': {'type': 'integer'},
                    'peak_hours': {
                        'type': 'array',
                        'items': {'type': 'integer'}
                    },
                    'concurrent_users': {'type': 'integer'},
                    'average_response_time': {'type': 'number'}
                }
            }
        }
    }
} 