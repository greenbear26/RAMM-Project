-- Fixed DDL for ramm_lobbying
-- Use this file to initialize the database if the default ddl.sql causes FK errors

CREATE DATABASE IF NOT EXISTS ramm_lobbying;
USE ramm_lobbying;
-- ok
CREATE TABLE IF NOT EXISTS country_indicator (
  country VARCHAR(100),
  country_code VARCHAR(3) NOT NULL PRIMARY KEY,
  gdp_usd DOUBLE,
  population BIGINT,
  inflation DOUBLE,
  gdp_per_capita DOUBLE
);
-- ok
CREATE TABLE IF NOT EXISTS app_user (
    user_id         INTEGER         PRIMARY KEY,
    first_name      VARCHAR(100)    NOT NULL,
    last_name       VARCHAR(100),
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255),
    role            VARCHAR(100),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
-- ok
CREATE TABLE IF NOT EXISTS lobbying_organization (
    org_id                  INTEGER         PRIMARY KEY,
    name                    VARCHAR(255)    NOT NULL,
    all_ep_passes           INTEGER,
    members_fte             FLOAT,
    lobbying_cost           FLOAT,
    interest_represented    VARCHAR(255),
    country_name            VARCHAR(100),
    ep_meetings             INTEGER,
    policy_areas            VARCHAR(255),

    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ok
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
    party_id            NUMERIC(6,1)    PRIMARY KEY,
    party_name_english  VARCHAR(100)    NOT NULL,
    country_name        VARCHAR(14)     NOT NULL,
    populist            BIT             NOT NULL,
    populist_bl         BIT             NOT NULL,
    farright            BIT             NOT NULL,
    farright_bl         BIT             NOT NULL,
    farleft             BIT             NOT NULL,
    farleft_bl          BIT             NOT NULL,
    eurosceptic         BIT             NOT NULL,
    eurosceptic_bl      BIT             NOT NULL,
    in_parliament       BIT             NOT NULL,
    family_name         VARCHAR(19)     NOT NULL,
    left_right          NUMERIC(6,4)    NOT NULL,
    state_market        NUMERIC(6,4)    NOT NULL,
    liberty_authority   NUMERIC(6,4)    NOT NULL,
    eu_anti_pro         NUMERIC(6,4)    NOT NULL,
    ep_party            VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS party_to_lobby_info (
    ep_party              VARCHAR(12) NOT NULL PRIMARY KEY,
    lobbyists             TEXT(134559) NOT NULL,
    meetings_per_lobbyist VARCHAR(12968) NOT NULL,
    total_meetings        INTEGER  NOT NULL
);