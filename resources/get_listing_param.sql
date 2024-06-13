CREATE OR REPLACE FUNCTION get_listing_param()
  RETURNS TABLE (
    geo_id VARCHAR,
    geo_label TEXT,
    price SMALLINT
  ) AS $$
  BEGIN
    RETURN QUERY SELECT s.geo_id, s.geo_label, max(s.price_limit) FROM subscriptions as s GROUP BY s.geo_id, s.geo_label;
  END;
$$ LANGUAGE plpgsql;