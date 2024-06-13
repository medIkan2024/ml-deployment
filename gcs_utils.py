from google.cloud import storage

def upload_image_to_gcs(image, bucket_name, destination_blob_name, content_type):
    client = storage.Client.from_service_account_json("key.json")
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload image data
    blob.upload_from_string(image, content_type=content_type)

    # Make the image publicly accessible
    blob.make_public()

    # Return the public URL of the uploaded image
    return blob.public_url
