"""
Model definition for vendor account credentials.

This module defines the ``VendorAccount`` model which stores credentials
and metadata required to communicate with external thermostat vendors such as
``Cielo``, ``Nest`` and ``NetHome/Pioneer``. Each vendor may have
different authentication requirements (e.g. OAuth tokens, API keys).  The
model is designed to be flexible enough to accommodate these differences
while maintaining a consistent interface for the rest of the application.

The ``VendorType`` enumeration lists all supported vendors.  New vendors
should be added here and to the corresponding integration factory.

The ``VendorAccount`` model can optionally be associated with a specific
property via the ``property_id`` foreign key.  This allows multiple
properties in the system to maintain their own vendor accounts when
necessary.  If a vendor account is meant to be used globally across all
properties, ``property_id`` can be left ``None``.
"""

from datetime import datetime
import enum

from src.models.base import db, BaseModel
from src.models.property import Property


class VendorType(enum.Enum):
    """Enumeration of supported thermostat vendors."""

    CIELO = "cielo"
    NEST = "nest"
    NETHOME = "nethome"  # Also covers Pioneer/NetHome brand integrations


class VendorAccount(db.Model, BaseModel):
    """Database model for storing vendor account credentials.

    Each row in the ``vendor_accounts`` table corresponds to a set of
    credentials required to communicate with a vendor's API.  Fields such
    as ``access_token`` and ``refresh_token`` are provided for OAuth-based
    vendors like Nest.  Vendors that rely on static API keys can store
    those in the ``api_key`` column.  The ``expires_at`` column can be
    used to track token expiry times when applicable.
    """

    __tablename__ = "vendor_accounts"

    id = db.Column(db.Integer, primary_key=True)
    #: The vendor this account belongs to.  Stored as an enum for type safety.
    vendor = db.Column(db.Enum(VendorType), nullable=False)
    #: Optional human-readable name or identifier for the account (e.g. email address).
    account_name = db.Column(db.String(255), nullable=True)
    #: Optional foreign key linking this account to a specific property.  Null
    #: indicates a global account.
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=True)
    #: API key for vendors that use static credentials (e.g. Cielo, NetHome/Pioneer).
    api_key = db.Column(db.String(512), nullable=True)
    #: Access token for OAuth-based vendors (e.g. Nest).  May expire.
    access_token = db.Column(db.String(1024), nullable=True)
    #: Refresh token for OAuth-based vendors.
    refresh_token = db.Column(db.String(1024), nullable=True)
    #: Expiry timestamp for the access token, if applicable.
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    property = db.relationship("Property", backref=db.backref("vendor_accounts", lazy="dynamic"))

    def is_expired(self) -> bool:
        """Return ``True`` if the stored access token is expired.

        If ``expires_at`` is not set, this method always returns ``False``.
        """
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at

    def to_dict(self) -> dict:
        """Serialize the vendor account to a dictionary for JSON responses."""
        return {
            "id": self.id,
            "vendor": self.vendor.value,
            "account_name": self.account_name,
            "property_id": self.property_id,
            "api_key": self.api_key,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }