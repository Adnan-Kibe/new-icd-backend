from models import Admin, Hospital, User
from services.logger import logger
from sqlalchemy.orm import Session

USERS = [
    {'work_id': 'EMP-22F3B1E4', 'first_name': 'Charity', 'last_name': 'Mutembei', 'email': 'charity.k.mutembei@gmail.com', 'occupation': 'Doctor', 'department': 'Cardiology', 'hospital_id': 'HOSP-38A2E9A1'},
    {'work_id': 'EMP-5F7D82C9', 'first_name': 'Adnan', 'last_name': 'Gitonga', 'email': 'adnangitonga@gmail.com', 'occupation': 'Nurse', 'department': 'Emergency', 'hospital_id': 'HOSP-A8C9F421'},
]
HOSPITALS = [
    {'hospital_id': 'HOSP-38A2E9A1', 'name': 'Boston General Hospital', 'email': 'contact@bostongeneralhospital.com', 'phone_number': '(555) 123-4567', 'location': '21 Main St, Boston, MA'},
    {'hospital_id': 'HOSP-A8C9F421', 'name': 'Denver General Hospital', 'email': 'contact@denvergeneralhospital.com', 'phone_number': '(555) 678-1234', 'location': '44 Elm St, Denver, CO'},
]
ADMINS = [
    {'admin_id': 'ADMIN-62B3C81F', 'username': 'adnan', 'email': 'adnang680@gmail.com'},
    {'admin_id': 'ADMIN-AB93D02E', 'username': 'charity', 'email': 'charity.k.mutembei@gmail.com'},
]
    
def generate_data(db: Session):
    logger.info("=== Starting database seeding process ===")

    # === 1. Insert Admins ===
    for admin in ADMINS:
        existing_admin = db.query(Admin).filter_by(email=admin["email"]).first()
        if existing_admin:
            logger.info(f"Admin already exists: {admin['email']}")
        else:
            new_admin = Admin(
                admin_id=admin["admin_id"],
                username=admin["username"],
                email=admin["email"]
            )
            db.add(new_admin)
            logger.info(f"Added new admin: {admin['username']}")

    # === 2. Insert Hospitals ===
    for hospital in HOSPITALS:
        existing_hospital = db.query(Hospital).filter_by(email=hospital["email"]).first()
        if existing_hospital:
            logger.info(f"Hospital already exists: {hospital['name']}")
        else:
            new_hospital = Hospital(
                hospital_id=hospital["hospital_id"],
                name=hospital["name"],
                email=hospital["email"],
                phone_number=hospital["phone_number"],
                location=hospital["location"]
            )
            db.add(new_hospital)
            logger.info(f"Added new hospital: {hospital['name']}")

    # === 3. Insert Users ===
    for user in USERS:
        existing_user = db.query(User).filter_by(email=user["email"]).first()
        if existing_user:
            logger.info(f"User already exists: {user['email']}")
        else:
            hospital = db.query(Hospital).filter_by(hospital_id=user["hospital_id"]).first()
            if not hospital:
                logger.warning(f"Skipping user {user['email']} — hospital not found.")
                continue
            new_user = User(
                work_id=user["work_id"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                email=user["email"],
                occupation=user["occupation"],
                department=user["department"],
                hospital_id=hospital.id,
            )
            db.add(new_user)
            logger.info(f"Added new user: {user['first_name']} {user['last_name']}")

    # === Commit changes ===
    db.commit()
    logger.info("=== Database seeding completed successfully ===")