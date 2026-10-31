"""Exasol connection helper (pyexasol)."""
import os
import ssl

import pyexasol
from dotenv import load_dotenv

load_dotenv()


def connect():
    opts = {}
    if os.getenv("EXASOL_VERIFY_CERT", "false").lower() != "true":
        # Exasol Personal typically uses a self-signed certificate
        opts["websocket_sslopt"] = {"cert_reqs": ssl.CERT_NONE}
    return pyexasol.connect(
        dsn=os.getenv("EXASOL_DSN", "localhost:8563"),
        user=os.getenv("EXASOL_USER", "sys"),
        password=os.environ["EXASOL_PASSWORD"],
        encryption=True,
        fetch_mapper=pyexasol.exasol_mapper,
        **opts,
    )
