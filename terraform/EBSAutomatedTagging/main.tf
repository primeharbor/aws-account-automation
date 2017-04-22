# EBSAutomatedTagging CloudFormation Lambda Deployment Stack Module

# This is something of a hack since CF can't support lambda in-line larger than 4096.

# What this module does
# 1) Zips up the lambda (How?)
# 1) Uploads the Lambda using aws_s3_bucket_object resource
# 3) Deploys the CF Template found in the ../../cloudformation directory

variable "StackName" {
	type = "string"
	description = "Name of the CloudFormation Stack this TF Module will deploy"
	default = "EBSAutomatedTagging"
}

variable "TagPrefix" {
	type = "string"
	description = "Prefix of the Tags added to the EBS Volumes"
	default = "EBS-Tagger"
}

variable "LambdaFunctionName" {
	type = "string"
	description = "Name of the Lambda Function to deploy"
	default = "ebs-tagger"
}

variable "LambdaAlias" {
	type = "string"
	description = "Alias of this Lambda Function"
	default = "prod"
}

variable "ArtifactBucket" {
	type = "string"
	description = "Bucket Holding Lambdas"
}

variable "ArtifactPrefix" {
	type = "string"
	description = "Directory where lambdas are"
    default =  "aws-account-automation"
}

variable "pEBSTaggingLambdaZipFile" {
	type = "string"
	description = "Filename of the Lambda Zip in S3"
	default = "EBSAutomatedTagging.zip"
}

variable "LocalLambdaZipFile" {
	type = "string"
	description = "Path and name to the local Zip File that is then uploaded to S3"
	default = "EBSAutomatedTaggingLambda.zip"
}


# Next thing to fix is using module path everywhere!!!

# First we need to zip the lambda up
data "archive_file" "lambda_zip" {
    type        = "zip"
    source_file  = "${path.module}/../../lambda/tag_ebs.py"
    output_path = "${var.LocalLambdaZipFile}"
}

resource "aws_s3_bucket_object" "lambda_zip" {
  bucket = "${var.ArtifactBucket}"
  key    = "${var.ArtifactPrefix}/${var.pEBSTaggingLambdaZipFile}"
  source = "${var.LocalLambdaZipFile}"
  etag   = "${md5(file(var.LocalLambdaZipFile))}"
}

resource "aws_cloudformation_stack" "EBSAutomatedTaggingStack" {
  name = "${var.StackName}"
  template_body = "${file("${path.module}/../../cloudformation/EBSAutomatedTagging.yaml")}"
  depends_on = ["aws_s3_bucket_object.lambda_zip"]
  capabilities = ["CAPABILITY_NAMED_IAM"]

  parameters {
  	pTagPrefix = "${var.TagPrefix}"
  	pLambdaFunctionName = "${var.LambdaFunctionName}"
  	pLambdaAlias = "${var.LambdaAlias}"
  	pArtifactBucket = "${var.ArtifactBucket}"
  	pArtifactPrefix = "${var.ArtifactPrefix}"
  	pEBSTaggingLambdaZipFile = "${var.pEBSTaggingLambdaZipFile}"
  }
}

output "LambdaArn" {
	value = "${aws_cloudformation_stack.EBSAutomatedTaggingStack.outputs.LambdaArn}"
}