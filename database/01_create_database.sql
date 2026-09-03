/*
  Run with sqlcmd from the repository root:
  sqlcmd -S "(localdb)\MSSQLLocalDB" -i database\01_create_database.sql -v DatabaseDirectory = "$((Get-Location).Path)\database"
*/

USE master;
GO

DECLARE @database_directory nvarchar(260) = N'$(DatabaseDirectory)';
DECLARE @data_file nvarchar(520) = @database_directory + N'\MlopsPlatformDb.mdf';
DECLARE @log_file nvarchar(520) = @database_directory + N'\MlopsPlatformDb_log.ldf';

IF DB_ID(N'MlopsPlatformDb') IS NULL
BEGIN
    DECLARE @sql nvarchar(max) =
        N'CREATE DATABASE [MlopsPlatformDb] ON PRIMARY '
        + N'(NAME = N''MlopsPlatformDb'', FILENAME = N''' + REPLACE(@data_file, N'''', N'''''') + N''') '
        + N'LOG ON '
        + N'(NAME = N''MlopsPlatformDb_log'', FILENAME = N''' + REPLACE(@log_file, N'''', N'''''') + N''')';

    EXEC sp_executesql @sql;
END;
ELSE IF NOT EXISTS
(
    SELECT 1
    FROM sys.master_files
    WHERE database_id = DB_ID(N'MlopsPlatformDb')
      AND physical_name = @data_file
)
BEGIN
    THROW 50000, 'MlopsPlatformDb is already attached from a different MDF path.', 1;
END;
GO
