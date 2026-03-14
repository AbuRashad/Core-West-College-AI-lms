"""
Seed script — creates the default admin user.

The admin password is read from the ``ADMIN_SEED_PASSWORD`` environment
variable.  If the variable is not set, the seed step is skipped with a
warning so that deployments never start with a known default password.

Run with:
    ADMIN_SEED_PASSWORD=... python -m auth.seed
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure the plugin root is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from auth.models import User  # noqa: E402
from auth.utils import validate_password_strength  # noqa: E402

DEFAULT_USERNAME = "admin"
DEFAULT_EMAIL = "admin@corewest.edu"
DEFAULT_ROLE = User.ROLE_ADMIN


def seed() -> None:
    """Create the default admin user if one does not already exist."""
    password = os.environ.get("ADMIN_SEED_PASSWORD", "")
    if not password:
        logger.warning(
            "[seed] ADMIN_SEED_PASSWORD is not set — skipping admin user creation. "
            "Set this environment variable to create the default admin on first run."
        )
        return

    existing = User.get_by_username(DEFAULT_USERNAME)
    if existing:
        logger.info("[seed] User '%s' already exists — skipping.", DEFAULT_USERNAME)
        return

    if not validate_password_strength(password):
        raise ValueError(
            "ADMIN_SEED_PASSWORD does not meet strength requirements "
            "(at least 8 characters, at least one digit)."
        )

    User.create(
        username=DEFAULT_USERNAME,
        email=DEFAULT_EMAIL,
        plain_password=password,
        role=DEFAULT_ROLE,
    )
    logger.info(
        "[seed] Default admin user '%s' created. Change the password after first login.",
        DEFAULT_USERNAME,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
