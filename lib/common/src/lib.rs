mod proto {
    tonic::include_proto!("wallet");
}

pub use proto::*;

mod config;
mod error;

pub use config::{ProcessConfig, ServiceConfig};
pub use error::{ProcessError, ServiceError};
