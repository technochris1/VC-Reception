from flask import Blueprint, render_template, jsonify
from app.models import Guest

guest = Blueprint('guest', __name__)


@guest.route('/guest/')
@guest.route('/guest/<uuid>')
def guest(uuid = None): 
    print("UUID:",uuid)
    result = Guest.query.filter_by(uuid = uuid).first()
    print("Returning User:",result.uuid)
    return jsonify(result)
