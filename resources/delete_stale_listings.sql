CREATE OR REPLACE FUNCTION delete_stale_listings()
RETURNS void AS $$
BEGIN
    DELETE FROM listings
    WHERE update_ts < NOW() - INTERVAL '7 days';
END;
$$ LANGUAGE plpgsql;