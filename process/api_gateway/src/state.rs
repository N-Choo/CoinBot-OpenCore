use std::time::Duration;

use common::ProcessError;
use kucoin::client::rest::{Credentials, KuCoinClient};
use moka::future::Cache;
use sqlx::{PgPool, migrate};
use tonic::transport::Channel;

use crate::config::AppConfig;
use crate::handlers::user::auth::{NonceCache, SessionCache};

#[derive(Clone)]
pub struct AppState {
    pub db_pool: PgPool,
    pub nonce_cache: NonceCache,
    pub session_cache: SessionCache,
    pub kc_client: KuCoinClient,
    pub grpc_deposit: Channel,
}

impl AppState {
    pub async fn new(config: &AppConfig) -> Result<Self, ProcessError> {
        let db_pool = PgPool::connect(&config.db_url).await?;
        migrate!("../migrations").run(&db_pool).await?;

        let nonce_cache = NonceCache::new(
            Cache::builder()
                .max_capacity(250)
                .time_to_live(Duration::from_secs(60 * 5))
                .build(),
        );

        let session_cache = SessionCache::new(
            Cache::builder()
                .max_capacity(250)
                .time_to_live(Duration::from_secs(60 * 60))
                .build(),
        );

        let master_key =
            Credentials::new(&config.api_key, &config.api_secret, &config.api_passphrase);

        let kc_client = KuCoinClient::new(master_key);

        let grpc_deposit = Channel::from_shared(config.grpc_deposit.clone())
            .map_err(|e| ProcessError::InvalidConfig(format!("Invalid gRPC endpoint: {e}")))?
            .connect_lazy();

        Ok(Self {
            db_pool,
            nonce_cache,
            session_cache,
            kc_client,
            grpc_deposit,
        })
    }
}
