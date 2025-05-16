import streamlit as st
from datetime import datetime
import random
import string

def generate_random_id():
    """Genera un ID con formato EA99999999999999 (EA fijo + 14 números aleatorios)"""
    fixed_letters = 'EA'
    random_digits = ''.join(random.choices(string.digits, k=14))
    return f"{fixed_letters}{random_digits}"

def process_line(line, date_str, counter):
    try:
        if not line.startswith('1'):
            return None
        
        # Split por comillas
        fields = line.split("'")
        
        # Extraer tipo de registro
        record_type = fields[1] + fields[2]  # D'E o I'E
        
        # Obtener código del registro (fields[3] contiene 7847 o 0847)
        original_code = fields[3]
        converted_code = original_code[-3:]  # Tomar últimos 3 dígitos
        
        # Extraer campos
        account_number = clean_number(fields[4])          # 000010000 -> 10000
        instrument = clean_number(fields[5])              # 05921 -> 5921
        quantity_str = fields[6].strip()                  # 00000000027.0000000
        counterparty_account = clean_number(fields[8])    # 000010018 -> 10018
        
        # Procesar cantidad
        quantity = float(quantity_str.replace(',', '').lstrip('0') or '0')
        
        # Determinar método de liquidación
        settlement_method = 'RTGS' if record_type == 'IE' else 'BATCH_SETTLEMENT'
        
        # Aplicar reglas específicas para las cuentas según el tipo de registro
        securities_account = f"7{converted_code}/{account_number}" if record_type == 'DE' else f"{converted_code}/{account_number}"
        securities_account_counterparty = f"7{converted_code}/{counterparty_account}" if record_type == 'IE' else f"{converted_code}/{counterparty_account}"
        
        # Construir línea de salida
        output_fields = [
            converted_code,                          # InstructingParty
            converted_code,                          # SettlementParty
            securities_account,                      # SecuritiesAccount
            instrument,                              # Instrument
            'LOCAL_CODE',                           # InstrumentIdentifierType
            'CVSA',                                 # CSDOfCounterparty
            converted_code,                          # SettlementCounterparty
            securities_account_counterparty,         # SecuritiesAccountOfCounterparty
            generate_random_id(),                    # InstructionReference (ahora completamente aleatorio)
            'DELIVER',                              # Instrument(MovementOfSecurities)
            f"{quantity:.1f}",                      # Quantity
            '',                                     # QuantityType
            'TRAD',                                 # TransactionType
            settlement_method,                      # SettlementMethod
            date_str,                              # TradeDate
            date_str,                              # IntendedSettlementDate
            'NOTHING'                              # PaymentType
        ]
        
        return ';'.join(output_fields)
    
    except Exception as e:
        st.error(f"Error procesando línea: {line}")
        st.error(f"Error: {str(e)}")
        return None

def clean_number(value):
    cleaned = value.strip().lstrip('0')
    return cleaned if cleaned else '0'

# FUNCIÓN CORREGIDA PARA EXTRAER LA FECHA DE MANERA FLEXIBLE
def extract_date_from_header(content):
    for line in content.split('\n'):
        if line.startswith('00'):
            # Extraer la parte donde debería estar la fecha (posición aproximada)
            date_section = line[11:21].strip()  # Ampliamos un poco el rango y eliminamos espacios
            
            # Extraer solo los dígitos de esta sección
            date_digits = ''.join(c for c in date_section if c.isdigit())
            
            # Si tenemos al menos 7 dígitos (mínimo para una fecha válida)
            if len(date_digits) >= 7:
                return date_digits[:8]  # Tomamos hasta 8 dígitos si están disponibles
            
    # Si no encontramos una fecha válida, usamos la fecha actual
    return datetime.now().strftime('%Y%m%d')

def convert_file(content):
    header = "InstructingParty;SettlementParty;SecuritiesAccount;Instrument;InstrumentIdentifierType;CSDOfCounterparty;SettlementCounterparty;SecuritiesAccountOfCounterparty;InstructionReference;Instrument(MovementOfSecurities);Quantity;QuantityType;TransactionType;SettlementMethod;TradeDate;IntendedSettlementDate;PaymentType"
    
    date_str = extract_date_from_header(content)
    
    output_lines = []
    counter = 0
    
    for line in content.split('\n'):
        if line.strip():
            processed_line = process_line(line.strip(), date_str, counter)
            if processed_line:
                output_lines.append(processed_line)
                counter += 1
    
    return header + '\n' + '\n'.join(output_lines)

def main():
    st.title("Conversor de Archivos TSA a SI2")
    
    uploaded_file = st.file_uploader("Selecciona el archivo TXT", type=['txt'])
    
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode('utf-8')
            output_content = convert_file(content)
            
            # Mostrar vista previa
            st.subheader("Vista previa del archivo convertido:")
            st.text_area("", output_content, height=300)
            
            # Crear botón de descarga
            st.download_button(
                label="Descargar archivo convertido",
                data=output_content,
                file_name="converted_file.si2",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"Error procesando el archivo: {str(e)}")

if __name__ == "__main__":
    main()
