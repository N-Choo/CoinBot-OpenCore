use actix_web::dev::HttpServiceFactory;
use actix_web::web::{self};

use crate::constants;
use crate::handlers::contracts::Contracts;
use crate::handlers::transaction::Transaction;
use crate::handlers::user::auth::AuthController;

pub fn api_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/api")
            .service(user_routes())
            .service(transaction_routes())
            .service(contract_routes())
            .route("/config", web::get().to(constants::get_config)),
    );
}

fn user_routes() -> impl HttpServiceFactory {
    web::scope("/user")
        .service(
            web::resource("/auth")
                .route(web::get().to(AuthController::request_challenge))
                .route(web::post().to(AuthController::login)),
        )
        .route("/logout", web::post().to(AuthController::logout))
        .route("/verify", web::post().to(AuthController::verify_session))
}

fn transaction_routes() -> impl HttpServiceFactory {
    web::scope("/transactions")
        .route("/deposit", web::post().to(Transaction::deposit))
        .route("", web::get().to(Transaction::list))
}

fn contract_routes() -> impl HttpServiceFactory {
    web::scope("/contracts")
        .route("/nonce", web::get().to(Contracts::get_nonce))
        .route("/sign", web::post().to(Contracts::sign))
}
