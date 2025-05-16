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
        
        fields = line.split("'")
        record_type = fields[1] + fields[2]
        
        original_code = fields[3]
        account_number = clean_number(fields[4])
        instrument = clean_number(fields[5])
        quantity_str = fields[6].strip()
        counterparty_account = clean_number(fields[8])
        
        quantity = float(quantity_str.replace(',', '').lstrip('0') or '0')

        # Siempre reducir el código numérico a dos dígitos (ej. '7046' -> '46')
        converted_code = str(int(original_code))[-2:]

        settlement_method = 'RTGS' if record_type == 'IE' else 'BATCH_SETTLEMENT'

        # Excepción SOLO para securities_account
        if record_type == 'DE' and original_code == '7046' and account_number == '10000':
            securities_account = f"77046/10000"
        else:
            securities_account = f"7{converted_code}/{account_number}" if record_type == 'DE' else f"{converted_code}/{account_number}"
        
        securities_account_counterparty = f"{converted_code}/{counterparty_account}"

        output_fields = [
            converted_code,
            converted_code,
            securities_account,
            instrument,
            'LOCAL_CODE',
            'CVSA',
            converted_code,
            securities_account_counterparty,
            generate_random_id(),
            'DELIVER',
            str(quantity),
            '',
            'TRAD',
            settlement_method,
            date_str,
            date_str,
            'NOTHING'
        ]

        return ';'.join(output_fields)
    
    except Exception as e:
        st.error(f"Error procesando línea: {line}")
        st.error(f"Error: {str(e)}")
        return None

def clean_number(value):
    cleaned = value.strip().lstrip('0')
    return cleaned if cleaned else '0'

def extract_date_from_header(content):
    for line in content.split('\n'):
        if line.startswith('00'):
            date_section = line[11:21].strip()
            date_digits = ''.join(c for c in date_section if c.isdigit())
            if len(date_digits) >= 7:
                return date_digits[:8]
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
    
    uploaded_file = st.file_uploader("Seleccioná el archivo TXT", type=['txt'])
    
    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode('utf-8')
            output_content = convert_file(content)
            
            st.subheader("Vista previa del archivo convertido:")
            st.text_area("", output_content, height=300)
            
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
