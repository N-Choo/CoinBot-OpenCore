#[derive(Debug, thiserror::Error)]
pub enum ServiceError {
    #[error("not found: {0}")]
    NotFound(String),
    #[error("insufficient funds")]
    InsufficientFunds,
    #[error("invalid request: {0}")]
    InvalidRequest(String),
    #[error("internal: {0}")]
    Internal(String),
}

#[derive(Debug, thiserror::Error)]
pub enum ProcessError {
    #[error("missing environment variable: {0}")]
    MissingEnv(String),
    #[error("invalid configuration: {0}")]
    InvalidConfig(String),
    #[error("database error: {0}")]
    Database(String),
    #[error("network error: {0}")]
    Network(String),
    #[error("{0}")]
    Internal(String),
}

impl From<sqlx::Error> for ProcessError {
    fn from(e: sqlx::Error) -> Self {
        ProcessError::Database(e.to_string())
    }
}

impl From<sqlx::migrate::MigrateError> for ProcessError {
    fn from(e: sqlx::migrate::MigrateError) -> Self {
        ProcessError::Database(format!("migration error: {e}"))
    }
}
impl From<tonic::transport::Error> for ProcessError {
    fn from(e: tonic::transport::Error) -> Self {
        ProcessError::Network(format!("gRPC transport error: {e}"))
    }
}

impl From<std::net::AddrParseError> for ProcessError {
    fn from(e: std::net::AddrParseError) -> Self {
        ProcessError::InvalidConfig(format!("address parse error: {e}"))
    }
}

impl From<std::io::Error> for ProcessError {
    fn from(e: std::io::Error) -> Self {
        ProcessError::Network(format!("I/O error: {e}"))
    }
}
