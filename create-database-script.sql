/*
Script de criação do banco de dados para o sistema de Assinaturas do Outlook
Data: 2025-04-18
Versão: 1.1 (Corrigido)
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
-- (Fazendo isso após a criação garante que o contexto está correto)
IF DB_NAME() = 'Microsoft365' AND SERVERPROPERTY('Collation') <> 'SQL_Latin1_General_CP1_CI_AI'
BEGIN
    ALTER DATABASE Microsoft365 COLLATE SQL_Latin1_General_CP1_CI_AI;
    PRINT 'Collation do banco de dados Microsoft365 alterado para SQL_Latin1_General_CP1_CI_AI.';
END
GO

-- Criar schema dbo se não existir (geralmente não necessário, mas inofensivo)
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
        [ms_id] NVARCHAR(100) NULL, -- Microsoft Graph User ID, por exemplo
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

    PRINT 'Tabela [dbo].[users] criada com sucesso.';
END
ELSE
BEGIN
    PRINT 'Tabela [dbo].[users] já existe.';
END
GO

-- Tabela de usuários administrativos
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[admin_users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[admin_users] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [username] NVARCHAR(100) NOT NULL,
        [password_hash] NVARCHAR(256) NOT NULL, -- Suficiente para SHA-256
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

    PRINT 'Tabela [dbo].[admin_users] criada com sucesso.';

    -- Inserir um usuário administrativo padrão (admin/admin123)
    IF NOT EXISTS (SELECT * FROM [dbo].[admin_users] WHERE [username] = 'admin')
    BEGIN
        -- IMPORTANTE: Este hash precisa ser gerado usando o mesmo algoritmo do Python
        -- Python: hashlib.sha256('admin123'.encode()).hexdigest()
        INSERT INTO [dbo].[admin_users] ([username], [password_hash], [role], [is_active])
        VALUES (
            'admin', 
            '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', -- Hash SHA-256 de 'admin123'
            'admin',
            1
        );
        PRINT 'Usuário administrativo padrão criado: admin/admin123';
    END
END
ELSE
BEGIN
    PRINT 'Tabela [dbo].[admin_users] já existe.';
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

    PRINT 'Tabela [dbo].[signature_templates] criada com sucesso.';

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
ELSE
BEGIN
    PRINT 'Tabela [dbo].[signature_templates] já existe.';
END
GO

-- Tabela de assinaturas (atribuições de templates a usuários)
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[signatures]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[signatures] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [user_email] NVARCHAR(255) NOT NULL, -- Chave lógica para a tabela users
        [signature_html] NVARCHAR(MAX) NOT NULL, -- HTML final (renderizado ou personalizado)
        [template_id] INT NOT NULL, -- FK para signature_templates
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME NOT NULL DEFAULT GETDATE(),

        CONSTRAINT [PK_signatures] PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT [UQ_signatures_user_email] UNIQUE NONCLUSTERED ([user_email] ASC), -- Garante uma assinatura por email
        CONSTRAINT [FK_signatures_template_id] FOREIGN KEY ([template_id]) REFERENCES [dbo].[signature_templates] ([id]) ON DELETE NO ACTION ON UPDATE NO ACTION
        -- Considerar adicionar FK para users(email) se a estabilidade do email for garantida, ou usar users.id
        -- CONSTRAINT [FK_signatures_user_email] FOREIGN KEY ([user_email]) REFERENCES [dbo].[users] ([email]) ON DELETE CASCADE ON UPDATE CASCADE -- CUIDADO: CASCADE pode não ser desejável
    );

    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_signatures_user_email] ON [dbo].[signatures] ([user_email]);
    CREATE NONCLUSTERED INDEX [IDX_signatures_template_id] ON [dbo].[signatures] ([template_id]);

    PRINT 'Tabela [dbo].[signatures] criada com sucesso.';
END
ELSE
BEGIN
    PRINT 'Tabela [dbo].[signatures] já existe.';
END
GO

-- Tabela de logs do sistema
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[system_logs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[system_logs] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [level] NVARCHAR(10) NOT NULL, -- Ex: INFO, WARN, ERROR
        [message] NVARCHAR(MAX) NOT NULL,
        [source] NVARCHAR(100) NULL, -- Ex: SyncJob, WebAPI
        [user_id] INT NULL, -- ID do usuário (se aplicável)
        [user_email] NVARCHAR(255) NULL, -- Email do usuário (se aplicável)
        [ip_address] NVARCHAR(45) NULL, -- Endereço IP da requisição
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),

        CONSTRAINT [PK_system_logs] PRIMARY KEY CLUSTERED ([id] ASC)
        -- Poderia adicionar FK para users(id) se user_id for preenchido
        -- CONSTRAINT [FK_system_logs_user_id] FOREIGN KEY ([user_id]) REFERENCES [dbo].[users] ([id]) ON DELETE SET NULL ON UPDATE CASCADE
    );

    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_system_logs_level] ON [dbo].[system_logs] ([level]);
    CREATE NONCLUSTERED INDEX [IDX_system_logs_created_at] ON [dbo].[system_logs] ([created_at] DESC); -- Logs são frequentemente consultados por data recente
    CREATE NONCLUSTERED INDEX [IDX_system_logs_user_email] ON [dbo].[system_logs] ([user_email]);

    PRINT 'Tabela [dbo].[system_logs] criada com sucesso.';
END
ELSE
BEGIN
    PRINT 'Tabela [dbo].[system_logs] já existe.';
END
GO

-- Tabela de sessões administrativas
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[admin_sessions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[admin_sessions] (
        [id] INT IDENTITY(1,1) NOT NULL,
        [user_id] INT NOT NULL, -- FK para admin_users
        [token] NVARCHAR(255) NOT NULL, -- Token da sessão (ex: JWT ou token opaco)
        [expires_at] DATETIME NOT NULL,
        [ip_address] NVARCHAR(45) NULL,
        [user_agent] NVARCHAR(255) NULL,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),

        CONSTRAINT [PK_admin_sessions] PRIMARY KEY CLUSTERED ([id] ASC),
        CONSTRAINT [UQ_admin_sessions_token] UNIQUE NONCLUSTERED ([token] ASC),
        CONSTRAINT [FK_admin_sessions_user_id] FOREIGN KEY ([user_id]) REFERENCES [dbo].[admin_users] ([id]) ON DELETE CASCADE -- Se o admin for deletado, suas sessões também são
    );

    -- Criar índices
    CREATE NONCLUSTERED INDEX [IDX_admin_sessions_token] ON [dbo].[admin_sessions] ([token]);
    CREATE NONCLUSTERED INDEX [IDX_admin_sessions_expires_at] ON [dbo].[admin_sessions] ([expires_at]);
    CREATE NONCLUSTERED INDEX [IDX_admin_sessions_user_id] ON [dbo].[admin_sessions] ([user_id]);

    PRINT 'Tabela [dbo].[admin_sessions] criada com sucesso.';
END
ELSE
BEGIN
    PRINT 'Tabela [dbo].[admin_sessions] já existe.';
END
GO

/*
========================
CRIAÇÃO DAS PROCEDURES E FUNCTIONS
========================
*/

