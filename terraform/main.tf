terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=5.0.0"
    }

    azapi = {
      source  = "Azure/azapi"
      version = "~> 2.0"
    }
  }
}

# ---------------------------------------------------------
# Configure Providers
# ---------------------------------------------------------

provider "azurerm" {
  features {}

  subscription_id = file("credentials.txt")
}

provider "azapi" {}

# ---------------------------------------------------------
# Resource Group
# ---------------------------------------------------------

resource "azurerm_resource_group" "urban_city" {
  name     = "urban-city-terraform-dev"
  location = "uksouth"
}

# ---------------------------------------------------------
# Storage Account
# ---------------------------------------------------------

resource "azurerm_storage_account" "urban_city" {
  name                     = "urbancitytfstorage"
  resource_group_name      = azurerm_resource_group.urban_city.name
  location                 = azurerm_resource_group.urban_city.location
  account_kind             = "StorageV2"
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = "staging"
    project     = "urban-city-service-request"
    managed_by  = "terraform"
  }
}

# ---------------------------------------------------------
# Bronze Container
# ---------------------------------------------------------

resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_id    = azurerm_storage_account.urban_city.id
  container_access_type = "private"
}

# ---------------------------------------------------------
# Silver Container
# ---------------------------------------------------------

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_id    = azurerm_storage_account.urban_city.id
  container_access_type = "private"
}

# ---------------------------------------------------------
# PostgreSQL Flexible Server
# ---------------------------------------------------------

resource "azurerm_postgresql_flexible_server" "urban_city" {
  name                = "urban-city-postgres"
  resource_group_name = azurerm_resource_group.urban_city.name
  location            = azurerm_resource_group.urban_city.location

  version = "16"

  public_network_access_enabled = true

  administrator_login    = var.postgres_admin_username
  administrator_password = var.postgres_admin_password

  authentication {
    active_directory_auth_enabled = false
    password_auth_enabled         = true
  }

  storage_mb   = 32768
  storage_tier = "P4"

  sku_name = "B_Standard_B1ms"

  depends_on = [
    azurerm_resource_group.urban_city
  ]

  lifecycle {
    ignore_changes = [
      zone
    ]
  }
}

# ---------------------------------------------------------
# PostgreSQL Database
# ---------------------------------------------------------

resource "azurerm_postgresql_flexible_server_database" "urban_city" {
  name      = "urban_city"
  server_id = azurerm_postgresql_flexible_server.urban_city.id
  collation = "en_US.utf8"
  charset   = "UTF8"

  lifecycle {
    prevent_destroy = true
  }
}

# ---------------------------------------------------------
# Data Factory - Storage Account Lookup
# ---------------------------------------------------------

data "azurerm_storage_account" "urban_city" {
  name                = azurerm_storage_account.urban_city.name
  resource_group_name = azurerm_resource_group.urban_city.name
}

# ---------------------------------------------------------
# Azure Data Factory
# ---------------------------------------------------------

resource "azurerm_data_factory" "urban_city" {
  name                = "urban-city-terraform-adf"
  location            = azurerm_resource_group.urban_city.location
  resource_group_name = azurerm_resource_group.urban_city.name

  identity {
    type = "SystemAssigned"
  }

  public_network_enabled = true

  tags = {
    environment = "development"
    project     = "urban-city-service-request"
    managed_by  = "terraform"
  }

  depends_on = [
    azurerm_resource_group.urban_city
  ]
}

# ---------------------------------------------------------
# ADF Linked Service - Azure Blob Storage
# ---------------------------------------------------------

resource "azurerm_data_factory_linked_service_azure_blob_storage" "urban_city" {
  name            = "ls_urban_city_storage"
  data_factory_id = azurerm_data_factory.urban_city.id

  connection_string = data.azurerm_storage_account.urban_city.primary_connection_string
}

# ---------------------------------------------------------
# ADF Dataset - Silver Parquet
# ---------------------------------------------------------

resource "azurerm_data_factory_dataset_parquet" "urban_city_silver" {
  name                = "ds_urban_city_silver_parquet"
  data_factory_id     = azurerm_data_factory.urban_city.id
  linked_service_name = azurerm_data_factory_linked_service_azure_blob_storage.urban_city.name

  compression_codec = "snappy"

  azure_blob_fs_location {
    file_system = "silver"
    filename    = "urban_service_requests.parquet"
  }
}

# ---------------------------------------------------------
# PostgreSQL Firewall Rule
# Allow Azure Services to Reach PostgreSQL
# ---------------------------------------------------------

resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_postgresql_flexible_server.urban_city.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# ---------------------------------------------------------
# EXISTING ADF Linked Service - Azure PostgreSQL
#
# This is the existing resource already deployed.
# We are intentionally leaving its body unchanged.
# ---------------------------------------------------------

resource "azapi_resource" "urban_city_postgresql_linked_service" {
  type      = "Microsoft.DataFactory/factories/linkedservices@2018-06-01"
  name      = "ls_urban_city_postgresql"
  parent_id = azurerm_data_factory.urban_city.id

  schema_validation_enabled = false

  ignore_body_changes = [
    "properties"
  ]

  body = {
    properties = {
      type    = "AzurePostgreSql"
      version = "2.0"

      typeProperties = {
        server             = azurerm_postgresql_flexible_server.urban_city.fqdn
        port               = 5432
        database           = azurerm_postgresql_flexible_server_database.urban_city.name
        sslMode            = 2
        username           = var.postgres_admin_username
        authenticationType = "BasicAuth"

        password = {
          type  = "SecureString"
          value = var.postgres_admin_password
        }
      }
    }
  }

  depends_on = [
    azurerm_postgresql_flexible_server_firewall_rule.allow_azure_services
  ]
}

# ---------------------------------------------------------
# NEW ADF Linked Service - Generic PostgreSQL V2
# ---------------------------------------------------------

resource "azapi_resource" "urban_city_postgresql_v2_linked_service" {
  type      = "Microsoft.DataFactory/factories/linkedservices@2018-06-01"
  name      = "ls_urban_city_postgresql_v2"
  parent_id = azurerm_data_factory.urban_city.id

  schema_validation_enabled = false

  body = {
    properties = {
      type = "PostgreSqlV2"

      typeProperties = {
        server   = azurerm_postgresql_flexible_server.urban_city.fqdn
        port     = 5432
        database = azurerm_postgresql_flexible_server_database.urban_city.name
        username = var.postgres_admin_username

        password = {
          type  = "SecureString"
          value = var.postgres_admin_password
        }

        sslmode            = 2
        authenticationType = "Basic"
      }
    }
  }

  depends_on = [
    azurerm_postgresql_flexible_server_firewall_rule.allow_azure_services
  ]
}

# ---------------------------------------------------------
# ADF Dataset - Generic PostgreSQL V2
# ---------------------------------------------------------

resource "azapi_resource" "urban_city_postgresql_dataset" {
  type      = "Microsoft.DataFactory/factories/datasets@2018-06-01"
  name      = "ds_urban_city_postgresql"
  parent_id = azurerm_data_factory.urban_city.id

  schema_validation_enabled = false

  body = {
    properties = {
      type = "PostgreSqlV2Table"

      linkedServiceName = {
        referenceName = azapi_resource.urban_city_postgresql_v2_linked_service.name
        type          = "LinkedServiceReference"
      }

      typeProperties = {
        schema = "staging"
        table  = "urban_city_requests"
      }
    }
  }

  depends_on = [
    azapi_resource.urban_city_postgresql_v2_linked_service
  ]
}