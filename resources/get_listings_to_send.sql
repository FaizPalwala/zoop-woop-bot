CREATE OR REPLACE FUNCTION get_listings_to_send(curr_geo_id VARCHAR, curr_chat VARCHAR, ignore_listings VARCHAR[])
  RETURNS SETOF listings AS $$
  BEGIN
    RETURN QUERY SELECT * FROM listings WHERE geo_id = curr_geo_id AND listing_id NOT IN (SELECT listing_id FROM transactions WHERE chat_id = curr_chat AND listing_id != any(ignore_listings));
  END;
$$ LANGUAGE plpgsql;