import pandas as pd
import numpy as np

def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    Carga el dataset sintético de POs, estandariza las fechas y maneja anomalías 
    como nulos y timestamps invertidos.
    """
    print(f"[*] Cargando datos desde {filepath}...")
    df = pd.read_csv(filepath)
    
    # 1. Definir columnas datetime y convertirlas
    date_columns = [
        'PO_DT', 'STA_DT', 'APPROVED_DT', 'TRAILER_ARRIVE_DT', 
        'CHECKIN_DT', 'CHECKOUT_DT', 'RECPT_DT'
    ]
    
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    print("[*] Timestamps convertidos a formato datetime.")

    # 2. Manejo del 10% de nulos en TRAILER_ARRIVE_DT
    # Creamos un flag para que el LLM y el motor de reglas sepan que el registro falló en patio
    df['MISSING_ARRIVAL_SCAN'] = df['TRAILER_ARRIVE_DT'].isnull().astype(int)
    
    # Imputación táctica: Si no hay registro de llegada, asumimos temporalmente que llegó directo al check-in
    df['TRAILER_ARRIVE_DT'] = df['TRAILER_ARRIVE_DT'].fillna(df['CHECKIN_DT'])
    print(f"[*] Manejados {df['MISSING_ARRIVAL_SCAN'].sum()} registros sin escaneo de llegada de tráiler.")

    # 3. Corrección del 5% de timestamps invertidos (Check-Out antes de Check-In)
    invalid_dock_times = df['CHECKOUT_DT'] < df['CHECKIN_DT']
    if invalid_dock_times.any():
        print(f"[*] Corrigiendo {invalid_dock_times.sum()} registros con tiempos de andén invertidos...")
        temp_checkout = df.loc[invalid_dock_times, 'CHECKOUT_DT']
        df.loc[invalid_dock_times, 'CHECKOUT_DT'] = df.loc[invalid_dock_times, 'CHECKIN_DT']
        df.loc[invalid_dock_times, 'CHECKIN_DT'] = temp_checkout

    # 4. KPI Principal: Cálculo de retraso real
    df['ACTUAL_DELAY_DAYS'] = (df['RECPT_DT'] - df['STA_DT']).dt.total_seconds() / (24 * 3600)
    df['IS_LATE_COMPUTED'] = (df['ACTUAL_DELAY_DAYS'] > 0).astype(int)

    print("[*] Limpieza completada exitosamente.\n")
    return df

def generate_eda_report(df: pd.DataFrame):
    """
    Genera el Análisis Exploratorio de Datos (EDA) inicial por consola.
    """
    print("=== REPORTE EDA: SEMANA 1 ===")
    total_pos = len(df)
    delayed_pos = df['IS_LATE_COMPUTED'].sum()
    
    print(f"Total de POs analizados: {total_pos}")
    print(f"POs con retraso real (RECPT_DT > STA_DT): {delayed_pos} ({(delayed_pos/total_pos)*100:.1f}%)")
    
    print("\nDistribución de retrasos por Vendor (Top 5):")
    delayed_df = df[df['IS_LATE_COMPUTED'] == 1]
    print(delayed_df['VENDOR_NAME'].value_counts().head(5))
    
    print("\nDistribución de retrasos por Centro de Distribución (DC):")
    print(delayed_df['DC_LOC_NAME'].value_counts())
    print("=============================\n")

if __name__ == "__main__":
    # Ruta relativa al archivo de datos
    csv_path = "../data/po_root_cause_synthetic.csv"
    output_path = "../data/processed_po_data_v1.csv"
    
    try:
        clean_df = load_and_clean_data(csv_path)
        generate_eda_report(clean_df)
        
        # Guardar el artefacto limpio
        clean_df.to_csv(output_path, index=False)
        print(f"[*] Archivo procesado guardado en {output_path}")
    except FileNotFoundError:
        print(f"[!] Error: No se encontró el archivo en {csv_path}. Verifica la ruta.")