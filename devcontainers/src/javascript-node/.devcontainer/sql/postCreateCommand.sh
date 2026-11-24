#!/usr/bin/env bash
# Builds the Library SQL Database project and publishes it to the local Azure SQL Database container.
# Runs when the container is created, and from the "3. Publish SQL Database project" task.
set -euo pipefail

step="start"
onExit() {
    local rc=$?
    if [ "$rc" -ne 0 ]; then echo "postCreateCommand.sh failed during: $step (exit $rc)" >&2; fi
}
trap onExit EXIT
cd "$(dirname "$0")/../.."
: "${MSSQL_SA_PASSWORD:?is not set; it comes from .devcontainer/.env}"
export SQLCMDPASSWORD=$MSSQL_SA_PASSWORD

step="wait for Azure SQL Database at localhost,1433"
echo "==> $step"
for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if sqlcmd -S localhost -U sa -C -l 5 -b -d master -Q "SELECT 1" >/dev/null; then break; fi
    if [ "$attempt" -eq 10 ]; then exit 1; fi
    sleep 3
done

step="create database/Library if needed"
echo "==> $step"
# In Azure SQL Database, DB_ID(name) only identifies the current database.
sqlcmd -S localhost -U sa -C -l 5 -b -d master -Q "IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = N'Library') CREATE DATABASE [Library];"

step="build database/Library"
echo "==> $step"
dotnet build database/Library -nodeReuse:false

step="publish database/Library/bin/Debug/Library.dacpac to the Library database"
echo "==> $step"
sqlpackage /Action:Publish \
    /SourceFile:database/Library/bin/Debug/Library.dacpac \
    /TargetServerName:localhost /TargetDatabaseName:Library \
    /TargetUser:sa /TargetPassword:"$MSSQL_SA_PASSWORD" /TargetTrustServerCertificate:True
