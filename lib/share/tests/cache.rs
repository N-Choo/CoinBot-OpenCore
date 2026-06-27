use share::cache::Cache;

fn redis_url() -> String {
    std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://127.0.0.1:6379".to_string())
}

async fn cache() -> Cache {
    Cache::new(&redis_url())
        .await
        .expect("Redis required — start it or set REDIS_URL")
}

#[tokio::test]
async fn test_set_get() {
    let cache = cache().await;

    let key = "test:set_get";
    cache.del(key).await;
    cache.set(key, "hello", 60).await;
    assert_eq!(cache.get(key).await.as_deref(), Some("hello"));
    cache.del(key).await;
}

#[tokio::test]
async fn test_get_missing() {
    let cache = cache().await;

    let key = "test:missing";
    cache.del(key).await;
    assert_eq!(cache.get(key).await, None);
}

#[tokio::test]
async fn test_ttl_expires() {
    let cache = cache().await;

    let key = "test:ttl";
    cache.del(key).await;
    cache.set(key, "goodbye", 1).await;
    assert_eq!(cache.get(key).await.as_deref(), Some("goodbye"));
    tokio::time::sleep(std::time::Duration::from_secs(2)).await;
    assert_eq!(cache.get(key).await, None);
}

#[tokio::test]
async fn test_set_overwrites() {
    let cache = cache().await;

    let key = "test:overwrite";
    cache.del(key).await;
    cache.set(key, "first", 60).await;
    cache.set(key, "second", 60).await;
    assert_eq!(cache.get(key).await.as_deref(), Some("second"));
    cache.del(key).await;
}

#[tokio::test]
async fn test_del_removes() {
    let cache = cache().await;

    let key = "test:del";
    cache.set(key, "delete_me", 60).await;
    assert_eq!(cache.get(key).await.as_deref(), Some("delete_me"));
    cache.del(key).await;
    assert_eq!(cache.get(key).await, None);
}

#[tokio::test]
async fn test_multiple_keys_independent() {
    let cache = cache().await;

    let key_a = "test:multi_a";
    let key_b = "test:multi_b";
    cache.del(key_a).await;
    cache.del(key_b).await;

    cache.set(key_a, "value_a", 60).await;
    cache.set(key_b, "value_b", 60).await;

    assert_eq!(cache.get(key_a).await.as_deref(), Some("value_a"));
    assert_eq!(cache.get(key_b).await.as_deref(), Some("value_b"));

    cache.del(key_a).await;
    assert_eq!(cache.get(key_a).await, None);
    assert_eq!(cache.get(key_b).await.as_deref(), Some("value_b"));

    cache.del(key_b).await;
}
