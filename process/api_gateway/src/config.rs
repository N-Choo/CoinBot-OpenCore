use actix_cors::Cors;
use actix_web::http;
use common::{ProcessConfig, ProcessError};

#[derive(Debug, Clone)]
pub struct AppConfig {
    pub ip: String,
    pub port: u16,
    pub n_worker: usize,
    pub n_queue: u32,
    pub db_url: String,
    pub session_redis_url: String,
    pub nonce_redis_url: String,
    pub api_key: String,
    pub api_secret: String,
    pub api_passphrase: String,
    pub grpc_deposit: String,
}

impl AppConfig {
    pub fn from_env() -> Result<Self, ProcessError> {
        let cfg = ProcessConfig::new("api_gateway");
        let redis_base = cfg.get_or_str("REDIS_URL", "redis://127.0.0.1:6379");

        Ok(Self {
            ip: cfg.get_or_str("HOST", "127.0.0.1"),
            port: cfg.get_or("TS_PORT", 3000u16),
            n_worker: cfg.get_or("N_WORKER", 4usize),
            n_queue: 100,
            db_url: cfg.get("DATABASE_URL")?,
            session_redis_url: format!("{}/0", redis_base.trim_end_matches('/')),
            nonce_redis_url: format!("{}/1", redis_base.trim_end_matches('/')),
            api_key: cfg.get("API_KEY")?,
            api_secret: cfg.get("API_SECRET")?,
            api_passphrase: cfg.get("API_PASSPHRASE")?,
            grpc_deposit: cfg.get_or_str("GRPC_DEPOSIT_ENDPOINT", "http://127.0.0.1:50051"),
        })
    }

    /// Helper method to build a fresh Cors instance for each worker
    pub fn get_cors(&self) -> Cors {
        Cors::default()
            .allowed_origin("http://127.0.0.1:5173") // Use the IP/Port Axios is calling from
            .allowed_methods(vec!["GET", "POST"])
            .allowed_headers(vec![
                http::header::AUTHORIZATION,
                http::header::ACCEPT,
                http::header::CONTENT_TYPE,
            ])
            .supports_credentials()
            .max_age(3600)
    }
}
