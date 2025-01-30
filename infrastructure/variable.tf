variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "speech-service-rg"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "speech_service_name" {
  description = "Name of the speech service account"
  type        = string
  default     = "speech-service-account"
}

variable "speech_service_sku" {
  description = "SKU for the speech service"
  type        = string
  default     = "S0"
}

variable "environment" {
  description = "Environment tag value"
  type        = string
  default     = "production"
}

variable "output_env_file" {
  description = "Whether to output speech key to .env file"
  type        = bool
  default     = false
}

variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}
