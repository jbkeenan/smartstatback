"""
Integration package for vendor-specific API adapters.

This package contains classes and helper functions that encapsulate the logic
for communicating with external thermostat vendors (e.g. Cielo, Nest, NetHome).
Each vendor may require different authentication mechanisms or API calls.
To keep the rest of the application decoupled from vendor-specific details,
integrations are provided via a factory function defined in ``factory.py``.
"""

from .factory import VendorIntegrationFactory, BaseVendorIntegration

__all__ = ["VendorIntegrationFactory", "BaseVendorIntegration"]