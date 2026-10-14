import sqlite3
from contextlib import closing
from pathlib import Path as FilePath
from typing import Optional

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware

# Absolute path to the SQLite database
DB_NAME = FilePath(__file__).parent / "mexico_geo_catalog.db"

app = FastAPI(
    title="Mexico Geo Catalog API",
    description="REST API to query Mexican postal codes and localities (SEPOMEX + INEGI).",
    version="1.0.0",
)

# CORS configuration to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection() -> sqlite3.Connection:
    if not DB_NAME.exists():
        raise HTTPException(
            status_code=500,
            detail="Database not found. Please run first: python process_catalogs.py",
        )
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/", tags=["Health Check"])
def root():
    return {"status": "ok", "message": "Mexico Geo Catalog API is running"}


# 1. Main Endpoint: Query by Postal Code (SEPOMEX)
@app.get("/api/v1/postal-codes/{postal_code}", tags=["Postal Codes"])
def get_postal_code_info(
    postal_code: str = Path(..., description="5-digit postal code", examples=["45200"]),
):
    """
    Queries the database for a given postal code and returns its state,
    municipality, and list of settlements (SEPOMEX).
    """
    formatted_cp = postal_code.strip().zfill(5)

    if not (formatted_cp.isdigit() and len(formatted_cp) == 5):
        raise HTTPException(
            status_code=422,
            detail="The postal code must contain only digits (maximum 5).",
        )

    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                postal_code,
                settlement_id,
                settlement,
                settlement_type,
                zone_type,
                municipality,
                state,
                cvegeo_mun,
                cvegeo_state AS cvegeo_est
            FROM sepomex_settlements
            WHERE postal_code = ?
            """,
            (formatted_cp,),
        )
        settlement_rows = [dict(row) for row in cursor.fetchall()]

        if not settlement_rows:
            raise HTTPException(
                status_code=404,
                detail=f"Postal Code '{formatted_cp}' not found.",
            )

        first_record = settlement_rows[0]
        cvegeo_mun = first_record["cvegeo_mun"]

    return {
        "postal_code": formatted_cp,
        "state": {
            "code": first_record["cvegeo_est"],
            "name": first_record["state"],
        },
        "municipality": {
            "cvegeo_mun": cvegeo_mun,
            "name": first_record["municipality"],
        },
        "settlements": [
            {
                "id": s["settlement_id"],
                "name": s["settlement"],
                "type": s["settlement_type"],
                "zone_type": s.get("zone_type"),
            }
            for s in settlement_rows
        ],
    }


# 2. Secondary Endpoint: Get/Filter Municipality Localities (INEGI)
@app.get("/api/v1/municipalities/{cvegeo_mun}/localities", tags=["Localities"])
def get_localities_by_municipality(
    cvegeo_mun: str = Path(..., description="Municipality CVEGEO (e.g., 14120)"),
    q: Optional[str] = Query(None, description="Optional text search filter"),
):
    """
    Returns INEGI localities for a given municipality.
    Used to populate the frontend locality <select> after entering a postal code,
    or to filter if the user types in the input field.
    """
    with closing(get_db_connection()) as conn:
        cursor = conn.cursor()

        if q and q.strip():
            search_pattern = f"%{q.strip()}%"
            cursor.execute(
                """
                SELECT cvegeo, locality_name
                FROM inegi_localities
                WHERE cvegeo_mun = ? AND locality_name LIKE ?
                ORDER BY locality_name ASC
                """,
                (cvegeo_mun, search_pattern),
            )
        else:
            cursor.execute(
                """
                SELECT cvegeo, locality_name
                FROM inegi_localities
                WHERE cvegeo_mun = ?
                ORDER BY locality_name ASC
                """,
                (cvegeo_mun,),
            )

        localities = [dict(row) for row in cursor.fetchall()]

    if not localities:
        raise HTTPException(
            status_code=404,
            detail=f"No localities found for municipality '{cvegeo_mun}'.",
        )

    return {
        "cvegeo_mun": cvegeo_mun,
        "total": len(localities),
        "localities": localities,
    }