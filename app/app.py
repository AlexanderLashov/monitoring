from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import os

app = Flask(__name__)


# Configuration for PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://root:root@localhost/monitoring_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# # Configure database URL from environment variable
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    last_checked = db.Column(db.DateTime)

    events = db.relationship('Event', backref='device', lazy=True)
    maintenance = db.relationship('Maintenance', backref='device', uselist=False, lazy=True)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)

class Maintenance(db.Model):
    __tablename__ = 'maintenance'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
    scheduled = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

# API to get the status of all devices
@app.route('/devices', methods=['GET'])
def get_devices():
    devices = Device.query.all()
    result = {}
    for device in devices:
        result[device.name] = {
            "status": device.status,
            "last_checked": device.last_checked,
            "events": [{"timestamp": e.timestamp, "event_type": e.event_type, "description": e.description} for e in device.events],
            "maintenance": {
                "scheduled": device.maintenance.scheduled if device.maintenance else False,
                "start_time": device.maintenance.start_time if device.maintenance else None,
                "end_time": device.maintenance.end_time if device.maintenance else None,
            }
        }
    return jsonify(result)

# API to get the status of a specific device
@app.route('/device/<device_name>', methods=['GET'])
def get_device(device_name):
    device = Device.query.filter_by(name=device_name).first()
    if device:
        return jsonify({
            "status": device.status,
            "last_checked": device.last_checked,
            "events": [{"timestamp": e.timestamp, "event_type": e.event_type, "description": e.description} for e in device.events],
            "maintenance": {
                "scheduled": device.maintenance.scheduled if device.maintenance else False,
                "start_time": device.maintenance.start_time if device.maintenance else None,
                "end_time": device.maintenance.end_time if device.maintenance else None,
            }
        })
    else:
        return jsonify({"error": "Device not found"}), 404

# API to add an event to a device
@app.route('/device/<device_name>/event', methods=['POST'])
def add_event(device_name):
    device = Device.query.filter_by(name=device_name).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    event = Event(
        device_id=device.id,
        event_type=request.json['event_type'],
        description=request.json.get('description', "")
    )
    device.status = request.json['event_type']
    device.last_checked=datetime.now(timezone.utc)

    db.session.add(event)
    db.session.commit()

    return jsonify({
        "status": device.status,
        "last_checked": device.last_checked,
        "events": [{"timestamp": e.timestamp, "event_type": e.event_type, "description": e.description} for e in device.events]
    }), 201

# API to schedule maintenance for a device
@app.route('/device/<device_name>/maintenance', methods=['POST'])
def schedule_maintenance(device_name):
    device = Device.query.filter_by(name=device_name).first()
    if not device:
        return jsonify({"error": "Device not found"}), 404

    if not device.maintenance:
        maintenance = Maintenance(device_id=device.id)
        db.session.add(maintenance)
    else:
        maintenance = device.maintenance

    maintenance.scheduled = True
    maintenance.start_time = request.json['start_time']
    maintenance.end_time = request.json['end_time']

    db.session.commit()

    return jsonify({
        "scheduled": maintenance.scheduled,
        "start_time": maintenance.start_time,
        "end_time": maintenance.end_time
    }), 201

@app.route('/device/<device_name>', methods=['DELETE'])
def delete_device(device_name):
    device = Device.query.filter_by(name=device_name).first()
    if device:
        db.session.delete(device)
        db.session.commit()
        return jsonify({"message": "Device deleted"}), 200
    else:
        return jsonify({"error": "Device not found"}), 404
    
@app.route('/device', methods=['POST'])
def add_device():
    data = request.json

    # Check if 'name' and 'status' fields are in the JSON data
    if not data or not 'name' in data or not 'status' in data:
        return jsonify({"error": "Device name and status are required"}), 400

    # Check if a device with the same name already exists
    existing_device = Device.query.filter_by(name=data['name']).first()
    if existing_device:
        return jsonify({"error": "Device with this name already exists"}), 400

    # Create a new device instance
    new_device = Device(
        name=data['name'],
        status=data['status'],
        last_checked=datetime.now(timezone.utc)
    )

    # Add the device to the session and commit to save it in the database
    db.session.add(new_device)
    db.session.commit()

    return jsonify({
        "id": new_device.id,
        "name": new_device.name,
        "status": new_device.status,
        "last_checked": new_device.last_checked
    }), 201


if __name__ == '__main__':
    app.run(debug=True)
