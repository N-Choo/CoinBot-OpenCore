use common::{ProcessConfig, ProcessError};
use share::{
    cache::Cache,
    db::{
        contracts::{self, Contract, ContractFilter, Status},
        user::User,
    },
};

use log::{info, warn};
use sqlx::PgPool;

#[tokio::main]
async fn main() -> Result<(), ProcessError> {
    dotenvy::dotenv().ok();
    share::logger::init_logger();

    let cfg = ProcessConfig::new("trade_engine");
    let database_url = cfg.get("DATABASE_URL")?;
    let pool = sqlx::PgPool::connect(&database_url).await?;
    let redis_url = cfg.get("REDIS_URL")?;

    let tickers = ContractFilter::new()
        .with_status(Status::Active)
        .execute_tickers(&pool)
        .await?;

    let msg = serde_json::to_string(&tickers)?;
    let cache = Cache::new(&redis_url).await?;
    cache.publish("tickers:analyze", &msg).await;

    Ok(())
}
