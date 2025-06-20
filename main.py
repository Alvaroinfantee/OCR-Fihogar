import streamlit as st
import base64
import json
from mistralai import Mistral
from pdf2image import convert_from_bytes
import os
import tempfile
from openai import OpenAI as OpenAIClient
import classification  # Import the classification module

# Set page configuration
st.set_page_config(page_title="PDF Page OCR Processor", layout="wide")

# Add this big string with the JSON structure
CLASSIFICATION_JSON_STRUCTURE = r'''
{
  "111": {
    "type": "string",
    "description": "Unknown purpose, single character string."
  },
  "ACTIVIDAD_PRESTAMO": {
    "type": "string",
    "description": "Purpose of the loan, e.g., 'Uso personal' (Personal use)."
  },
  "ANO_VEHICULO": {
    "type": "integer",
    "description": "Year of the vehicle being acquired with the loan."
  },
  "AÑO_VEHICULO_PROPIO": {
    "type": "string",
    "description": "Year of a vehicle already owned by the applicant."
  },
  "BANCO1": {
    "type": "string",
    "description": "Name of the first bank."
  },
  "BANCO2": {
    "type": "string",
    "description": "Name of the second bank."
  },
  "BANCO3": {
    "type": "string",
    "description": "Name of the third bank."
  },
  "BIENES_INMUEBLES_APARTAMENTO": {
    "type": "string",
    "description": "Indicates if the applicant owns an apartment."
  },
  "BIENES_INMUEBLES_CASAS": {
    "type": "string",
    "description": "Indicates if the applicant owns a house."
  },
  "BIENES_INMUEBLES_SOLARES": {
    "type": "string",
    "description": "Indicates if the applicant owns land plots."
  },
  "BURO_CLIENTE_CONFIRMA": {
    "type": "string",
    "description": "Confirmation from the credit bureau, e.g., 'SI'."
  },
  "CALLE": {
    "type": "string",
    "description": "Street name of the applicant's address."
  },
  "CANTIDAD_EMPLEADOS": {
    "type": "string",
    "description": "Number of employees if applicable (e.g., for self-employment)."
  },
  "CARGO_OCUPA": {
    "type": "string",
    "description": "Job title or position held by the applicant."
  },
  "CATEGORIA_OCUPACIONAL": {
    "type": "object",
    "description": "Categorization of the applicant's occupation.",
    "properties": {
      "codigo": {
        "type": "string",
        "description": "Code for the occupational category, e.g., 'Cuenta propia profesional'."
      },
      "descripcion": {
        "type": "string",
        "description": "Description of the occupational category, e.g., 'Cuenta propia profesional'."
      }
    }
  },
  "CEDULA": {
    "type": "string",
    "description": "Applicant's national identification number (Cedula)."
  },
  "CEDULA_CONYUGE": {
    "type": "string",
    "description": "Spouse's national identification number (Cedula)."
  },
  "CIUDAD": {
    "type": "integer",
    "description": "Code representing the applicant's city."
  },
  "CIUDADANIA_CONYUGE": {
    "type": "string",
    "description": "Spouse's citizenship."
  },
  "CONCEPTO_COBRAR": {
    "type": "string",
    "description": "Description of accounts receivable."
  },
  "CONCEPTO_INVERSIONES": {
    "type": "string",
    "description": "Description of investments."
  },
  "CONCEPTO_MOBILIARIO": {
    "type": "string",
    "description": "Description of furniture and fixtures."
  },
  "CONCEPTO_OTROS_COMPROMISOS_PAGOS": {
    "type": "string",
    "description": "Description of other financial commitments or payments."
  },
  "CORREO_ELECTRONICO": {
    "type": "string",
    "description": "Applicant's email address."
  },
  "CUANTO_PAGA_ALQUILER": {
    "type": "string",
    "description": "Monthly rent payment amount."
  },
  "CUENTA_COBRAR": {
    "type": "string",
    "description": "Amount of accounts receivable."
  },
  "CUENTABANCO1": {
    "type": "string",
    "description": "Account number for the first bank."
  },
  "CUENTABANCO2": {
    "type": "string",
    "description": "Account number for the second bank."
  },
  "CUENTABANCO3": {
    "type": "string",
    "description": "Account number for the third bank."
  },
  "DEPENDIENTES": {
    "type": "string",
    "description": "Number of dependents for the applicant."
  },
  "DEPENDIENTES_CONYUGE": {
    "type": "string",
    "description": "Number of dependents for the spouse."
  },
  "DESCRIPCION_OTROS_INGRESOS": {
    "type": "string",
    "description": "Description of other income sources."
  },
  "DIRECCION DE LA MADRE": {
    "type": "string",
    "description": "Mother's address."
  },
  "DIRECCION_PADRE": {
    "type": "string",
    "description": "Father's address."
  },
  "DIRECCION_REFERENCIA_PERSONAL": {
    "type": "string",
    "description": "Address of a personal reference."
  },
  "DIRRECCION_EMPLEO": {
    "type": "string",
    "description": "Applicant's employment address."
  },
  "DONDE_OTROS_COMPROMISO_PAGOS": {
    "type": "string",
    "description": "Institution or entity for other financial commitments/payments."
  },
  "EDIFICIO": {
    "type": "string",
    "description": "Building name or number of the applicant's address."
  },
  "EMAIL_CONYUGE": {
    "type": "string",
    "description": "Spouse's email address."
  },
  "ESTADO_CIVIL": {
    "type": "string",
    "description": "Applicant's marital status, e.g., 'S' (Soltero/Single)."
  },
  "FECHA_NACIMIENTO": {
    "type": "string",
    "format": "date-time",
    "description": "Applicant's date of birth in ISO 8601 format."
  },
  "FECHA_NACIMIENTO_CONYUGE": {
    "type": ["string", "null"],
    "format": "date-time",
    "description": "Spouse's date of birth in ISO 8601 format, or null if not applicable."
  },
  "GASTOS": {
    "type": "string",
    "description": "Applicant's monthly expenses."
  },
  "INDICICIO_ESTADUNIDENSE": {
    "type": "string",
    "description": "Indication of U.S. connections or status."
  },
  "INGRESOS": {
    "type": "string",
    "description": "Applicant's total monthly income."
  },
  "INGRESOS_EXTRAS": {
    "type": "string",
    "description": "Indicates if the applicant has extra income, e.g., 'No'."
  },
  "INTITUCION_PEP": {
    "type": "string",
    "description": "Institution related to Politically Exposed Person (PEP) status."
  },
  "LUGAR_NACIMIENTO": {
    "type": "string",
    "description": "Applicant's place of birth."
  },
  "LUGAR_NACIMIENTO_CONYUGE": {
    "type": "string",
    "description": "Spouse's place of birth."
  },
  "LUGAR_TRABAJO": {
    "type": "string",
    "description": "Applicant's place of work."
  },
  "LUGAR_TRABAJO_CONYUGE": {
    "type": "string",
    "description": "Spouse's place of work."
  },
  "MARCA_VEHICULO": {
    "type": "integer",
    "description": "Code representing the brand of the vehicle being acquired with the loan."
  },
  "MARCA_VEHICULO_PROPIO": {
    "type": "string",
    "description": "Brand of a vehicle already owned by the applicant."
  },
  "MESES": {
    "type": "string",
    "description": "Duration in months, likely for loan term or time in current residence/job."
  },
  "MODELO_VEHICULO": {
    "type": "integer",
    "description": "Code representing the model of the vehicle being acquired with the loan."
  },
  "MODELO_VEHICULO_PROPIO": {
    "type": "string",
    "description": "Model of a vehicle already owned by the applicant."
  },
  "MONTO_INICIAL": {
    "type": "string",
    "description": "Initial amount or down payment for the loan."
  },
  "MONTO_PRESTAMO": {
    "type": "string",
    "description": "Total loan amount."
  },
  "NACIONALIDAD": {
    "type": "integer",
    "description": "Code representing the applicant's nationality."
  },
  "NEGOCIO_PROPIO": {
    "type": "string",
    "description": "Indicates if the applicant has their own business, e.g., 'No'."
  },
  "NIVEL_EDUCATIVO": {
    "type": "string",
    "description": "Applicant's educational level."
  },
  "NIVEL_EDUCATIVO_CONYUGE": {
    "type": "string",
    "description": "Spouse's educational level."
  },
  "NOMBRE_BANCO1": {
    "type": "string",
    "description": "Full name of the first bank."
  },
  "NOMBRE_BANCO2": {
    "type": "string",
    "description": "Full name of the second bank."
  },
  "NOMBRE_BANCO3": {
    "type": "string",
    "description": "Full name of the third bank."
  },
  "NOMBRE_COMPLETO": {
    "type": "string",
    "description": "Applicant's full name."
  },
  "NOMBRE_DEL_CONYUGE": {
    "type": "string",
    "description": "Spouse's full name."
  },
  "NOMBRE_MADRE": {
    "type": "string",
    "description": "Mother's full name."
  },
  "NOMBRE_PADRE": {
    "type": "string",
    "description": "Father's full name."
  },
  "NOMBRE_PEP": {
    "type": "string",
    "description": "Name of the Politically Exposed Person (PEP)."
  },
  "NOMBRE_REFERENCIA_COMERCIAL_1": {
    "type": "string",
    "description": "Name of the first commercial reference."
  },
  "NOMBRE_REFERENCIA_COMERCIAL_2": {
    "type": "string",
    "description": "Name of the second commercial reference."
  },
  "NOMBRE_REFERENCIA_PERSONAL": {
    "type": "string",
    "description": "Name of a personal reference."
  },
  "NUMERO_CASA_APATAMENTO": {
    "type": "string",
    "description": "House or apartment number of the applicant's address."
  },
  "OCUPACION": {
    "type": "integer",
    "description": "Code representing the applicant's occupation."
  },
  "OCUPACION_CONYUGE": {
    "type": "string",
    "description": "Spouse's occupation."
  },
  "OTRA_CIUDADANIA_DOCUMENTO": {
    "type": "string",
    "description": "Document number for another citizenship."
  },
  "OTRA_CIUDADANIA_FECHA_EMISIÓN": {
    "type": ["string", "null"],
    "format": "date-time",
    "description": "Issue date of the other citizenship document, or null if not applicable."
  },
  "OTRA_CIUDADANIA_FECHA_VENCIMIENTO": {
    "type": ["string", "null"],
    "format": "date-time",
    "description": "Expiration date of the other citizenship document, or null if not applicable."
  },
  "OTRA_CIUDADANIA_STATUS": {
    "type": "string",
    "description": "Status of other citizenship."
  },
  "OTRA_CIUDADANIA_TIPO_DOCUMENTO": {
    "type": "string",
    "description": "Type of document for another citizenship."
  },
  "OTROS INGRESOS": {
    "type": "string",
    "description": "General field for other income."
  },
  "OTROS_INGRESOS": {
    "type": ["string", "null"],
    "description": "Other income sources, or null if not applicable."
  },
  "PAIS_DE_REESIDENCIA": {
    "type": "integer",
    "description": "Code representing the applicant's country of residence."
  },
  "PAIS_OTRA_CIUDADANIA": {
    "type": "string",
    "description": "Country of other citizenship."
  },
  "PAISBANCO1": {
    "type": "string",
    "description": "Country of the first bank."
  },
  "PAISBANCO2": {
    "type": "string",
    "description": "Country of the second bank."
  },
  "PAISBANCO3": {
    "type": "string",
    "description": "Country of the third bank."
  },
  "PARENTEZO_PEP": {
    "type": "string",
    "description": "Relationship to the Politically Exposed Person (PEP)."
  },
  "PASSAPORTE_CONYUGE": {
    "type": "string",
    "description": "Spouse's passport number."
  },
  "PEP_CARGO": {
    "type": "string",
    "description": "Position held by the Politically Exposed Person (PEP)."
  },
  "PRECIO_VEHICULO": {
    "type": "string",
    "description": "Price of the vehicle being acquired with the loan."
  },
  "PROVINCIA": {
    "type": "integer",
    "description": "Code representing the applicant's province."
  },
  "REF_POR_DEALER": {
    "type": "string",
    "description": "Indicates if the applicant was referred by a dealer, e.g., 'No'."
  },
  "REFENCIAS_BANCARIAS": {
    "type": "string",
    "description": "General field for bank references."
  },
  "REFERENCIA_FINANCIERA": {
    "type": "string",
    "description": "General field for financial references."
  },
  "RELACION_REFERENCIA": {
    "type": "string",
    "description": "Relationship to the personal reference."
  },
  "SECTOR": {
    "type": "string",
    "description": "Neighborhood or sector of the applicant's address."
  },
  "SELECCION_VEHICULO": {
    "type": "string",
    "description": "Indicates if a vehicle has been selected, e.g., 'Si'."
  },
  "SEXO": {
    "type": "string",
    "description": "Applicant's gender, e.g., 'M' (Male)."
  },
  "SEXO_CONYUGE": {
    "type": "string",
    "description": "Spouse's gender."
  },
  "TASA_INTERES": {
    "type": "string",
    "description": "Interest rate for the loan."
  },
  "TELEFONO_CASA": {
    "type": "string",
    "description": "Applicant's home phone number."
  },
  "TELEFONO_CELULAR": {
    "type": "string",
    "description": "Applicant's cell phone number."
  },
  "TELEFONO_CONYUGE": {
    "type": "string",
    "description": "Spouse's phone number."
  },
  "TELEFONO_MADRE": {
    "type": "string",
    "description": "Mother's phone number."
  },
  "TELEFONO_PADRE": {
    "type": "string",
    "description": "Father's phone number."
  },
  "TELEFONO_REFERENCIA_COMERCIAL_1": {
    "type": "string",
    "description": "Phone number of the first commercial reference."
  },
  "TELEFONO_REFERENCIA_COMERCIAL_2": {
    "type": "string",
    "description": "Phone number of the second commercial reference."
  },
  "TELEFONO_REFERENCIA_PERSONAL": {
    "type": "string",
    "description": "Phone number of a personal reference."
  },
  "TELEFONO_TRABAJO": {
    "type": "string",
    "description": "Applicant's work phone number."
  },
  "TIEMPO_LABORANDO": {
    "type": "integer",
    "description": "Time (likely in years or months) working at current job."
  },
  "TIEMPO_NEGOCIO_PROPIO": {
    "type": "string",
    "description": "Time (likely in years or months) operating own business."
  },
  "TIEMPO_VIVIENDA": {
    "type": "string",
    "description": "Time (likely in years or months) at current residence."
  },
  "TIENE_CONYUGE": {
    "type": "string",
    "description": "Indicates if the applicant has a spouse."
  },
  "TIENE_INMUEBLES": {
    "type": "string",
    "description": "Indicates if the applicant owns real estate."
  },
  "TIENE_INVERSIONES": {
    "type": "string",
    "description": "Indicates if the applicant has investments."
  },
  "TIENE_MOBILIARIO": {
    "type": "string",
    "description": "Indicates if the applicant owns furniture/fixtures."
  },
  "TIENE_OTROS_COMPROMISOS_PAGO": {
    "type": "string",
    "description": "Indicates if the applicant has other financial commitments/payments."
  },
  "TIENE_REFERECIA_COMERCIAL": {
    "type": "string",
    "description": "Indicates if the applicant has commercial references."
  },
  "TIENE_REFERENCIA_PERSONALES": {
    "type": "string",
    "description": "Indicates if the applicant has personal references."
  },
  "TIENE_VEHICULO": {
    "type": "string",
    "description": "Indicates if the applicant owns a vehicle."
  },
  "TIPO_CUENTA_BANCO1": {
    "type": "string",
    "description": "Type of account for the first bank."
  },
  "TIPO_CUENTA_BANCO2": {
    "type": "string",
    "description": "Type of account for the second bank."
  },
  "TIPO_CUENTA_BANCO3": {
    "type": "string",
    "description": "Type of account for the third bank."
  },
  "TIPO_EMPLEO": {
    "type": "integer",
    "description": "Code representing the type of employment."
  },
  "TIPO_PERSONA": {
    "type": "string",
    "description": "Type of person, e.g., 'PF' (Persona Física/Individual)."
  },
  "TIPO_VEHICULO_CAMIONETAS": {
    "type": "string",
    "description": "Indicates if the vehicle is a pickup truck."
  },
  "TIPO_VEHICULO_CARROS": {
    "type": "string",
    "description": "Indicates if the vehicle is a car."
  },
  "TIPO_VEHICULO_JEEPETAS": {
    "type": "string",
    "description": "Indicates if the vehicle is an SUV."
  },
  "TRABAJA_ACTUALMENTE": {
    "type": "string",
    "description": "Indicates if the applicant is currently working, e.g., 'No'."
  },
  "TRABAJA_CONYUGE": {
    "type": "string",
    "description": "Indicates if the spouse is currently working."
  },
  "VALOR_COBRAR": {
    "type": ["string", "null"],
    "description": "Value of accounts receivable, or null if not applicable."
  },
  "VALOR_INMUBLES": {
    "type": ["string", "null"],
    "description": "Value of real estate owned, or null if not applicable."
  },
  "VALOR_INVERSIONES": {
    "type": ["string", "null"],
    "description": "Value of investments, or null if not applicable."
  },
  "VALOR_MOBILIARIO": {
    "type": ["string", "null"],
    "description": "Value of furniture and fixtures, or null if not applicable."
  },
  "VALOR_OTROS_COMPROMISOS_DE_PAGO": {
    "type": ["string", "null"],
    "description": "Value of other financial commitments/payments, or null if not applicable."
  },
  "VALOR_VEHICULO_PROPIO": {
    "type": ["string", "null"],
    "description": "Value of a vehicle already owned by the applicant, or null if not applicable."
  },
  "VEHICULO_NUEVO_USADO": {
    "type": "string",
    "description": "Condition of the vehicle (new or used), e.g., 'Usado' (Used)."
  },
  "VENTAS_MENSUALES": {
    "type": "string",
    "description": "Monthly sales, likely for self-employed individuals."
  }
}
'''

