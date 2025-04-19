/*
Script de criação do banco de dados para o sistema de Assinaturas do Outlook
Data: 2025-04-18
Versão: 1.0
*/

-- Verificar e criar o banco de dados se não existir
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'Microsoft365')
BEGIN
    CREATE DATABASE Microsoft365;
    PRINT 'Banco de dados Microsoft365 criado com sucesso.';
END
ELSE
BEGIN
    PRINT 'Banco de dados Microsoft365 já existe.';
END
GO

USE Microsoft365;
GO

-- Configurar o banco para usar o modo de colação SQL_Latin1_General_CP1_CI_AI
ALTER DATABASE Microsoft365 COLLATE SQL_Latin1_General_CP1_CI_AI;
GO

-- Criar schema se não existir
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'dbo')
BEGIN
    EXEC('CREATE SCHEMA dbo');
    PRINT 'Schema dbo criado com sucesso.';
END
GO

/*
========================
CRIAÇÃO DAS TABELAS
========================
*/

-- Tabela de usuários
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[users] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [email] NVARCHAR(255) NOT NULL,
        [nome_completo] NVARCHAR(255) NOT NULL,
        [cargo] NVARCHAR(100) NULL,
        [setor] NVARCHAR(100) NULL,
        [empresa] NVARCHAR(100) NULL,
        [telefone] NVARCHAR(50) NULL,
        [ramal] NVARCHAR(20) NULL,
        [ms_id] NVARCHAR(100) NULL,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT [PK_users] PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT [UQ_users_email] UNIQUE NONCLUSTERED ([email] ASC)
    );
    
    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_users_email] ON [dbo].[users] ([email]);
    CREATE NONCLUSTERED INDEX [IDX_users_nome_completo] ON [dbo].[users] ([nome_completo]);
    CREATE NONCLUSTERED INDEX [IDX_users_setor] ON [dbo].[users] ([setor]);
    CREATE NONCLUSTERED INDEX [IDX_users_ms_id] ON [dbo].[users] ([ms_id]);
    
    PRINT 'Tabela users criada com sucesso.';
END
GO

-- Tabela de usuários administrativos
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[admin_users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[admin_users] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [username] NVARCHAR(100) NOT NULL,
        [password_hash] NVARCHAR(256) NOT NULL,
        [role] NVARCHAR(50) NOT NULL DEFAULT 'admin',
        [is_active] BIT NOT NULL DEFAULT 1,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT [PK_admin_users] PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT [UQ_admin_users_username] UNIQUE NONCLUSTERED ([username] ASC)
    );
    
    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_admin_users_username] ON [dbo].[admin_users] ([username]);
    CREATE NONCLUSTERED INDEX [IDX_admin_users_role] ON [dbo].[admin_users] ([role]);
    
    PRINT 'Tabela admin_users criada com sucesso.';
    
    -- Inserir um usuário administrativo padrão (admin/admin123)
    -- A senha "admin123" foi transformada em hash SHA-256: a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3
    IF NOT EXISTS (SELECT * FROM [dbo].[admin_users] WHERE [username] = 'admin')
    BEGIN
        INSERT INTO [dbo].[admin_users] ([username], [password_hash], [role], [is_active])
        VALUES ('admin', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'admin', 1);
        
        PRINT 'Usuário administrativo padrão criado: admin/admin123';
    END
END
GO

-- Tabela de templates de assinatura
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[signature_templates]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[signature_templates] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [name] NVARCHAR(100) NOT NULL,
        [template_html] NVARCHAR(MAX) NOT NULL,
        [is_default] BIT NOT NULL DEFAULT 0,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT [PK_signature_templates] PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT [UQ_signature_templates_name] UNIQUE NONCLUSTERED ([name] ASC)
    );
    
    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_signature_templates_name] ON [dbo].[signature_templates] ([name]);
    CREATE NONCLUSTERED INDEX [IDX_signature_templates_is_default] ON [dbo].[signature_templates] ([is_default]);
    
    PRINT 'Tabela signature_templates criada com sucesso.';
    
    -- Inserir um template de assinatura padrão
    IF NOT EXISTS (SELECT * FROM [dbo].[signature_templates] WHERE [is_default] = 1)
    BEGIN
        INSERT INTO [dbo].[signature_templates] ([name], [template_html], [is_default])
        VALUES (
            'Template Padrão', 
            N'<table style="font-family: Arial, sans-serif; font-size: 12px; color: #333333; border-top: 1px solid #cccccc; padding-top: 10px; width: 500px;">
                <tr>
                    <td style="vertical-align: top; padding-right: 10px;">
                        <strong style="font-size: 14px; color: #003366;">{{NomeCompleto}}</strong><br/>
                        <span style="font-size: 12px; color: #666666;">{{Cargo}}</span><br/>
                        <span style="font-size: 12px;">{{Setor}} | {{Empresa}}</span><br/>
                        <span style="font-size: 12px;">Tel: {{Telefone}} {{Ramal}}</span><br/>
                        <span style="font-size: 12px;">Email: <a href="mailto:{{Email}}" style="color: #003366; text-decoration: none;">{{Email}}</a></span>
                    </td>
                </tr>
            </table>', 
            1
        );
        
        PRINT 'Template de assinatura padrão criado.';
    END
