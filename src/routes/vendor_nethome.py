"""
Blueprint for NetHome/Pioneer vendor integration.

The NetHome (also marketed as Pioneer) integration uses simple API keys
for authentication.  This blueprint exposes endpoints to query
connectivity status, list existing vendor accounts and create new
accounts.  Only administrators may create new vendor accounts.
"""

from flask import Blueprint, jsonify, request
from src.routes.auth import token_required, role_required
from src.models.user import UserRole
from src.models.vendor_account import VendorType, VendorAccount
from src.models.base import db

vendor_nethome_bp = Blueprint("vendor_nethome", __name__)


@vendor_nethome_bp.route("/status", methods=["GET"])
@token_required
def nethome_status(current_user):
    """Return a simple status indicating the NetHome/Pioneer integration is online."""
    return jsonify({"vendor": VendorType.NETHOME.value, "status": "ok"}), 200


@vendor_nethome_bp.route("/accounts", methods=["GET"])
@token_required
def list_nethome_accounts(current_user):
    """List all NetHome vendor accounts visible to the current user."""
    query = VendorAccount.query.filter_by(vendor=VendorType.NETHOME)
    if current_user.role != UserRole.ADMIN:
        query = query.filter(VendorAccount.property_id.in_([p.id for p in current_user.properties]))
    accounts = query.all()
    return jsonify({"accounts": [a.to_dict() for a in accounts]}), 200


@vendor_nethome_bp.route("/accounts", methods=["POST"])
@token_required
@role_required([UserRole.ADMIN])
def create_nethome_account(current_user):
    """Create a new NetHome/Pioneer vendor account.

    Required field:
    - ``api_key``: static API key used to authenticate with the vendor

    Optional fields:
    - ``account_name``: human-readable name for the account
    - ``property_id``: associate account with a specific property
    """
    data = request.get_json() or {}
    api_key = data.get("api_key")
    if not api_key:
        return jsonify({"error": "api_key is required"}), 400
    account = VendorAccount(
        vendor=VendorType.NETHOME,
        account_name=data.get("account_name"),
        property_id=data.get("property_id"),
        api_key=api_key
    )
    db.session.add(account)
    db.session.commit()
    return jsonify({"message": "NetHome account created", "account": account.to_dict()}), 201