# Title and Description
st.title("📄 PDF Page OCR Processor")
st.markdown("Upload PDF files to extract text from each page using Mistral OCR.")

# --- API Key Input Section ---
if "mistral_api_key" not in st.session_state or "openai_api_key" not in st.session_state:
    st.markdown("### 🔑 Enter Your API Keys")
    mistral_key = st.text_input("Mistral API Key", type="password", help="Enter your Mistral API key here.")
    openai_key = st.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key here.")
    if st.button("Submit API Keys"):
        if not mistral_key.strip() or not openai_key.strip():
            st.error("Both API keys are required.")
        else:
            st.session_state.mistral_api_key = mistral_key
            st.session_state.openai_api_key = openai_key
            st.success("API keys set successfully. You can now upload PDFs.")
            st.rerun()
else:
    st.markdown("### 🔐 API Keys Set")
    st.success("You are ready to upload PDFs.")
    if st.button("Change API Keys"):
        del st.session_state.mistral_api_key
        del st.session_state.openai_api_key
        st.rerun()

    # --- PDF Upload Section ---
    uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        st.success(f"Uploaded {len(uploaded_files)} PDFs. Processing each file...")
        
        # Initialize session state for storing OCR data
        if 'pdf_ocr_data' not in st.session_state:
            st.session_state.pdf_ocr_data = {}
        
        # Initialize combined OCR text
        if 'combined_ocr_text' not in st.session_state:
            st.session_state.combined_ocr_text = ""
        
        # Progress tracking
        processed_files = 0
        
        # Process each file
        for uploaded_file in uploaded_files:
            st.markdown(f"### 📁 File: {uploaded_file.name}")
            
            # Check if we have OCR data for this file
            file_data = st.session_state.pdf_ocr_data.get(uploaded_file.name, {})
            
            try:
                # Only process if we haven't already stored OCR data
                if 'full_ocr_text' not in file_data:
                    # Convert PDF to list of PIL images
                    with st.spinner(f"Converting {uploaded_file.name} to images..."):
                        pdf_bytes = uploaded_file.getvalue()
                        pages = convert_from_bytes(pdf_bytes, dpi=200)  # Higher DPI for better OCR quality

                    # Retrieve API keys
                    mistral_api_key = st.session_state.mistral_api_key
                    mistral_client = Mistral(api_key=mistral_api_key)

                    st.success(f"Found {len(pages)} pages in {uploaded_file.name}. Starting OCR...")

                    full_ocr_text = ""
                    
                    # Process each page
                    for i, page_image in enumerate(pages):
                        with st.spinner(f"Processing Page {i+1}/{len(pages)}..."):
                            # Save image to temporary file
                            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
                                page_image.save(tmpfile.name, format="JPEG")
                                tmpfile_path = tmpfile.name

                            # Encode image to base64
                            with open(tmpfile_path, "rb") as image_file:
                                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

                            # Clean up temp file
                            os.unlink(tmpfile_path)

                            # Prepare image URL with base64 data
                            image_data_url = f"data:image/jpeg;base64,{base64_image}"

                            # Send request to Mistral OCR
                            ocr_response = mistral_client.ocr.process(
                                model="mistral-ocr-latest",
                                document={
                                    "type": "image_url",
                                    "image_url": image_data_url
                                }
                            )

                            # Extract text from response
                            ocr_text = ""
                            try:
                                # Get pages from response
                                pages_list = getattr(ocr_response, "pages", [])
                                
                                # Extract markdown from each page
                                page_texts = []
                                for page in pages_list:
                                    if hasattr(page, "markdown"):
                                        page_texts.append(page.markdown)
                                
                                ocr_text = "\n\n---\n\n".join(page_texts)  # Combine pages with separators
                            except Exception as e:
                                ocr_text = f"Error extracting text: {str(e)}"
                            
                            # Add page text to full document text
                            full_ocr_text += f"\n\n--- PAGE {i+1} ---\n\n{ocr_text}"
                    
                    # Store OCR data in session state
                    file_data['full_ocr_text'] = full_ocr_text
                    st.session_state.pdf_ocr_data[uploaded_file.name] = file_data
                    
                    # Add to combined OCR text
                    st.session_state.combined_ocr_text += f"\n\n=== FILE: {uploaded_file.name} ===\n\n{full_ocr_text}"
                    
                    st.success(f"OCR completed for {uploaded_file.name}!")
                    processed_files += 1
                else:
                    st.info("OCR text already available for this file")
                    processed_files += 1
                
                # Show OCR results for this file
                with st.expander(f"View OCR Text for {uploaded_file.name}"):
                    st.text_area("", 
                                 value=st.session_state.pdf_ocr_data[uploaded_file.name]['full_ocr_text'], 
                                 height=300,
                                 key=f"ocr_{uploaded_file.name}")
                
                st.markdown("---")

            except Exception as e:
                error_msg = str(e).lower()
                if "poppler" in error_msg:
                    st.error("Error: poppler not found. Please install poppler and add it to PATH.")
                    st.markdown("Download Poppler from [here](https://github.com/oschwartz106/poppler-windows/releases/ ).")
                elif "invalid api" in error_msg or "unauthorized" in error_msg:
                    st.error("Authentication failed: Invalid or missing API key.")
                elif "timeout" in error_msg:
                    st.error("Request timed out. Please try again later.")
                else:
                    st.error(f"Unexpected error processing {uploaded_file.name}: {e}")
        
        # Show combined OCR text and classification option
        if st.session_state.combined_ocr_text and processed_files == len(uploaded_files):
            st.markdown("## 🔗 Combined OCR Text")
            with st.expander("View Combined OCR Text"):
                st.text_area("", 
                             value=st.session_state.combined_ocr_text, 
                             height=400,
                             key="combined_ocr")
            
            # New classification button for O1 model
            st.markdown("## 🚀 Combined Classification")
            if st.button("Classify All with O1 Model"):
                with st.spinner("Classifying combined text with O1 model..."):
                    try:
                        classification_result = classification.classify_with_o1_model(
                            st.session_state.combined_ocr_text,
                            st.session_state.openai_api_key,
                            CLASSIFICATION_JSON_STRUCTURE
                        )
                        
                        if classification_result:
                            st.markdown("### ✅ Classification Result")
                            st.json(classification_result)
                            
                            # Add download button for JSON
                            json_str = json.dumps(classification_result, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="Download JSON",
                                data=json_str,
                                file_name="classification_result.json",
                                mime="application/json"
                            )
                        else:
                            st.error("Classification returned no results")
                    except Exception as e:
                        st.error(f"Classification failed: {str(e)}")
