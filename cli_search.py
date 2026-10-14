import sqlite3
import pandas as pd

DB_NAME = "mexico_geo_catalog.db"

def search_postal_code():
    conn = sqlite3.connect(DB_NAME)

    user_input = input("\nEnter Postal Code to query (e.g., 45200, 01000): ").strip()
    formatted_cp = user_input.zfill(5)

    query = """
    SELECT 
        s.postal_code AS [Postal Code],
        s.settlement AS [Settlement / Colonia],
        s.settlement_type AS [Type],
        s.municipality AS [Municipality],
        s.state AS [State],
        i.locality_name AS [INEGI Locality],
        i.CVEGEO AS [CVEGEO Code]
    FROM sepomex_settlements s
    JOIN inegi_localities i ON s.cvegeo_mun = i.cvegeo_mun
    WHERE s.postal_code = ?
    """

    df_result = pd.read_sql_query(query, conn, params=(formatted_cp,))

    if df_result.empty:
        print(f"\n [!] No results found for Postal Code '{formatted_cp}'.")
    else:
        print("\n" + "=" * 105)
        print(f" SEARCH RESULTS FOR POSTAL CODE: {formatted_cp} ".center(105))
        print("=" * 105)
        print(df_result.to_string(index=False))
        print("=" * 105 + "\n")

    conn.close()

if __name__ == "__main__":
    search_postal_code()