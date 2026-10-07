variable "postgres_admin_username" {
  description = "Administrator username for the PostgreSQL Flexible Server"
  type        = string
}

variable "postgres_admin_password" {
  description = "Administrator password for the PostgreSQL Flexible Server"
  type        = string
  sensitive   = true
}