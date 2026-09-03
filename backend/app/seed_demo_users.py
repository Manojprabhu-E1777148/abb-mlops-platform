from app.auth import hash_password
from app.core.config import settings
from app.database import engine
from app.models.user import UserModel
from sqlmodel import Session, select


DEMO_USERS = (
    (
        "manojprabhu@example.com",
        "MLOps Administrator",
        "admin",
        settings.demo_admin_password,
    ),
    (
        "mlops.member@example.com",
        "MLOps Member",
        "member",
        settings.demo_member_password,
    ),
)


def seed_demo_users() -> None:
    missing_credentials = [
        email for email, _, _, password in DEMO_USERS if not password
    ]
    if missing_credentials:
        raise RuntimeError(
            "Set DEMO_ADMIN_PASSWORD and DEMO_MEMBER_PASSWORD before seeding demo users."
        )

    with Session(engine) as session:
        for email, full_name, role, password in DEMO_USERS:
            user = session.exec(
                select(UserModel).where(UserModel.email == email)
            ).first()
            if user is None:
                session.add(
                    UserModel(
                        email=email,
                        full_name=full_name,
                        password_hash=hash_password(password),
                        role=role,
                    )
                )
        session.commit()


if __name__ == "__main__":
    seed_demo_users()
