select
    current_database() as database_name,
    current_user as database_user,
    current_schema() as active_schema,
    current_timestamp as checked_at

