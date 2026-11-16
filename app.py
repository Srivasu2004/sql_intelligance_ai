
import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

from sqlalchemy import create_engine
from dotenv import load_dotenv

from app.agent import SQLAnalyticsAgent

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="SQL Intelligence Agent",
    page_icon="📊",
    layout="wide"
)

# Application title
st.title("📊 SQL Intelligence Agent")

st.caption(
    "Ask questions about your data using natural language and AI."
)

# Database configuration
database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///./analytics.db"
)

# Create database engine
engine = create_engine(database_url)

# Sidebar
st.sidebar.header("📁 Database")

uploaded_file = st.sidebar.file_uploader(
    "Upload your CSV dataset",
    type=["csv"]
)

# CSV upload functionality
if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file)

        # Generate valid SQL table name
        table_name = re.sub(
            r"[^a-zA-Z0-9_]",
            "_",
            uploaded_file.name.rsplit(".", 1)[0]
        )

        if not table_name:
            table_name = "uploaded_data"

        # Save CSV data into database
        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False
        )

        st.sidebar.success(
            f"Successfully uploaded {len(df)} rows!"
        )

        st.session_state["uploaded_table"] = table_name

        st.sidebar.write(
            f"**Table Name:** {table_name}"
        )

        st.sidebar.write(
            f"**Total Columns:** {len(df.columns)}"
        )

    except Exception as error:

        st.sidebar.error(
            f"CSV Upload Error: {error}"
        )


# Main interface
st.subheader("💬 Ask Your Data")

question = st.text_area(
    "Enter your analytics question",
    placeholder=(
        "Example: Show the top 10 products by sales."
    ),
    height=120
)

# Generate insights button
if st.button(
    "🚀 Generate Insights",
    type="primary",
    width="stretch"
):

    if not question.strip():

        st.warning(
            "Please enter an analytics question."
        )

    else:

        try:

            with st.spinner(
                "Analyzing your database..."
            ):

                # Initialize SQL Agent
                agent = SQLAnalyticsAgent(
                    database_url=database_url
                )

                # Generate SQL and execute query
                result = agent.ask(question)

            st.success(
                "Analysis completed successfully!"
            )

            # Generated SQL
            st.subheader("📝 Generated SQL")

            st.code(
                result["sql"],
                language="sql"
            )

            # Query results
            st.subheader("📊 Query Results")

            data = result["data"]

            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)

            if data.empty:

                st.info(
                    "No records found for your question."
                )

            else:

                # Display data
                st.dataframe(
                    data,
                    width="stretch"
                )

                # Total records
                st.metric(
                    label="Total Records",
                    value=result.get(
                        "rows",
                        len(data)
                    )
                )

                # Data visualization
                numeric_columns = data.select_dtypes(
                    include="number"
                ).columns.tolist()

                all_columns = data.columns.tolist()

                if numeric_columns and len(all_columns) >= 2:

                    st.subheader(
                        "📈 Data Visualization"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        chart_type = st.selectbox(
                            "Select Chart Type",
                            [
                                "Bar Chart",
                                "Line Chart",
                                "Scatter Plot"
                            ]
                        )

                    with col2:

                        x_column = st.selectbox(
                            "Select X-axis",
                            all_columns
                        )

                    y_column = st.selectbox(
                        "Select Y-axis",
                        numeric_columns
                    )

                    # Generate chart
                    if chart_type == "Bar Chart":

                        fig = px.bar(
                            data,
                            x=x_column,
                            y=y_column,
                            title="Analytics Bar Chart"
                        )

                    elif chart_type == "Line Chart":

                        fig = px.line(
                            data,
                            x=x_column,
                            y=y_column,
                            title="Analytics Line Chart"
                        )

                    else:

                        fig = px.scatter(
                            data,
                            x=x_column,
                            y=y_column,
                            title="Analytics Scatter Plot"
                        )

                    # Display chart
                    st.plotly_chart(
                        fig,
                        width="stretch"
                    )

                else:

                    st.info(
                        "Charts require at least two columns "
                        "and one numeric column."
                    )

                # Download results
                csv_data = data.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    label="⬇️ Download Results CSV",
                    data=csv_data,
                    file_name="sql_analysis_results.csv",
                    mime="text/csv",
                    width="stretch"
                )

        except Exception as error:

            st.error(
                f"Error: {error}"
            )

            st.info(
                "Please check your Groq API key, "
                "database connection and SQL Agent configuration."
            )


# Footer
st.divider()

st.caption(
    "Built with Python, Streamlit, SQLAlchemy, "
    "Groq, Pandas and Plotly."
)
