"""
Configuration module that loads environment variables from .env file
and exposes them through a dataclass.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


# Load .env file from project root (go up from src/utils to project root)
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


@dataclass
class _Config:
    """
    Configuration dataclass that exposes environment variables from .env file.
    Internal class - use the 'config' instance instead.
    """
    
    project_id: Optional[str] = field(default=None)
    location: Optional[str] = field(default=None)
    agent_model: Optional[str] = field(default=None)
    top_p: Optional[float] = field(default=None)
    temperature: Optional[float] = field(default=None)
    max_output_tokens: Optional[int] = field(default=None)
    
    def __post_init__(self):
        """
        Load values from environment variables after initialization.
        Environment variable names should be uppercase versions of field names.
        """
        # Get all field names from the dataclass
        for field_name in self.__dataclass_fields__:
            env_var_name = field_name.upper()
            env_value = os.getenv(env_var_name)
            
            if env_value is not None:
                # Get the field type to handle type conversion
                field_type = self.__dataclass_fields__[field_name].type
                
                # Convert to appropriate type
                if field_type == bool:
                    env_value = env_value.lower() in ("true", "1", "yes", "on")
                elif field_type == float:
                    env_value = float(env_value)
                elif field_type == int:
                    env_value = int(env_value)
                
                # Set the value
                setattr(self, field_name, env_value)


# Create a singleton instance
config = _Config()
