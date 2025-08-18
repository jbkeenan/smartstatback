"""
Factory and adapter classes for vendor integrations.

The purpose of this module is to provide a unified way to obtain a vendor
integration class based on a ``VendorAccount`` record.  Each vendor may have
its own authentication and request handling requirements.  By encapsulating
those differences behind a common interface, the rest of the application can
interact with vendors uniformly.

Note:
    At this stage of development the integration classes are placeholders.
    They log calls but do not make outbound network requests.  Future work
    should implement the actual API interactions for each supported vendor.
"""

from __future__ import annotations

from typing import Type
from src.models.vendor_account import VendorAccount, VendorType


class BaseVendorIntegration:
    """Abstract base class for vendor integrations.

    Implementations should override methods to perform actual API calls.
    """

    def __init__(self, account: VendorAccount) -> None:
        self.account = account

    def get_status(self) -> dict:
        """Return a health/status payload for the vendor.

        Subclasses should call the vendor's API if appropriate.  The default
        implementation simply returns a static response.
        """
        return {"vendor": self.account.vendor.value, "status": "ok"}


class CieloIntegration(BaseVendorIntegration):
    """Integration adapter for the Cielo vendor."""

    # In a real implementation, methods would call the Cielo REST API using
    # the stored API key from ``self.account.api_key``.
    pass


class NestIntegration(BaseVendorIntegration):
    """Integration adapter for the Nest vendor."""

    # In a real implementation, methods would call the Nest API using OAuth
    # tokens stored on ``self.account``.  Tokens may need to be refreshed.
    pass


class NetHomeIntegration(BaseVendorIntegration):
    """Integration adapter for the NetHome/Pioneer vendor."""

    # In a real implementation, methods would call the NetHome API using
    # the stored API key from ``self.account.api_key``.
    pass


class VendorIntegrationFactory:
    """Factory for obtaining vendor integration instances."""

    _mapping: dict[VendorType, Type[BaseVendorIntegration]] = {
        VendorType.CIELO: CieloIntegration,
        VendorType.NEST: NestIntegration,
        VendorType.NETHOME: NetHomeIntegration,
    }

    @staticmethod
    def get_integration(account: VendorAccount) -> BaseVendorIntegration:
        """Return an integration instance for the provided vendor account.

        Args:
            account: The ``VendorAccount`` instance representing an external
                thermostat vendor account.

        Raises:
            ValueError: If no integration is registered for the account's vendor.
        """
        vendor = account.vendor
        integration_cls = VendorIntegrationFactory._mapping.get(vendor)
        if not integration_cls:
            raise ValueError(f"No integration registered for vendor {vendor}")
        return integration_cls(account)
