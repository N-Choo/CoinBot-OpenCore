use share::cache::Cache;

#[derive(Clone)]
pub struct SessionCache {
    cache: Cache,
}

#[derive(Clone)]
pub struct NonceCache {
    cache: Cache,
}

impl SessionCache {
    const TTL: u64 = 3600;

    pub async fn new(redis_url: &str) -> Result<Self, redis::RedisError> {
        Ok(Self {
            cache: Cache::new(redis_url).await?,
        })
    }
    pub async fn get(&self, k: &str) -> Option<String> {
        self.cache.get(k).await
    }
    pub async fn insert(&self, k: String, v: String) {
        self.cache.set(&k, &v, Self::TTL).await
    }
    pub async fn invalidate(&self, k: &str) {
        self.cache.del(k).await
    }
}

impl NonceCache {
    const TTL: u64 = 300;

    pub async fn new(redis_url: &str) -> Result<Self, redis::RedisError> {
        Ok(Self {
            cache: Cache::new(redis_url).await?,
        })
    }
    pub async fn get(&self, k: &str) -> Option<String> {
        self.cache.get(k).await
    }
    pub async fn insert(&self, k: String, v: String) {
        self.cache.set(&k, &v, Self::TTL).await
    }
    pub async fn invalidate(&self, k: &str) {
        self.cache.del(k).await
    }
}
