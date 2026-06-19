use common::{ProcessConfig, ProcessError};

#[tokio::main]
async fn main() -> Result<(), ProcessError> {
    let cfg = ProcessConfig::new("trade_engine");
    cfg.get("API")?;

    println!("Hello, world!");
    Ok(())
}