-- Procedure para sincronizar (inserir/atualizar) usuários
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SyncUser]') AND type in (N'P'))
BEGIN
    DROP PROCEDURE [dbo].[SyncUser];
    PRINT 'Procedure [dbo].[SyncUser] existente removida.';
END
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
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        DECLARE @user_id INT;
        
        -- Usar MERGE ao invés de SELECT + IF para melhor performance
        MERGE [dbo].[users] AS target
        USING (SELECT @email AS email) AS source
        ON (target.[email] = source.email)
        WHEN MATCHED THEN
            UPDATE SET 
                [nome_completo] = @nome_completo,
                [cargo] = COALESCE(@cargo, target.[cargo]),
                [setor] = COALESCE(@setor, target.[setor]),
                [empresa] = COALESCE(@empresa, target.[empresa]),
                [telefone] = COALESCE(@telefone, target.[telefone]),
                [ramal] = COALESCE(@ramal, target.[ramal]),
                [ms_id] = COALESCE(@ms_id, target.[ms_id]),
                [updated_at] = GETDATE()
        WHEN NOT MATCHED THEN
            INSERT ([email], [nome_completo], [cargo], [setor], [empresa], [telefone], [ramal], [ms_id], [created_at], [updated_at])
            VALUES (@email, @nome_completo, @cargo, @setor, @empresa, @telefone, @ramal, @ms_id, GETDATE(), GETDATE());

        SET @user_id = SCOPE_IDENTITY();
        
        COMMIT TRANSACTION;
        
        -- Retornar o ID do usuário
        SELECT @user_id AS [user_id];
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();

        RAISERROR (@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END
GO
PRINT 'Procedure [dbo].[SyncUser] criada com sucesso.';
GO

-- Procedure para atribuir assinatura a um usuário
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[AssignSignature]') AND type in (N'P'))
BEGIN
    DROP PROCEDURE [dbo].[AssignSignature];
    PRINT 'Procedure [dbo].[AssignSignature] existente removida.';
END
GO

CREATE PROCEDURE [dbo].[AssignSignature]
    @user_email NVARCHAR(255),
    @template_id INT,
    @signature_html NVARCHAR(MAX) = NULL -- Opcional: HTML personalizado, senão usa o do template
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @final_html NVARCHAR(MAX);
    DECLARE @template_exists BIT = 0;
    DECLARE @user_exists BIT = 0;

    -- Verificar se o usuário existe na tabela users
    SELECT @user_exists = 1 FROM [dbo].[users] WHERE [email] = @user_email;
    IF @user_exists = 0
    BEGIN
        RAISERROR('Usuário com email %s não encontrado na tabela [users].', 16, 1, @user_email);
        RETURN;
    END

    -- Verificar se o template existe
    SELECT @template_exists = 1 FROM [dbo].[signature_templates] WHERE [id] = @template_id;
    IF @template_exists = 0
    BEGIN
        RAISERROR('Template com ID %d não encontrado.', 16, 1, @template_id);
        RETURN;
    END

    -- Determinar o HTML final a ser salvo
    IF @signature_html IS NULL OR LTRIM(RTRIM(@signature_html)) = ''
    BEGIN
        -- Usar o HTML do template se nenhum HTML personalizado foi fornecido
        SELECT @final_html = [template_html] FROM [dbo].[signature_templates] WHERE [id] = @template_id;
    END
    ELSE
    BEGIN
        -- Usar o HTML personalizado fornecido
        SET @final_html = @signature_html;
    END

    -- Verificar se já existe uma assinatura para o usuário (UPSERT)
    IF EXISTS (SELECT 1 FROM [dbo].[signatures] WHERE [user_email] = @user_email)
    BEGIN
        -- Atualizar assinatura existente
        UPDATE [dbo].[signatures]
        SET [signature_html] = @final_html,
            [template_id] = @template_id,
            [updated_at] = GETDATE()
        WHERE [user_email] = @user_email;
        PRINT 'Assinatura atualizada para: ' + @user_email;
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
        PRINT 'Assinatura criada para: ' + @user_email;
    END
END
GO
PRINT 'Procedure [dbo].[AssignSignature] criada com sucesso.';
GO

-- Função para obter a assinatura renderizada para um usuário
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[GetRenderedSignature]') AND type in (N'FN', N'IF', N'TF', N'FS', N'FT'))
BEGIN
    DROP FUNCTION [dbo].[GetRenderedSignature];
    PRINT 'Function [dbo].[GetRenderedSignature] existente removida.';
END
GO

CREATE FUNCTION [dbo].[GetRenderedSignature] (
    @user_email NVARCHAR(255)
)
RETURNS NVARCHAR(MAX)
AS
BEGIN
    DECLARE @signature_html_template NVARCHAR(MAX); -- Template ou HTML atribuído
    DECLARE @rendered_html NVARCHAR(MAX);          -- HTML final com dados substituídos
    DECLARE @user_nome NVARCHAR(255);
    DECLARE @user_cargo NVARCHAR(100);
    DECLARE @user_setor NVARCHAR(100);
    DECLARE @user_empresa NVARCHAR(100);
    DECLARE @user_telefone NVARCHAR(50);
    DECLARE @user_ramal NVARCHAR(20);

    -- 1. Obter o HTML base da assinatura atribuída ao usuário
    SELECT @signature_html_template = s.[signature_html]
    FROM [dbo].[signatures] s
    WHERE s.[user_email] = @user_email;

    -- 2. Se não houver assinatura atribuída, usar o template padrão
    IF @signature_html_template IS NULL
    BEGIN
        SELECT TOP 1 @signature_html_template = t.[template_html]
        FROM [dbo].[signature_templates] t
        WHERE t.[is_default] = 1
        ORDER BY t.[id]; -- Garantir determinismo se houver mais de um default (não deveria)
    END

    -- Se ainda assim não houver template (nem atribuído, nem padrão), retornar vazio ou uma mensagem
    IF @signature_html_template IS NULL
    BEGIN
        RETURN N'<!-- Assinatura não configurada -->';
    END

    -- 3. Obter os dados do usuário para preencher o template
    SELECT
        @user_nome = u.[nome_completo],
        @user_cargo = u.[cargo],
        @user_setor = u.[setor],
        @user_empresa = u.[empresa],
        @user_telefone = u.[telefone],
        @user_ramal = u.[ramal]
    FROM [dbo].[users] u
    WHERE u.[email] = @user_email;

    -- 4. Se não encontrar o usuário na tabela, tentar extrair informações básicas do e-mail (fallback)
    IF @user_nome IS NULL
    BEGIN
        DECLARE @at_position INT;
        SET @at_position = CHARINDEX(N'@', @user_email);
        
        IF @at_position > 1
        BEGIN
            -- Extrair nome do e-mail de forma mais segura
            SET @user_nome = SUBSTRING(@user_email, 1, @at_position - 1);
            SET @user_nome = CONCAT(
                UPPER(LEFT(@user_nome, 1)),
                LOWER(SUBSTRING(@user_nome, 2, LEN(@user_nome)))
            );
            -- Extrair domínio
            SET @user_empresa = SUBSTRING(@user_email, @at_position + 1, LEN(@user_email) - @at_position);
        END
        ELSE
        BEGIN
            -- Email inválido ou sem '@', usar o próprio email como nome
            SET @user_nome = @user_email;
            SET @user_empresa = '';
        END
        -- Definir outros campos como vazios no fallback
        SET @user_cargo = '';
        SET @user_setor = '';
        SET @user_telefone = '';
        SET @user_ramal = '';
    END

    -- 5. Substituir as variáveis (placeholders) no template HTML
    SET @rendered_html = @signature_html_template;
    SET @rendered_html = REPLACE(@rendered_html, N'{{NomeCompleto}}', ISNULL(@user_nome, N''));
    SET @rendered_html = REPLACE(@rendered_html, N'{{Cargo}}', ISNULL(@user_cargo, N''));
    SET @rendered_html = REPLACE(@rendered_html, N'{{Setor}}', ISNULL(@user_setor, N''));
    SET @rendered_html = REPLACE(@rendered_html, N'{{Empresa}}', ISNULL(@user_empresa, N''));
    SET @rendered_html = REPLACE(@rendered_html, N'{{Telefone}}', ISNULL(@user_telefone, N''));
    -- Adicionar lógica para ramal (ex: " R. {{Ramal}}" se ramal existir)
    SET @rendered_html = REPLACE(@rendered_html, N'{{Ramal}}', 
        CASE 
            WHEN NULLIF(LTRIM(RTRIM(@user_ramal)), N'') IS NOT NULL 
            THEN CONCAT(N' R. ', @user_ramal)
            ELSE N''
        END
    );
    SET @rendered_html = REPLACE(@rendered_html, N'{{Email}}', @user_email);

    -- Retornar o HTML renderizado
    RETURN @rendered_html;
END
GO
PRINT 'Function [dbo].[GetRenderedSignature] criada com sucesso.';
GO

-- Procedure para criar/atualizar sessão administrativa
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ManageAdminSession]') AND type in (N'P'))
BEGIN
    DROP PROCEDURE [dbo].[ManageAdminSession];
    PRINT 'Procedure [dbo].[ManageAdminSession] existente removida.';
