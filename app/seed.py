from app import create_app, db
from app.models import Department

app = create_app()

with app.app_context():
    # Clear existing if you want a fresh start, or just check if empty
    if not Department.query.first():
        print("Adding your departments to the database...")
        
        dept_list = ["MDC", "Cyber", "Legal", "Accounting"]
        
        for name in dept_list:
            new_dept = Department(department_name=name)
            db.session.add(new_dept)
            
        db.session.commit()
        print("MDC, Cyber, Legal, and Accounting have been added!")
    else:
        print("Departments already exist in the database.")