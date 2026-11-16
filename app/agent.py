
import os
import re

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class SQLAnalyticsAgent:

    def __init__(self, database_url=None):

        self.database_url = (
            database_url or
            os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
        )

        self.engine = create_engine(self.database_url)

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing from .env"
            )

        self.client = Groq(api_key=api_key)

        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    def get_schema(self):

        inspector = inspect(self.engine)

        schema = []

        for table_name in inspector.get_table_names():

            columns = inspector.get_columns(table_name)

            column_names = [
                f"{column['name']} ({column['type']})"
                for column in columns
            ]

            schema.append(
                f"Table: {table_name}\n"
                f"Columns: {', '.join(column_names)}"
            )

        return "\n\n".join(schema)

    def generate_sql(self, question):

        schema = self.get_schema()

        if not schema:
            raise ValueError(
                "No tables found in the database."
            )

        prompt = f"""
You are an expert SQL analytics assistant.

Database schema:
{schema}

User question:
{question}

Rules:
1. Generate only one SQL SELECT query.
2. Never generate INSERT, UPDATE, DELETE or DROP.
3. Never modify database structure.
4. Use only tables and columns in the schema.
5. Return SQL only, without markdown.
6. Use LIMIT 100 for large result sets.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You generate safe read-only SQL queries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        sql_query = response.choices[0].message.content.strip()

        sql_query = re.sub(
            r"^```(?:sql)?\s*|\s*```$",
            "",
            sql_query,
            flags=re.IGNORECASE
        ).strip()

        return sql_query

    def validate_sql(self, sql_query):

        query = sql_query.strip()

        if query.endswith(";"):
            query = query[:-1].strip()

        if ";" in query:
            raise ValueError("Multiple SQL statements are not allowed.")

        if not re.match(
            r"^(SELECT|WITH)\b",
            query,
            re.IGNORECASE
        ):
            raise ValueError("Only SELECT queries are allowed.")

        blocked = [
            "INSERT", "UPDATE", "DELETE", "DROP",
            "ALTER", "CREATE", "TRUNCATE",
            "REPLACE", "ATTACH", "DETACH",
            "PRAGMA", "GRANT", "REVOKE",
            "EXEC", "CALL"
        ]

        for keyword in blocked:

            if re.search(
                rf"\b{keyword}\b",
                query,
                re.IGNORECASE
            ):
                raise ValueError(
                    f"Unsafe SQL keyword detected: {keyword}"
                )

        return query

    def execute_sql(self, sql_query):

        safe_query = self.validate_sql(sql_query)

        with self.engine.connect() as connection:

            result = connection.execute(
                text(safe_query)
            )

            rows = result.fetchall()

            columns = list(result.keys())

            return pd.DataFrame(
                rows,
                columns=columns
            )

    def ask(self, question):

        sql_query = self.generate_sql(question)

        dataframe = self.execute_sql(sql_query)

        return {
            "question": question,
            "sql": sql_query,
            "data": dataframe,
            "rows": len(dataframe)
        }
