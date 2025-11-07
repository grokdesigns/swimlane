# connector/src/runner_override.py
"""
Runner override for actions that don't require authentication
"""

class RunnerOverride:
    """
    Base runner for actions without authentication requirements
    """
    
    def __init__(self, asset, asset_schema, http_proxy):
        # No authentication needed - just store what we need
        self.asset = asset
        self.asset_schema = asset_schema
        self.http_proxy = http_proxy
    
    def run(self, inputs, action_schema):
        """
        Override this method in action implementations
        """
        raise NotImplementedError("Action must implement run() method")