
import getpass
import pyodbc


SERVER = "tcp:127.0.0.1,1433"
DATABASE = "ColdChainDB"

LOGIN_NAME = "coldchain_agent_login"
USER_NAME = "coldchain_agent"

CONNECTION_OPTIONS = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "Connection Timeout=15;"
)


def get_admin_connection(database):
    password = getpass.getpass("SQL Server administrator password: ")

    connection_string = (
        CONNECTION_OPTIONS
        + f"DATABASE={database};"
        + "UID=sa;"
        + f"PWD={{{password}}};"
    )

    return pyodbc.connect(connection_string, autocommit=True)


def create_server_login(cursor):
    cursor.execute(
        "SELECT COUNT(*) FROM sys.server_principals WHERE name = ?",
        LOGIN_NAME
    )

    login_exists = cursor.fetchone()[0] > 0

    if login_exists:
        print("Server login already exists. Skipping creation.")
        return

    print("\nCreate a strong password for the AI agent SQL login.")
    print("Use at least 14 characters and save it securely.")

    password = getpass.getpass("New agent login password: ")
    confirmation = getpass.getpass("Confirm agent login password: ")

    if password != confirmation:
        raise ValueError("Passwords do not match.")

    if len(password) < 14:
        raise ValueError("Password must contain at least 14 characters.")

    escaped_password = password.replace("'", "''")

    sql = f"""
    CREATE LOGIN [{LOGIN_NAME}]
    WITH PASSWORD = N'{escaped_password}',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
    """

    cursor.execute(sql)

    print("Server login created successfully.")


def create_database_user():
    connection = get_admin_connection(DATABASE)

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            IF NOT EXISTS (
                SELECT 1
                FROM sys.database_principals
                WHERE name = ?
            )
            BEGIN
                CREATE USER [coldchain_agent]
                FOR LOGIN [coldchain_agent_login]
                WITH DEFAULT_SCHEMA = [agent_views];
            END;
            """,
            USER_NAME
        )

        cursor.execute(
            """
            GRANT SELECT
            ON SCHEMA::[agent_views]
            TO [coldchain_agent];
            """
        )

        print("Database user and permissions configured.")

    finally:
        connection.close()


def main():
    print("Connecting to SQL Server master database...")

    connection = get_admin_connection("master")

    try:
        cursor = connection.cursor()

        print("\nChecking AI agent server login...")
        create_server_login(cursor)

    finally:
        connection.close()

    print("\nConfiguring ColdChainDB permissions...")
    create_database_user()

    print("\n========== SECURITY SETUP ==========")
    print(f"Server login: {LOGIN_NAME}")
    print(f"Database user: {USER_NAME}")
    print("Granted: SELECT on agent_views schema")
    print("No broad database roles have been assigned.")
    print("Security setup completed.")


if __name__ == "__main__":
    main()
