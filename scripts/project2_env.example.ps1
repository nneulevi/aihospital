# Copy this file to scripts/project2_env.local.ps1 and adjust for your local PostgreSQL.
# The local file is ignored by git.

$env:PROJECT2_DB_USERNAME = "postgres"
$env:PROJECT2_DB_PASSWORD = "postgres"
$env:PROJECT2_DB_URL = "jdbc:postgresql://localhost:5432/hospital?useSSL=false&serverTimezone=Asia/Shanghai&characterEncoding=utf8"
$env:PROJECT2_DB_DSN = "postgresql://postgres:postgres@localhost:5432/hospital"
