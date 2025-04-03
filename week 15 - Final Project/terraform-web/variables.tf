variable "region" {
  type = string
  description = "Region that the web server is hosted in"
}

variable "public_subnets" {
  type = list(string)
  description = "Cidr blocks of public subnets in the web vpc"
}

variable "private_subnets" {
  type = list(string)
  description = "Cidr blocks of private subnets in the web vpc"
}