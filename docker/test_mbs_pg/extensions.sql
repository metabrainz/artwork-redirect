CREATE SCHEMA IF NOT EXISTS musicbrainz;
CREATE SCHEMA IF NOT EXISTS cover_art_archive;

ALTER ROLE musicbrainz SET search_path TO a,b,c;

CREATE EXTENSION IF NOT EXISTS cube WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS earthdistance WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS musicbrainz_unaccent WITH SCHEMA musicbrainz;
CREATE EXTENSION IF NOT EXISTS musicbrainz_collate WITH SCHEMA musicbrainz;
