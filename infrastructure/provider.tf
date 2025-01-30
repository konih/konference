# Configure the Azure provider
provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
}
