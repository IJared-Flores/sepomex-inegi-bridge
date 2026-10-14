import os
import sqlite3
import pandas as pd

# FILE PATHS & CONFIGURATION
FILEPATH_CP = 'CODIGO_POSTAL_20260914.xls'
FILEPATH_LOC = 'LOCALIDADES_202607.xlsx'
DB_NAME = 'mexico_geo_catalog.db'

def build_database():
    print("=" * 65)
    print(" BUILDING MEXICO GEOGRAPHIC DATABASE (SEPOMEX ↔ INEGI) ")
    print("=" * 65)

    # STEP 1: LOAD & PROCESS SEPOMEX (POSTAL CODES)
    print("\n[1/3] Loading SEPOMEX dataset...")
    xls_cp = pd.ExcelFile(FILEPATH_CP)

    # Filter state sheets (exclude 'Nota')
    state_sheets = [s for s in xls_cp.sheet_names if s != 'Nota']

    dataframes_list = []
    for sheet in state_sheets:
        df_temp = pd.read_excel(
            FILEPATH_CP,
            sheet_name=sheet,
            dtype={
                'd_codigo': str,
                'c_estado': str,
                'c_mnpio': str,
                'c_tipo_asenta': str,
                'id_asenta_cpcons': str,
            },
        )

        # Clean decimal points and format zero-padded strings
        c_state = df_temp['c_estado'].astype(str).str.split('.').str[0].str.zfill(2)
        c_mun = df_temp['c_mnpio'].astype(str).str.split('.').str[0].str.zfill(3)

        # Standardized municipal keys
        df_temp['cvegeo_state'] = c_state
        df_temp['cvegeo_mun'] = c_state + c_mun
        df_temp['d_codigo'] = (
            df_temp['d_codigo'].astype(str).str.split('.').str[0].str.zfill(5)
        )

        dataframes_list.append(df_temp)

    # Single concatenation step outside the loop for high performance
    df_sepomex = pd.concat(dataframes_list, ignore_index=True)
    print(f"   -> Settlements processed: {len(df_sepomex):,}")

    # Select and rename relevant columns to English standards
    df_sepomex_clean = df_sepomex[[
        'd_codigo',
        'id_asenta_cpcons',
        'd_asenta',
        'd_tipo_asenta',
        'd_zona',
        'D_mnpio',
        'd_estado',
        'cvegeo_mun',
        'cvegeo_state',
    ]].rename(
        columns={
            'd_codigo': 'postal_code',
            'id_asenta_cpcons': 'settlement_id',
            'd_asenta': 'settlement',
            'd_tipo_asenta': 'settlement_type',
            'd_zona': 'zone_type',
            'D_mnpio': 'municipality',
            'd_estado': 'state',
            'cvegeo_state': 'cvegeo_state',
        }
    )

    # STEP 2: LOAD & PROCESS INEGI LOCALITIES
    print('\n[2/3] Loading INEGI Localities dataset...')
    df_loc = pd.read_excel(FILEPATH_LOC, dtype={'CVEGEO': str})

    # Ensure 9-digit CVEGEO code and slice 5-digit municipal key
    df_loc['CVEGEO'] = df_loc['CVEGEO'].astype(str).str.zfill(9)
    df_loc['cvegeo_mun'] = df_loc['CVEGEO'].str.slice(0, 5)

    # Rename locality text column if available
    if 'LOCALIDAD' in df_loc.columns:
        df_loc = df_loc.rename(columns={'LOCALIDAD': 'locality_name'})

    print(f"   -> Localities processed: {len(df_loc):,}")

    # STEP 3: EXPORT TO SQLITE & BUILD B-TREE INDEXES
    print('\n[3/3] Exporting to SQLite and creating search indexes...')

    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)

    df_sepomex_clean.to_sql(
        'sepomex_settlements', conn, if_exists='replace', index=False
    )
    df_loc.to_sql('inegi_localities', conn, if_exists='replace', index=False)

    # Create B-Tree indexes for sub-millisecond lookups
    cursor = conn.cursor()
    cursor.execute(
        'CREATE INDEX idx_cp_postal_code ON sepomex_settlements(postal_code);'
    )
    cursor.execute(
        'CREATE INDEX idx_cp_cvegeo_mun ON sepomex_settlements(cvegeo_mun);'
    )
    cursor.execute('CREATE INDEX idx_loc_cvegeo ON inegi_localities(CVEGEO);')
    cursor.execute(
        'CREATE INDEX idx_loc_cvegeo_mun ON inegi_localities(cvegeo_mun);'
    )

    conn.commit()
    conn.close()

    print("\n" + "=" * 65)
    print(f" SUCCESS! Database generated: {DB_NAME}")
    print("=" * 65 + "\n")

if __name__ == '__main__':
    build_database()