use common::{ProcessConfig, ProcessError};
use share::{
    cache::Cache,
    db::{
        contracts::{self, Contract, ContractFilter, Status},
        user::User,
    },
};

mod app_config;
mod app_state;

use app_config::AppConfig;
use app_state::AppState;

#[tokio::main]
async fn main() -> Result<(), ProcessError> {
    dotenvy::dotenv().ok();
    share::logger::init_logger();

    let config = AppConfig::from_env()?;
    let app_state = AppState::new(&config).await?;

    let pool = app_state.db_pool;
    let cache = app_state.redis_cache;

    let tickers = ContractFilter::new()
        .with_status(Status::Active)
        .execute_tickers(&pool)
        .await?;
    let msg = serde_json::to_string(&tickers)?;

    loop {
        cache.publish("tickers:analyze", &msg).await;
    }
}