END
GO

-- Tabela de assinaturas (atribuições de templates a usuários)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[signatures]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[signatures] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [user_email] NVARCHAR(255) NOT NULL,
        [signature_html] NVARCHAR(MAX) NOT NULL,
        [template_id] INT NOT NULL,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT [PK_signatures] PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT [UQ_signatures_user_email] UNIQUE NONCLUSTERED ([user_email] ASC)
    );
    
    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_signatures_user_email] ON [dbo].[signatures] ([user_email]);
    CREATE NONCLUSTERED INDEX [IDX_signatures_template_id] ON [dbo].[signatures] ([template_id]);
    
    -- Adicionar constraints de chave estrangeira
    ALTER TABLE [dbo].[signatures] ADD CONSTRAINT [FK_signatures_template_id]
    FOREIGN KEY ([template_id]) REFERENCES [dbo].[signature_templates] ([id])
    ON DELETE NO ACTION ON UPDATE NO ACTION;
    
    PRINT 'Tabela signatures criada com sucesso.';
END
GO

-- Tabela de logs do sistema (opcional, mas útil para auditoria)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[system_logs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[system_logs] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [level] NVARCHAR(10) NOT NULL,
        [message] NVARCHAR(MAX) NOT NULL,
        [source] NVARCHAR(100) NULL,
        [user_id] INT NULL,
        [user_email] NVARCHAR(255) NULL,
        [ip_address] NVARCHAR(45) NULL,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        
        CONSTRAINT [PK_system_logs] PRIMARY KEY CLUSTERED ([id] ASC)
    );
    
    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_system_logs_level] ON [dbo].[system_logs] ([level]);
    CREATE NONCLUSTERED INDEX [IDX_system_logs_created_at] ON [dbo].[system_logs] ([created_at]);
    CREATE NONCLUSTERED INDEX [IDX_system_logs_user_email] ON [dbo].[system_logs] ([user_email]);
    
    PRINT 'Tabela system_logs criada com sucesso.';
END
GO

/*
========================
CRIAÇÃO DAS PROCEDURES
========================
*/

-- Procedure para sincronizar usuários com o Microsoft 365
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SyncUser]') AND type in (N'P'))
    DROP PROCEDURE [dbo].[SyncUser];
GO

CREATE PROCEDURE [dbo].[SyncUser]
    @email NVARCHAR(255),
    @nome_completo NVARCHAR(255),
    @cargo NVARCHAR(100) = NULL,
    @setor NVARCHAR(100) = NULL,
    @empresa NVARCHAR(100) = NULL,
    @telefone NVARCHAR(50) = NULL,
    @ramal NVARCHAR(20) = NULL,
    @ms_id NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @user_id INT;
    
    -- Verificar se o usuário já existe
    SELECT @user_id = [id] FROM [dbo].[users] WHERE [email] = @email;
    
    IF @user_id IS NULL
    BEGIN
        -- Inserir novo usuário
        INSERT INTO [dbo].[users] (
            [email], [nome_completo], [cargo], [setor], [empresa], [telefone], [ramal], [ms_id], [created_at], [updated_at]
        )
        VALUES (
            @email, @nome_completo, @cargo, @setor, @empresa, @telefone, @ramal, @ms_id, GETDATE(), GETDATE()
        );
        
        SET @user_id = SCOPE_IDENTITY();
    END
    ELSE
    BEGIN
        -- Atualizar usuário existente
        UPDATE [dbo].[users]
        SET [nome_completo] = @nome_completo,
            [cargo] = @cargo,
            [setor] = @setor,
            [empresa] = @empresa,
            [telefone] = @telefone,
            [ramal] = @ramal,
            [ms_id] = @ms_id,
            [updated_at] = GETDATE()
        WHERE [id] = @user_id;
    END
    
    -- Retornar o ID do usuário
    SELECT @user_id AS [user_id];
END
GO

-- Procedure para atribuir assinatura a um usuário
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AssignSignature]') AND type in (N'P'))
    DROP PROCEDURE [dbo].[AssignSignature];
GO

