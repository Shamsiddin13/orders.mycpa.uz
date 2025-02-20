from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    # PostgreSQL Configuration
    POSTGRESQL_HOST: str = "45.153.71.38"
    POSTGRESQL_PORT: int = 5432
    POSTGRESQL_USER: str = "apimuser"
    POSTGRESQL_PASSWORD: str = "VM1A8YrCh0odg"
    POSTGRESQL_DBNAME: str = "apiCRM"

    # MySQL Configuration
    MYSQL_HOST: str = "176.124.209.127"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "mymgoods"
    MYSQL_PASSWORD: str = "shc\?$kN@G}<7O"
    MYSQL_DATABASE: str = "my_mgoods"

    @property
    def POSTGRESQL_URL(self) -> str:
        return f"postgresql://{self.POSTGRESQL_USER}:{self.POSTGRESQL_PASSWORD}@{self.POSTGRESQL_HOST}:{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DBNAME}"

    @property
    def MYSQL_URL(self) -> str:
        return f"mysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

settings = Settings()
