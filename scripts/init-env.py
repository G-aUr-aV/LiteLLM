#!/usr/bin/env python3
"""Create private local gateway credentials without replacing an existing file."""

import argparse
import os
from pathlib import Path
import secrets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        default=Path(__file__).resolve().parents[1] / ".env",
        help="Destination (default: .env in the repository root)",
    )
    destination = parser.parse_args().output
    credentials = {
        "LITELLM_MASTER_KEY": "sk-" + secrets.token_hex(32),
        "LITELLM_SALT_KEY": "sk-" + secrets.token_hex(32),
        # Hex is safe to interpolate into the PostgreSQL connection URL.
        "POSTGRES_PASSWORD": secrets.token_hex(24),
    }
    try:
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        print(f"Existing {destination} preserved.")
        return
    with os.fdopen(fd, "w") as env_file:
        for name, value in credentials.items():
            env_file.write(f"{name}={value}\n")
    print(f"Created {destination} with owner-only permissions.")


if __name__ == "__main__":
    main()
