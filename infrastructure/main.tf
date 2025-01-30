
# Create resource group
resource "azurerm_resource_group" "speech_rg" {
  name     = var.resource_group_name
  location = var.location
}

# Create Azure Speech Service
resource "azurerm_cognitive_account" "speech_service" {
  name                = var.speech_service_name
  location            = azurerm_resource_group.speech_rg.location
  resource_group_name = azurerm_resource_group.speech_rg.name
  kind                = "SpeechServices"
  sku_name            = var.speech_service_sku

  tags = {
    environment = var.environment
  }
}

# Output the speech service key and endpoint
output "speech_key" {
  value     = azurerm_cognitive_account.speech_service.primary_access_key
  sensitive = true
}

output "speech_endpoint" {
  value = azurerm_cognitive_account.speech_service.endpoint
}

# Create .env file with speech key if enabled
resource "local_file" "env_file" {
  count    = var.output_env_file ? 1 : 0
  filename = "${path.module}/../.env"
  content  = <<EOF
export AZURE_SPEECH_KEY=${azurerm_cognitive_account.speech_service.primary_access_key}
export AZURE_SPEECH_ENDPOINT=${azurerm_cognitive_account.speech_service.endpoint}
export AZURE_SPEECH_REGION=${azurerm_resource_group.speech_rg.location}
EOF
}