CREATE PROCEDURE [dbo].[AssignSignature]
    @user_email NVARCHAR(255),
    @template_id INT,
    @signature_html NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @final_html NVARCHAR(MAX);
    DECLARE @template_exists BIT = 0;
    
    -- Verificar se o template existe
    SELECT @template_exists = 1 FROM [dbo].[signature_templates] WHERE [id] = @template_id;
    
    IF @template_exists = 0
    BEGIN
        RAISERROR('Template não encontrado', 16, 1);
        RETURN;
    END
    
    -- Se não foi fornecido um HTML personalizado, usar o HTML do template
    IF @signature_html IS NULL
    BEGIN
        SELECT @final_html = [template_html] FROM [dbo].[signature_templates] WHERE [id] = @template_id;
    END
    ELSE
    BEGIN
        SET @final_html = @signature_html;
    END
    
    -- Verificar se já existe uma assinatura para o usuário
    IF EXISTS (SELECT 1 FROM [dbo].[signatures] WHERE [user_email] = @user_email)
    BEGIN
        -- Atualizar assinatura existente
        UPDATE [dbo].[signatures]
        SET [signature_html] = @final_html,
            [template_id] = @template_id,
            [updated_at] = GETDATE()
        WHERE [user_email] = @user_email;
    END
    ELSE
    BEGIN
        -- Inserir nova assinatura
        INSERT INTO [dbo].[signatures] (
            [user_email], [signature_html], [template_id], [created_at], [updated_at]
        )
        VALUES (
            @user_email, @final_html, @template_id, GETDATE(), GETDATE()
        );
    END
END
GO

-- Função para obter a assinatura renderizada para um usuário
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[GetRenderedSignature]') AND type in (N'FN', N'IF', N'TF', N'FS', N'FT'))
    DROP FUNCTION [dbo].[GetRenderedSignature];
GO

CREATE FUNCTION [dbo].[GetRenderedSignature] (
    @user_email NVARCHAR(255)
)
RETURNS NVARCHAR(MAX)
AS
BEGIN
    DECLARE @signature_html NVARCHAR(MAX);
    DECLARE @rendered_html NVARCHAR(MAX);
    DECLARE @user_nome NVARCHAR(255);
    DECLARE @user_cargo NVARCHAR(100);
    DECLARE @user_setor NVARCHAR(100);
    DECLARE @user_empresa NVARCHAR(100);
    DECLARE @user_telefone NVARCHAR(50);
    DECLARE @user_ramal NVARCHAR(20);
    
    -- Obter a assinatura do usuário
    SELECT @signature_html = s.[signature_html]
    FROM [dbo].[signatures] s
    WHERE s.[user_email] = @user_email;
    
    -- Se não existir assinatura, usar o template padrão
    IF @signature_html IS NULL
    BEGIN
        SELECT TOP 1 @signature_html = t.[template_html]
        FROM [dbo].[signature_templates] t
        WHERE t.[is_default] = 1;
    END
    
    -- Obter os dados do usuário
    SELECT 
        @user_nome = u.[nome_completo],
        @user_cargo = u.[cargo],
        @user_setor = u.[setor],
        @user_empresa = u.[empresa],
        @user_telefone = u.[telefone],
        @user_ramal = u.[ramal]
    FROM [dbo].[users] u
    WHERE u.[email] = @user_email;
    
    -- Se não encontrar o usuário, tentar extrair informações do e-mail
    IF @user_nome IS NULL
    BEGIN
        SET @user_nome = LEFT(@user_email, CHARINDEX('@', @user_email) - 1);
        SET @user_nome = UPPER(LEFT(@user_nome, 1)) + SUBSTRING(@user_nome, 2, LEN(@user_nome));
        SET @user_cargo = '';
        SET @user_setor = '';
        SET @user_empresa = SUBSTRING(@user_email, CHARINDEX('@', @user_email) + 1, LEN(@user_email));
        SET @user_telefone = '';
        SET @user_ramal = '';
    END
    
    -- Substituir as variáveis no template
    SET @rendered_html = REPLACE(@signature_html, '{{NomeCompleto}}', ISNULL(@user_nome, ''));
    SET @rendered_html = REPLACE(@rendered_html, '{{Cargo}}', ISNULL(@user_cargo, ''));
    SET @rendered_html = REPLACE(@rendered_html, '{{Setor}}', ISNULL(@user_setor, ''));
    SET @rendered_html = REPLACE(@rendered_html, '{{Empresa}}', ISNULL(@user_empresa, ''));
    SET @rendered_html = REPLACE(@rendered_html, '{{Telefone}}', ISNULL(@user_telefone, ''));
    SET @rendered_html = REPLACE(@rendered_html, '{{Ramal}}', ISNULL(@user_ramal, ''));
    SET @rendered_html = REPLACE(@rendered_html, '{{Email}}', @user_email);
    
    RETURN @rendered_html;
END
GO

PRINT 'Todas as tabelas, índices e procedures foram criados com sucesso.';
PRINT 'Script finalizado.';
GO
