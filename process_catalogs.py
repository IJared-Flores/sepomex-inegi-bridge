import sqlite3
import pandas as pd

FILEPATH_CP = 'CODIGO_POSTAL_20260914.xls'
FILEPATH_LOC = 'LOCALIDADES_202607.xls'
DB_PATH = 'geo_mexico.db'


def process_sepomex_catalog() -> pd.DataFrame:
    print("Processing SEPOMEX catalog...")
    xls = pd.ExcelFile(FILEPATH_CP)
    sheets_estados = [s for s in xls.sheet_names if s != 'Nota']
    lista_dfs = []

    for sheet in sheets_estados:
        df = pd.read_excel(
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

        # Formatting geopolitical codes with leading zeros
        state_code = (
            df['c_estado'].astype(str).str.split('.').str[0].str.zfill(2)
        )
        mun_code = (
            df['c_mnpio'].astype(str).str.split('.').str[0].str.zfill(3)
        )

        df['state_code'] = state_code
        df['municipality_code'] = mun_code
        df['cvegeo_mun'] = state_code + mun_code
        df['postal_code'] = (
            df['d_codigo'].astype(str).str.split('.').str[0].str.zfill(5)
        )

        lista_dfs.append(df)

    df_total = pd.concat(lista_dfs, ignore_index=True)

    column_mapping = {
        'postal_code': 'postal_code',
        'd_asenta': 'settlement',
        'd_tipo_asenta': 'settlement_type',
        'D_mnpio': 'municipality',
        'd_estado': 'state',
        'cvegeo_mun': 'cvegeo_mun',
        'state_code': 'state_code',
        'municipality_code': 'municipality_code',
        'd_zona': 'zone_type',
    }

    return df_total[list(column_mapping.keys())].rename(columns=column_mapping)


def process_inegi_catalog() -> pd.DataFrame:
    print("Processing INEGI catalog...")
    df_loc = pd.read_excel(FILEPATH_LOC, dtype={'CVEGEO': str})

    # Extract municipal geographic code (5 digits)
    df_loc['cvegeo_mun'] = df_loc['CVEGEO'].str.slice(0, 5)

    return df_loc.rename(
        columns={
            'CVEGEO': 'cvegeo',
            'NOM_LOC': 'locality_name',
            'AMBITO': 'scope',
        }
    )

if __name__ == '__main__':
    df_cp = process_sepomex_catalog()
    df_loc = process_inegi_catalog()

    print(f"Writing processed catalogs to: {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)

    # Guardar en tablas estandarizadas
    df_cp.to_sql('sepomex_settlements', conn, if_exists='replace', index=False)
    df_loc.to_sql('inegi_localities', conn, if_exists='replace', index=False)

    # Crear índices de consulta
    cursor = conn.cursor()
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_postal_code ON sepomex_settlements(postal_code);'
    )
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_cvegeo_mun_sepomex ON sepomex_settlements(cvegeo_mun);'
    )
    cursor.execute(
        'CREATE INDEX IF NOT EXISTS idx_cvegeo_mun_inegi ON inegi_localities(cvegeo_mun);'
    )

    conn.commit()
    conn.close()

    print(f'¡Successfully processed and indexed catalogs in: {DB_PATH}!')