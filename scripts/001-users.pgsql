--
-- Table of users
--

CREATE TABLE users
(
  id            SERIAL UNIQUE,
  cell_phone    TEXT,
  name          TEXT,
  region		TEXT,
  village		TEXT,
  calls			TEXT[]
);