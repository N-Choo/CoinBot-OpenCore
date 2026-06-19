use serde::Deserialize;

use crate::error::ProcessError;

#[derive(Debug, Clone, Deserialize)]
pub struct ServiceConfig {
    pub grpc_host: String,
    pub grpc_port: u16,
    pub database_url: String,
    pub redis_url: String,
}

impl ServiceConfig {
    pub fn grpc_addr(&self) -> String {
        format!("{}:{}", self.grpc_host, self.grpc_port)
    }
}

/// Loads environment variables scoped to a process name prefix.
///
/// Checks `PREFIX_KEY` first, falls back to `KEY` so shared vars like
/// `DATABASE_URL` work without per-process duplication while per-process
/// overrides (e.g. `API_GATEWAY_DATABASE_URL`) are supported.
#[derive(Debug, Clone)]
pub struct ProcessConfig {
    prefix: String,
}

impl ProcessConfig {
    pub fn new(name: &str) -> Self {
        Self {
            prefix: name.to_uppercase(),
        }
    }

    /// Get a raw env var. Tries `PREFIX_KEY` then `KEY`.
    pub fn get(&self, key: &str) -> Result<String, ProcessError> {
        let prefixed = format!("{}_{}", self.prefix, key);

        match std::env::var(&prefixed) {
            Ok(val) => Ok(val),
            Err(_) => std::env::var(key).map_err(|_| {
                ProcessError::MissingEnv(format!("neither {} nor {} is set", prefixed, key))
            }),
        }
    }

    /// Get a parsed value with a default fallback.
    pub fn get_or<T: std::str::FromStr>(&self, key: &str, default: T) -> T {
        self.get(key)
            .ok()
            .and_then(|v| v.parse().ok())
            .unwrap_or(default)
    }

    /// Get a raw env var with a default string fallback.
    pub fn get_or_str(&self, key: &str, default: &str) -> String {
        self.get(key).unwrap_or_else(|_| default.to_string())
    }
}
