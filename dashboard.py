import streamlit as st
import sqlite3
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Page Configuration
st.set_page_config(
    page_title="Medical Records Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 1rem;
        text-align: center;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stAlert {
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
    .entity-tag {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Load all data sources"""
    data = {}
    
    # Load JSON files
    json_files = {
        'patient_info': 'patient_info.json',
        'medical_data': 'medical_data.json',
        'ner_results': 'ner_results.json'
    }
    
    for key, filepath in json_files.items():
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data[key] = json.load(f)
        else:
            data[key] = None
    
    # Load raw text
    if os.path.exists('arztbrief.txt'):
        with open('arztbrief.txt', 'r', encoding='utf-8') as f:
            data['raw_text'] = f.read()
    else:
        data['raw_text'] = None
    
    # Load database
    if os.path.exists('medical_records.db'):
        conn = sqlite3.connect('medical_records.db')
        data['db_conn'] = conn
        data['patients'] = pd.read_sql_query("SELECT * FROM patients", conn)
        data['documents'] = pd.read_sql_query("SELECT * FROM documents", conn)
        data['entities'] = pd.read_sql_query("SELECT * FROM entities", conn)
    else:
        data['db_conn'] = None
        data['patients'] = pd.DataFrame()
        data['documents'] = pd.DataFrame()
        data['entities'] = pd.DataFrame()
    
    return data

def render_sidebar(data):
    """Render sidebar with navigation and info"""
    st.sidebar.image("https://img.icons8.com/color/96/healthcare.png", width=80)
    st.sidebar.title("🏥 Medical Dashboard")
    
    menu_options = ["Overview", "Patient Details", "Medical Analysis", "NER Entities", "Database Stats", "Raw Document"]
    selection = st.sidebar.radio("Navigation", menu_options)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Quick Stats")
    
    if not data['patients'].empty:
        st.sidebar.metric("Total Patients", len(data['patients']))
        st.sidebar.metric("Total Documents", len(data['documents']))
        st.sidebar.metric("Total Entities", len(data['entities']))
    else:
        st.sidebar.warning("No data loaded yet. Run the pipeline first.")
    
    st.sidebar.markdown("---")
    st.sidebar.info(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    return selection

def render_overview(data):
    """Render overview page"""
    st.markdown('<p class="main-header">🏥 Medical Records Overview</p>', unsafe_allow_html=True)
    
    if data['patients'].empty:
        st.error("⚠️ No data found! Please run `python run_pipeline.py` first to generate the data.")
        return
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Patients",
            value=len(data['patients']),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Medical Documents",
            value=len(data['documents']),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Extracted Entities",
            value=len(data['entities']),
            delta=None
        )
    
    with col4:
        # Count unique entity types
        if not data['entities'].empty:
            unique_types = data['entities']['entity_type'].nunique()
        else:
            unique_types = 0
        st.metric(
            label="Entity Types",
            value=unique_types,
            delta=None
        )
    
    st.markdown("---")
    
    # Two columns for charts
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📈 Entity Distribution by Type")
        
        if not data['entities'].empty:
            entity_counts = data['entities'].groupby('entity_type').size().reset_index(name='count')
            entity_counts = entity_counts.sort_values('count', ascending=True)
            
            fig = px.bar(
                entity_counts,
                x='count',
                y='entity_type',
                orientation='h',
                color='count',
                color_continuous_scale='Blues',
                labels={'count': 'Count', 'entity_type': 'Entity Type'}
            )
            fig.update_layout(height=400, showlegend=False, xaxis_title="Count", yaxis_title="Entity Type")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No entities available")
    
    with col_right:
        st.subheader("📊 Data Source Breakdown")
        
        if not data['entities'].empty:
            source_counts = data['entities'].groupby('source').size().reset_index(name='count')
            
            fig = px.pie(
                source_counts,
                values='count',
                names='source',
                color_discrete_sequence=['#667eea', '#764ba2'],
                hole=0.4
            )
            fig.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data available")
    
    # Recent documents table
    st.subheader("📄 Recent Documents")
    
    if not data['documents'].empty:
        docs_display = data['documents'].copy()
        if 'created_at' in docs_display.columns:
            docs_display['created_at'] = pd.to_datetime(docs_display['created_at']).dt.strftime('%Y-%m-%d %H:%M')
        
        display_cols = ['id', 'behandlungsdatum', 'arzt_name', 'created_at']
        available_cols = [col for col in display_cols if col in docs_display.columns]
        
        if available_cols:
            st.dataframe(
                docs_display[available_cols].tail(10),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("No documents available")

def render_patient_details(data):
    """Render patient details page"""
    st.markdown('<p class="main-header">👤 Patient Information</p>', unsafe_allow_html=True)
    
    if data['patient_info'] is None:
        st.error("⚠️ No patient information found. Run the pipeline first.")
        return
    
    patient = data['patient_info']
    
    # Patient info cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        st.markdown(f"""
        - **Name:** {patient.get('name', 'N/A')}
        - **Date of Birth:** {patient.get('geburtsdatum', 'N/A')}
        - **Address:** {patient.get('address', 'N/A')}
        """)
    
    with col2:
        st.subheader("Insurance Information")
        st.markdown(f"""
        - **Health Insurer:** {patient.get('krankenkasse', 'N/A')}
        - **Insurance Number:** {patient.get('versicherungsnummer', 'N/A')}
        """)
    
    st.markdown("---")
    
    # Treatment info
    if data['medical_data']:
        st.subheader("🩺 Treatment Information")
        med_data = data['medical_data']
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.info(f"**Treating Doctor:** {med_data.get('arzt_name', 'N/A')}")
        
        with col_b:
            st.info(f"**Treatment Date:** {med_data.get('behandlungsdatum', 'N/A')}")

def render_medical_analysis(data):
    """Render medical analysis page"""
    st.markdown('<p class="main-header">🔬 Medical Analysis</p>', unsafe_allow_html=True)
    
    if data['medical_data'] is None:
        st.error("⚠️ No medical data found. Run the pipeline first.")
        return
    
    med_data = data['medical_data']
    
    # Diagnoses Section
    st.subheader("📋 Diagnoses")
    
    if 'diagnosen' in med_data and med_data['diagnosen']:
        diag_df = pd.DataFrame(med_data['diagnosen'])
        
        if not diag_df.empty:
            # Create a styled table
            st.dataframe(
                diag_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "bezeichnung": st.column_config.TextColumn("Diagnosis", width="medium"),
                    "icd10": st.column_config.TextColumn("ICD-10 Code", width="small")
                }
            )
            
            # ICD-10 code visualization
            if 'icd10' in diag_df.columns:
                st.markdown("**ICD-10 Code Distribution:**")
                icd_counts = diag_df['icd10'].value_counts().reset_index()
                icd_counts.columns = ['ICD-10', 'Count']
                
                fig = px.bar(icd_counts, x='ICD-10', y='Count', color='Count', color_continuous_scale='Reds')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No diagnoses extracted")
    
    st.markdown("---")
    
    # Medications Section
    st.subheader("💊 Medications")
    
    if 'medikamente' in med_data and med_data['medikamente']:
        med_df = pd.DataFrame(med_data['medikamente'])
        
        if not med_df.empty:
            st.dataframe(
                med_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name": st.column_config.TextColumn("Medication", width="medium"),
                    "dosierung": st.column_config.TextColumn("Dosage", width="small"),
                    "frequenz": st.column_config.TextColumn("Frequency", width="small")
                }
            )
    else:
        st.info("No medications extracted")
    
    st.markdown("---")
    
    # Symptoms and Recommendations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤒 Symptoms")
        if 'symptome' in med_data and med_data['symptome']:
            for symptom in med_data['symptome']:
                st.markdown(f"- {symptom}")
        else:
            st.info("No symptoms extracted")
    
    with col2:
        st.subheader("✅ Recommendations")
        if 'empfehlungen' in med_data and med_data['empfehlungen']:
            for rec in med_data['empfehlungen']:
                st.markdown(f"- {rec}")
        else:
            st.info("No recommendations extracted")
    
    # Summary
    if 'zusammenfassung' in med_data and med_data['zusammenfassung']:
        st.markdown("---")
        st.subheader("📝 AI Summary")
        st.info(med_data['zusammenfassung'])

def render_ner_entities(data):
    """Render NER entities page"""
    st.markdown('<p class="main-header">🏷️ Named Entity Recognition Results</p>', unsafe_allow_html=True)
    
    if data['ner_results'] is None or len(data['ner_results']) == 0:
        st.error("⚠️ No NER results found. Run the pipeline first.")
        return
    
    ner_data = data['ner_results']
    ner_df = pd.DataFrame(ner_data)
    
    # Summary stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Entities", len(ner_df))
    
    with col2:
        unique_labels = ner_df['entity_group'].nunique() if 'entity_group' in ner_df.columns else 0
        st.metric("Unique Labels", unique_labels)
    
    with col3:
        avg_confidence = ner_df['score'].mean() if 'score' in ner_df.columns else 0
        st.metric("Avg Confidence", f"{avg_confidence:.3f}")
    
    st.markdown("---")
    
    # Entity distribution chart
    st.subheader("📊 Entity Distribution by Label")
    
    if 'entity_group' in ner_df.columns:
        label_counts = ner_df['entity_group'].value_counts().reset_index()
        label_counts.columns = ['Label', 'Count']
        
        fig = px.bar(label_counts, x='Label', y='Count', color='Count', color_continuous_scale='Viridis')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Detailed table
    st.subheader("📋 All Extracted Entities")
    
    display_cols = ['word', 'entity_group', 'score', 'start', 'end']
    available_cols = [col for col in display_cols if col in ner_df.columns]
    
    if available_cols:
        # Format score column
        if 'score' in ner_df.columns:
            ner_df['score'] = ner_df['score'].round(4)
        
        st.dataframe(
            ner_df[available_cols],
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    # Filter by entity type
    st.markdown("---")
    st.subheader("🔍 Filter by Entity Type")
    
    if 'entity_group' in ner_df.columns:
        selected_type = st.selectbox(
            "Select Entity Type",
            options=sorted(ner_df['entity_group'].unique())
        )
        
        filtered_df = ner_df[ner_df['entity_group'] == selected_type]
        st.write(f"**Found {len(filtered_df)} entities of type '{selected_type}'**")
        
        for _, row in filtered_df.iterrows():
            st.markdown(f"- **{row['word']}** (confidence: {row['score']:.4f})")

def render_database_stats(data):
    """Render database statistics page"""
    st.markdown('<p class="main-header">🗄️ Database Statistics</p>', unsafe_allow_html=True)
    
    if data['db_conn'] is None:
        st.error("⚠️ Database not found. Run the pipeline first.")
        return
    
    conn = data['db_conn']
    
    # Table sizes
    st.subheader("📊 Table Sizes")
    
    tables = ['patients', 'documents', 'entities']
    table_sizes = []
    
    for table in tables:
        count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)['count'][0]
        table_sizes.append({'Table': table.capitalize(), 'Rows': count})
    
    table_df = pd.DataFrame(table_sizes)
    
    fig = px.bar(table_df, x='Table', y='Rows', color='Rows', color_continuous_scale='Teal')
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Entity breakdown by source
    st.subheader("📈 Entities by Source")
    
    if not data['entities'].empty:
        source_breakdown = data['entities'].groupby(['source', 'entity_type']).size().reset_index(name='count')
        
        fig = px.sunburst(
            source_breakdown,
            path=['source', 'entity_type'],
            values='count',
            color='count',
            color_continuous_scale='RdYlBu'
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Sample data from each table
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Patients Preview")
        st.dataframe(data['patients'].head(5), use_container_width=True, hide_index=True)
    
    with col2:
        st.subheader("Documents Preview")
        docs_preview = data['documents'].copy()
        if 'created_at' in docs_preview.columns:
            docs_preview['created_at'] = pd.to_datetime(docs_preview['created_at']).dt.strftime('%Y-%m-%d')
        st.dataframe(docs_preview.head(5), use_container_width=True, hide_index=True)
    
    with col3:
        st.subheader("Entities Preview")
        st.dataframe(data['entities'].head(5), use_container_width=True, hide_index=True)

def render_raw_document(data):
    """Render raw document view"""
    st.markdown('<p class="main-header">📄 Original Document</p>', unsafe_allow_html=True)
    
    if data['raw_text'] is None:
        st.error("⚠️ Raw document not found. Run the pipeline first.")
        return
    
    st.subheader("Arztbrief (Doctor's Letter)")
    
    # Display in a code block for better formatting
    st.code(data['raw_text'], language="text")
    
    # Download button
    st.download_button(
        label="📥 Download Original Document",
        data=data['raw_text'],
        file_name="arztbrief.txt",
        mime="text/plain"
    )

def main():
    # Load all data
    data = load_data()
    
    # Render sidebar and get selection
    selection = render_sidebar(data)
    
    # Render main content based on selection
    if selection == "Overview":
        render_overview(data)
    elif selection == "Patient Details":
        render_patient_details(data)
    elif selection == "Medical Analysis":
        render_medical_analysis(data)
    elif selection == "NER Entities":
        render_ner_entities(data)
    elif selection == "Database Stats":
        render_database_stats(data)
    elif selection == "Raw Document":
        render_raw_document(data)
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <small>Medical Records Dashboard | Built with Streamlit | Data extracted via NLP Pipeline</small>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
