import boto3

CHOICE_IMAGE_BUCKET = "metabet-choice-uploads"
UPLOAD_FOLDER = "uploads"

def upload_files(file_names, bucket):
    responses = []
    s3_client = boto3.client('s3')
    for file_name in file_names:
        object_name = file_name
        responses.append(s3_client.upload_file(file_name, bucket, object_name))
    print("s3 responses: " +responses)
    return responses
