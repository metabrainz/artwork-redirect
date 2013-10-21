BEGIN;
SET client_min_messages TO 'WARNING';
SET search_path=cover_art_archive,musicbrainz;

TRUNCATE TABLE artist CASCADE;
TRUNCATE TABLE artist_credit CASCADE;
TRUNCATE TABLE art_type CASCADE;
TRUNCATE TABLE image_type CASCADE;
TRUNCATE TABLE editor CASCADE;
TRUNCATE TABLE release_group_primary_type CASCADE;
TRUNCATE TABLE release_status CASCADE;

INSERT INTO artist (id, gid, name, sort_name)
    VALUES (1, '75b8a771-52a3-49a0-b2b6-993ed1250dfa', 'J Alvarez', 'J Alvarez');

INSERT INTO artist_credit (id, name, artist_count) VALUES (1, 'J Alvarez', 1);
INSERT INTO artist_credit_name (artist_credit, artist, name, position, join_phrase)
    VALUES (1, 1, 'J Alvarez', 0, '');

INSERT INTO release_group_primary_type (id, name) VALUES (1, 'Album'), (2, 'Single');
INSERT INTO release_status (id, name) VALUES (1, 'Official');

INSERT INTO release_group (id, gid, name, artist_credit, type, comment, edits_pending)
    VALUES (1, '67a63246-0de4-4cd8-8ce2-35f70a17f92b', 'El dueño del sistema', 1, 1, '', 0);
INSERT INTO release (id, gid, name, artist_credit, release_group)
    VALUES (1, '353710ec-1509-4df9-8ce2-9bd5011e3b80', 'El dueño del sistema', 1, 1);
INSERT INTO release (id, gid, name, artist_credit, release_group)
    VALUES (2, '98f08de3-c91c-4180-a961-06c205e63669', 'El dueño del sistema', 1, 1);

INSERT INTO release_unknown_country (release, date_year) VALUES (1, 2012);
INSERT INTO release_unknown_country (release, date_year) VALUES (2, 1976);

INSERT INTO editor (id, name, password, email, email_confirm_date, ha1)
VALUES (1, 'kuno', 'topsecret', 'kuno@kunoenterprises.ltd', now(), '');

INSERT INTO art_type (id, name) VALUES (1, 'Front'), (2, 'Back'), (3, 'Booklet');

INSERT INTO edit (id, editor, type, status, data, expire_time)
    VALUES (1, 1, 314, 2, '{"foo":"bar"}', now());

INSERT INTO image_type (mime_type, suffix) VALUES ('image/jpeg', 'jpg');

INSERT INTO cover_art (id, release, edit, ordering, mime_type)
    VALUES (100000001, 1, 1, 1, 'image/jpeg'), (999999999, 1, 1, 1, 'image/jpeg');

INSERT INTO cover_art_type (id, type_id)
    VALUES (100000001, 1), (100000001, 3), (999999999, 2);

COMMIT;