END
GO

CREATE PROCEDURE [dbo].[ManageAdminSession]
    @user_id INT,
    @token NVARCHAR(255),
    @expires_at DATETIME,
    @ip_address NVARCHAR(45) = NULL,
    @user_agent NVARCHAR(255) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- Limpar sessões expiradas
        DELETE FROM [dbo].[admin_sessions]
        WHERE [expires_at] <= GETDATE();

        -- Usar MERGE para upsert da sessão
        MERGE [dbo].[admin_sessions] AS target
        USING (SELECT @user_id AS user_id) AS source
        ON (target.[user_id] = source.user_id)
        WHEN MATCHED THEN
            UPDATE SET 
                [token] = @token,
                [expires_at] = @expires_at,
                [ip_address] = @ip_address,
                [user_agent] = @user_agent
        WHEN NOT MATCHED THEN
            INSERT ([user_id], [token], [expires_at], [ip_address], [user_agent], [created_at])
            VALUES (@user_id, @token, @expires_at, @ip_address, @user_agent, GETDATE());

        COMMIT TRANSACTION;
        
        -- Log usando FORMATMESSAGE ao invés de concatenação
        DECLARE @log_message NVARCHAR(200);
        SET @log_message = FORMATMESSAGE(N'Sessão administrativa atualizada para user_id: %d', @user_id);
        RAISERROR(@log_message, 10, 1) WITH NOWAIT;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        THROW;
    END CATCH
END
GO
PRINT 'Procedure [dbo].[ManageAdminSession] criada com sucesso.';
GO

PRINT '=============================================================='
PRINT 'Script de criação/atualização do banco de dados finalizado.'
PRINT 'Todas as tabelas, índices, procedures e functions foram verificados/criados.'
PRINT '=============================================================='
GO
