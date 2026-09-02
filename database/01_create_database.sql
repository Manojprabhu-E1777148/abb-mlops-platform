/*
  ABB MLOps Platform
  Initial SQL Server LocalDB database setup script.
*/

USE master;
GO

IF DB_ID(N'MlopsPlatformDb') IS NULL
BEGIN
    CREATE DATABASE MlopsPlatformDb;
END;
GO
