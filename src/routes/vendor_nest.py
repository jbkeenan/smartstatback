"""
Blueprint for Nest vendor integration.

This blueprint defines a small set of endpoints for Nest-specific
operations such as listing and creating vendor accounts.  Nest
integrations typically use OAuth tokens, so the ``create`` endpoint
accepts ``access_token``, ``refresh_token`` and ``expires_at`` in the
request body.  Expiry times should be provided as ISO 8601 strings.

These routes are intended to complement the generic thermostat API
defined in ``src/routes/thermostats.py`` and provide a focused surface
for vendor account management and diagnostics.
"""

from datetime import datetime
from flask import Blueprint, jsonify, request
from src.routes.auth import token_required, role_required
from src.models.user import UserRole
from src.models.vendor_account import VendorType, VendorAccount
from src.models.base import db


vendor_nest_bp = Blueprint("vendor_nest", __name__)


@vendor_nest_bp.route("/status", methods=["GET"])
@token_required
def nest_status(current_user):
    """Return a simple status indicating the Nest integration is online."""
    return jsonify({"vendor": VendorType.NEST.value, "status": "ok"}), 200


@vendor_nest_bp.route("/accounts", methods=["GET"])
@token_required
def list_nest_accounts(current_user):
    """List all Nest vendor accounts visible to the current user."""
    query = VendorAccount.query.filter_by(vendor=VendorType.NEST)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(VendorAccount.property_id.in_([p.id for p in current_user.properties]))
    accounts = query.all()
    return jsonify({"accounts": [a.to_dict() for a in accounts]}), 200


@vendor_nest_bp.route("/accounts", methods=["POST"])
@token_required
@role_required([UserRole.ADMIN])
def create_nest_account(current_user):
    """Create a new Nest vendor account.

    Required fields:
    - ``access_token``: OAuth access token for Nest API
    - ``refresh_token``: OAuth refresh token
    - ``expires_at``: ISO 8601 timestamp when the access token expires

    Optional fields:
    - ``account_name``: Human-readable name for the account
    - ``property_id``: Associate account with a property
    """
    data = request.get_json() or {}
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_at_str = data.get("expires_at")
    if not access_token or not refresh_token or not expires_at_str:
        return jsonify({"error": "access_token, refresh_token and expires_at are required"}), 400
    try:
        expires_at = datetime.fromisoformat(expires_at_str)
    except Exception:
        return jsonify({"error": "expires_at must be a valid ISO 8601 timestamp"}), 400
    account = VendorAccount(
        vendor=VendorType.NEST,
        account_name=data.get("account_name"),
        property_id=data.get("property_id"),
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({"message": "Nest account created", "account": account.to_dict()}), 201