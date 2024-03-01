import boto3
import os


class ObjectStorage():
    def __init__(self):
        self.s3 = boto3.client(service_name=os.environ["OS_SERVICE_NAME"], endpoint_url=os.environ["OS_ENDPOINT_URL"], aws_access_key_id=os.environ["OS_ACCESS_KEY"],
                      aws_secret_access_key=os.environ["OS_SECRET_KEY"])
    
    
    def create_bucket(self, bucket_name):
        self.s3.create_bucket(Bucket=bucket_name)

    def delete_bucket(self, bucket_name):
        self.s3.delete_bucket(Bucket=bucket_name)
    
    def get_bucket_list(self):
        response = self.s3.list_buckets()
        for bucket in response.get('Buckets', []):
            print (bucket.get('Name'))
        
        
    def file_upload(self, bucket_name, path_forder, object_name, local_file_path):
        # bucket_name = 'sample-bucket'

        # create folder
        # object_name = 'sample-folder/'

        self.s3.put_object(Bucket=bucket_name, Key=path_forder)

        # upload file
        # object_name = 'sample-object'
        # local_file_path = '/tmp/test.txt'

        self.s3.upload_file(local_file_path, bucket_name, object_name)
    
    def download_file(self, bucket_name, object_name, local_file_path):
        # bucket_name = 'sample-bucket'
        # object_name = 'sample-object'
        # local_file_path = '/tmp/test.txt'
        self.s3.download_file(bucket_name, object_name, local_file_path)
    
    def delete_file(self, bucket_name, object_name):
        # bucket_name = 'sample-bucket'
        # object_name = 'sample-object'
        self.s3.delete_object(Bucket=bucket_name, Key=object_name)