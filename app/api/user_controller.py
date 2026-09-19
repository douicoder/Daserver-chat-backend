from flask import Blueprint, jsonify, g

from app.services.user_service import UserService
from app.security.permissions import require_auth

user_bp = Blueprint("users", __name__, url_prefix="/api/users")
user_service = UserService()


@user_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    user = user_service.get_user(g.current_user.id)
    return jsonify(user), 200
