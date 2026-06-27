use redis::{AsyncCommands, Client};

#[derive(Clone)]
pub struct Cache {
    conn: redis::aio::MultiplexedConnection,
}

impl Cache {
    pub async fn new(redis_url: &str) -> Result<Self, redis::RedisError> {
        let client = Client::open(redis_url)?;
        let conn = client.get_multiplexed_async_connection().await?;
        Ok(Self { conn })
    }

    pub async fn get(&self, key: &str) -> Option<String> {
        let mut conn = self.conn.clone();
        conn.get(key).await.ok()
    }

    pub async fn set(&self, key: &str, value: &str, ttl_secs: u64) {
        let mut conn = self.conn.clone();
        if let Err(e) = conn.set_ex::<&str, &str, ()>(key, value, ttl_secs).await {
            log::error!("Redis set failed: {e}");
        }
    }

    pub async fn del(&self, key: &str) {
        let mut conn = self.conn.clone();
        if let Err(e) = conn.del::<&str, ()>(key).await {
            log::error!("Redis del failed: {e}");
        }
    }
}
