import logging
import azure.functions as func
from azure.storage.blob import BlobServiceClient
import qrcode
from io import BytesIO
import os
import json
from datetime import datetime

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('QR Code generator triggered.')

    if req.method == "OPTIONS":
        return func.HttpResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    try:
        req_body = req.get_json()
        url = req_body.get("url")
        if not url:
            raise ValueError("URL is missing")
    except Exception as e:
        logging.error(f"Invalid input: {e}")
        return func.HttpResponse("Bad Request", status_code=400)

    try:
        # Generate QR code
        img = qrcode.make(url)
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Upload to Blob Storage
        blob_connection_string = os.getenv("STORAGE_CONNECTION_STRING")
        blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
        container_name = "qr-codes"  # Make sure this container exists in your storage account
        blob_name = f"qr-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.png"

        blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.upload_blob(img_bytes, blob_type="BlockBlob")

        # Return QR code image back to frontend
        img_bytes.seek(0)
        return func.HttpResponse(
            body=img_bytes.read(),
            status_code=200,
            mimetype="image/png",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Content-Disposition": f"inline; filename={blob_name}"
            }
        )
    except Exception as e:
        logging.error(f"Error during QR generation or upload: {e}")
        return func.HttpResponse("Internal Server Error", status_code=500)
