mod wallet {
    tonic::include_proto!("wallet");
}

mod analyzer {
    tonic::include_proto!("analyzer");
}

pub use wallet::*;
pub use analyzer::*;

mod config;
mod error;

pub use config::{ProcessConfig, ServiceConfig};
pub use error::{ProcessError, ServiceError};
