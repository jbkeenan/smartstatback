"""
Blueprint for Cielo vendor integration.

This blueprint exposes a handful of endpoints for managing and testing
connectivity with Cielo thermostats.  The endpoints are intentionally
minimal – the system's primary thermostat operations remain under
``src/routes/thermostats.py`` via the ``ThermostatAPIFactory``.  These
vendor-specific routes provide a place to implement account linking,
token refreshes, or diagnostic checks for the Cielo API.
"""

from flask import Blueprint, jsonify, request
from src.routes.auth import token_required, role_required
from src.models.user import UserRole
from src.models.vendor_account import VendorType, VendorAccount
from src.models.base import db


# Create blueprint for Cielo vendor
vendor_cielo_bp = Blueprint("vendor_cielo", __name__)


@vendor_cielo_bp.route("/status", methods=["GET"])
@token_required
def cielo_status(current_user):
    """Return a simple status indicating the Cielo integration is online.

    This endpoint can be used for smoke tests or health checks to verify
    that the application can handle requests for Cielo-specific routes.
    """
    return jsonify({"vendor": VendorType.CIELO.value, "status": "ok"}), 200


@vendor_cielo_bp.route("/accounts", methods=["GET"])
@token_required
def list_cielo_accounts(current_user):
    """List all Cielo vendor accounts.

    Admin users see all accounts; non-admins only see accounts linked to
    properties they own.  Accounts with a ``property_id`` of ``None`` are
    considered global and visible only to administrators.
    """
    query = VendorAccount.query.filter_by(vendor=VendorType.CIELO)
    # Restrict non-admin users to accounts associated with their properties
    if current_user.role != UserRole.ADMIN:
        query = query.filter(VendorAccount.property_id.in_([p.id for p in current_user.properties]))
    accounts = query.all()
    return jsonify({"accounts": [a.to_dict() for a in accounts]}), 200


@vendor_cielo_bp.route("/accounts", methods=["POST"])
@token_required
@role_required([UserRole.ADMIN])
def create_cielo_account(current_user):
    """Create a new Cielo vendor account.

    Only administrators may create vendor accounts.  For Cielo integrations
    the payload typically contains a static API key.  Additional fields
    (e.g. ``account_name`` or ``property_id``) are optional.
    """
    data = request.get_json() or {}
    api_key = data.get("api_key")
    if not api_key:
        return jsonify({"error": "api_key is required"}), 400
    account = VendorAccount(
        vendor=VendorType.CIELO,
        api_key=api_key,
        account_name=data.get("account_name"),
        property_id=data.get("property_id")
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({"message": "Cielo account created", "account": account.to_dict()}), 201