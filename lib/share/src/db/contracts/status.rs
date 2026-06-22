use std::fmt::{self, Display};

pub enum Status {
    Active = 0,
    Inactive = 1,
    Completed = 2,
    Cancelled = 3,
    Failed = 4,
}

impl Display for Status {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Status::Active => write!(f, "active"),
            Status::Inactive => write!(f, "inactive"),
            Status::Completed => write!(f, "completed"),
            Status::Cancelled => write!(f, "cancelled"),
            Status::Failed => write!(f, "failed"),
        }
    }
}
