# OceanShield AI - Configuration Package
# Contains application configuration, taxonomy, and settings

from .hazard_taxonomy import (
    OCEAN_HAZARD_TYPES,
    SEVERITY_LEVELS,
    get_hazard_type,
    get_all_hazard_types,
    get_hazard_label,
)

__all__ = [
    "OCEAN_HAZARD_TYPES",
    "SEVERITY_LEVELS",
    "get_hazard_type",
    "get_all_hazard_types",
    "get_hazard_label",
]
