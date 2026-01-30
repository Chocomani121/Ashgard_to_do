from app import db, app

# Create all database tables within the Flask app context
with app.app_context():
    db.create_all()
    print("✔ Database created successfully!")