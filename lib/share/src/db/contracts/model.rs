use sqlx::FromRow;
use uuid::Uuid;

pub struct Contracts;

#[derive(Debug, Clone, FromRow, serde::Serialize)]
pub struct Contract {
    pub id: Uuid,
    pub user_uid: Uuid,
    pub signature: String,
    pub message: String,
    pub nonce: String,
    pub ticker: String,
    pub amount: String,
    pub sl_pct: f32,
    pub tp_pct: f32,
    pub status: String,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub updated_at: chrono::DateTime<chrono::Utc>,
}

impl Contracts {
    #[allow(clippy::too_many_arguments)]
    pub async fn create(
        pool: &sqlx::PgPool,
        user_uid: Uuid,
        signature: &str,
        message: &str,
        nonce: &str,
        ticker: &str,
        amount: &str,
        sl_pct: f32,
        tp_pct: f32,
    ) -> Result<(), sqlx::Error> {
        sqlx::query(
            r#"INSERT INTO contracts (user_uid, signature, message, nonce, ticker, amount, sl_pct, tp_pct, status)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')"#,
        )
        .bind(user_uid)
        .bind(signature)
        .bind(message)
        .bind(nonce)
        .bind(ticker.to_uppercase())
        .bind(amount)
        .bind(sl_pct)
        .bind(tp_pct)
        .execute(pool)
        .await?;
        Ok(())
    }
}
