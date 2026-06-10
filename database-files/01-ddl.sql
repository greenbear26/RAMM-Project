-- Fixed DDL for ramm_lobbying
-- Use this file to initialize the database if the default ddl.sql causes FK errors

CREATE DATABASE IF NOT EXISTS ramm_lobbying;
USE ramm_lobbying;

CREATE TABLE IF NOT EXISTS country_indicator (
  country VARCHAR(100),
  country_code VARCHAR(3) NOT NULL PRIMARY KEY,
  gdp_usd DOUBLE,
  population BIGINT,
  inflation DOUBLE,
  gdp_per_capita DOUBLE
);

CREATE TABLE IF NOT EXISTS industry (
    industry_id     INTEGER         PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policy_area (
    policy_area_id  INTEGER         PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    description     VARCHAR(10000),
    tags            VARCHAR(255),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_user (
    user_id         INTEGER         PRIMARY KEY,
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,
    role            VARCHAR(100),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organization (
    org_id                  INTEGER         PRIMARY KEY,
    name                    VARCHAR(255)    NOT NULL,
    lobbyfacts_url          VARCHAR(500),
    members_eu              INTEGER,
    members_fte             INTEGER,
    lobbying_cost           FLOAT,
    log_lobbying_cost       FLOAT,
    interest_represented    VARCHAR(255),
    country_code            VARCHAR(10),
    industry_id             INTEGER,
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (industry_id) REFERENCES industry(industry_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS lobbying_activity (
    activity_id     INTEGER         PRIMARY KEY,
    org_id          INTEGER         NOT NULL,
    policy_area_id  INTEGER         NOT NULL,
    eu_institution  VARCHAR(255),
    activity_type   VARCHAR(100),
    description     VARCHAR(10000),
    source          VARCHAR(255),
    start_date      DATE,
    end_date        DATE,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organization(org_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (policy_area_id) REFERENCES policy_area(policy_area_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS expenditure_record (
    expenditure_id          INTEGER         PRIMARY KEY,
    org_id                  INTEGER         NOT NULL,
    policy_area_id          INTEGER,
    year                    INTEGER         NOT NULL,
    amount_eur              FLOAT,
    amount_range_min_eur    FLOAT,
    amount_range_max_eur    FLOAT,
    currency                VARCHAR(20),
    source                  VARCHAR(255),
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organization(org_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (policy_area_id) REFERENCES policy_area(policy_area_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS meeting (
    meeting_id      INTEGER         PRIMARY KEY,
    org_id          INTEGER         NOT NULL,
    eu_body         VARCHAR(255),
    meeting_date    DATE,
    subject         VARCHAR(10000),
    attendees_count INTEGER,
    source          VARCHAR(255),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organization(org_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS access_pass (
    pass_id         INTEGER         PRIMARY KEY,
    org_id          INTEGER         NOT NULL,
    person_name     VARCHAR(255),
    role_title      VARCHAR(255),
    eu_body         VARCHAR(255),
    issue_date      DATE,
    expiry_date     DATE,
    source          VARCHAR(255),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES organization(org_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lobby_model_weights (
    model_id        INTEGER         PRIMARY KEY,
    beta_vals       TEXT            NOT NULL
);

CREATE TABLE IF NOT EXISTS lobby_model_scaler (
    sequence_number INT,
    feature_means   TEXT,
    feature_stds    TEXT
);

CREATE TABLE IF NOT EXISTS party_model_weights (
    model_id        INTEGER         PRIMARY KEY,
    beta_vals       TEXT            NOT NULL
);

CREATE TABLE IF NOT EXISTS party_model_scaler (
    sequence_number INT,
    feature_means   TEXT,
    feature_stds    TEXT
);

CREATE TABLE IF NOT EXISTS party_info (
    party_name_english  VARCHAR(100)    NOT NULL PRIMARY KEY,
    country_name        VARCHAR(14)     NOT NULL,
    populist            BIT             NOT NULL,
    populist_bl         BIT             NOT NULL,
    farright            BIT             NOT NULL,
    farright_bl         BIT             NOT NULL,
    farleft             BIT             NOT NULL,
    farleft_bl          BIT             NOT NULL,
    eurosceptic         BIT             NOT NULL,
    eurosceptic_bl      BIT             NOT NULL,
    in_parliament       NUMERIC(3,1)    NOT NULL,
    party_id            NUMERIC(6,1)    NOT NULL,
    family_name         VARCHAR(19)     NOT NULL,
    left_right          NUMERIC(6,4)    NOT NULL,
    state_market        NUMERIC(6,4)    NOT NULL,
    liberty_authority   NUMERIC(6,4)    NOT NULL,
    eu_anti_pro         NUMERIC(6,4)    NOT NULL,
    ep_party            VARCHAR(50)
);

CREATE TABLE mytable(
   group                 VARCHAR(12) NOT NULL PRIMARY KEY
  ,lobbyists             VARCHAR(134559) NOT NULL
  ,meetings_per_lobbyist VARCHAR(12968) NOT NULL
  ,total_meetings        INTEGER  NOT NULL
);