import streamlit as st
import pandas as pd
import json
import io
import xml.etree.ElementTree as ET

# Custom CSS for styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: white;
    }

    .header-title {
        font-size: 32px;
        color: white;  /* White text for header */
        background-color: #00539b;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }

    .stButton>button {
        background-color: #00539b;  /* Blue background */
        color: white;  /* White text */
        border-radius: 4px;
        border: none;
        padding: 10px;
        font-size: 16px;
        margin: 10px 0px;
    }

    .stTextInput>div>div>input {
        background-color: white;
        color: #333333;
        border: 2px solid #00539b;
        padding: 5px;
    }

    .center-header {
        text-align: center;
        font-size: 20px;
        color: #333333;
        margin: 20px 0;
    }

    /* Stretch table dynamically to fit the white block */
    .stDataFrame {
        max-width: 100%;  /* Allow table to stretch out fully */
        overflow-x: auto;  /* Allow horizontal scroll if needed */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Set header with the title
st.markdown(
    """
    <div class="header-title">
        <h1>Import Wizard</h1>  <!-- Simplified header name -->
    </div>
    """,
    unsafe_allow_html=True
)

# Step 1: File Upload
uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt", "xlsx", "xml"])

# Function to load a mapping template
def load_mapping_template(template_file):
    if template_file:
        return json.load(template_file)
    return {}

# Function to parse XML file using ElementTree
def parse_xml(file):
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        data = []

        # Iterate through elements and build a dictionary for each element
        for child in root:
            row = {elem.tag: elem.text for elem in child}
            data.append(row)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        return df

    except ET.ParseError as e:
        st.error(f"Error parsing XML file: {e}")
        return pd.DataFrame()

# Sidebar for template options
with st.sidebar:
    st.header("Template Options")
    
    # Load a previously saved template
    template_file = st.file_uploader("Load a Mapping Template", type=["json"])
    if template_file:
        column_mapping_template = load_mapping_template(template_file)
        st.success("Template loaded successfully.")
    else:
        column_mapping_template = {}

if uploaded_file is not None:
    try:
        st.write("**File uploaded successfully. Processing...**")

        # Read the file based on its type
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.txt'):
            df = pd.read_csv(uploaded_file, delimiter='\t')  # Assuming tab-delimited text files
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.xml'):
            try:
                # Try using pandas to read the XML
                df = pd.read_xml(uploaded_file)
            except Exception:
                # Fallback to manual parsing using ElementTree
                df = parse_xml(uploaded_file)

        st.write("**File processed. Displaying preview...**")

        # Step 3: Hide/Unhide functionality
        if 'show_preview' not in st.session_state:
            st.session_state.show_preview = True

        # Toggle button for preview
        if st.session_state.show_preview:
            if st.button("Hide Preview"):
                st.session_state.show_preview = False
        else:
            if st.button("Unhide Preview"):
                st.session_state.show_preview = True

        # Centered layout with "Original File Preview"
        col1, col2, col3 = st.columns([1, 2, 1])  # Three columns with middle one wider

        # Display original file preview in the center column if preview is not hidden
        if st.session_state.show_preview:
            with col2:
                st.write("### Original File Preview")
                st.dataframe(df.head())  # Display the first few rows of the file

        # Dropdown to select desired format
        file_format = st.selectbox("Select the desired output format", ["Personalfil 2.0", "Personalfil 1.9"])

        # Pre-defined output column names for each format
        output_columns = {
            "Personalfil 2.0": ["ClientID", "Org.namn", "Orgnr", "Personnr", "AnställningsID", "Efternamn", "Förnamn", "E-postadress", "Utdelningsadress", "Postnr", "c/o-adress", "Land", "Telefonnr", "Mobilnr", "Pensionsmedförande lön", "Datum PMF-lön", "Kontant utbetald bruttolön", "Datum KUB-lön", "Lön/månad", "Alternativ årslön", "Datum alternativ årslön", "Anställningsdatum", "Anst.datum koncern", "Slutdatum anställning", "Avgors", "Frånvarotyp", "Frånvarodatum", "Antal dagar frånvaro", "Sjukkod", "Sjukdatum", "Sjuk antal dagar", "Tjänstepensionskod", "Anställningsgrad", "Enhetsnummer", "Kostnadsställe", "Anställningstyp", "Kategori", "Mpremie", "Arbetsoförmåga", "Frånvarodatum_2"],
            "Personalfil 1.9": ["Org.namn", "Orgnr", "Personnr", "AnställningsID", "Efternamn", "Förnamn", "E-postadress", "Utdelningsadress", "Postnr", "Postort", "Telefonnr", "Mobilnr", "Pensionsmedförande lön", "Datum PMF-lön", "Kontant utbetald bruttolön", "Datum KUB-lön", "Alternativ årslön", "Datum alternativ årslön", "Anställningsdatum", "Slutdatum anställning", "Frånvarotyp", "Frånvarodatum", "Tjänstepensionskod", "Anställningsgrad", "Enhetsnummer", "Kostnadsställe", "Anställningstyp"]
        }

        selected_columns = output_columns[file_format]  # Select columns based on user choice
        mapped_columns = {}

        # Center the header for mapping
        st.markdown("<div class='center-header'>Map Columns to Personalfil 1.9 or 2.0</div>", unsafe_allow_html=True)

        # Dynamic layout for mapping columns
        col_mapping_layout = st.columns(2)
        total_columns = len(selected_columns)

        # Create select boxes dynamically
        for i, output_col in enumerate(selected_columns):
            column_number = i % 10
            col = col_mapping_layout[column_number // 5]  # Dynamically choose left or right side to avoid scrolling
            with col:
                # Assign a unique key for each select box
                mapped_columns[output_col] = st.selectbox(
                    f"Map to '{output_col}'",
                    options=[None] + df.columns.tolist(),
                    index=df.columns.tolist().index(column_mapping_template.get(output_col, None)) + 1 if column_mapping_template.get(output_col) in df.columns else 0,
                    key=f"selectbox_{output_col}_{i}"  # Ensure unique key by appending index
                )

        # Filter out unmapped columns
        mapped_df = pd.DataFrame()
        for output_col, input_col in mapped_columns.items():
            if input_col:
                mapped_df[output_col] = df[input_col]
            else:
                mapped_df[output_col] = None  # Empty column if not mapped

        # Center the "Mapped File Preview" header and table
        st.markdown("<div class='center-header'>Mapped File Preview</div>", unsafe_allow_html=True)
        st.dataframe(mapped_df.head())

        # Instructional text and save mapping template functionality
        st.write("If you wish to save the mapped columns for later use, please click the button below.")

        if st.button("Save Mapping Template"):
            template_name = st.text_input("Enter a name for your template", value="mapping_template.json")
            if template_name:
                # Save the template to JSON
                json_str = json.dumps(mapped_columns)
                st.download_button(
                    label="Download Template as JSON",
                    data=json_str,
                    file_name=template_name,
                    mime="application/json"
                )
                st.success("Template saved successfully.")

        # Generate Downloadable Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            mapped_df.to_excel(writer, index=False, sheet_name='MappedData')
        output.seek(0)

        # Provide a download link for the mapped file
        st.download_button(
            label="Download Mapped File as Excel",
            data=output,
            file_name="mapped_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error processing the file: {e}")

else:
    st.info("Please upload a file to continue.")
