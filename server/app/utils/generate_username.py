import random
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


def generate_username(full_name: str, db: Session) -> str:
    first_name = full_name.strip().split(" ")[0].lower()

    first_name = re.sub(r"[^a-z0-9]", "", first_name)

    while True:
        random_number = random.randint(1000, 9999)
        username = f"{first_name}-{random_number}"

        existing_user = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        if not existing_user:
            return username