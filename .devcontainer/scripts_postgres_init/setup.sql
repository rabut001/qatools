CREATE OR REPLACE FUNCTION try_cast_date(arg_text text)
    RETURNS date AS 
$$
BEGIN 
	BEGIN 
		RETURN arg_text::date;
	EXCEPTION WHEN OTHERS THEN
		RETURN null;
	END;
END;
$$
LANGUAGE plpgsql;
