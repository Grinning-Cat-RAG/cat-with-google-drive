# Cat with Google Drive Plugin

This plugin enables the Grinning Cat Core to ingest documents from Google Drive into its knowledge base (RabbitHole). It supports both individual files and entire folders, recursively processing all content.

## Features

- 🔐 **Secure Authentication**: Uses Google Service Account for secure API access
- 📁 **Recursive Folder Processing**: Automatically processes all files within folders and subfolders
- 📄 **Google Docs Support**: Automatically exports Google Workspace documents (Docs, Sheets, etc.) to PDF format
- 🔄 **Background Processing**: Ingestion happens asynchronously without blocking the API
- 📊 **Metadata Tracking**: Files are tagged with their Google Drive ID for reference

## Installation

### Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with Drive API enabled
2. **Service Account**: Create a service account with appropriate permissions
3. **Service Account JSON Key**: Download the JSON key file for your service account

### Setup Steps

1. **Enable Google Drive API**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create or select a project
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API" and enable it

2. **Create Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Grant appropriate roles (e.g., "Viewer" for read-only access)
   - Create and download the JSON key file

3. **Share Drive Content**:
   - Share the Google Drive folders/files you want to ingest with the service account email
   - The service account email looks like: `your-service-account@your-project.iam.gserviceaccount.com`
   - Grant at least "Viewer" permissions

4. **Configure Plugin**:
   - Install the plugin in Grinning Cat Core
   - Navigate to plugin settings
   - Paste the entire content of your Service Account JSON key file into the "Google Service Account JSON" field, as a JSON-formatted string
   - Save the settings

## Configuration

### Settings

| Setting                | Description                                                         | Required |
|------------------------|---------------------------------------------------------------------|----------|
| `service_account_json` | The complete JSON content from your Google Service Account key file | Yes      |

The Service Account JSON is encrypted when stored in the database for security.

## Usage

### API Endpoint

The plugin exposes a REST API endpoint to trigger ingestion:

**Endpoint**: `POST /drive/ingest`

**Request Body**:
```json
{
  "drive_id": "your-google-drive-file-or-folder-id"
}
```

**Response**:
```json
{
  "drive_id": "your-google-drive-file-or-folder-id",
  "message": "Ingestion started for the Drive object.",
  "info": "The processing of resource(s) is happening in the background. Check logs for details."
}
```

### Getting Google Drive IDs

You can find the Drive ID in the URL when viewing a file or folder:

- File: `https://drive.google.com/file/d/{FILE_ID}/view`
- Folder: `https://drive.google.com/drive/folders/{FOLDER_ID}`

### Example Usage

#### Using cURL

```bash
curl -X POST "http://your-cat-instance/drive/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "drive_id": "1abc123def456ghi789jkl"
  }'
```

#### Using Python

```python
import requests

response = requests.post(
    "http://your-cat-instance/drive/ingest",
    json={"drive_id": "1abc123def456ghi789jkl"}
)
print(response.json())
```

## How It Works

1. **Request Received**: The endpoint receives a Google Drive ID (file or folder)
2. **Background Task**: Processing is delegated to a background task
3. **Recursive Processing**: 
   - If it's a folder, the plugin recursively explores all subfolders
   - Each file is downloaded to a temporary location
   - Google Workspace files are automatically exported to PDF
4. **Ingestion**: Each file is passed to the RabbitHole for processing
5. **Cleanup**: Temporary files are deleted after ingestion
6. **Metadata**: Files are tagged with their Google Drive ID for reference

## Supported File Types

- All file types supported by Grinning Cat Core's RabbitHole
- Google Workspace documents (automatically converted to PDF):
  - Google Docs
  - Google Sheets
  - Google Slides
  - Google Drawings
  - And other Google Apps formats

## Security

- **Encrypted Storage**: Service Account credentials are encrypted in the database
- **Background Processing**: Large ingestion tasks don't block the API
- **Permission Checks**: Requires WRITE permission on UPLOAD resource
- **Service Account Isolation**: Uses service account credentials instead of user OAuth

## Troubleshooting

### Common Issues

1. **"Google Service Account JSON not configured"**
   - Ensure you've configured the plugin settings with valid Service Account JSON

2. **"Permission denied" errors**
   - Verify the service account email has access to the Drive content
   - Check that the Drive API is enabled in your Google Cloud project

3. **Files not being ingested**
   - Check the application logs for detailed error messages
   - Verify the Drive ID is correct
   - Ensure the file types are supported by RabbitHole

4. **Background task fails silently**
   - Monitor application logs for background task errors
   - Check temporary directory permissions

### Debugging

Enable detailed logging to track the ingestion process:
- Look for messages starting with "Explore the Google Drive folder"
- Check for "File downloaded" and "Starting the ingestion to the RabbitHole"
- Monitor for any error messages in the logs

## Dependencies

This plugin requires the following Python packages (automatically installed):
- `google-api-python-client`: Google API client library
- `google-auth-httplib2`: HTTP library for Google Auth
- `google-auth-oauthlib`: OAuth library for Google Auth
- `google-api-python-client-stubs`: Type stubs for better IDE support

## Permissions

This plugin requires:
- **Resource**: `UPLOAD`
- **Permission**: `WRITE`

## Limitations

- Processing large folders may take considerable time
- Google Workspace files are converted to PDF (original formatting may vary)
- Requires service account to have access to the Drive content
- Background tasks are not cancelable once started

## Contributing

To contribute to this plugin, please follow the Grinning Cat Core contribution guidelines.

## License

This plugin follows the same license as Grinning Cat Core.

## Support

For issues, questions, or contributions, please refer to the main Grinning Cat Core repository.

