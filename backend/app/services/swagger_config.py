from typing import Any, Dict


class SwaggerConfig:
    @staticmethod
    def get_config() -> Dict[str, Any]:
        """Get the Swagger configuration."""
        return {
            "headers": [],
            "specs": [{
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/docs"
        }

    @staticmethod
    def get_template() -> Dict[str, Any]:
        """Get the Swagger template configuration."""
        return {
            "info": {
                "title": "JAMAL",
                "description": "API documentation for the JAMAL application",
                "version": "1.0"
            },
            "schemes": ["http", "https"]
        } 