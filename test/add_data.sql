SET client_min_messages TO 'WARNING';
SET search_path=cover_art_archive,musicbrainz;

INSERT INTO musicbrainz.artist (id, gid, name, sort_name)
    VALUES (1, '75b8a771-52a3-49a0-b2b6-993ed1250dfa', 'J Alvarez', 'J Alvarez');

INSERT INTO musicbrainz.artist_credit (id, gid, name, artist_count) VALUES (1, '0b58a811-e62c-4d06-be71-3418516c668d', 'J Alvarez', 1);
INSERT INTO musicbrainz.artist_credit_name (artist_credit, artist, name, position, join_phrase)
    VALUES (1, 1, 'J Alvarez', 0, '');

INSERT INTO musicbrainz.release_group (id, gid, name, artist_credit, type, comment, edits_pending)
    VALUES (1, '67a63246-0de4-4cd8-8ce2-35f70a17f92b', 'El dueño del sistema', 1, 1, '', 0);
INSERT INTO musicbrainz.release (id, gid, name, artist_credit, release_group)
     VALUES (1, '353710ec-1509-4df9-8ce2-9bd5011e3b80', 'El dueño del sistema', 1, 1),
            (2, '98f08de3-c91c-4180-a961-06c205e63669', 'El dueño del sistema', 1, 1),
            (3, 'f0b08d73-d827-4dde-ad2b-75a63f0c38be', 'El dueño del sistema', 1, 1);

INSERT INTO musicbrainz.release_unknown_country (release, date_year)
     VALUES (1, 2012),
            (2, 1976),
            (3, 2023);

INSERT INTO musicbrainz.event (id, gid, name, begin_date_year, begin_date_month, begin_date_day, end_date_year, end_date_month, end_date_day, "time", type, cancelled, setlist, comment, edits_pending, last_updated, ended)
    VALUES (1607, 'ebe6ce0f-22c0-4fe7-bfd4-7a0397c9fe94', 'Taubertal-Festival 2004, Day 1', 2004, 8, 13, 2004, 8, 13, NULL, 2, 'f', '', '', 0, '2016-05-13 21:24:52.037707+00', 't');

INSERT INTO musicbrainz.editor (id, name, password, email, email_confirm_date, ha1)
VALUES (1, 'kuno', 'topsecret', 'kuno@kunoenterprises.ltd', now(), '');

INSERT INTO musicbrainz.edit (id, editor, type, status, expire_time)
    -- FIXME: replace 9999 with the "add event artwork" edit type ID, once that's known.
    VALUES (1, 1, 314, 2, now()), (2, 1, 9999, 2, now());
INSERT INTO musicbrainz.edit_data (edit, data)
    VALUES (1, '{"foo":"bar"}'), (2, '{"foo":"bar"}');

INSERT INTO cover_art_archive.cover_art (id, release, edit, ordering, mime_type)
     VALUES (100000001, 1, 1, 1, 'image/jpeg'),
            (999999999, 1, 1, 1, 'image/jpeg'),
            (900000009, 3, 1, 1, 'image/jpeg');

INSERT INTO cover_art_archive.cover_art_type (id, type_id)
    VALUES (100000001, 1), (100000001, 3), (999999999, 2), (900000009, 1);

INSERT INTO event_art_archive.event_art (id, event, edit, ordering, mime_type)
    VALUES (100000001, 1607, 1, 1, 'image/jpeg');

INSERT INTO event_art_archive.event_art_type (id, type_id)
    VALUES (100000001, 1);
